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


def page_url(path: str) -> str:
    """Public URL for a site file. Cloudflare Pages 308-redirects "x.html" to "x", so links
    that crawlers treat as authoritative (canonical, sitemap, feed, schema) use the short form."""
    path = path[:-5] if path.endswith(".html") else path
    return f"{SITE_URL}/" if path in ("", "index") else f"{SITE_URL}/{path}"


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

    url = page_url(brief["url"])
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": brief.get("excerpt", ""),
        "datePublished": d.strftime("%Y-%m-%d"),
        "author": {"@type": "Organization", "name": "O'Dwyer Capital"},
        "publisher": {"@type": "Organization", "name": "O'Dwyer Capital", "url": SITE_URL},
        "mainEntityOfPage": url,
    }
    sources_html = "".join(
        f'<li><a href="{u}" target="_blank" rel="noopener"><b>{_domain(u)}</b>'
        f'{html.escape(urllib.parse.urlparse(u).path[:60])}</a></li>'
        for u in sources)
    values = {
        "TITLE": html.escape(title),
        "DESCRIPTION": html.escape(brief.get("excerpt", "")),
        "URL": url,
        "URL_ENC": urllib.parse.quote(url, safe=""),
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


def _fill(page: str, name: str, content: str) -> str:
    """Replace the content between <!-- static:name --> and <!-- /static:name --> markers"""
    pattern = re.compile(rf"(<!-- static:{name} -->).*?(<!-- /static:{name} -->)", re.DOTALL)
    if not pattern.search(page):
        raise ValueError(f"missing <!-- static:{name} --> markers")
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), page, count=1)


def update_listing_pages(archive: List[Dict], base_dir: str) -> None:
    """Write the brief listings into index.html and thoughts.html as plain HTML.

    Both pages re-render these from articles_data.json in the browser, but most AI crawlers
    don't run JavaScript, so the markup they need to find the briefs has to be in the file.
    It mirrors what the pages' scripts draw on first load.
    """
    briefs = sorted(archive, key=_date, reverse=True)
    esc = html.escape

    def label(b):
        return b.get("headline") or b.get("title", "")

    def fmt(b):
        return _nice_date(_date(b), "%b %d, %Y")

    # Homepage: brief count, latest-brief button and this week's three cards
    sector = {"energy-transition": "Energy", "emerging-tech": "Technology", "materials": "Materials"}
    path = os.path.join(base_dir, "index.html")
    with open(path, encoding="utf-8") as f:
        page = f.read()
    page = _fill(page, "brief-count", str(len(briefs)))
    page = re.sub(r'(<a href=")[^"]*(" class="btn btn-gold" id="latest-link">)',
                  lambda m: m.group(1) + esc(briefs[0]["url"]) + m.group(2), page)
    page = _fill(page, "latest-briefs", "".join(f"""
        <a class="brief" href="{esc(b['url'])}">
          <div class="brief-meta"><span class="sector">{sector.get(b['slug'], '')}</span><span>{fmt(b)}</span></div>
          <h3>{esc(label(b))}</h3>
          <p>{esc(b.get('excerpt', ''))}</p>
          <span class="link-arrow">Read brief <span>→</span></span>
        </a>""" for b in briefs[:3]) + "\n        ")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)

    # Thoughts: hero stats, featured panel, and every earlier brief (first 12 shown, the rest
    # hidden until "Load more", but their links are still in the page for crawlers)
    page_size = 12
    latest = briefs[0]
    same_day = [b for b in briefs[1:] if b["date"] == latest["date"]]
    pool = [b for b in briefs if b["date"] != latest["date"]]
    first = _date(briefs[-1])

    def sources(b, suffix):
        return f"{b['article_count']} {suffix}" if b.get("article_count") else ""

    def chips(b):
        return "".join(f'<span class="chip" data-theme="{esc(t.lower())}">{esc(t[:1].upper() + t[1:])}</span>'
                       for t in (b.get("themes") or [])[:3])

    stats = f"""
      <div><b>{len(briefs)}</b><span>Briefs published</span></div>
      <div><b>3</b><span>Research series</span></div>
      <div><b>{first.strftime('%b')} ’{first.strftime('%y')}</b><span>Publishing since</span></div>"""
    featured = f"""
      <div class="featured">
        <a class="featured-main" href="{esc(latest['url'])}" data-series="{latest['slug']}">
          <div class="featured-label"><span class="pill-new">Latest</span><span class="series">{SERIES.get(latest['slug'], '')}</span></div>
          <h2>{esc(label(latest))}</h2>
          <p>{esc(latest.get('excerpt', ''))}</p>
          <div class="meta-row"><span>{fmt(latest)} · {sources(latest, 'sources analyzed') or 'O’Dwyer Analysis'}</span><span class="link-arrow">Read brief <span>→</span></span></div>
        </a>
        <div class="featured-side">
          <div>
            <div class="side-label">Also this week</div>
            <ul class="also-list">
              {''.join(f'<li><a href="{esc(b["url"])}" data-series="{b["slug"]}"><span class="series">{SERIES.get(b["slug"], "")}</span><strong>{esc(label(b))}</strong></a></li>' for b in same_day)}
            </ul>
          </div>
        </div>
      </div>"""
    grid = "".join(f"""
        <a class="card" href="{esc(b['url'])}" data-series="{b['slug']}"{' hidden' if i >= page_size else ''}>
          <div class="card-top"><span class="series">{SERIES.get(b['slug'], '')}</span><time>{fmt(b)}</time></div>
          <h3>{esc(label(b))}</h3>
          <p>{esc(b.get('excerpt', ''))}</p>
          <div class="chips">{chips(b)}</div>
          <div class="meta-row"><span>{sources(b, 'sources')}</span><span class="link-arrow">Read <span>→</span></span></div>
        </a>""" for i, b in enumerate(pool))
    shown = min(page_size, len(pool))
    more = (f'<span>Showing {shown} of {len(pool)}</span><div class="progress"><i style="width:{shown / len(pool) * 100:g}%"></i></div>'
            f'<button class="btn" id="load">Load more briefs</button>') if len(pool) > shown else ""

    path = os.path.join(base_dir, "thoughts.html")
    with open(path, encoding="utf-8") as f:
        page = f.read()
    page = _fill(page, "hero-stats", stats)
    page = _fill(page, "featured", featured)
    page = _fill(page, "count", f"<b>Archive</b> · {len(pool)} earlier briefs")
    page = _fill(page, "grid", grid)
    page = _fill(page, "more", more)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
