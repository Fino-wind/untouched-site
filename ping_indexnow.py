#!/usr/bin/env python3
"""Tell IndexNow (Bing, Yandex, Seznam, Naver…) that pages changed. Run AFTER a deploy is live.

    python3 ping_indexnow.py            # every URL in sitemap.xml
    python3 ping_indexnow.py /guides/   # just these paths

Why it matters for GEO: ChatGPT search and Copilot lean on Bing's index, and IndexNow gets a
changed page recrawled in minutes instead of whenever Bing gets round to it.
The key file (<key>.txt at the site root) proves we own the host; its value lives in src/facts.json.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
facts = json.loads((ROOT / "src" / "facts.json").read_text())
site = facts["site_url"].rstrip("/")
key = facts["indexnow_key"]
host = re.sub(r"^https?://", "", site)

if len(sys.argv) > 1:
    urls = [site + p for p in sys.argv[1:]]
else:
    urls = re.findall(r"<loc>(.*?)</loc>", (ROOT / "sitemap.xml").read_text())

body = json.dumps({"host": host, "key": key, "keyLocation": f"{site}/{key}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"IndexNow: HTTP {r.status} for {len(urls)} URLs (200/202 = accepted)")
except urllib.error.HTTPError as e:
    print(f"IndexNow: HTTP {e.code} {e.read().decode(errors='replace')[:300]}")
    sys.exit(1)
