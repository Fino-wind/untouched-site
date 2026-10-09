#!/usr/bin/env python3
"""Build the Untouched site: src/ -> repo root (GitHub Pages serves main:/).

    python3 build.py          # build + checks; exits non-zero if any check fails

Sources
  src/facts.json   the only place product facts live ({{key}} placeholders)
  src/pages/**     one HTML fragment per page, starting with <!--meta {json} -->
  src/llms.txt     template for /llms.txt
  src/site.css, src/site.js

Everything outside src/, build.py, README.md, CNAME, .nojekyll and assets/ is generated.
Generated files are listed in .build-manifest so pages that disappear from src/ get deleted.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
FACTS = json.loads((SRC / "facts.json").read_text())
SITE = FACTS["site_url"].rstrip("/")
MANIFEST = ROOT / ".build-manifest"

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


# ---------------------------------------------------------------- parsing

META_RE = re.compile(r"\A\s*<!--meta\s*(\{.*?\})\s*-->\s*", re.S)


def load_pages() -> list[dict]:
    pages = []
    for f in sorted((SRC / "pages").rglob("*.html")):
        text = f.read_text()
        m = META_RE.match(text)
        if not m:
            err(f"{f.relative_to(ROOT)}: missing <!--meta {{...}} --> header")
            continue
        meta = json.loads(m.group(1))
        meta["_src"] = f.relative_to(ROOT).as_posix()
        meta["_body"] = text[m.end():]
        for k in ("path", "lang", "title", "description", "type"):
            if k not in meta:
                err(f"{meta['_src']}: meta is missing '{k}'")
        pages.append(meta)
    return pages


# ---------------------------------------------------------------- substitution

PRICE_LITERAL = re.compile(r"\$\s?\d+\.\d\d")


def t(lang: str, en: str, zh: str) -> str:
    return zh if lang == "zh" else en


def badge(lang: str, size: str = "") -> str:
    label = t(lang, "Download Untouched on the App Store", "在 App Store 下载 Untouched")
    return (
        f'<a class="badge-link" href="{FACTS["app_store_url"]}" aria-label="{label}">'
        f'<img src="/assets/app-store-badge.svg" alt="{t(lang, "Download on the App Store", "在 App Store 下载")}" '
        f'width="156" height="52"{size}></a>'
    )


def app_card(lang: str) -> str:
    return (
        '<aside class="app-card">'
        '<img class="icon" src="/assets/icon-128.png" width="64" height="64" alt="">'
        f'<div class="t">{FACTS["app_name"]}</div>'
        + t(
            lang,
            f'<p>Keeps byte-for-byte originals of the photos and videos you choose, in a folder that storage optimization can’t reach. One item free; then {FACTS["price_monthly"]}/month, {FACTS["price_yearly"]}/year or {FACTS["price_lifetime"]} once. iPhone, iOS {FACTS["min_ios"]} or later.</p>',
            f'<p>把你选中的照片和视频原件逐字节留在本机，放在储存优化碰不到的文件夹里。免费保留 1 项；更多：{FACTS["price_monthly"]}/月、{FACTS["price_yearly"]}/年，或一次性 {FACTS["price_lifetime"]}（美区价格）。需要 iOS {FACTS["min_ios"]} 或更高版本的 iPhone。</p>',
        )
        + badge(lang)
        + "</aside>"
    )


def substitute(text: str, lang: str, where: str) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        if key == "badge":
            return badge(lang)
        if key == "app_card":
            return app_card(lang)
        if key in FACTS:
            return html.escape(FACTS[key], quote=False) if (not key.startswith("definition") and not where.endswith(".txt")) else FACTS[key]
        err(f"{where}: unknown placeholder {{{{{key}}}}}")
        return m.group(0)

    return re.sub(r"\{\{\s*([a-z0-9_]+)\s*\}\}", repl, text)


# ---------------------------------------------------------------- structured data

def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


FAQ_RE = re.compile(r'<details class="faq-item"[^>]*>\s*<summary>(.*?)</summary>\s*<div class="answer">(.*?)</div>\s*</details>', re.S)


def faq_entities(body: str) -> list[dict]:
    return [
        {"@type": "Question", "name": strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
        for q, a in FAQ_RE.findall(body)
    ]


def crumbs_for(page: dict) -> list[tuple[str, str]]:
    lang = page["lang"]
    home = ("/zh/" if lang == "zh" else "/", t(lang, "Untouched", "Untouched"))
    trail = [home]
    for name, path in page.get("crumbs", []):
        trail.append((path, name))
    return trail


def jsonld(page: dict, body: str) -> list[dict]:
    lang = page["lang"]
    url = SITE + page["path"]
    graph: list[dict] = []
    publisher = {"@type": "Organization", "name": FACTS["app_name"], "url": SITE + "/", "logo": SITE + "/assets/icon-256.png"}
    if page["type"] == "home":
        graph.append({
            "@type": "MobileApplication",
            "name": FACTS["app_name"],
            "alternateName": FACTS["store_name"],
            "description": FACTS["definition_zh" if lang == "zh" else "definition_en"],
            "operatingSystem": f"iOS {FACTS['min_ios']} or later",
            "applicationCategory": "UtilitiesApplication",
            "applicationSubCategory": "Photo & Video",
            "installUrl": FACTS["app_store_url"],
            "downloadUrl": FACTS["app_store_url"],
            "url": url,
            "image": SITE + "/assets/icon-256.png",
            "screenshot": SITE + "/assets/app-list.webp",
            "inLanguage": ["en", "zh-Hans"],
            "offers": [
                {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "USD", "description": "Keep one item"},
                {"@type": "Offer", "name": "Monthly", "price": FACTS["price_monthly_num"], "priceCurrency": "USD"},
                {"@type": "Offer", "name": "Yearly", "price": FACTS["price_yearly_num"], "priceCurrency": "USD"},
                {"@type": "Offer", "name": "Lifetime", "price": FACTS["price_lifetime_num"], "priceCurrency": "USD"},
            ],
            "publisher": publisher,
        })
        graph.append({"@type": "WebSite", "name": FACTS["app_name"], "url": SITE + "/", "inLanguage": "zh-Hans" if lang == "zh" else "en"})
    elif page["type"] == "article":
        graph.append({
            "@type": "Article",
            "headline": page.get("h1", page["title"]),
            "description": page["description"],
            "inLanguage": "zh-Hans" if lang == "zh" else "en",
            "datePublished": page.get("published", FACTS["updated"]),
            "dateModified": page.get("updated", FACTS["updated"]),
            "mainEntityOfPage": url,
            "image": SITE + "/assets/og.jpg",
            "author": publisher,
            "publisher": publisher,
            "about": page.get("about", []),
        })
    if page["type"] != "home":
        trail = crumbs_for(page) + [(page["path"], page.get("crumb", page.get("h1", page["title"])))]
        graph.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + path}
                for i, (path, name) in enumerate(trail)
            ],
        })
    faqs = faq_entities(body)
    if faqs:
        graph.append({"@type": "FAQPage", "mainEntity": faqs})
    return graph


# ---------------------------------------------------------------- layout

ICON_SVG = {
    "arrows": '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M7 5 2 10l5 5M13 5l5 5-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}


def header(page: dict, alt_path: str | None) -> str:
    lang = page["lang"]
    home = "/zh/" if lang == "zh" else "/"
    active = page.get("nav", "")
    def link(href: str, label: str, key: str, cls: str = "") -> str:
        cur = ' aria-current="page"' if key and key == active else ""
        c = f' class="{cls}"' if cls else ""
        return f'<a href="{href}"{c}{cur}>{label}</a>'
    lang_link = ""
    if alt_path:
        lang_link = (
            f'<a class="lang" href="{alt_path}" hreflang="{"en" if lang == "zh" else "zh-Hans"}" lang="{"en" if lang == "zh" else "zh-Hans"}">'
            f'{"English" if lang == "zh" else "中文"}</a>'
        )
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home}"><img src="/assets/icon-128.png" width="30" height="30" alt="">Untouched</a>
    <nav class="nav" aria-label="{t(lang, 'Main', '主导航')}">
      {link(home + '#how', t(lang, 'How it works', '原理'), 'how', 'hide-sm')}
      {link(('/zh/guides/' if lang == 'zh' else '/guides/'), t(lang, 'Guides', '指南'), 'guides')}
      {link(home + '#faq', t(lang, 'FAQ', '常见问题'), 'faq', 'hide-sm')}
      {lang_link}
      <a class="btn" href="{FACTS['app_store_url']}">{t(lang, 'Get the app', '下载')}</a>
    </nav>
  </div>
</header>"""


