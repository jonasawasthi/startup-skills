#!/usr/bin/env python3
"""Re-verify every URL cited in knowledge/ and in the shark-tank investor profiles (front matter and links).

Checks HTTP status *and* page title, because some sites (e.g. the YC Library)
route by ID prefix and return 200 for a wrong slug, and others (e.g. closed
firms' blogs) redirect every old URL to their homepage.  When a knowledge file
lists ``sources:`` in its front matter with a ``title`` per URL, the live page
title must contain most of the expected title's significant words.  Usage:
    python3 scripts/check_links.py [--only-frontmatter] [--timeout 15]
"""
import argparse
import concurrent.futures as cf
import glob
import html
import os
import re
import sys
import urllib.parse
import urllib.request
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_RE = re.compile(r"https?://[^\s)>\]\"'`]+")
UA = "Mozilla/5.0 (compatible; startup-skills-linkcheck/1.0)"
# investor profiles: their `sources:` are re-verified by title like the knowledge base
INVESTORS = os.path.join(ROOT, "skills", "investor-panel-evaluator", "investors")


def _files():
    """knowledge/ files, then investor profiles (README.md in the library is not a profile)."""
    out = glob.glob(os.path.join(ROOT, "knowledge", "**", "*.md"), recursive=True)
    out += [p for p in sorted(glob.glob(os.path.join(INVESTORS, "*.md")))
            if os.path.basename(p).lower() != "readme.md"]
    return out


def expected_titles():
    """url -> expected title, from `sources:` lists in knowledge and investor-profile front matter."""
    import yaml
    out = {}
    for p in _files():
        text = open(p, encoding="utf-8").read()
        if not text.startswith("---"):
            continue
        try:
            fm = yaml.safe_load(text.split("\n---", 1)[0][3:]) or {}
        except yaml.YAMLError:
            continue
        for s in fm.get("sources") or []:
            if isinstance(s, dict) and s.get("url") and s.get("title"):
                out[str(s["url"])] = str(s["title"])
    return out


def _words(s):
    s = s.lower().replace("’", "'").replace("‘", "'")
    return [w for w in re.findall(r"[a-z0-9]+", s.replace("'", "")) if len(w) > 2]


def title_matches(expected, actual, threshold=0.6):
    """True when most significant words of the expected title appear in the live title."""
    want = set(_words(expected))
    if not want:
        return True
    have = set(_words(actual))
    return len(want & have) / len(want) >= threshold


def collect(only_fm):
    urls = {}
    for p in _files():
        text = open(p, encoding="utf-8").read()
        scope = text.split("\n---", 2)[1] if (only_fm and text.startswith("---")) else text
        for u in URL_RE.findall(scope):
            u = u.rstrip(".,;")
            urls.setdefault(u, set()).add(os.path.relpath(p, ROOT))
    return urls


META_TITLE_RE = re.compile(r"<meta\b[^>]*>", re.I)
PDF = "(PDF: status checked, no title to compare)"


def page_titles(body):
    """The page's <title>, then its og:title and twitter:title (many sites share one generic <title> across
    pages and carry the real headline only in these meta tags)."""
    out = []
    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    if m:
        out.append(html.unescape(m.group(1).strip()))
    for tag in META_TITLE_RE.findall(body):
        key = re.search(r"""(?:property|name)\s*=\s*["']((?:og|twitter):title)["']""", tag, re.I)
        val = re.search(r"""content\s*=\s*(?:"([^"]*)"|'([^']*)')""", tag, re.I | re.S)
        if key and val:
            t = html.unescape((val.group(1) if val.group(1) is not None else val.group(2)).strip())
            if t and t not in out:
                out.append(t)
    return out


def any_title_matches(expected, titles):
    return any(title_matches(expected, t) for t in titles) if titles else title_matches(expected, "")


def fetch(u, timeout):
    """(status, <title> or error text, [all candidate titles])"""
    try:
        # non-ASCII paths ("₹6650") are percent-encoded; a PDF has no title, so only its status is checked
        req = urllib.request.Request(urllib.parse.quote(u, safe=":/?#[]@!$&'()*+,;=%~"), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if "pdf" in (r.headers.get("Content-Type") or "").lower():
                return r.status, PDF, [PDF]
            raw = r.read(400_000)
            if (r.headers.get("Content-Encoding") or "").lower() == "gzip" or raw[:2] == b"\x1f\x8b":
                raw = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(raw)    # sent compressed unasked
            body = raw.decode("utf-8", "ignore")
            m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
            return r.status, html.unescape(m.group(1).strip()) if m else "", page_titles(body)
    except urllib.error.HTTPError as e:
        return e.code, "", []
    except Exception as e:  # network errors
        return 0, str(e)[:80], []


def slug_matches(u, title):
    m = re.search(r"ycombinator\.com/library/[A-Za-z0-9]+-([a-z0-9-]+)", u)
    if not m:
        return True
    words = [w for w in m.group(1).split("-") if len(w) > 3][:3]
    t = title.lower()
    return all(w in t.replace("'", "").replace("’", "") for w in words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-frontmatter", action="store_true")
    ap.add_argument("--timeout", type=int, default=15)
    a = ap.parse_args()
    urls = collect(a.only_frontmatter)
    titles = expected_titles()
    bad = 0
    with cf.ThreadPoolExecutor(8) as ex:
        results = dict(zip(urls, ex.map(lambda u: fetch(u, a.timeout), urls)))
    for u in sorted(urls):
        status, title, alts = results[u]
        ok = 200 <= status < 400 and slug_matches(u, title) and (
            u not in titles or title == PDF or title_matches(titles[u], title) or any_title_matches(titles[u], alts))
        flag = "OK  " if ok else ("BLOCK" if status in (401, 403, 429) else "NET " if status == 0 else "FAIL")
        if flag == "FAIL":
            bad += 1
        print(f"{flag} {status:>3} {u}  — {title[:70]}")
        if 200 <= status < 400 and u in titles and title != PDF and not (title_matches(titles[u], title)
                                                         or any_title_matches(titles[u], alts)):
            print(f"        expected title: {titles[u]}")
        if flag != "OK  ":
            print(f"        cited in: {', '.join(sorted(urls[u]))}")
    print(f"\n{len(urls)} URLs checked, {bad} failing (NET = network/TLS error on this machine, re-check with curl; BLOCK = bot protection)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
