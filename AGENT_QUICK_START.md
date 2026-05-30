# O'Dwyer Capital News Agent - Quick Start

## What It Does

The News Scanner Agent automatically searches the internet for investment-relevant articles, trends, and data across 5 key sectors:

🔋 **Energy** - Renewable energy, oil, nuclear, hydrogen, solar, wind
🚀 **Space** - Satellites, launch vehicles, space commerce  
💻 **Technology** - AI, quantum, semiconductors, cloud, cybersecurity
💰 **Finance** - Fintech, crypto, digital banking, markets
⚡ **Innovation** - Startups, disruptive tech, emerging trends

## Quick Setup (5 minutes)

### 1. Get API Key
Visit https://newsapi.org/ and sign up for free API key

### 2. Configure
Set environment variable:
```
NEWS_API_KEY=your_api_key_here
```

### 3. Enable Live Scanning
Edit `news_scanner.py` - uncomment lines 45-49 in the `search_sector_news()` function

### 4. Run It
```bash
python news_scanner.py
```

## How It Works

```
Scanner → Search APIs → Collect Articles → Analyze Trends → Format for Website
```

**Input:** API keys, sector keywords
**Processing:** Searches, filters, categorizes
**Output:** `articles_data.json` ready for Thoughts page

## Automation Options

### Option A: Daily Automatic Scans
Set up Windows Task Scheduler or cron job to run daily

### Option B: Weekly Manual Review
Run weekly, review articles, manually add best ones

### Option C: Hybrid
Auto-scan daily for monitoring, manual curation for publishing

## Integration with Thoughts Page

Current: Manual paste from `articles_data.json`

Simple update (2 lines of code):
```javascript
// In thoughts.html, replace the sample articles array with:
fetch('articles_data.json')
    .then(r => r.json())
    .then(data => { articles = data; filterArticles('all'); })
```

## What Gets Collected

For each article:
- **Title** - Article headline
- **Date** - Publication date
- **Excerpt** - First 200 characters
- **Tags** - Sector (energy, space, etc.)
- **Link** - URL to full article
- **Source** - Publication name

## Expected Output

~20-50 articles per week from quality sources covering:
- Investment trends
- Emerging opportunities
- Risk indicators
- Industry analysis
- Market data
- Technology breakthroughs

## Cost

✅ **FREE** - NewsAPI free tier: 100 requests/day
✅ **No credit card** - Just sign up

Premium sources (optional):
- Alpha Vantage (market data)
- Finnhub (financial news)
- Industry APIs (specialized coverage)

## Example Workflow

**Day 1:** Set up API key
**Day 2:** Run first scan → Get 30+ articles
**Day 3+:** Schedule daily scans
**Weekly:** Review, select best articles
**Publish:** Add to Thoughts page

## Key Features

✨ **Automatic** - Set it and forget it
✨ **Multi-Source** - Aggregates from 100+ news outlets
✨ **Smart Tagging** - Auto-categorizes by sector
✨ **Web-Ready** - Formatted for immediate use
✨ **Flexible** - Add/remove sectors as needed

## Next Steps

1. ✅ Download API key from NewsAPI
2. ✅ Follow full setup in NEWS_SCANNER_SETUP.md
3. ✅ Run `python news_scanner.py` first time
4. ✅ Set up automation (optional but recommended)
5. ✅ Integrate with Thoughts page

## Support Files

- `news_scanner.py` - Main agent script
- `NEWS_SCANNER_SETUP.md` - Detailed setup guide
- `articles_data.json` - Output file (auto-generated)
- `AGENT_QUICK_START.md` - This file

## Questions?

See NEWS_SCANNER_SETUP.md for detailed troubleshooting and customization options.

---

**Ready to start?** Follow the 5-minute setup above!
