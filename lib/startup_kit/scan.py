"""Codebase intelligence: a read-only, evidence-producing inventory of a startup repository.

The scanner does not decide what a product *is*.  It collects facts with file
paths so that the analyst (Claude) can read the right files and classify each
product with evidence.  Safety rules:

* never opens ``.env`` / credential files; only ``.env.example``-style files, and
  then only variable *names* are reported;
* skips dependency, build and VCS directories;
* caps file sizes and counts so huge repos stay fast.
"""
from __future__ import annotations

import datetime as _dt
import fnmatch
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from typing import Dict, List, Optional

SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", ".turbo", ".vercel", "coverage", "vendor", ".venv",
             "venv", "__pycache__", ".cache", ".expo", "ios/Pods", "Pods", ".gradle", "target", "out", ".svelte-kit",
             ".nuxt", ".output", "storybook-static", ".idea", ".vscode", "tmp", ".pnpm-store", ".yarn"}
SECRET_PATTERNS = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.keystore", "*.jks", "id_rsa*", "credentials*",
                   "*secret*", "service-account*.json", "*.mobileprovision"]
ENV_EXAMPLES = (".env.example", ".env.sample", ".env.template", ".env.local.example", ".env.example.local",
                "env.example", ".env.dist")
CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".rb", ".php", ".go", ".rs", ".java", ".kt",
            ".swift", ".dart", ".vue", ".svelte", ".sql", ".prisma", ".cs"}
MAX_FILE = 400_000
MAX_FILES = 25_000

FRAMEWORKS = {
    "next": "Next.js", "react": "React", "vite": "Vite", "expo": "Expo (React Native)", "react-native": "React Native",
    "express": "Express", "@nestjs/core": "NestJS", "hono": "Hono", "fastify": "Fastify", "nuxt": "Nuxt",
    "vue": "Vue", "svelte": "Svelte", "@sveltejs/kit": "SvelteKit", "@remix-run/react": "Remix", "astro": "Astro",
    "electron": "Electron", "@medusajs/medusa": "Medusa", "@medusajs/framework": "Medusa", "trpc": "tRPC",
    "@trpc/server": "tRPC", "drizzle-orm": "Drizzle ORM", "prisma": "Prisma", "@prisma/client": "Prisma",
    "mongoose": "Mongoose", "typeorm": "TypeORM", "sequelize": "Sequelize", "tailwindcss": "Tailwind CSS",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "rails": "Rails", "laravel/framework": "Laravel",
}

