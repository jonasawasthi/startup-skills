import json
import os

from startup_kit.scan import scan, to_markdown

SECRET = "sk_live_THIS_MUST_NEVER_APPEAR"


def make_repo(tmp_path):
    web = tmp_path / "apps" / "web"
    (web / "app" / "creators" / "[slug]").mkdir(parents=True)
    (web / "app" / "api" / "checkout").mkdir(parents=True)
    (web / "app" / "(marketing)" / "pricing").mkdir(parents=True)
    (web / "package.json").write_text(json.dumps({"name": "web", "dependencies": {"next": "15", "stripe": "1",
                                                                                 "drizzle-orm": "1"}}))
    (web / "app" / "page.tsx").write_text("export default function P(){return null}")
    (web / "app" / "creators" / "[slug]" / "page.tsx").write_text("// TODO: payouts\n")
    (web / "app" / "(marketing)" / "pricing" / "page.tsx").write_text("const plan = 'pro'; // coming soon\n")
    (web / "app" / "api" / "checkout" / "route.ts").write_text("export async function POST(){ /* subscription checkout */ }")
    (web / "db.ts").write_text("export const users = pgTable('users', {});\nexport const role = pgEnum('role', ['admin','creator','member']);\n")
    (web / ".env").write_text(f"STRIPE_SECRET_KEY={SECRET}\n")
    (web / ".env.example").write_text("STRIPE_SECRET_KEY=\nNEXT_PUBLIC_SITE_URL=\n")
    (tmp_path / "README.md").write_text("# Demo\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("pgTable('ignored')")
    return tmp_path


def test_scan_inventory(tmp_path):
    r = scan(str(make_repo(tmp_path)))
    unit = next(u for u in r["units"] if u["path"].endswith("web"))
    assert "Next.js" in unit["frameworks"] and "Stripe (payments)" in unit["integrations"]
    assert "/creators/[slug]" in unit["routes"] and "/pricing" in unit["routes"]
    assert "/api/checkout [api]" in unit["routes"]
    assert any("users" in t for t in r["schemas"]["drizzle"])
    assert ["admin", "creator", "member"] in r["roles"].values()
    assert unit["unfinished_markers"] >= 2
    assert "subscription" in unit["revenue_terms"]
    assert not any("ignored" in t for t in r["schemas"]["drizzle"])  # node_modules skipped


def test_scan_never_reads_secrets(tmp_path):
    r = scan(str(make_repo(tmp_path)))
    blob = json.dumps(r) + to_markdown(r)
    assert SECRET not in blob
    unit = next(u for u in r["units"] if u["path"].endswith("web"))
    assert "STRIPE_SECRET_KEY" in unit["env_var_names"]
    assert r["secret_files_skipped"] >= 1
