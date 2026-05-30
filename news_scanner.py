#!/usr/bin/env python3
"""
O'Dwyer Capital News & Trend Scanner
Scans the internet for investment-relevant articles and trends by sector
"""

import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import os

class NewsScanner:
    """Scans for investment-relevant news and trends by sector"""

    def __init__(self):
        self.sectors = {
            'space': ['Rocket Lab', 'SpaceX'],
            'materials': ['graphene'],
            'reshoring': ['US manufacturing', 'energy transportation'],
            'energy_transition': ['renewable energy', 'grid storage', 'battery'],
            'emerging_tech': ['semiconductors', 'artificial intelligence']
        }
        self.articles = []

    def search_sector_news(self, sector: str, keywords: List[str]) -> List[Dict]:
        """
        Search for news and articles related to a specific sector

        Args:
            sector: The industry sector
            keywords: List of keywords to search for

        Returns:
            List of article dictionaries
        """
        articles = []

        for keyword in keywords:
            try:
                search_query = f"{keyword} investment trends analysis"
                print(f"Scanning {sector}: {keyword}...")

                api_key = os.getenv('NEWS_API_KEY')
                if not api_key:
                    print("Warning: NEWS_API_KEY not set. Using template structure.")
                    continue

                url = f"https://newsapi.org/v2/everything?q={search_query}&sortBy=publishedAt&apiKey={api_key}"

                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    articles.extend(response.json().get('articles', []))
                else:
                    print(f"API error for {keyword}: {response.status_code}")

            except Exception as e:
                print(f"Error searching {keyword}: {e}")

        return articles

    def analyze_trends(self, articles: List[Dict]) -> Dict:
        """
        Analyze trends from collected articles

        Args:
            articles: List of articles

        Returns:
            Summary of trends and insights
        """
        trends = {
            'total_articles': len(articles),
            'date_scanned': datetime.now().isoformat(),
            'sectors_analyzed': len(self.sectors),
            'key_themes': [],
            'emerging_opportunities': [],
            'risk_indicators': []
        }

        return trends

    def scan_all_sectors(self) -> List[Dict]:
        """
        Scan all sectors for investment-relevant information

        Returns:
            Organized list of articles by sector
        """
        results = []

        for sector, keywords in self.sectors.items():
            sector_articles = self.search_sector_news(sector, keywords)
            results.append({
                'sector': sector,
                'articles_found': len(sector_articles),
                'articles': sector_articles,
                'scan_date': datetime.now().isoformat()
            })

        return results

    def format_for_thoughts_page(self, articles: List[Dict]) -> List[Dict]:
        """
        Format collected articles for the Thoughts page

        Args:
            articles: Raw articles from search

        Returns:
            Formatted articles ready for the website
        """
        formatted = []

        for article in articles:
            formatted_article = {
                'id': len(formatted) + 1,
                'title': article.get('title', 'Untitled'),
                'date': datetime.fromisoformat(article.get('publishedAt', datetime.now().isoformat())).strftime('%B %d, %Y'),
                'excerpt': article.get('description', article.get('content', ''))[:200],
                'tags': self.extract_tags(article),
                'link': article.get('url', '#'),
                'source': article.get('source', {}).get('name', 'Unknown')
            }
            formatted.append(formatted_article)

        return formatted

    def extract_tags(self, article: Dict) -> List[str]:
        """Extract relevant tags from article"""
        tags = []
        content = f"{article.get('title', '')} {article.get('description', '')}".lower()

        for sector, keywords in self.sectors.items():
            if any(keyword.lower() in content for keyword in keywords):
                tags.append(sector)

        return tags if tags else ['emerging_tech']

    def save_to_json(self, articles: List[Dict], filename: str = 'articles_data.json'):
        """
        Save formatted articles to JSON for website integration

        Args:
            articles: Formatted articles
            filename: Output filename
        """
        output_path = os.path.join(os.path.dirname(__file__), filename)

        with open(output_path, 'w') as f:
            json.dump(articles, f, indent=2)

        print(f"Saved {len(articles)} articles to {filename}")
        return output_path

    def run(self):
        """Execute full scan and process"""
        print("Starting O'Dwyer Capital News Scanner...")
        print(f"Scanning sectors: {', '.join(self.sectors.keys())}")

        sector_results = self.scan_all_sectors()

        all_articles = []
        for sector_result in sector_results:
            all_articles.extend(sector_result['articles'])

        formatted_articles = self.format_for_thoughts_page(all_articles)

        self.save_to_json(formatted_articles)

        print(f"\n=== SCAN COMPLETE ===")
        print(f"Total articles collected: {len(all_articles)}")
        print(f"Articles formatted: {len(formatted_articles)}")
        print(f"Sectors scanned: {len(self.sectors)}")

        return formatted_articles


def main():
    """Main entry point"""
    import sys

    skip_analyzer = '--skip-analyzer' in sys.argv or '--no-analyze' in sys.argv

    scanner = NewsScanner()
    articles = scanner.run()

    if skip_analyzer:
        print("\n" + "="*50)
        print("Raw articles collected and saved")
        print("="*50)
        print(f"\nCollected: {len(articles)} articles")
        print("Status: Ready for analysis")
        print("\nTo generate AI analysis and publish:")
        print("python article_analyzer.py")
        return

    print("\n" + "="*50)
    print("Starting Article Analyzer...")
    print("="*50 + "\n")

    try:
        from article_analyzer import ArticleAnalyzer
        analyzer = ArticleAnalyzer()
        analyzer.run()
        print("\n" + "="*50)
        print("PIPELINE COMPLETE")
        print("="*50)
        print("Articles analyzed and published to Thoughts page!")
    except Exception as e:
        print(f"Error running analyzer: {e}")
        print("Run 'python article_analyzer.py' manually if needed")


if __name__ == '__main__':
    main()