INTEGRATIONS = {
    # payments
    "stripe": "Stripe (payments)", "@stripe/stripe-js": "Stripe (payments)", "razorpay": "Razorpay (payments)",
    "khalti": "Khalti (payments, Nepal)", "esewa": "eSewa (payments, Nepal)", "fonepay": "Fonepay (payments, Nepal)",
    "paypal": "PayPal (payments)", "@paypal/checkout-server-sdk": "PayPal (payments)", "lemonsqueezy": "Lemon Squeezy",
    "@lemonsqueezy/lemonsqueezy.js": "Lemon Squeezy", "paddle": "Paddle", "revenuecat": "RevenueCat",
    "react-native-purchases": "RevenueCat (in-app purchases)",
    # auth
    "next-auth": "NextAuth/Auth.js", "@auth/core": "Auth.js", "@clerk/nextjs": "Clerk (auth)", "better-auth": "Better Auth",
    "lucia": "Lucia (auth)", "firebase": "Firebase", "firebase-admin": "Firebase Admin", "@supabase/supabase-js": "Supabase",
    # comms
    "twilio": "Twilio", "resend": "Resend (email)", "@sendgrid/mail": "SendGrid (email)", "nodemailer": "Nodemailer (email)",
    "postmark": "Postmark (email)", "expo-notifications": "Expo push notifications", "onesignal": "OneSignal",
    "firebase-messaging": "FCM", "@react-native-firebase/messaging": "FCM",
    # realtime / media
    "livekit-client": "LiveKit (real-time A/V)", "livekit-server-sdk": "LiveKit (real-time A/V)",
    "@livekit/components-react": "LiveKit", "agora-rtc-sdk-ng": "Agora (real-time A/V)", "socket.io": "Socket.IO",
    "pusher": "Pusher", "ably": "Ably", "@mux/mux-node": "Mux (video)", "cloudinary": "Cloudinary (media)",
    "@aws-sdk/client-s3": "AWS S3", "aws-sdk": "AWS SDK", "@vercel/blob": "Vercel Blob", "uploadthing": "UploadThing",
    "@cloudflare/workers-types": "Cloudflare Workers", "wrangler": "Cloudflare Workers",
    # data / infra
    "@neondatabase/serverless": "Neon (Postgres)", "pg": "PostgreSQL", "postgres": "PostgreSQL", "mysql2": "MySQL",
    "redis": "Redis", "ioredis": "Redis", "@upstash/redis": "Upstash Redis", "bullmq": "BullMQ (jobs)",
    "inngest": "Inngest (jobs)", "@trigger.dev/sdk": "Trigger.dev (jobs)", "meilisearch": "Meilisearch",
    "algoliasearch": "Algolia (search)", "@elastic/elasticsearch": "Elasticsearch",
    # analytics / monitoring
    "posthog-js": "PostHog (analytics)", "posthog-node": "PostHog (analytics)", "mixpanel": "Mixpanel",
    "@segment/analytics-next": "Segment", "@vercel/analytics": "Vercel Analytics", "@sentry/nextjs": "Sentry",
    "@sentry/node": "Sentry", "@sentry/react-native": "Sentry", "@amplitude/analytics-browser": "Amplitude",
    "react-ga4": "Google Analytics", "@next/third-parties": "Google third-parties (GA/GTM)",
    # AI
    "openai": "OpenAI API", "@anthropic-ai/sdk": "Anthropic API", "ai": "Vercel AI SDK", "@google/generative-ai": "Gemini API",
    "langchain": "LangChain", "replicate": "Replicate",
    # maps / misc
    "mapbox-gl": "Mapbox", "@react-google-maps/api": "Google Maps", "react-native-maps": "Maps (RN)",
}

REVENUE_TERMS = ["checkout", "subscription", "subscribe", "payment", "payout", "invoice", "commission", "platform_fee",
                 "platformFee", "take_rate", "pricing", "price", "plan", "tier", "wallet", "refund", "billing", "tip",
                 "donation", "membership", "settlement", "fee"]
UNFINISHED_TERMS = re.compile(r"\b(TODO|FIXME|HACK|XXX|WIP|coming soon|not implemented|NotImplemented|placeholder|"
                              r"lorem ipsum|mock data|dummy)\b", re.I)
ANALYTICS_CALL = re.compile(r"\b(?:posthog\.capture|analytics\.track|mixpanel\.track|gtag\(|track(?:Event)?\()\s*\(?\s*['\"]([\w .:/-]{2,60})['\"]")
ROLE_ENUM = re.compile(r"(?:pgEnum|mysqlEnum|enum)\s*\(?\s*['\"]?(\w*role\w*)['\"]?\s*,?\s*\[([^\]]{1,400})\]", re.I)
PRISMA_ENUM = re.compile(r"enum\s+(\w*Role\w*)\s*\{([^}]*)\}", re.I)
DRIZZLE_TABLE = re.compile(r"(?:pgTable|mysqlTable|sqliteTable)\s*\(\s*['\"]([\w-]+)['\"]")
PRISMA_MODEL = re.compile(r"^model\s+(\w+)\s*\{", re.M)
SQL_TABLE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?[`\"]?(?:\w+[`\"]?\.[`\"]?)?(\w+)", re.I)
DJANGO_MODEL = re.compile(r"^class\s+(\w+)\((?:models\.)?Model\)", re.M)
URL_RE = re.compile(r"https?://[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s'\"`)<>]*)?", re.I)


def _is_secret(name: str) -> bool:
    low = name.lower()
    if low in ENV_EXAMPLES:
        return False
    return any(fnmatch.fnmatch(low, p) for p in SECRET_PATTERNS)


def _read(path: str) -> str:
    try:
        if os.path.getsize(path) > MAX_FILE:
            return ""
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def _git(repo: str, *args) -> str:
    try:
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def walk(repo: str):
    count = 0
    for root, dirs, files in os.walk(repo):
        rel_root = os.path.relpath(root, repo)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".git")
                         and os.path.join(rel_root, d).replace("./", "") not in SKIP_DIRS)
        for fn in sorted(files):
            count += 1
            if count > MAX_FILES:
                return
            yield os.path.join(root, fn)


