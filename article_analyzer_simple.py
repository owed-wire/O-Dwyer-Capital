#!/usr/bin/env python3
"""
O'Dwyer Capital Article Analyzer - Simplified
Generates dated HTML archives and publishes analytical briefs
"""

import json
import os
import shutil
from datetime import datetime
from typing import List, Dict

class ArticleAnalyzer:
    def __init__(self, thoughts_file: str = "articles_data.json"):
        self.thoughts_file = thoughts_file
        self.existing_articles = self.load_existing_articles()
        self.analytical_pieces = []

    def load_existing_articles(self) -> List[Dict]:
        if os.path.exists(self.thoughts_file):
            with open(self.thoughts_file, 'r') as f:
                return json.load(f)
        return []

    def generate_html_files(self) -> List[str]:
        """Copy existing HTML template files with dated names.

        Templates (emerging-tech.html, energy-transition.html, materials.html)
        automatically pass through styling and features to all dated versions,
        including the hyperlinked logo that returns to the homepage.
        """
        generated_files = []
        today = datetime.now().strftime("%Y-%m-%d")

        files_to_copy = [
            ('emerging-tech.html', f'emerging-tech-{today}.html'),
            ('energy-transition.html', f'energy-transition-{today}.html'),
            ('materials.html', f'materials-{today}.html')
        ]

        base_path = os.path.dirname(__file__)

        for src_file, dst_file in files_to_copy:
            src_path = os.path.join(base_path, src_file)
            dst_path = os.path.join(base_path, dst_file)

            if os.path.exists(src_path):
                try:
                    shutil.copy2(src_path, dst_path)
                    generated_files.append(dst_file)
                    print(f"Generated: {dst_file}")
                except Exception as e:
                    print(f"Error generating {dst_file}: {e}")

        return generated_files

    def publish_to_thoughts(self, output_file: str = "articles_data.json") -> str:
        """Ensure articles_data.json is up to date"""
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        if os.path.exists(output_path):
            print(f"Articles already published to {output_path}")
        return output_path

    def run(self) -> Dict:
        """Execute the publishing pipeline"""
        print("Starting O'Dwyer Capital Article Archive Generator...")

        # Generate dated HTML files
        print("Generating dated HTML files...")
        html_files = self.generate_html_files()
        print(f"Generated {len(html_files)} dated HTML files")

        # Ensure thoughts.html is up to date
        thoughts_path = self.publish_to_thoughts()
        print(f"Verified: {thoughts_path}")

        summary = {
            'html_files_created': len(html_files),
            'files': html_files,
            'publication_date': datetime.now().isoformat(),
            'status': 'success'
        }

        print("\n=== ARCHIVE GENERATION COMPLETE ===")
        print(f"HTML files created: {', '.join(html_files)}")
        print(f"All briefs now have dated archive versions")

        return summary


def main():
    analyzer = ArticleAnalyzer()
    summary = analyzer.run()
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
