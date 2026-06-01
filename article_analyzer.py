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

class ArticleAnalyzer:
    def __init__(self, api_key: str = None, thoughts_file: str = "articles_data.json"):
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')
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
        """
        now = datetime.utcnow()

        # If it's Monday
        if now.weekday() == 0:  # 0 = Monday
            # Get articles from Friday 5pm through Monday 8am
            friday = now - timedelta(days=3)
            friday = friday.replace(hour=17, minute=0, second=0, microsecond=0)
            from_date = friday
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

    def generate_professional_excerpt(self, category: str, titles: List[str]) -> str:
        """Generate a professional summary based on actual article themes"""
        themes = self.extract_key_themes(titles)

        if not themes:
            # Fallback descriptions if no themes found
            defaults = {
                'Energy': "Recent developments in renewable energy and grid infrastructure transforming market dynamics",
                'Technology': "Emerging technology trends reshaping competitive landscapes and investor priorities",
                'Innovation': "Breakthrough innovations creating new investment opportunities across sectors"
            }
            return defaults.get(category, defaults['Innovation'])

        # Create professional summary from themes
        theme_text = ' and '.join(themes)
        summaries = {
            'Energy': f"Explore how {theme_text} are reshaping the energy sector and creating investment opportunities",
            'Technology': f"Discover key developments in {theme_text} and their implications for technology investments",
            'Innovation': f"Learn about breakthrough progress in {theme_text} and emerging market opportunities"
        }

        return summaries.get(category, summaries['Innovation'])

    def h(self, category_slug: str, current_themes: List[str]) -> Dict:
        """Analyze trends from historical briefs in this category"""
        historical_themes = {}
        category_briefs = [b for b in self.existing_articles if category.lower() in b.get('slug', '').lower()]

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

        # Analyze historical trends
        trend_analysis = self.analyze_historical_trends(category_slug, current_themes)

                # Map category name to slug for trend analysis
                category_slug_map = {'Energy': 'energy-transition', 'Technology': 'emerging-tech', 'Innovation': 'materials'}
                category_slug = category_slug_map.get(category, category.lower().replace(' ', '-'))hanalyze_historical_trends(category, current_themes)    
        # Generate professional excerpt based on actual themes
        excerpt = self.generate_professional_excerpt(category, titles)

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

    def generate_html_files(self) -> List[str]:
        """Copy template HTML files with dated names"""
        generated_files = []
        today = datetime.now().strftime("%Y-%m-%d")

        template_map = {
            'energy-transition': 'energy-transition.html',
            'emerging-tech': 'emerging-tech.html',
            'materials': 'materials.html'
        }

        base_path = os.path.dirname(__file__)

        for slug, template_file in template_map.items():
            src_path = os.path.join(base_path, template_file)
            dst_file = f"{slug}-{today}.html"
            dst_path = os.path.join(base_path, dst_file)

            if os.path.exists(src_path):
                try:
                    shutil.copy2(src_path, dst_path)
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
                # Override slug with template-matching slug
                brief['slug'] = category
                briefs.append(brief)
                print(f"   Created brief: {brief['title']}")

        # Update JSON
        print("\n4. Updating articles_data.json...")
        json_path = self.update_articles_json(briefs)

        # Generate dated HTML files
        print("\n5. Generating dated HTML files...")
        html_files = self.generate_html_files()

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
