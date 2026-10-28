"""Render a brief's body HTML into a full page using templates/brief.html.

Used by article_analyzer.py for each new brief and by rebuild_briefs.py to migrate
existing brief pages. Brief bodies use plain h2/h3/p/a/strong markup, but section
headings vary from week to week, so each special treatment only applies when its
heading is present.
"""
import html
import json
import os
import re
import urllib.parse
from datetime import datetime
from typing import Dict, List, Tuple

SITE_URL = "https://www.odwyercapital.com"
SERIES = {"energy-transition": "Energy Transition", "emerging-tech": "Emerging Tech", "materials": "Materials"}
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "brief.html")


def _date(brief: Dict) -> datetime:
    return datetime.strptime(brief["date"], "%B %d, %Y")


def _nice_date(d: datetime, fmt: str) -> str:
    return d.strftime(fmt).replace(" 0", " ")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<.*?>", "", text)).lower()).strip("-")


def _sentence_case(text: str) -> str:
    return text[0] + text[1:].lower() if text == text.title() else text


def _domain(url: str) -> str:
    d = urllib.parse.urlparse(url).netloc
    return d[4:] if d.startswith("www.") else d


def headline_of(body_html: str, fallback: str = "") -> str:
    """The brief's own opening <h2> headline, as plain text"""
    m = re.search(r"<h2[^>]*>(.*?)</h2>", body_html or "", re.DOTALL)
    text = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
    return text or fallback


def extract_legacy_body(page_html: str) -> str:
    """Body HTML from a brief page in the pre-redesign layout, or '' if it isn't one"""
    m = re.search(r'<div class="article-body">(.*?)(?:<div class="related-briefs">|<div class="tags">)',
                  page_html, re.DOTALL)
    return m.group(1) if m else ""


def render_body(body_html: str) -> Tuple[str, List[str], List[str]]:
    """Restructure the body for the new layout. Returns (html, table of contents items, source URLs)."""
    body = re.sub(r"<script.*?</script>", "", body_html, flags=re.DOTALL)

    # The page hero shows the headline, so drop the opening <h2> from the body
    body = re.sub(r"<h2[^>]*>.*?</h2>", "", body, count=1, flags=re.DOTALL)

    # Number external sources in order of first appearance
    sources: List[str] = []

    def link(m):
        href, text = m.group(1), m.group(2)
        if href not in sources:
            sources.append(href)
        return (f'<a class="src" href="{href}" target="_blank" rel="noopener">{text}</a>'
                f'<sup class="fn">{sources.index(href) + 1}</sup>')

    body = re.sub(r'<a\s+[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', link, body, flags=re.DOTALL)

    # Split into an intro plus (level, title, content) sections
    parts = re.split(r"(<h[23]>.*?</h[23]>)", body, flags=re.DOTALL)
    intro, sections = parts[0].strip(), []
    for p in parts[1:]:
        h = re.match(r"<h([23])>(.*?)</h[23]>", p, re.DOTALL)
        if h:
            sections.append({"level": int(h.group(1)), "title": h.group(2).strip(), "html": ""})
        elif sections:
            sections[-1]["html"] += p

    toc: List[str] = []
    out: List[str] = []
    used = set()
    parent, dev_n = None, 0
    has_summary = any(s["title"] == "Executive Summary" for s in sections)
    if intro:
        # Briefs without an executive summary open with a plain paragraph: style it as the lede
        out.append(intro if has_summary else re.sub(r"^<p>", '<p class="lede">', intro, count=1))

    for s in sections:
        t, content = s["title"], s["html"].strip()
        sid = _slug(t) or "section"
        while sid in used:
            sid += "-2"
        used.add(sid)
        if s["level"] == 2:
            parent, dev_n = t, 0
            out.append(f'<h2 id="{sid}">{t}</h2>{content}')
            toc.append(f'<li><a href="#{sid}">{_sentence_case(t)}</a></li>')
        elif t == "Executive Summary":
            out.append(f'<section class="summary" id="{sid}"><h3 class="label">Executive summary</h3>{content}</section>')
            toc.insert(0, f'<li><a href="#{sid}">Executive summary</a></li>')
        elif parent == "Key Developments":
            dev_n += 1
            out.append(f'<div class="dev" id="{sid}"><div class="n">{dev_n:02d}</div><div><h3>{t}</h3>{content}</div></div>')
        elif t == "Portfolio Positioning":
            out.append(f'<h3 class="label" id="{sid}">{t}</h3><div class="callout">{content}</div>')
        elif t == "Risk Factors":
            paras = re.findall(r"<p>(.*?)</p>", content, re.DOTALL)
            cards = [re.match(r"\s*<strong>(.*?)</strong>:?\s*(.*)", p, re.DOTALL) for p in paras]
            if paras and all(cards):
                grid = "".join(f'<div class="risk"><h4>{c.group(1).rstrip(":")}</h4><p>{c.group(2)}</p></div>' for c in cards)
                out.append(f'<h3 id="{sid}">{t}</h3><div class="risks">{grid}</div>')
            else:
                out.append(f'<h3 id="{sid}">{t}</h3>{content}')
            toc.append(f'<li class="sub"><a href="#{sid}">Risk factors</a></li>')
        else:
            out.append(f'<h3 id="{sid}">{t}</h3>{content}')

    return "\n".join(out), toc, sources


