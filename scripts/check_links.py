#!/usr/bin/env python3
"""Check every href and src of the built pages: local files, anchors and external URLs."""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
pages = [ROOT / "index.html"] + sorted(ROOT.glob("*/index.html"))
seen, bad = {}, 0
for page in pages:
    text = page.read_text()
    ids = set(re.findall(r'\bid="([^"]+)"', text))
    for url in set(re.findall(r'(?:href|src|srcset)="([^"]+)"', text)):
        if url.startswith("#"):
            if url[1:] not in ids:
                print(f"{page.relative_to(ROOT)}: no anchor {url}")
                bad += 1
            continue
        if url.startswith("/"):
            path = ROOT / url.split("#")[0].lstrip("/")
            if path.is_dir():
                path = path / "index.html"
            if not path.exists():
                print(f"{page.relative_to(ROOT)}: missing {url}")
                bad += 1
            continue
        if re.fullmatch(r"https://fonts\.(googleapis|gstatic)\.com", url):
            continue  # preconnect hosts, not links
        if url.startswith("http") and url not in seen:
            try:
                req = urllib.request.Request(url, method="GET", headers={"User-Agent": "link-check"})
                seen[url] = urllib.request.urlopen(req, timeout=20).status
            except Exception as e:
                seen[url] = str(e)
            if seen[url] != 200:
                print(f"{url}: {seen[url]}")
                bad += 1
print(f"{len(pages)} pages, {len(seen)} external links, {bad} problems")
sys.exit(1 if bad else 0)