def lang_hint(page: dict, alt_path: str | None) -> str:
    if page["lang"] != "en" or not alt_path:
        return ""
    return f"""<div class="lang-hint" data-lang-hint lang="zh-Hans">
  <div class="wrap"><span>这个页面有中文版。</span><a href="{alt_path}" hreflang="zh-Hans">查看中文</a><button type="button" aria-label="关闭">关闭</button></div>
</div>"""


def footer(page: dict, alt_path: str | None) -> str:
    lang = page["lang"]
    p = "/zh" if lang == "zh" else ""
    links = [
        (f"{p}/support/", t(lang, "Support", "支持")),
        (f"{p}/privacy/", t(lang, "Privacy", "隐私政策")),
        (f"{p}/guides/", t(lang, "Guides", "指南")),
    ]
    if lang == "en":
        links.append(("/compare/", "Compare options"))
    if alt_path:
        links.append((alt_path, "English" if lang == "zh" else "中文"))
    nav = "".join(f'<a href="{h}">{l}</a>' for h, l in links)
    tm = t(
        lang,
        "Apple, iPhone and iCloud are trademarks of Apple Inc., registered in the U.S. and other countries. Untouched is an independent app and is not affiliated with or endorsed by Apple.",
        "Apple、iPhone 和 iCloud 是 Apple Inc. 在美国及其他国家和地区注册的商标。Untouched 是独立开发的 App，与 Apple 没有关联，也未获 Apple 认可。",
    )
    return f"""<footer class="site-footer">
  <div class="wrap">
    <nav aria-label="{t(lang, 'Footer', '页脚')}">{nav}</nav>
    <p>© 2026 Untouched · <a href="mailto:{FACTS['support_email']}">{FACTS['support_email']}</a></p>
    <p>{tm}</p>
  </div>
</footer>"""


