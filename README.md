# untouched.tetherme.app

Website for **Untouched** (iOS, App Store id 6808529019): landing page, guides, support, privacy policy, in English and Simplified Chinese. Static HTML on GitHub Pages (branch `main`, root). No framework, no external requests, system fonts.

**This repo is the source of truth for the site.** (The old copy in the app repo's `web/` folder is retired.)

## Edit → build → deploy

```bash
python3 build.py                 # regenerates every page, llms.txt, robots.txt, sitemap.xml; runs checks
python3 -m http.server 8765      # preview at http://127.0.0.1:8765
git add . && git commit && git push    # GitHub Pages deploys main in ~1 minute
python3 ping_indexnow.py         # after it's live: ask Bing & co. to recrawl
```

## Where things live

| | |
|---|---|
| `src/facts.json` | **Every product fact** (prices, free allowance, iOS floor, definition). Pages use `{{price_monthly}}` etc. Change a price here, rebuild. |
| `src/pages/en/**`, `src/pages/zh/**` | One HTML fragment per page, starting with `<!--meta {…} -->` (path, alt-language path, title, description, type) |
| `src/llms.txt` | Template for `/llms.txt`, the summary written for AI engines |
| `src/site.css`, `src/site.js` | Copied to `assets/` on build |
| `assets/` | Images, icons, the official App Store badge |
| `build.py` | Renders pages, JSON-LD (MobileApplication, Article, FAQPage, BreadcrumbList), hreflang, sitemap |

Generated (don't edit by hand): `index.html`, `*/index.html`, `404.html`, `llms.txt`, `robots.txt`, `sitemap.xml`, `assets/site.css`, `assets/site.js`. `.build-manifest` lists them so a page removed from `src/` is deleted on the next build.

## What the build refuses

- A hardcoded price in a page or in `llms.txt` (use the `{{price_*}}` placeholders)
- The word **iCloud** in the main content of the home pages. They are the App Store "marketing URL", and comparative use of Apple trademarks there is what got 1.0 rejected under guideline 5.2.5. Guides may name Apple features factually; the footer carries the trademark notice.
- Broken internal links or anchors, `<img>` without `alt`, duplicate titles, one-way `alt` language links, the old name "Keepsake"

## Rules for the words on this site

- **Every claim about the app is checked against the app's code**, not its marketing. Known traps: deleting the app deletes its folder (never say files survive uninstall); Hidden album items added while the album is locked are a single file that may not be the original; the folder is excluded from device backups by default; verification is on demand, not automatic; there is no percentage progress.
- **Every claim about iOS cites Apple's documentation** in the page's Sources list.
- Guides open with a **Short answer** that stands on its own. AI engines quote the first paragraph.
- The app's definition sentence (`definition_en` in facts) is repeated verbatim where the product is introduced, so "Untouched" and "keeps original photos and videos on iPhone" keep appearing together.

The App Store links `/privacy` and `/support` from inside the app. Those paths must keep working.