def _units(repo: str) -> Dict[str, str]:
    """Deployable units: directories containing a manifest (package.json, pyproject, etc.)."""
    units = {}
    manifests = ("package.json", "pyproject.toml", "requirements.txt", "Gemfile", "composer.json", "go.mod",
                 "Cargo.toml", "pubspec.yaml")
    for path in walk(repo):
        if os.path.basename(path) in manifests:
            d = os.path.dirname(path)
            rel = os.path.relpath(d, repo)
            units.setdefault(rel, path)
    return units


def _unit_for(rel_path: str, unit_dirs: List[str]) -> str:
    best = "."
    for u in unit_dirs:
        if u == ".":
            continue
        if rel_path == u or rel_path.startswith(u + os.sep):
            if len(u) > len(best) or best == ".":
                best = u
    return best


def _next_routes(unit_abs: str) -> List[str]:
    routes = []
    for base in ("app", "src/app"):
        root = os.path.join(unit_abs, base)
        if not os.path.isdir(root):
            continue
        for path in walk(root):
            fn = os.path.basename(path)
            if re.fullmatch(r"(page|route)\.(tsx|ts|jsx|js|mdx)", fn):
                rel = os.path.relpath(os.path.dirname(path), root)
                parts = [p for p in rel.split(os.sep) if p != "." and not (p.startswith("(") and p.endswith(")"))
                         and not p.startswith("@")]
                r = "/" + "/".join(parts)
                routes.append(r + (" [api]" if fn.startswith("route") else ""))
    for base in ("pages", "src/pages"):
        root = os.path.join(unit_abs, base)
        if not os.path.isdir(root):
            continue
        for path in walk(root):
            fn = os.path.basename(path)
            if re.search(r"\.(tsx|ts|jsx|js)$", fn) and not fn.startswith("_"):
                rel = os.path.relpath(path, root)
                r = "/" + re.sub(r"(/?index)?\.(tsx|ts|jsx|js)$", "", rel)
                routes.append(r + (" [api]" if rel.startswith("api") else ""))
    return sorted(set(routes))


def _expo_routes(unit_abs: str) -> List[str]:
    root = os.path.join(unit_abs, "app")
    routes = []
    if os.path.isdir(root) and os.path.exists(os.path.join(unit_abs, "app.json")):
        for path in walk(root):
            fn = os.path.basename(path)
            if re.search(r"\.(tsx|jsx)$", fn) and not fn.startswith("_"):
                rel = os.path.relpath(path, root)
                routes.append("/" + re.sub(r"(/?index)?\.(tsx|jsx)$", "", rel))
    return sorted(set(routes))


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()[:120]
    return ""


