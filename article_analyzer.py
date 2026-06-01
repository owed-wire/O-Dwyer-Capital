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

        # Optimized for free tier: 2 queries instead of 3
        # Uses AND/OR operators to combine keywords efficiently
        queries = [
            "(renewable OR energy OR battery OR storage) AND (transition OR investment)",
            "(AI OR space OR technology OR materials) AND (innovation OR emerging)"
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
                        if url not in seen_urls:
                            all_articles.append(article)
                            seen_urls.add(url)
                else:
                    print(f"NewsAPI error: {response.status_code}")
            except Exception as e:
                print(f"Error fetching articles for '{query}': {e}")

        print(f"Fetched {len(all_articles)} articles")
        return all_articles

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

        # Build trend context for the brief
        trend_context = []
        if trend_analysis['new_themes']:
            trend_context.append(f"New developments: {', '.join(trend_analysis['new_themes'])}")
        if trend_analysis['accelerating_themes']:
            trend_context.append(f"Accelerating trends: {', '.join(trend_analysis['accelerating_themes'])}")

        brief = {
            "id": 119,
            "title": f"{category} Investment Brief",
            "slug": category.lower().replace(' ', '-'),
            "date": datetime.now().strftime("%B %d, %Y"),
            "excerpt": excerpt,
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
        """Update articles_data.json with new briefs"""
        for brief in briefs:
            if brief:
                self.existing_articles.insert(0, brief)

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
        """Generate HTML files from brief data - ONLY for categories with new briefs"""
        if not briefs:
            # No new briefs created, don't generate any HTML files
            return []

        generated_files = []
        base_path = os.path.dirname(__file__)

        for brief in briefs:
            slug = brief.get('slug', '')
            if not slug:
                continue

            # Extract date and format for filename
            date_str = brief.get('date', '')
            # Parse "June 01, 2026" to "2026-06-01"
            try:
                date_obj = datetime.strptime(date_str, "%B %d, %Y")
                date_filename = date_obj.strftime("%Y-%m-%d")
            except:
                date_filename = datetime.now().strftime("%Y-%m-%d")

            dst_file = f"{slug}-{date_filename}.html"
            dst_path = os.path.join(base_path, dst_file)

            try:
                html_content = self.generate_html_from_brief(brief)
                with open(dst_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                generated_files.append(dst_file)
                print(f"Generated: {dst_file}")
            except Exception as e:
                print(f"Error generating {dst_file}: {e}")

        return generated_files

    def generate_html_from_brief(self, brief: Dict) -> str:
        """Generate HTML content from brief data"""
        title = brief.get('title', 'Investment Brief')
        date = brief.get('date', '')
        excerpt = brief.get('excerpt', '')
        tags = brief.get('tags', [])
        themes = brief.get('themes', [])

        # Create tag HTML
        tag_html = ''.join([f'<span class="tag">{tag}</span>' for tag in tags])
        theme_html = ''.join([f'<span class="tag">{theme}</span>' for theme in themes])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - O'Dwyer Capital</title>
    <link rel="icon" type="image/png" href="favicon.png">
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-32PXHG0656"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-32PXHG0656');
    </script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --primary-green: #1a4d2e;
            --secondary-green: #2d6a4f;
            --accent-gold: #d4a574;
            --dark-gold: #c9965f;
            --light-bg: #f9f8f6;
            --white: #ffffff;
            --text-dark: #333333;
            --text-gray: #666666;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-dark);
            background: var(--white);
        }}

        a {{
            color: var(--accent-gold);
            text-decoration: none;
            transition: color 0.3s;
        }}

        a:hover {{
            color: var(--dark-gold);
        }}

        header {{
            background: var(--white);
            padding: 15px 50px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e0e0e0;
        }}

        .logo-container {{
            display: flex;
            align-items: center;
            text-decoration: none;
        }}

        .logo-container img {{
            height: 60px;
            width: auto;
        }}

        nav {{
            display: flex;
            gap: 40px;
            margin-left: auto;
        }}

        nav a {{
            color: var(--text-dark);
            font-weight: 500;
            font-size: 15px;
        }}

        .page-header {{
            background: linear-gradient(135deg, var(--primary-green) 0%, var(--secondary-green) 100%);
            padding: 60px 50px;
            color: var(--white);
        }}

        .page-header h1 {{
            font-size: 48px;
            margin-bottom: 15px;
        }}

        .page-header p {{
            font-size: 18px;
            color: var(--accent-gold);
        }}

        .content {{
            max-width: 900px;
            margin: 0 auto;
            padding: 60px 50px;
        }}

        .article-meta {{
            color: var(--text-gray);
            font-size: 14px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e0e0e0;
        }}

        .article-body {{
            font-size: 16px;
            line-height: 1.8;
            color: var(--text-dark);
        }}

        .article-body h2 {{
            color: var(--primary-green);
            font-size: 28px;
            margin: 40px 0 20px 0;
        }}

        .article-body p {{
            margin-bottom: 15px;
        }}

        .article-body strong {{
            color: var(--primary-green);
            font-weight: 600;
        }}

        .back-link {{
            display: inline-block;
            margin-bottom: 30px;
            color: var(--accent-gold);
            font-weight: 500;
        }}

        .tags {{
            display: flex;
            gap: 8px;
            margin-top: 40px;
            padding-top: 40px;
            border-top: 1px solid #e0e0e0;
            flex-wrap: wrap;
        }}

        .tag {{
            background: var(--light-bg);
            color: var(--primary-green);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            border: 1px solid var(--accent-gold);
        }}

        footer {{
            background: var(--primary-green);
            color: var(--white);
            padding: 50px;
            text-align: center;
            margin-top: 60px;
        }}

        footer p {{
            margin-bottom: 10px;
            font-size: 15px;
        }}

        footer p.tagline {{
            color: var(--accent-gold);
            font-style: italic;
            font-weight: 500;
        }}

        footer p.copyright {{
            font-size: 13px;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <!-- HEADER -->
    <header>
        <a href="index.html" class="logo-container">
            <img src="odwyer_capital_logo_primary.png" alt="O'Dwyer Capital">
        </a>
        <nav>
            <a href="index.html">Home</a>
            <a href="thoughts.html" class="active">Thoughts</a>
            <a href="contact.html">Contact</a>
        </nav>
    </header>

    <!-- PAGE HEADER -->
    <section class="page-header">
        <h1>{title}</h1>
        <p>Strategic analysis for family office allocation</p>
    </section>

    <!-- MAIN CONTENT -->
    <section class="content">
        <a href="thoughts.html" class="back-link">← Back to Thoughts</a>

        <div class="article-meta">
            <strong>Date:</strong> {date} | <strong>Source:</strong> O'Dwyer Analysis
        </div>

        <div class="article-body">
            <p>{excerpt}</p>

            <div class="tags">
                {tag_html}
                {theme_html}
            </div>
        </div>
    </section>

    <!-- FOOTER -->
    <footer>
        <p>&copy; 2026 O'Dwyer Capital. All rights reserved.</p>
        <p class="tagline">Invested in What Endures</p>
        <p class="copyright">Private Family Office | Generational Wealth Stewardship</p>
    </footer>
</body>
</html>"""
        return html

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

        # Update JSON
        print("\n4. Updating articles_data.json...")
        json_path = self.update_articles_json(briefs)

        # Generate dated HTML files ONLY for categories with new briefs
        print("\n5. Generating dated HTML files...")
        html_files = self.generate_html_files(briefs)

        summary = {
            'articles_fetched': len(articles),
            'briefs_created': len(briefs),
            'html_files_created': len(html_files),
            'files': html_files,
            'publication_date': datetime.now().isoformat(),
            'status': 'success'
        }

        print("\n" + "=" * 60)
        print("PUBLICATION COMPLETE")
        print("=" * 60)
        print(f"Articles fetched: {len(articles)}")
        print(f"Briefs created: {len(briefs)}")
        print(f"HTML files: {', '.join(html_files)}")

        return summary


def main():
    analyzer = ArticleAnalyzer()
    summary = analyzer.run()
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