def render(page: dict, body: str, alt_path: str | None) -> str:
    lang = page["lang"]
    html_lang = "zh-Hans" if lang == "zh" else "en"
    url = SITE + page["path"]
    title = page["title"] if page.get("title_exact") else f'{page["title"]} · Untouched'
    alts = ""
    if alt_path:
        en_path = page["path"] if lang == "en" else alt_path
        zh_path = alt_path if lang == "en" else page["path"]
        alts = (
            f'<link rel="alternate" hreflang="en" href="{SITE + en_path}">\n'
            f'<link rel="alternate" hreflang="zh-Hans" href="{SITE + zh_path}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE + en_path}">\n'
        )
    robots = '<meta name="robots" content="noindex">\n' if page.get("noindex") else ""
    ld = jsonld(page, body)
    ld_tag = ""
    if ld:
        ld_tag = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": ld}, ensure_ascii=False, separators=(",", ":")) + "</script>\n"
    og_type = "article" if page["type"] == "article" else "website"
    return f"""<!doctype html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(page['description'])}">
<link rel="canonical" href="{url}">
{alts}{robots}<meta name="apple-itunes-app" content="app-id={FACTS['app_id']}">
<meta name="theme-color" content="#F3F5F9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0A111C" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Untouched">
<meta property="og:title" content="{html.escape(page.get('og_title', page.get('h1', page['title'])))}">
<meta property="og:description" content="{html.escape(page['description'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{'zh_CN' if lang == 'zh' else 'en_US'}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/site.css">
{ld_tag}</head>
<body>
<a class="visually-hidden" href="#main">{t(lang, 'Skip to content', '跳到正文')}</a>
{header(page, alt_path)}
{lang_hint(page, alt_path)}
<main id="main">
{body}
</main>
{footer(page, alt_path)}
<script src="/assets/site.js" defer></script>
</body>
</html>
"""


def article_shell(page: dict, body: str) -> str:
    """Wrap article-type bodies with breadcrumbs + H1 + meta line."""
    lang = page["lang"]
    trail = crumbs_for(page)
    parts = []
    for path, name in trail:
        parts.append(f'<a href="{path}">{html.escape(name)}</a><span aria-hidden="true">/</span>')
    crumb_html = f'<nav class="crumbs" aria-label="{t(lang, "Breadcrumb", "面包屑")}">{"".join(parts)}<span aria-current="page">{html.escape(page.get("crumb", page.get("h1", page["title"])))}</span></nav>'
    meta_line = page.get("meta_line")
    if meta_line is None:
        meta_line = t(lang, f'Updated {FACTS["updated_en"]}', f'更新于 {FACTS["updated_zh"]}')
    return f"""<div class="wrap">
  <header class="article-head">
    {crumb_html}
    <h1>{page.get('h1', page['title'])}</h1>
    <p class="article-meta">{meta_line}</p>
  </header>
  <article class="prose">
{body}
  </article>
</div>"""


# ---------------------------------------------------------------- build

def out_file(path: str) -> Path:
    if path.endswith(".html"):
        return ROOT / path.lstrip("/")
    return ROOT / path.lstrip("/") / "index.html"