def scan(repo: str, max_samples: int = 8) -> Dict:
    repo = os.path.abspath(repo)
    if not os.path.isdir(repo):
        raise FileNotFoundError(repo)
    result: Dict = {"repo": repo, "scanned_at": _dt.datetime.now().isoformat(timespec="seconds"),
                    "generator": "startup-kit scan", "notes": []}

    # ---- git ----
    git = {}
    if _git(repo, "rev-parse", "--is-inside-work-tree") == "true":
        git["branch"] = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        git["commits"] = int(_git(repo, "rev-list", "--count", "HEAD") or 0)
        git["first_commit"] = (_git(repo, "log", "--reverse", "--format=%ad", "--date=short") or "\n").split("\n")[0]
        git["last_commit"] = _git(repo, "log", "-1", "--format=%ad %s", "--date=short")
        git["contributors"] = len(set(_git(repo, "log", "--format=%ae").splitlines()))
        since = _git(repo, "log", "--since=90.days", "--name-only", "--format=")
        top = Counter()
        for line in since.splitlines():
            if line.strip():
                parts = line.split("/")
                top["/".join(parts[:2]) if parts[0] in ("apps", "packages", "services") and len(parts) > 1 else parts[0]] += 1
        git["activity_90d_by_area"] = dict(top.most_common(15))
        git["recent_subjects"] = _git(repo, "log", "-15", "--format=%ad %s", "--date=short").splitlines()
    result["git"] = git

    # ---- workspace & units ----
    units = _units(repo)
    unit_dirs = sorted(units)
    ws = {}
    for f in ("pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json"):
        if os.path.exists(os.path.join(repo, f)):
            ws[f] = _read(os.path.join(repo, f))[:800]
    result["workspace"] = ws

    unit_info: Dict[str, Dict] = {}
    for rel, manifest in units.items():
        info: Dict = {"path": rel, "manifest": os.path.relpath(manifest, repo), "frameworks": [], "integrations": [],
                      "scripts": [], "routes": []}
        if manifest.endswith("package.json"):
            try:
                pkg = json.loads(_read(manifest) or "{}")
            except json.JSONDecodeError:
                pkg = {}
            info["name"] = pkg.get("name")
            info["description"] = pkg.get("description")
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            info["frameworks"] = sorted({v for k, v in FRAMEWORKS.items() if k in deps})
            ints = set()
            for d in deps:
                if d in INTEGRATIONS:
                    ints.add(INTEGRATIONS[d])
                else:
                    for k, v in INTEGRATIONS.items():
                        if k in ("khalti", "esewa", "fonepay") and k in d.lower():
                            ints.add(v)
            info["integrations"] = sorted(ints)
            info["scripts"] = sorted(pkg.get("scripts", {}).keys())
            info["dependency_count"] = len(deps)
        else:
            txt = _read(manifest).lower()
            info["frameworks"] = sorted({v for k, v in FRAMEWORKS.items() if re.search(r"\b" + re.escape(k) + r"\b", txt)})
        abs_u = os.path.join(repo, rel)
        if "Next.js" in info["frameworks"]:
            info["routes"] = _next_routes(abs_u)
        elif any("Expo" in f or "React Native" in f for f in info["frameworks"]):
            info["routes"] = _expo_routes(abs_u)
        for f in ("README.md", "readme.md", "README"):
            if os.path.exists(os.path.join(abs_u, f)):
                info["readme"] = os.path.relpath(os.path.join(abs_u, f), repo)
                info["readme_title"] = _first_heading(_read(os.path.join(abs_u, f)))
        info["has_tests"] = False
        info["deploy"] = [f for f in ("vercel.json", "Dockerfile", "fly.toml", "netlify.toml", "app.json", "eas.json",
                                      "wrangler.toml", "render.yaml", "Procfile", "railway.json", "serverless.yml")
                          if os.path.exists(os.path.join(abs_u, f))]
        info["files"] = 0
        info["loc"] = 0
        unit_info[rel] = info

    # ---- file walk ----
    docs, schemas, env_names, assets, screenshots = [], defaultdict(list), defaultdict(set), [], []
    roles, unfinished, revenue, analytics, urls = {}, defaultdict(list), defaultdict(Counter), Counter(), Counter()
    ext_counter = Counter()
    brand_colors = {}
    skipped_secrets = 0
    for path in walk(repo):
        rel = os.path.relpath(path, repo)
        fn = os.path.basename(path)
        low = fn.lower()
        unit = _unit_for(os.path.dirname(rel), unit_dirs)
        if _is_secret(fn):
            skipped_secrets += 1
            continue
        ext = os.path.splitext(fn)[1].lower()
        ext_counter[ext] += 1
        if unit in unit_info:
            unit_info[unit]["files"] += 1
            if re.search(r"(\.test\.|\.spec\.|_test\.|test_)", low) or "/__tests__/" in rel or "/e2e/" in rel:
                unit_info[unit]["has_tests"] = True
        if low in ENV_EXAMPLES:
            for line in _read(path).splitlines():
                m = re.match(r"\s*(?:export\s+)?([A-Z][A-Z0-9_]{2,})\s*=", line)
                if m:
                    env_names[unit].add(m.group(1))
            continue
        if ext in (".md", ".mdx") and ("docs" in rel.split(os.sep) or low.startswith("readme") or rel.count(os.sep) <= 1):
            txt = _read(path)
            docs.append({"path": rel, "title": _first_heading(txt), "words": len(txt.split())})
            continue
        if ext in (".png", ".jpg", ".jpeg", ".svg", ".webp"):
            if re.search(r"logo|brand|wordmark|icon-512|app-icon", low):
                assets.append(rel)
            elif re.search(r"screenshot|screen|mockup|preview|hero|og-image|opengraph", rel.lower()):
                screenshots.append(rel)
            continue
        if ext not in CODE_EXT and fn not in ("tailwind.config.js", "tailwind.config.ts"):
            if ext in (".css", ".scss"):
                txt = _read(path)
                for m in re.finditer(r"--(primary|brand|accent|secondary)(?:-[\w]+)?\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|[\d.]+ [\d.]+% [\d.]+%|oklch\([^)]*\))", txt):
                    brand_colors.setdefault(f"{rel}: --{m.group(1)}", m.group(2))
            continue
        txt = _read(path)
        if not txt:
            continue
        if unit in unit_info:
            unit_info[unit]["loc"] += txt.count("\n")
        # schemas
        for m in DRIZZLE_TABLE.finditer(txt):
            schemas["drizzle"].append(f"{m.group(1)}  ({rel})")
        if ext == ".prisma":
            for m in PRISMA_MODEL.finditer(txt):
                schemas["prisma"].append(f"{m.group(1)}  ({rel})")
            for m in PRISMA_ENUM.finditer(txt):
                roles[f"{m.group(1)} ({rel})"] = [v.strip() for v in m.group(2).split() if v.strip()]
        if ext == ".sql":
            for m in SQL_TABLE.finditer(txt):
                schemas["sql"].append(f"{m.group(1)}  ({rel})")
        if ext == ".py":
            for m in DJANGO_MODEL.finditer(txt):
                schemas["django"].append(f"{m.group(1)}  ({rel})")
        for m in ROLE_ENUM.finditer(txt):
            vals = re.findall(r"['\"]([\w-]+)['\"]", m.group(2))
            if vals:
                roles[f"{m.group(1)} ({rel})"] = vals
        # unfinished markers
        for i, line in enumerate(txt.splitlines(), 1):
            if UNFINISHED_TERMS.search(line):
                if len(unfinished[unit]) < 400:
                    unfinished[unit].append(f"{rel}:{i}: {line.strip()[:140]}")
        # revenue-related code
        lowtxt = txt.lower()
        for term in REVENUE_TERMS:
            if term.lower() in lowtxt:
                revenue[unit][term] += 1
        for m in ANALYTICS_CALL.finditer(txt):
            analytics[m.group(1)] += 1
        if fn.startswith("tailwind.config"):
            for m in re.finditer(r"(primary|brand|accent)\s*:\s*['\"](#[0-9a-fA-F]{3,6})['\"]", txt):
                brand_colors.setdefault(f"{rel}: {m.group(1)}", m.group(2))
        for m in URL_RE.finditer(txt):
            host = re.sub(r"^https?://", "", m.group(0)).split("/")[0].lower()
            if not re.search(r"(localhost|example\.|schema\.org|w3\.org|github\.com|npmjs|googleapis|cdn|unpkg|"
                             r"jsdelivr|vercel\.app$|fonts\.|reactjs|nextjs|tailwind|mozilla|apple\.com|google\.com|"
                             r"microsoft|stackoverflow|json-schema|openai\.com|anthropic)", host):
                urls[host] += 1

    for u, info in unit_info.items():
        info["env_var_names"] = sorted(env_names.get(u, []))
        info["unfinished_markers"] = len(unfinished.get(u, []))
        info["unfinished_samples"] = unfinished.get(u, [])[:max_samples]
        info["revenue_terms"] = dict(revenue.get(u, Counter()).most_common(10))
    result["units"] = [unit_info[k] for k in sorted(unit_info)]
    result["schemas"] = {k: sorted(set(v)) for k, v in schemas.items()}
    result["roles"] = roles
    result["docs"] = sorted(docs, key=lambda d: d["path"])
    result["brand"] = {"logo_candidates": sorted(assets)[:40], "colors": brand_colors}
    result["screenshots"] = sorted(screenshots)[:60]
    result["analytics_events"] = dict(analytics.most_common(40))
    result["external_hosts"] = dict(urls.most_common(40))
    result["languages"] = dict(ext_counter.most_common(15))
    result["secret_files_skipped"] = skipped_secrets
    result["notes"].append("Scanner output is evidence of what exists in code, not proof that anything is deployed or "
                           "used. 'live' status requires deployment evidence (URL check, store listing, analytics, "
                           "founder confirmation).")
    return result


