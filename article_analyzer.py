#!/usr/bin/env python3
"""
O'Dwyer Capital Article Analyzer
Fetches articles from NewsAPI, analyzes them, and publishes daily briefs
"""

import json
import os
import shutil
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from urllib.parse import urlparse
import re
from anthropic import Anthropic

class ArticleAnalyzer:
    def __init__(self, api_key: str = None, thoughts_file: str = "articles_data.json"):
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.claude_client = Anthropic(api_key=self.anthropic_key) if self.anthropic_key else None
        self.thoughts_file = thoughts_file
        self.base_url = "https://newsapi.org/v2/everything"
        self.existing_articles = self.load_existing_articles()
        self.new_articles = []

    def load_existing_articles(self) -> List[Dict]:
        """Load existing articles from JSON"""
        if os.path.exists(self.thoughts_file):
            try:
                with open(self.thoughts_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def get_time_window(self) -> tuple:
        """
        Determine the time window for fetching articles.
        Monday: weekend + Monday morning (Friday 5pm through Monday 8am)
        Tue-Fri: from previous post to now
        Sat-Sun: from most recent article date to now
        """
        now = datetime.utcnow()
        weekday = now.weekday()  # 0=Mon, 1=Tue, ..., 5=Sat, 6=Sun

        # If it's Monday
        if weekday == 0:  # 0 = Monday
            # Get articles from Friday 5pm through Monday 8am
            friday = now - timedelta(days=3)
            friday = friday.replace(hour=17, minute=0, second=0, microsecond=0)
            from_date = friday
            to_date = now
        # If it's Saturday or Sunday, look back to most recent article
        elif weekday in [5, 6]:  # 5=Saturday, 6=Sunday
            # Find the most recent article date
            if self.existing_articles and len(self.existing_articles) > 0:
                # Try to parse the date from the most recent article
                try:
                    latest_date_str = self.existing_articles[0].get('date', '')
                    # Parse common date formats (e.g., "May 30, 2026" or "2026-05-30")
                    if latest_date_str:
                        # Try parsing "Month DD, YYYY" format
                        try:
                            latest_date = datetime.strptime(latest_date_str, "%B %d, %Y")
                        except:
                            # Try ISO format
                            latest_date = datetime.strptime(latest_date_str.split('T')[0], "%Y-%m-%d")
                        # Start from the latest article date
                        from_date = latest_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    else:
                        # Fallback: use 7 days ago
                        from_date = now - timedelta(days=7)
                except:
                    # Fallback: use 7 days ago
                    from_date = now - timedelta(days=7)
            else:
                # No existing articles, use 7 days ago
                from_date = now - timedelta(days=7)
            to_date = now
        else:
            # For Tue-Fri: assume previous post was yesterday at 8am
            yesterday = now - timedelta(days=1)
            from_date = yesterday.replace(hour=8, minute=0, second=0, microsecond=0)
            to_date = now

        return from_date, to_date

    def fetch_articles(self) -> List[Dict]:
        """Fetch articles from NewsAPI based on time window"""
        if not self.api_key:
            print("ERROR: NEWSAPI_KEY environment variable not set")
            return []

        from_date, to_date = self.get_time_window()
        from_str = from_date.isoformat() + "Z"
        to_str = to_date.isoformat() + "Z"

        print(f"Fetching articles from {from_str} to {to_str}")

        # Three queries, one per category focus (free tier allows 100 requests/day).
        # The materials query is dedicated - it was chronically starved (1-4 articles/day)
        # when piggybacking on the tech query, producing single-source briefs.
        queries = [
            "(renewable OR energy OR battery OR storage) AND (transition OR investment)",
            "(AI OR space OR technology OR semiconductor) AND (innovation OR emerging)",
            "(\"advanced materials\" OR composites OR graphene OR lithium OR \"rare earth\" OR mining OR alloy) AND (market OR manufacturing OR \"supply chain\")"
        ]

        all_articles = []
        seen_urls = set()

        for query in queries:
            try:
                response = requests.get(
                    self.base_url,
                    params={
                        'q': query,
                        'from': from_str,
                        'to': to_str,
                        'sortBy': 'relevancy',
                        'language': 'en',
                        'apiKey': self.api_key
                    }
                )

                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    for article in articles:
                        url = article.get('url', '')
                        if url and url not in seen_urls and not self.is_blocked_source(url):
                            all_articles.append(article)
                            seen_urls.add(url)
                else:
                    print(f"NewsAPI error: {response.status_code}")
            except Exception as e:
                print(f"Error fetching articles for '{query}': {e}")

        print(f"Fetched {len(all_articles)} articles")
        return all_articles

    # Ephemeral aggregators whose links rot within days - never cite these
    BLOCKED_DOMAINS = {'biztoc.com', 'news.google.com', 'slickdeals.net'}

    # Don't publish a brief built on fewer live sources than this - a one-source
    # "brief" is just a reprint of that source, not analysis
    MIN_LIVE_SOURCES = 3

    def is_blocked_source(self, url: str) -> bool:
        try:
            domain = urlparse(url).netloc.lower()
            domain = domain[4:] if domain.startswith('www.') else domain
            return domain in self.BLOCKED_DOMAINS
        except Exception:
            return True

    def verify_url(self, url: str, timeout: int = 6) -> bool:
        """Check that a source URL actually resolves before we cite it"""
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; ODwyerBot/1.0)'}
        try:
            r = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
            if r.status_code in (405, 501):  # HEAD not allowed - retry with GET
                r = requests.get(url, timeout=timeout, stream=True, headers=headers)
            # 403 usually means bot-blocking, not a dead page - treat as alive
            return r.status_code < 400 or r.status_code == 403
        except Exception:
            return False

    def filter_live_articles(self, articles: List[Dict], limit: int = 15) -> List[Dict]:
        """Keep only articles whose links are verified live (checks up to `limit`)"""
        live = []
        checked = 0
        for a in articles:
            if len(live) >= limit or checked >= limit * 2:
                break
            url = a.get('url', '')
            if not url or self.is_blocked_source(url):
                continue
            checked += 1
            if self.verify_url(url):
                live.append(a)
            else:
                print(f"   Dropping dead/unreachable source: {url[:90]}")
        return live

    def categorize_article(self, article: Dict) -> str:
        """Categorize article into Technology, Energy, or Innovation"""
        text = (
            article.get('title', '').lower() +
            ' ' +
            article.get('description', '').lower()
        ).lower()

        energy_keywords = ['energy', 'battery', 'storage', 'renewable', 'solar', 'wind', 'grid', 'transition']
        tech_keywords = ['ai', 'space', 'satellite', 'digital', 'technology', 'quantum', 'chip']
        innovation_keywords = ['material', 'graphene', 'composite', 'manufacturing', 'process']

        energy_score = sum(1 for kw in energy_keywords if kw in text)
        tech_score = sum(1 for kw in tech_keywords if kw in text)
        innovation_score = sum(1 for kw in innovation_keywords if kw in text)

        scores = {'Energy': energy_score, 'Technology': tech_score, 'Innovation': innovation_score}
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'Technology'

    def extract_key_themes(self, titles: List[str]) -> List[str]:
        """Extract key themes from article titles"""
        themes = []
        all_text = ' '.join(titles).lower()

        # Theme keywords by category
        theme_keywords = {
            'ai': 'artificial intelligence',
            'quantum': 'quantum computing',
            'battery': 'battery technology',
            'renewable': 'renewable energy',
            'solar': 'solar energy',
            'wind': 'wind energy',
            'storage': 'energy storage',
            'semiconductor': 'semiconductor',
            'chip': 'chip manufacturing',
            'grid': 'power grid',
            'electric': 'electrification',
            'fusion': 'fusion energy',
            'space': 'space technology',
            'satellite': 'satellite technology'
        }

        for keyword, theme in theme_keywords.items():
            if keyword in all_text:
                themes.append(theme)

        return list(set(themes))[:3]  # Return up to 3 unique themes

    def generate_ai_excerpt(self, category: str, themes: List[str], articles: List[Dict]) -> str:
        """Generate a factual, concise excerpt using Claude AI based on brief content"""
        if not self.claude_client:
            return self.generate_professional_excerpt(category, articles)

        try:
            # Prepare article summaries for context
            article_titles = [a.get('title', '') for a in articles[:5]]
            article_summaries = "\n".join([f"- {title}" for title in article_titles])

            prompt = f"""You are helping create investment briefing excerpts for O'Dwyer Capital.

Based on this brief's themes and articles, generate a SHORT, FACTUAL excerpt (2-3 sentences max) that:
1. States specific market trends or developments
2. Includes concrete details (market size, growth %, timelines if available)
3. Is written for investment professionals
4. Feels like a headline summary, not a marketing tagline

Category: {category}
Themes: {', '.join(themes)}
Articles:
{article_summaries}

Generate ONLY the excerpt text, nothing else. No quotes, no preamble."""

            message = self.claude_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            excerpt = message.content[0].text.strip()
            print(f"   Generated AI excerpt: {excerpt}")
            return excerpt

        except Exception as e:
            print(f"   Error generating AI excerpt: {e}")
            return self.generate_professional_excerpt(category, articles)

    def extract_key_insights(self, articles: List[Dict]) -> List[str]:
        """Extract key insights from actual article descriptions"""
        insights = []

        for article in articles[:10]:  # Look at top 10 articles
            description = article.get('description', '')

            if description:
                # Extract first sentence as key insight
                sentences = description.split('.')
                key_sentence = sentences[0].strip()

                # Only include substantial insights (>15 chars, <200 chars to avoid truncation)
                if 15 < len(key_sentence) < 200:
                    insights.append(key_sentence)

        # Remove duplicates while preserving order
        seen = set()
        unique_insights = []
        for insight in insights:
            if insight not in seen:
                seen.add(insight)
                unique_insights.append(insight)

        return unique_insights

    def generate_professional_excerpt(self, category: str, articles: List[Dict]) -> str:
        """Generate excerpt based on actual article content, not templates"""
        if not articles:
            # Fallback descriptions if no articles
            defaults = {
                'Energy': "Recent developments in renewable energy and grid infrastructure transforming market dynamics",
                'Technology': "Emerging technology trends reshaping competitive landscapes and investor priorities",
                'Innovation': "Breakthrough innovations creating new investment opportunities across sectors"
            }
            return defaults.get(category, defaults['Innovation'])

        # Extract real insights from article descriptions
        insights = self.extract_key_insights(articles)

        if insights and len(insights) >= 2:
            # Combine top 2-3 insights into a coherent excerpt
            excerpt_parts = insights[:3]
            excerpt = "; ".join(excerpt_parts)
            # Capitalize first letter
            excerpt = excerpt[0].upper() + excerpt[1:] if excerpt else ""
            if not excerpt.endswith('.'):
                excerpt += "."
            return excerpt

        # Fallback to theme-based if no good insights found
        titles = [a.get('title', '') for a in articles[:5]]
        themes = self.extract_key_themes(titles)

        if themes:
            theme_text = ' and '.join(themes)
            summaries = {
                'Energy': f"Key developments in {theme_text} reshaping the energy sector and creating investment opportunities",
                'Technology': f"Important trends in {theme_text} impacting technology investments and competitive positioning",
                'Innovation': f"Breakthrough progress in {theme_text} creating emerging market opportunities"
            }
            return summaries.get(category, summaries['Innovation'])

        # Final fallback
        return "Strategic market developments creating new investment opportunities"

    def next_id(self) -> int:
        """Return a unique incrementing id (accounts for multiple briefs in one run)"""
        existing_ids = [a.get('id', 0) for a in self.existing_articles if isinstance(a.get('id'), int)]
        base = max(existing_ids) if existing_ids else 0
        self._ids_assigned_this_run = getattr(self, '_ids_assigned_this_run', 0) + 1
        return base + self._ids_assigned_this_run

    def find_related_briefs(self, slug: str, themes: List[str], limit: int = 3) -> List[Dict]:
        """Find prior briefs in the same category or with overlapping themes, newest first"""
        related = []
        theme_set = {t.lower() for t in (themes or [])}

        for brief in self.existing_articles:
            b_slug = brief.get('slug', '')
            b_themes = {t.lower() for t in brief.get('themes', [])}
            if b_slug == slug or (theme_set & b_themes):
                url = brief.get('url')
                if not url:
                    # Reconstruct the dated filename from the brief's date
                    try:
                        d = datetime.strptime(brief.get('date', ''), "%B %d, %Y")
                        url = f"{b_slug}-{d.strftime('%Y-%m-%d')}.html"
                    except Exception:
                        continue
                related.append({
                    'title': brief.get('title', ''),
                    'date': brief.get('date', ''),
                    'excerpt': brief.get('excerpt', ''),
                    'url': url
                })
            if len(related) >= limit:
                break

        return related

    def generate_article_body(self, category: str, themes: List[str], articles: List[Dict],
                              trend_analysis: Dict, related_briefs: List[Dict]) -> str:
        """Generate the FULL article body HTML using Claude, based on today's news.

        This is the core fix for duplicate articles: previously only the excerpt was
        AI-generated and the article page was a copy of a static template. Now the
        entire body is written fresh from the day's fetched articles.
        """
        if not self.claude_client:
            print("   WARNING: No ANTHROPIC_API_KEY - falling back to insight-based body")
            return self.generate_fallback_body(category, articles)

        # Today's source material, numbered. The model cites by NUMBER, never by URL -
        # models mis-transcribe long URLs (a one-digit typo = dead link on the site).
        cited = articles[:12]
        source_lines = []
        for i, a in enumerate(cited, 1):
            title = a.get('title', '')
            desc = (a.get('description') or '')[:300]
            src = a.get('source', {}).get('name', 'Unknown')
            source_lines.append(f"[{i}] TITLE: {title}\n    SOURCE: {src}\n    SUMMARY: {desc}")
        source_material = "\n".join(source_lines)

        # Prior coverage so the model writes what's NEW, not a rehash
        prior_lines = []
        for rb in related_briefs:
            prior_lines.append(f"- \"{rb['title']}\" ({rb['date']}): {rb['excerpt']}")
        prior_coverage = "\n".join(prior_lines) if prior_lines else "None - this is the first brief in this category."

        today_str = datetime.now().strftime("%B %d, %Y")

        prompt = f"""You are the research analyst for O'Dwyer Capital, a private family investment office. Write today's ({today_str}) {category} investment brief as an HTML fragment.

TODAY'S NEWS (your ONLY source material - every claim must come from these):
{source_material}

CURRENT THEMES: {', '.join(themes) if themes else 'n/a'}
NEW THEMES vs prior briefs: {', '.join(trend_analysis.get('new_themes', [])) or 'none'}
ACCELERATING THEMES: {', '.join(trend_analysis.get('accelerating_themes', [])) or 'none'}

PRIOR O'DWYER COVERAGE (do NOT repeat this analysis - focus on what has CHANGED or emerged since):
{prior_coverage}

REQUIREMENTS:
1. 500-800 words, written for investment professionals. Factual, specific, no marketing fluff.
2. Structure with these tags only: <h2>, <h3>, <p>, <strong>, <a>. No <html>, <head>, <body>, or <div> wrappers.
3. Sections: an opening <h2> headline specific to today's developments (NOT a generic category name), <h3>Executive Summary</h3>, <h2>Key Developments</h2> (2-4 subsections), <h2>Investment Implications</h2> including risk factors.
4. Link claims to sources inline by NUMBER: <a href="[N]" target="_blank">anchor text</a> where N is the source number above (e.g. <a href="[3]" target="_blank">the report</a>). NEVER write out a URL - use only the bracketed number as the href.
5. Include concrete figures (market sizes, growth rates, timelines) ONLY when they appear in the source material. Never invent numbers.
6. Where prior coverage exists, add one short paragraph noting how today's developments extend or diverge from it.

Output ONLY the HTML fragment. No markdown, no code fences, no preamble."""

        try:
            message = self.claude_client.messages.create(
                model=os.getenv('ARTICLE_MODEL', 'claude-haiku-4-5-20251001'),
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            body = message.content[0].text.strip()
            # Strip accidental code fences
            body = re.sub(r'^```(?:html)?\s*|\s*```$', '', body).strip()

            # Substitute numbered tokens with the EXACT source URLs (byte-for-byte)
            for i, a in enumerate(cited, 1):
                url = a.get('url', '')
                body = body.replace(f'href="[{i}]"', f'href="{url}"')
                body = body.replace(f"href='[{i}]'", f'href="{url}"')

            # Safety net: any anchor whose href is not one of our verified URLs
            # (a hallucinated or leftover link) is unwrapped to plain text.
            allowed = {a.get('url', '') for a in cited}
            def _scrub(m):
                return m.group(0) if m.group(1) in allowed else m.group(2)
            body = re.sub(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', _scrub, body, flags=re.DOTALL)

            print(f"   Generated AI article body ({len(body)} chars)")
            return body
        except Exception as e:
            print(f"   Error generating AI article body: {e}")
            return self.generate_fallback_body(category, articles)

    def generate_fallback_body(self, category: str, articles: List[Dict]) -> str:
        """Non-AI fallback: build a body from today's actual articles so content is still unique per day"""
        today_str = datetime.now().strftime("%B %d, %Y")
        parts = [f"<h2>{category} Investment Brief &mdash; {today_str}</h2>",
                 "<h3>Today's Developments</h3>"]
        for a in articles[:8]:
            title = a.get('title', '')
            desc = (a.get('description') or '').strip()
            url = a.get('url', '')
            src = a.get('source', {}).get('name', '')
            if title and url:
                parts.append(f'<p><strong><a href="{url}" target="_blank">{title}</a></strong> ({src})</p>')
                if desc:
                    parts.append(f"<p>{desc}</p>")
        return "\n".join(parts)

    def build_related_section(self, related_briefs: List[Dict]) -> str:
        """Build the Related Coverage HTML section linking to earlier briefs"""
        if not related_briefs:
            return ""
        items = "\n".join(
            f'                <li><a href="{rb["url"]}">{rb["title"]} &mdash; {rb["date"]}</a></li>'
            for rb in related_briefs
        )
        return f"""
            <div class="related-briefs">
                <h2>Related Coverage</h2>
                <p>Earlier O'Dwyer briefs on similar themes:</p>
                <ul>
{items}
                </ul>
            </div>"""

    SITE_URL = "https://www.odwyercapital.com"

    def extract_headline(self, body_html: str, fallback: str) -> str:
        """Pull the article's unique opening <h2> headline for use as page title"""
        m = re.search(r'<h2[^>]*>(.*?)</h2>', body_html or '', re.DOTALL)
        if m:
            text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if text:
                return text
        return fallback

    def inject_seo(self, html_content: str, brief: Dict) -> str:
        """Give each article a unique <title>, meta description, canonical URL and Article schema"""
        headline = self.extract_headline(
            brief.get('body_html', ''),
            f"{brief.get('title', '')} - {brief.get('date', '')}"
        )
        excerpt = (brief.get('excerpt') or '').strip()
        page_url = f"{self.SITE_URL}/{brief.get('url', '')}"

        try:
            iso_date = datetime.strptime(brief.get('date', ''), "%B %d, %Y").strftime("%Y-%m-%d")
        except Exception:
            iso_date = datetime.now().strftime("%Y-%m-%d")

        # Unique <title> (use lambda so special chars in headline can't break the regex)
        new_title = f"{headline} | O'Dwyer Capital"
        html_content = re.sub(r'<title>.*?</title>', lambda m: f'<title>{new_title}</title>',
                              html_content, count=1, flags=re.DOTALL)

        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": headline,
            "description": excerpt,
            "datePublished": iso_date,
            "author": {"@type": "Organization", "name": "O'Dwyer Capital"},
            "publisher": {"@type": "Organization", "name": "O'Dwyer Capital", "url": self.SITE_URL},
            "mainEntityOfPage": page_url
        }
        meta_desc = excerpt.replace('"', '&quot;')
        head_extra = (
            f'    <meta name="description" content="{meta_desc}">\n'
            f'    <link rel="canonical" href="{page_url}">\n'
            f'    <script type="application/ld+json">{json.dumps(schema)}</script>\n'
        )
        return html_content.replace('</head>', head_extra + '</head>', 1)

    def generate_sitemap(self) -> str:
        """Regenerate sitemap.xml including every published article"""
        today = datetime.now().strftime("%Y-%m-%d")
        entries = [(f"{self.SITE_URL}/", today),
                   (f"{self.SITE_URL}/thoughts.html", today),
                   (f"{self.SITE_URL}/contact.html", today)]
        for a in self.existing_articles:
            u = a.get('url')
            if not u:
                continue
            try:
                lastmod = datetime.strptime(a.get('date', ''), "%B %d, %Y").strftime("%Y-%m-%d")
            except Exception:
                lastmod = today
            entries.append((f"{self.SITE_URL}/{u}", lastmod))

        urls = "\n".join(
            f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>"
            for loc, lastmod in entries
        )
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f'{urls}\n</urlset>\n')
        path = os.path.join(os.path.dirname(__file__), 'sitemap.xml')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(xml)
        print(f"Generated sitemap.xml with {len(entries)} URLs")
        return path

    def generate_feed(self) -> str:
        """Regenerate RSS feed (feed.xml) from the most recent published briefs"""
        def esc(s):
            return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        items = []
        for a in self.existing_articles[:20]:
            u = a.get('url')
            if not u:
                continue
            try:
                pub = datetime.strptime(a.get('date', ''), "%B %d, %Y").strftime("%a, %d %b %Y 13:30:00 GMT")
            except Exception:
                continue
            link = f"{self.SITE_URL}/{u}"
            items.append(
                f"    <item>\n"
                f"      <title>{esc(a.get('title', ''))} — {esc(a.get('date', ''))}</title>\n"
                f"      <link>{link}</link>\n"
                f"      <guid>{link}</guid>\n"
                f"      <pubDate>{pub}</pubDate>\n"
                f"      <description>{esc(a.get('excerpt', ''))}</description>\n"
                f"    </item>"
            )

        feed = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<rss version="2.0">\n'
                '  <channel>\n'
                "    <title>O'Dwyer Capital — Investment Briefs</title>\n"
                f'    <link>{self.SITE_URL}/thoughts.html</link>\n'
                "    <description>Daily investment briefs on energy transition, emerging technology, and strategic materials from O'Dwyer Capital.</description>\n"
                '    <language>en-us</language>\n'
                + "\n".join(items) + "\n"
                '  </channel>\n'
                '</rss>\n')
        path = os.path.join(os.path.dirname(__file__), 'feed.xml')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(feed)
        print(f"Generated feed.xml with {len(items)} items")
        return path

    def analyze_historical_trends(self, category_slug: str, current_themes: List[str]) -> Dict:
        """Analyze trends from historical briefs in this category"""
        historical_themes = {}
        category_briefs = [b for b in self.existing_articles if category_slug.lower() in b.get('slug', '').lower()]

        # Extract themes from historical briefs
        for brief in category_briefs[-10:]:  # Last 10 briefs
            excerpt = brief.get('excerpt', '').lower()
            for theme in current_themes:
                if theme.lower() in excerpt:
                    historical_themes[theme] = historical_themes.get(theme, 0) + 1

        # Identify new vs ongoing themes
        new_themes = [t for t in current_themes if historical_themes.get(t, 0) == 0]
        ongoing_themes = [t for t in current_themes if historical_themes.get(t, 0) > 0]
        accelerating_themes = [t for t in current_themes if historical_themes.get(t, 0) >= 2]

        return {
            'new_themes': new_themes,
            'ongoing_themes': ongoing_themes,
            'accelerating_themes': accelerating_themes,
            'historical_context': f"Based on analysis of {len(category_briefs)} historical briefs"
        }

    def create_brief(self, category: str, articles: List[Dict]) -> Dict:
        """Create an analytical brief from articles in a category"""
        if not articles:
            return None

        # Drop blocked aggregators and verify every candidate link is live
        # BEFORE anything cites it - dead links never reach the site.
        total = len(articles)
        articles = self.filter_live_articles(articles)
        print(f"   Source validation: {len(articles)} live of {total} fetched")
        if len(articles) < self.MIN_LIVE_SOURCES:
            print(f"   Skipped {category}: only {len(articles)} live sources "
                  f"(minimum {self.MIN_LIVE_SOURCES} required for a credible brief)")
            return None

        # Summarize key themes
        titles = [a.get('title', '') for a in articles[:5]]
        sources = [a.get('source', {}).get('name', '') for a in articles[:3]]

        # Extract current themes
        current_themes = self.extract_key_themes(titles)

        # Map category name to slug for trend analysis
        category_slug_map = {'Energy': 'energy-transition', 'Technology': 'emerging-tech', 'Innovation': 'materials'}
        category_slug = category_slug_map.get(category, category.lower().replace(' ', '-'))

        # Analyze historical trends
        trend_analysis = self.analyze_historical_trends(category_slug, current_themes)

        # Generate AI excerpt based on brief content and themes
        excerpt = self.generate_ai_excerpt(category, current_themes, articles)

        # Find related prior briefs (used for linking + so the body focuses on what's new)
        related_briefs = self.find_related_briefs(category_slug, current_themes)

        # Generate the FULL article body from today's news
        body_html = self.generate_article_body(category, current_themes, articles,
                                               trend_analysis, related_briefs)

        # Build trend context for the brief
        trend_context = []
        if trend_analysis['new_themes']:
            trend_context.append(f"New developments: {', '.join(trend_analysis['new_themes'])}")
        if trend_analysis['accelerating_themes']:
            trend_context.append(f"Accelerating trends: {', '.join(trend_analysis['accelerating_themes'])}")

        today_iso = datetime.now().strftime("%Y-%m-%d")

        # Display names matching the article page templates, so the listing title
        # and the page header agree (was: "Innovation" listing vs "Materials" page)
        display_map = {'Energy': 'Energy Transition', 'Technology': 'Emerging Tech', 'Innovation': 'Materials'}

        brief = {
            "id": self.next_id(),
            "title": f"{display_map.get(category, category)} Investment Brief",
            "slug": category.lower().replace(' ', '-'),
            "date": datetime.now().strftime("%B %d, %Y"),
            "url": f"{category_slug}-{today_iso}.html",
            "excerpt": excerpt,
            "body_html": body_html,
            "related_briefs": related_briefs,
            "tags": [category],
            "source": "O'Dwyer Analysis",
            "analysis_type": "analytical",
            "themes": current_themes if current_themes else ["Growth"],
            "investment_relevance": "high",
            "article_count": len(articles),
            "primary_sources": list(set(sources))[:3],
            "trend_analysis": trend_analysis,
            "trend_context": trend_context
        }

        return brief

    def update_articles_json(self, briefs: List[Dict]) -> str:
        """Update articles_data.json with new briefs (body_html lives in the HTML file, not the JSON)"""
        for brief in briefs:
            if brief:
                entry = {k: v for k, v in brief.items() if k not in ('body_html', 'related_briefs')}
                self.existing_articles.insert(0, entry)

        output_path = os.path.join(os.path.dirname(__file__), self.thoughts_file)

        try:
            with open(output_path, 'w') as f:
                json.dump(self.existing_articles, f, indent=2)
            print(f"Updated {output_path} with {len(briefs)} new briefs")
            return output_path
        except Exception as e:
            print(f"Error writing articles_data.json: {e}")
            return None

    def generate_html_files(self, briefs: List[Dict] = None) -> List[str]:
        """Copy template HTML files and update date from brief data - ONLY for categories with new briefs"""
        if not briefs:
            # No new briefs created, don't generate any HTML files
            return []

        generated_files = []
        today = datetime.now().strftime("%Y-%m-%d")

        template_map = {
            'energy-transition': 'energy-transition.html',
            'emerging-tech': 'emerging-tech.html',
            'materials': 'materials.html'
        }

        base_path = os.path.dirname(__file__)

        # Create a map of slug -> brief for easy lookup
        brief_map = {brief.get('slug', ''): brief for brief in briefs if brief.get('slug')}

        # Only generate HTML for categories that had new briefs
        for brief in briefs:
            slug = brief.get('slug', '')
            if slug not in template_map:
                continue

            template_file = template_map[slug]
            src_path = os.path.join(base_path, template_file)
            dst_file = f"{slug}-{today}.html"
            dst_path = os.path.join(base_path, dst_file)

            if os.path.exists(src_path):
                try:
                    # Read template (only used for page chrome: header, nav, styles, footer)
                    with open(src_path, 'r', encoding='utf-8', errors='replace') as f:
                        html_content = f.read()

                    # 1. Update date - matches ANY existing date, not a hardcoded one.
                    #    If the template has no Date line, inject one into article-meta.
                    brief_date = brief.get('date', '')
                    if re.search(r'<strong>Date:</strong>', html_content):
                        html_content = re.sub(
                            r'(<strong>Date:</strong>\s*)[A-Za-z]+ \d{1,2}, \d{4}',
                            lambda m: m.group(1) + brief_date,
                            html_content
                        )
                    else:
                        html_content = html_content.replace(
                            '<div class="article-meta">',
                            f'<div class="article-meta"><strong>Date:</strong> {brief_date} | ',
                            1
                        )

                    # 2. Replace the ENTIRE article body with today's AI-generated content.
                    #    This is the duplicate-article fix: previously the old body was
                    #    copied verbatim, so every "new" article had identical content.
                    body_html = brief.get('body_html', '')
                    if body_html:
                        tags_html = "".join(
                            f'<span class="tag">{t}</span>'
                            for t in (brief.get('tags', []) + brief.get('themes', []))
                        )
                        related_html = self.build_related_section(brief.get('related_briefs', []))
                        new_body = (
                            f'<div class="article-body">\n{body_html}\n'
                            f'{related_html}\n'
                            f'            <div class="tags">{tags_html}</div>\n'
                            f'        </div>'
                        )
                        html_content, n = re.subn(
                            r'<div class="article-body">.*?</div>\s*(?=</section>)',
                            lambda m: new_body,
                            html_content,
                            count=1,
                            flags=re.DOTALL
                        )
                        if n == 0:
                            print(f"WARNING: could not locate article-body in {template_file}; "
                                  f"skipping {dst_file} to avoid publishing a duplicate")
                            continue
                    else:
                        print(f"WARNING: no body generated for {slug}; "
                              f"skipping {dst_file} to avoid publishing a duplicate")
                        continue

                    # 3. Unique title, meta description, canonical URL, Article schema
                    html_content = self.inject_seo(html_content, brief)

                    # Write the dated article file
                    with open(dst_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)

                    generated_files.append(dst_file)
                    print(f"Generated: {dst_file}")
                except Exception as e:
                    print(f"Error generating {dst_file}: {e}")

        return generated_files

    def run(self) -> Dict:
        """Execute the publishing pipeline"""
        print("=" * 60)
        print("Starting O'Dwyer Capital Article Analyzer...")
        print("=" * 60)

        # Fetch articles from NewsAPI
        print("\n1. Fetching articles from NewsAPI...")
        articles = self.fetch_articles()

        if not articles:
            print("No articles fetched. Skipping brief generation.")
            return {'status': 'no_articles', 'publication_date': datetime.now().isoformat()}

        # Categorize articles
        print("\n2. Categorizing articles...")
        categorized = {'energy-transition': [], 'emerging-tech': [], 'materials': []}

        for article in articles:
            category = self.categorize_article(article)
            # Map Energy to energy-transition, Technology to emerging-tech, Innovation to materials
            if category == 'Energy':
                categorized['energy-transition'].append(article)
            elif category == 'Technology':
                categorized['emerging-tech'].append(article)
            elif category == 'Innovation':
                categorized['materials'].append(article)

        for cat, arts in categorized.items():
            print(f"   {cat}: {len(arts)} articles")

        # Create briefs
        print("\n3. Creating analytical briefs...")
        briefs = []
        category_names = {'energy-transition': 'Energy', 'emerging-tech': 'Technology', 'materials': 'Innovation'}
        for category, articles_list in categorized.items():
            brief = self.create_brief(category_names[category], articles_list)
            if brief:
                # Only publish if there are NEW or ACCELERATING themes
                has_new_content = (brief['trend_analysis']['new_themes'] or
                                  brief['trend_analysis']['accelerating_themes'])
                if has_new_content:
                    # Override slug with template-matching slug
                    brief['slug'] = category
                    briefs.append(brief)
                    print(f"   Created brief: {brief['title']} (NEW/ACCELERATING themes found)")
                else:
                    print(f"   Skipped {category}: No new themes since last brief")

        # Generate dated HTML files FIRST, so the JSON only lists articles that actually exist
        print("\n4. Generating dated HTML files...")
        html_files = self.generate_html_files(briefs)
        published_briefs = [b for b in briefs if b.get('url') in html_files]

        # Update JSON only for successfully generated articles
        print("\n5. Updating articles_data.json...")
        json_path = self.update_articles_json(published_briefs)

        # Keep search engines and feed readers up to date
        print("\n6. Regenerating sitemap.xml and feed.xml...")
        self.generate_sitemap()
        self.generate_feed()

        summary = {
            'articles_fetched': len(articles),
            'briefs_created': len(published_briefs),
            'html_files_created': len(html_files),
            'files': html_files,
            'publication_date': datetime.now().isoformat(),
            'status': 'success'
        }

        print("\n" + "=" * 60)
        print("PUBLICATION COMPLETE")
        print("=" * 60)
        print(f"Articles fetched: {len(articles)}")
        print(f"Briefs created: {len(published_briefs)}")
        print(f"HTML files: {', '.join(html_files)}")

        return summary


def main():
    analyzer = ArticleAnalyzer()
    summary = analyzer.run()
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