def render_brief_page(brief: Dict, body_html: str, archive: List[Dict]) -> str:
    """Full page HTML for one brief.

    brief:   its archive entry (slug, date, url, excerpt, themes)
    archive: every published brief, used for related briefs and previous/next links;
             it may or may not already contain `brief`
    """
    title = headline_of(body_html, brief.get("title", ""))
    body, toc, sources = render_body(body_html)
    words = len(re.sub(r"<.*?>", " ", body).split())
    d = _date(brief)
    slug = brief["slug"]
    series = SERIES.get(slug, brief.get("title", ""))
    themes = brief.get("themes") or []

    def label(b):
        return b.get("headline") or b.get("title", "")

    # Pager: previous/next in the same series; related: the three most recent other earlier briefs sharing a theme
    others = [b for b in archive if b.get("url") != brief["url"]]
    same = sorted(others + [brief], key=_date)
    same = [b for b in same if b.get("slug") == slug]
    i = same.index(brief)
    prev_b = same[i - 1] if i > 0 else None
    next_b = same[i + 1] if i + 1 < len(same) else None
    earlier = sorted([b for b in others if _date(b) < d], key=_date, reverse=True)
    related = [b for b in earlier if b is not prev_b and set(b.get("themes") or []) & set(themes)][:3]
    if len(related) < 3:
        related += [b for b in earlier if b is not prev_b and b not in related][:3 - len(related)]
    heading = "Earlier briefs on <em>these themes</em>"
    if len(related) < 3:
        # The first briefs have nothing earlier to point to, so show the nearest later ones
        later = sorted([b for b in others if _date(b) > d and b is not next_b], key=_date)
        related += later[:3 - len(related)]
        heading = "More from <em>our research</em>"

    def card(b):
        return (f'<a class="rel" href="{b["url"]}" data-series="{b["slug"]}">'
                f'<div class="rel-top"><span class="series">{SERIES.get(b["slug"], "")}</span>'
                f'<span>{_nice_date(_date(b), "%b %d, %Y")}</span></div>'
                f'<h3>{html.escape(label(b))}</h3><span class="link-arrow">Read brief <span>→</span></span></a>')

    pager = ""
    if prev_b:
        pager += (f'<a class="prev" href="{prev_b["url"]}"><small>← Previous {series} brief</small>'
                  f'<strong>{html.escape(label(prev_b))}</strong></a>')
    if next_b:
        pager += (f'<a class="next" href="{next_b["url"]}"><small>Next {series} brief →</small>'
                  f'<strong>{html.escape(label(next_b))}</strong></a>')

    page_url = f"{SITE_URL}/{brief['url']}"
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": brief.get("excerpt", ""),
        "datePublished": d.strftime("%Y-%m-%d"),
        "author": {"@type": "Organization", "name": "O'Dwyer Capital"},
        "publisher": {"@type": "Organization", "name": "O'Dwyer Capital", "url": SITE_URL},
        "mainEntityOfPage": page_url,
    }
    sources_html = "".join(
        f'<li><a href="{u}" target="_blank" rel="noopener"><b>{_domain(u)}</b>'
        f'{html.escape(urllib.parse.urlparse(u).path[:60])}</a></li>'
        for u in sources)
    values = {
        "TITLE": html.escape(title),
        "DESCRIPTION": html.escape(brief.get("excerpt", "")),
        "URL": page_url,
        "URL_ENC": urllib.parse.quote(page_url, safe=""),
        "TITLE_ENC": urllib.parse.quote(title),
        "ISO_DATE": d.strftime("%Y-%m-%d"),
        "SCHEMA": json.dumps(schema).replace("</", "<\\/"),
        "SLUG": slug,
        "SERIES": series,
        "DATE": _nice_date(d, "%B %d, %Y"),
        "READ_MIN": str(max(1, round(words / 230))),
        "SOURCE_COUNT": str(len(sources)),
        "LAYOUT_CLASS": "" if len(toc) >= 2 else " no-toc",
        "TOC": "".join(toc),
        "BODY": body,
        "SOURCES": sources_html,
        "TAGS": "".join(f'<span class="tag">{html.escape(t[:1].upper() + t[1:])}</span>' for t in [series] + themes),
        "RELATED": "".join(card(b) for b in related),
        "RELATED_HEADING": heading,
        "PAGER": pager,
    }
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        page = f.read()
    # One pass, so placeholder-like text inside a brief is never substituted
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], page)
    return page