def main() -> int:
    pages = load_pages()
    by_path = {p["path"]: p for p in pages}
    generated: list[Path] = []

    # alternates must be reciprocal
    for p in pages:
        alt = p.get("alt")
        if alt:
            other = by_path.get(alt)
            if not other:
                err(f"{p['_src']}: alt {alt} does not exist")
            elif other.get("alt") != p["path"]:
                err(f"{p['_src']}: alt {alt} does not point back (it says {other.get('alt')})")

    for p in pages:
        src_body = p["_body"]
        if PRICE_LITERAL.search(src_body):
            err(f"{p['_src']}: hardcoded price {PRICE_LITERAL.search(src_body).group(0)} — use {{{{price_*}}}} from facts.json")
        body = substitute(src_body, p["lang"], p["_src"])
        p["title"] = substitute(p["title"], p["lang"], p["_src"])
        p["description"] = substitute(p["description"], p["lang"], p["_src"])
        if "h1" in p:
            p["h1"] = substitute(p["h1"], p["lang"], p["_src"])
        if p["type"] in ("article", "page"):
            body = article_shell(p, body)
        page_html = render(p, body, p.get("alt"))
        f = out_file(p["path"])
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(page_html)
        generated.append(f)
        p["_html"] = page_html

    # assets that live in src
    (ROOT / "assets").mkdir(exist_ok=True)
    for name in ("site.css", "site.js"):
        shutil.copyfile(SRC / name, ROOT / "assets" / name)

    # llms.txt
    llms = substitute((SRC / "llms.txt").read_text(), "en", "src/llms.txt")
    if PRICE_LITERAL.search((SRC / "llms.txt").read_text()):
        err("src/llms.txt: hardcoded price — use placeholders")
    (ROOT / "llms.txt").write_text(llms)
    generated.append(ROOT / "llms.txt")

    # robots.txt — every crawler welcome, AI crawlers named explicitly so intent is unambiguous
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot",
            "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot", "Applebot-Extended",
            "CCBot", "Bingbot", "DuckAssistBot", "meta-externalagent", "MistralAI-User"]
    robots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
    robots += f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(robots)
    generated.append(ROOT / "robots.txt")

    # sitemap.xml with hreflang alternates
    urls = []
    for p in sorted(pages, key=lambda x: (x["lang"] != "en", x["path"])):
        if p.get("noindex"):
            continue
        alt_xml = ""
        if p.get("alt"):
            en_path = p["path"] if p["lang"] == "en" else p["alt"]
            zh_path = p["alt"] if p["lang"] == "en" else p["path"]
            alt_xml = (
                f'\n    <xhtml:link rel="alternate" hreflang="en" href="{SITE + en_path}"/>'
                f'\n    <xhtml:link rel="alternate" hreflang="zh-Hans" href="{SITE + zh_path}"/>'
                f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE + en_path}"/>'
            )
        urls.append(f"  <url>\n    <loc>{SITE + p['path']}</loc>\n    <lastmod>{p.get('updated', FACTS['updated'])}</lastmod>{alt_xml}\n  </url>")
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
               + "\n".join(urls) + "\n</urlset>\n")
    (ROOT / "sitemap.xml").write_text(sitemap)
    generated.append(ROOT / "sitemap.xml")

    # ------------------------------------------------ checks on the output
    titles: dict[str, str] = {}
    for p in pages:
        h = p["_html"]
        src = p["_src"]
        if "{{" in h:
            err(f"{src}: unreplaced placeholder in output")
        if re.search(r"keepsake", h, re.I):
            err(f"{src}: the old name 'Keepsake' appears in output")
        title = re.search(r"<title>(.*?)</title>", h).group(1)
        if title in titles:
            err(f"{src}: duplicate <title> with {titles[title]}")
        titles[title] = src
        dlen = len(p["description"])
        if not (50 <= dlen <= 170) and not p.get("noindex"):
            warnings.append(f"{src}: description is {dlen} chars (aim for 50–170)")
        for m in re.finditer(r'<img\b(?![^>]*\balt=)[^>]*>', h):
            err(f"{src}: <img> without alt: {m.group(0)[:80]}")
        # internal links
        for href in re.findall(r'href="(/[^"#?]*)(?:#([^"]*))?"', h):
            path, anchor = href
            target = ROOT / path.lstrip("/")
            if path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                err(f"{src}: broken internal link {path}")
            elif anchor:
                if f'id="{anchor}"' not in target.read_text():
                    err(f"{src}: link to missing anchor {path}#{anchor}")

    # remove files generated last time that were not generated now
    keep = {g.relative_to(ROOT).as_posix() for g in generated}
    if MANIFEST.exists():
        for old in MANIFEST.read_text().split():
            if old not in keep:
                f = ROOT / old
                if f.exists():
                    f.unlink()
                    try:
                        f.parent.rmdir()
                    except OSError:
                        pass
                    print(f"removed stale {old}")
    MANIFEST.write_text("\n".join(sorted(keep)) + "\n")

    for w in warnings:
        print("warn:", w)
    if errors:
        for e in errors:
            print("ERROR:", e)
        print(f"\n{len(errors)} error(s).")
        return 1
    print(f"built {len(pages)} pages · llms.txt · robots.txt · sitemap.xml — all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