def to_markdown(r: Dict) -> str:
    L = [f"# Codebase inventory: `{os.path.basename(r['repo'])}`", "",
         f"Scanned {r['scanned_at']} by `{r['generator']}`. Paths are relative to the repository root. "
         "This is raw evidence for analysis; it does not establish what is live.", ""]
    g = r.get("git") or {}
    if g:
        L += ["## Repository activity", "",
              f"- Commits: {g.get('commits')} | first: {g.get('first_commit')} | last: {g.get('last_commit')}",
              f"- Contributors (distinct emails): {g.get('contributors')}", "",
              "Activity in the last 90 days (files changed, by area):", ""]
        L += [f"- `{k}`: {v}" for k, v in g.get("activity_90d_by_area", {}).items()]
        L += ["", "Recent commits:", ""] + [f"- {s}" for s in g.get("recent_subjects", [])] + [""]
    L += ["## Deployable units", "", "| Unit | Name | Frameworks | Integrations | Routes | Files | LOC | Tests | Deploy cfg | TODO-type markers |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for u in r["units"]:
        L.append(f"| `{u['path']}` | {u.get('name') or ''} | {', '.join(u['frameworks'])} | {', '.join(u['integrations'])} | "
                 f"{len(u['routes'])} | {u['files']} | {u['loc']} | {'yes' if u['has_tests'] else 'no'} | "
                 f"{', '.join(u['deploy'])} | {u['unfinished_markers']} |")
    L.append("")
    for u in r["units"]:
        if not (u["routes"] or u["env_var_names"] or u["unfinished_samples"] or u["revenue_terms"]):
            continue
        L += [f"### `{u['path']}` {('(' + u['name'] + ')') if u.get('name') else ''}", ""]
        if u.get("description"):
            L += [f"Manifest description: {u['description']}", ""]
        if u["routes"]:
            shown = u["routes"][:60]
            L += [f"Routes ({len(u['routes'])}):", "", "```", *shown, *(["…"] if len(u["routes"]) > 60 else []), "```", ""]
        if u["env_var_names"]:
            L += ["Environment variable names (values never read): " + ", ".join(f"`{e}`" for e in u["env_var_names"]), ""]
        if u["revenue_terms"]:
            L += ["Revenue-related terms (file counts): " + ", ".join(f"{k} {v}" for k, v in u["revenue_terms"].items()), ""]
        if u["unfinished_samples"]:
            L += ["Unfinished-work markers (sample):", "", "```", *u["unfinished_samples"], "```", ""]
    if r["schemas"]:
        L += ["## Data model", ""]
        for kind, tables in r["schemas"].items():
            L += [f"**{kind}** ({len(tables)}):", "", "```", *tables[:150], "```", ""]
    if r["roles"]:
        L += ["## Roles / enums that look like user roles", ""]
        L += [f"- `{k}`: {', '.join(v)}" for k, v in r["roles"].items()] + [""]
    if r["docs"]:
        L += ["## Documentation", "", "| Path | Title | Words |", "|---|---|---|"]
        L += [f"| `{d['path']}` | {d['title']} | {d['words']} |" for d in r["docs"][:120]] + [""]
    b = r.get("brand", {})
    if b.get("logo_candidates") or b.get("colors"):
        L += ["## Brand assets", ""]
        L += [f"- logo candidate: `{p}`" for p in b.get("logo_candidates", [])]
        L += [f"- colour `{k}` = `{v}`" for k, v in b.get("colors", {}).items()] + [""]
    if r["screenshots"]:
        L += ["## Screenshot candidates", ""] + [f"- `{p}`" for p in r["screenshots"]] + [""]
    if r["analytics_events"]:
        L += ["## Analytics events tracked in code", ""] + [f"- `{k}` ({v})" for k, v in r["analytics_events"].items()] + [""]
    if r["external_hosts"]:
        L += ["## External hosts referenced (possible production domains / services)", ""]
        L += [f"- {k} ({v})" for k, v in r["external_hosts"].items()] + [""]
    L += ["## Scanner notes", "", f"- Secret-like files skipped without reading: {r['secret_files_skipped']}"]
    L += [f"- {n}" for n in r["notes"]]
    return "\n".join(L) + "\n"
