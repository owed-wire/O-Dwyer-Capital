# O'Dwyer Capital News & Trend Scanner Setup

## Overview
Automated system to scan the internet for investment-relevant articles and trends across multiple sectors (Energy, Space, Technology, Finance, Innovation).

## Features

✅ **Multi-Sector Coverage**
- Energy (renewable, oil, nuclear, hydrogen, solar, wind)
- Space (satellites, launch vehicles, space commerce)
- Technology (AI, quantum, semiconductors, cloud, cybersecurity)
- Finance (fintech, crypto, digital banking, markets)
- Innovation (startups, disruptive tech, emerging trends)

✅ **Automated Scanning**
- Searches for investment-relevant articles and news
- Analyzes trends and patterns
- Extracts key themes and opportunities
- Identifies potential risks

✅ **Website Integration**
- Formats articles for Thoughts page
- Auto-tags by sector
- Saves as JSON for easy updates

## Setup Instructions

### Step 1: Get News API Key
1. Visit https://newsapi.org/
2. Sign up for free account
3. Copy your API key
4. Save as environment variable:

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("NEWS_API_KEY", "your_api_key_here", "User")
```

**Mac/Linux:**
```bash
export NEWS_API_KEY="your_api_key_here"
```

### Step 2: Enable Live News Scanning
Edit `news_scanner.py` and uncomment the NewsAPI section in `search_sector_news()`:

```python
# Uncomment these lines:
api_key = os.getenv('NEWS_API_KEY')
url = f"https://newsapi.org/v2/everything?q={search_query}&sortBy=publishedAt&apiKey={api_key}"
response = requests.get(url, timeout=10)
if response.status_code == 200:
    articles.extend(response.json().get('articles', []))
```

### Step 3: Run Manually
```bash
python news_scanner.py
```

This creates `articles_data.json` with formatted articles.

### Step 4: Set Up Scheduled Scanning
Option A: Windows Task Scheduler
- Task name: "O'Dwyer News Scanner"
- Trigger: Daily (or desired frequency)
- Action: Run `python news_scanner.py`
- Location: O'Dwyer Capital project folder

Option B: Linux/Mac Cron
```bash
# Run daily at 6 AM
0 6 * * * /usr/bin/python3 /path/to/news_scanner.py
```

Option C: Cloud Scheduler
- Use AWS Lambda, Google Cloud Scheduler, or Azure Functions
- Trigger: Daily or weekly
- Action: Run Python script

## Integration with Thoughts Page

### Manual Integration
1. Run `news_scanner.py`
2. Copy output from `articles_data.json`
3. Paste into `thoughts.html` JavaScript articles array

### Automated Integration (Advanced)
1. Set up webhook or API endpoint
2. Have Thoughts page fetch from `articles_data.json`
3. Auto-update articles list

### Example JavaScript Update
```javascript
// In thoughts.html, replace sample articles with:
fetch('articles_data.json')
    .then(response => response.json())
    .then(data => {
        articles = data;
        filterArticles('all');
    });
```

## Data Sources

### Recommended APIs
- **NewsAPI** - General news and articles (free tier: 100 requests/day)
- **Google News RSS** - No API key needed, RSS feeds available
- **Financial APIs**:
  - Alpha Vantage (market data)
  - IEX Cloud (company data)
  - Finnhub (financial news)
- **Industry-Specific**:
  - SpaceNews.com (space industry)
  - PV Magazine (energy)
  - TechCrunch (technology)

### Alternative Approach
Combine multiple free sources:
```python
# Add to scanner:
- Google News RSS feeds
- Industry blogs and publications
- Company press releases
- Research papers and whitepapers
```

## Customization

### Add New Sectors
Edit `__init__()`:
```python
self.sectors = {
    'your_sector': ['keyword1', 'keyword2', 'keyword3']
}
```

### Change Scan Frequency
Edit scheduler to run more/less often:
- Daily: Most current
- Weekly: Balanced
- Monthly: Summary view

### Filter Articles
Modify `search_sector_news()` to filter by:
- Publication date
- Source credibility
- Keyword relevance
- Article length/quality

## Output Format

### articles_data.json Structure
```json
[
    {
        "id": 1,
        "title": "Article Title",
        "date": "January 15, 2026",
        "excerpt": "Brief excerpt...",
        "tags": ["energy", "innovation"],
        "link": "https://...",
        "source": "NewsAPI"
    }
]
```

## Best Practices

✅ **DO:**
- Run scanner during off-peak hours
- Filter for high-quality sources
- Remove duplicate articles
- Manually review summaries before publishing
- Keep disclaimer visible on Thoughts page

❌ **DON'T:**
- Republish copyrighted content
- Present analysis as investment advice
- Forget to attribute sources
- Run scanner too frequently (API limits)

## Troubleshooting

**Issue: API Rate Limit Exceeded**
- Solution: Increase time between scans or upgrade API plan

**Issue: No Articles Found**
- Solution: Check API key, expand keywords, add new sources

**Issue: Articles Not Appearing**
- Solution: Verify JSON format, check file permissions

## Future Enhancements

🔮 **Potential Upgrades:**
- ML-powered trend analysis
- Sentiment analysis on articles
- Automatic summary generation
- Cross-reference with financial data
- Portfolio impact analysis
- Anomaly detection for risks

## Support

For API issues:
- NewsAPI: https://newsapi.org/docs
- Python docs: https://docs.python.org/
- Error messages contain troubleshooting info

## Version History

**v1.0** (January 2026)
- Initial framework
- Multi-sector support
- NewsAPI integration ready
- Thoughts page formatting

---

**Last Updated:** January 2026
**Framework Version:** 1.0
**Status:** Ready for setup
