#!/usr/bin/env python3
"""Build the SecretBar landing: templates/home.html + i18n/<lang>.json -> /index.html, /<lang>/index.html.

Also writes sitemap.xml, robots.txt and llms.txt. `--check` only validates the string files.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://secretbar.github.io"
REPO = "https://github.com/secretbar/secretbar"
BREW = "brew install secretbar/tap/secretbar"
SETUP = '"$(brew --prefix secretbar)/libexec/install.sh" --claude-hook --app'
VERSION_FILE = ROOT / "version.txt"

LANGS = json.loads((ROOT / "i18n/languages.json").read_text())
EN = json.loads((ROOT / "i18n/en.json").read_text())
PLACEHOLDER = re.compile(r"\{\{([a-z0-9_.]+)\}\}")
TAGS = re.compile(r"</?[a-z]+[^>]*>")


def load(code):
    return json.loads((ROOT / f"i18n/{code}.json").read_text())


def check():
    bad = 0
    en_keys = set(EN)
    for lang in LANGS:
        d = load(lang["code"])
        missing, extra = en_keys - set(d), set(d) - en_keys
        for k in sorted(missing):
            print(f"{lang['code']}: missing {k}")
        for k in sorted(extra):
            print(f"{lang['code']}: extra {k}")
        for k in en_keys & set(d):
            if sorted(TAGS.findall(EN[k])) != sorted(TAGS.findall(d[k])):
                print(f"{lang['code']}: tags differ in {k}")
                bad += 1
        bad += len(missing) + len(extra)
    print("i18n ok" if not bad else f"i18n: {bad} problems")
    return bad == 0


def url_for(code):
    return f"{SITE}/" if code == "en" else f"{SITE}/{code}/"


def strip(s):
    return html.unescape(TAGS.sub("", s))


def jsonld(t, lang):
    app = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "SecretBar",
        "description": strip(t["meta.description"]),
        "applicationCategory": "SecurityApplication",
        "operatingSystem": "macOS 14 or later",
        "url": url_for(lang),
        "downloadUrl": f"{REPO}/releases",
        "installUrl": url_for(lang) + "#install",
        "softwareVersion": VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else None,
        "license": "https://opensource.org/licenses/MIT",
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "codeRepository": REPO,
        "inLanguage": lang,
        "image": f"{SITE}/assets/img/og.png",
    }
    app = {k: v for k, v in app.items() if v is not None}
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "inLanguage": lang,
        "mainEntity": [
            {"@type": "Question", "name": strip(t[f"faq.q{i}"]),
             "acceptedAnswer": {"@type": "Answer", "text": strip(t[f"faq.a{i}"])}}
            for i in range(1, 7)
        ],
    }
    return json.dumps([app, faq], ensure_ascii=False).replace("</", "<\\/")


def render(lang):
    code = lang["code"]
    t = dict(EN)
    t.update(load(code))
    hreflang = "\n".join(
        f'<link rel="alternate" hreflang="{l["code"]}" href="{url_for(l["code"])}">' for l in LANGS
    ) + f'\n<link rel="alternate" hreflang="x-default" href="{url_for("en")}">'
    options = "".join(
        f'<option value="{url_for(l["code"])}"{" selected" if l["code"] == code else ""} lang="{l["code"]}">{l["name"]}</option>'
        for l in LANGS
    )
    ctx = {
        "lang": code,
        "url": url_for(code),
        "site": SITE,
        "repo": REPO,
        "brew": BREW,
        "setup": html.escape(SETUP, quote=True),
        "setup_html": html.escape(SETUP, quote=False),
        "og_locale": lang["og"],
        "hreflang": hreflang,
        "langoptions": options,
        "jsonld": jsonld(t, code),
    }
    attr_keys = {"meta.title", "meta.description", "meta.og_title", "meta.og_description", "js.copied",
                 "js.copy_failed", "hero.copy_label", "install.copy", "nav.language", "app.alt",
                 "hero.redacted_hint", "doc.title"}
    tpl = (ROOT / "templates/home.html").read_text()

    def sub(m):
        k = m.group(1)
        if k in ctx:
            return ctx[k]
        if k not in t:
            raise KeyError(f"{code}: no string {k}")
        v = t[k]
        return html.escape(strip(v), quote=True) if k in attr_keys else v

    return PLACEHOLDER.sub(sub, tpl)


def build():
    for lang in LANGS:
        out = ROOT / ("index.html" if lang["code"] == "en" else f"{lang['code']}/index.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(lang))
    urls = []
    for lang in LANGS:
        alts = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l["code"]}" href="{url_for(l["code"])}"/>' for l in LANGS
        )
        urls.append(f"  <url>\n    <loc>{url_for(lang['code'])}</loc>{alts}\n"
                    f'    <xhtml:link rel="alternate" hreflang="x-default" href="{url_for("en")}"/>\n  </url>')
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls) + "\n</urlset>\n")
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "# AI crawlers are welcome: the site is documentation for a free tool.\n"
        "User-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\n"
        "User-agent: PerplexityBot\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\n"
        f"Sitemap: {SITE}/sitemap.xml\n")
    t = EN
    feats = [k[:-6] for k in EN if re.fullmatch(r"c\d\.title", k)]
    lines = [
        "# SecretBar", "",
        f"> {strip(t['meta.description'])}", "",
        f"- Website: {SITE}/",
        f"- Source: {REPO}",
        f"- Install: `{BREW}`",
        "- License: MIT. Platform: macOS. Command: `secret`. Menu bar app: SecretBar.", "",
        "## The protocol", "",
    ] + [f"- {strip(t[f + '.title'])}: {strip(t[f + '.text'])}" for f in feats] + [
        "", "## Also included", "",
    ] + [f"- {strip(t[k])}" for k in EN if k.startswith("more.") and k != "more.title"] + [
        "", "## FAQ", "",
    ] + [f"- {strip(t[f'faq.q{i}'])} {strip(t[f'faq.a{i}'])}" for i in range(1, 7)] + [
        "", "## Agent rules", "",
        "- Find a secret: `secret ls -l`. Use it: `secret run --mask NAME -- cmd`.",
        "- Never print a value. Never ask the user to paste a value into the chat: run `secret ask NAME`.",
        f"- Full rules: {REPO}/blob/main/docs/claude-md-secrets.md",
        "", "## Languages", "",
    ] + [f"- {l['name']}: {url_for(l['code'])}" for l in LANGS]
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n")
    print(f"built {len(LANGS)} pages")


if __name__ == "__main__":
    ok = check()
    if "--check" in sys.argv:
        sys.exit(0 if ok else 1)
    build()
