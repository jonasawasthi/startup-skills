#!/usr/bin/env python3
"""Re-verify every URL cited in knowledge/ (front matter and inline links).

Checks HTTP status *and* page title, because some sites (e.g. the YC Library)
route by ID prefix and return 200 for a wrong slug.  Usage:
    python3 scripts/check_links.py [--only-frontmatter] [--timeout 15]
"""
import argparse
import concurrent.futures as cf
import glob
import html
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_RE = re.compile(r"https?://[^\s)>\]\"'`]+")
UA = "Mozilla/5.0 (compatible; startup-skills-linkcheck/1.0)"


def collect(only_fm):
    urls = {}
    for p in glob.glob(os.path.join(ROOT, "knowledge", "**", "*.md"), recursive=True):
        text = open(p, encoding="utf-8").read()
        scope = text.split("\n---", 2)[1] if (only_fm and text.startswith("---")) else text
        for u in URL_RE.findall(scope):
            u = u.rstrip(".,;")
            urls.setdefault(u, set()).add(os.path.relpath(p, ROOT))
    return urls


def fetch(u, timeout):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(400_000).decode("utf-8", "ignore")
            m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
            return r.status, html.unescape(m.group(1).strip()) if m else ""
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # network errors
        return 0, str(e)[:80]


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
    bad = 0
    with cf.ThreadPoolExecutor(8) as ex:
        results = dict(zip(urls, ex.map(lambda u: fetch(u, a.timeout), urls)))
    for u in sorted(urls):
        status, title = results[u]
        ok = 200 <= status < 400 and slug_matches(u, title)
        flag = "OK  " if ok else ("BLOCK" if status in (401, 403, 429) else "NET " if status == 0 else "FAIL")
        if flag == "FAIL":
            bad += 1
        print(f"{flag} {status:>3} {u}  — {title[:70]}")
        if flag != "OK  ":
            print(f"        cited in: {', '.join(sorted(urls[u]))}")
    print(f"\n{len(urls)} URLs checked, {bad} failing (NET = network/TLS error on this machine, re-check with curl; BLOCK = bot protection)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
