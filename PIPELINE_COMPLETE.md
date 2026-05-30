# O'Dwyer Capital Complete Content Pipeline

## Full Workflow Overview

The complete system has three integrated agents working together:

```
STEP 1: NEWS SCANNER              STEP 2: ARTICLE ANALYZER          STEP 3: PUBLISH
(Collect Raw Data)                (Enhance & Analyze)               (Display on Website)

news_scanner.py                   article_analyzer.py               thoughts.html
    |                                  |                                  |
    v                                  v                                  v
Search 100+ sources          Analyze & extract themes         Automatically display
Aggregate articles           Generate analytical pieces        articles by sector
Filter by sector             Cross-reference content           Tag filtering
Output: 30-50/week          Output: 15-25/week                Real-time updates
```

## Three-Step Process

### STEP 1: News Scanner (news_scanner.py)

**What it does:**
- Searches internet for investment-relevant articles
- Covers 5 sectors: Energy, Space, Technology, Finance, Innovation
- Filters for quality sources
- Tags articles by sector

**Output:** `articles_data.json` with raw articles
**Frequency:** Daily or weekly
**Cost:** Free (NewsAPI free tier)

**Run command:**
```bash
python news_scanner.py
```

### STEP 2: Article Analyzer (article_analyzer.py)

**What it does:**
- Reads raw articles from news_scanner
- Analyzes themes, trends, relevance
- Cross-references with existing articles
- Generates analytical pieces
- Optional: AI-enhanced content using Claude

**Output:** Enhanced `articles_data.json` with analysis
**Frequency:** After news_scanner completes
**Cost:** Free (or optional Claude API)

**Run command:**
```bash
python article_analyzer.py
```

### STEP 3: Publish to Website

**What it does:**
- Articles automatically appear on Thoughts page
- Filtered by sector tags
- Cross-linked to related content
- Real-time updates if using fetch()

**Display:** thoughts.html with interactive filters
**Update:** Automatic (no manual steps)
**Cost:** Free

## Quick Start: 10 Minutes

### 1. Configure News Scanner (5 min)
```bash
# Get API key from https://newsapi.org/
# Set environment variable
set NEWS_API_KEY=your_key_here

# Enable live scanning in news_scanner.py (lines 45-49)
# Uncomment: api_key = os.getenv('NEWS_API_KEY')
```

### 2. Test Pipeline (3 min)
```bash
# Run news scanner
python news_scanner.py

# Run analyzer
python article_analyzer.py

# Check output
# articles_data.json now has raw articles + analytical pieces
```

### 3. Publish (2 min)
Articles automatically appear on Thoughts page!

## Detailed Workflows

### Daily Workflow

**Morning (7 AM):**
1. `news_scanner.py` runs automatically
2. Collects 30-50 articles from overnight
3. Tags by sector

**Mid-morning (8 AM):**
1. `article_analyzer.py` runs automatically
2. Analyzes collected articles
3. Generates 15-25 analytical pieces
4. Publishes to website

**Result:** Fresh analytical content every morning

### Weekly Curation Workflow

**Monday 9 AM:**
1. Both scanners run
2. Accumulate week's articles (150-250)

**Monday 4 PM:**
1. Manual review of articles
2. Select best 10-15 pieces
3. Mark as "featured"
4. Publish to Thoughts page

**Result:** High-quality, curated weekly content

### Manual Workflow (No Automation)

Perfect if you want full control:

**Step 1: Run scanners manually**
```bash
python news_scanner.py  # Collect news
python article_analyzer.py  # Analyze
```

**Step 2: Review and curate**
- Open articles_data.json
- Select articles you want
- Remove duplicates/low-quality items
- Add commentary

**Step 3: Publish**
- Copy curated articles to thoughts.html
- Or use fetch() to auto-import
- Articles appear on website

## System Architecture

```
+-------------------+
| News Scanner      |
| - Search APIs     |
| - Filter articles |
| - Tag by sector   |
+------- + --------+
         |
    articles_data.json (raw)
         |
         v
+-------------------+
| Article Analyzer  |
| - Extract themes  |
| - Assess relevance|
| - Cross-reference |
| - Generate analysis
+------- + --------+
         |
    articles_data.json (enhanced)
         |
         v
+-------------------+
| Thoughts Page     |
| - Display articles|
| - Filter by tag   |
| - Show analysis   |
+-------------------+
```

## Data Flow

**Raw Article:**
```json
{
    "id": 1,
    "title": "Energy Company Invests in Solar",
    "excerpt": "Major energy company announces...",
    "tags": ["energy"],
    "source": "NewsAPI"
}
```

**Enhanced Article (After Analysis):**
```json
{
    "id": 1,
    "title": "Analysis: Energy Company Invests in Solar",
    "excerpt": "Analysis of energy company's solar investment...",
    "tags": ["energy"],
    "themes": ["innovation", "growth"],
    "investment_relevance": "high",
    "trend_type": "accelerating",
    "related_articles": [
        {id: 5, title: "Solar Energy Market Growth"},
        {id: 8, title: "Renewable Energy Trends"}
    ],
    "analysis_type": "analytical"
}
```

## Automation Options

### Option A: Windows Task Scheduler
1. Create batch file: `run_pipeline.bat`
2. Add to Task Scheduler
3. Set trigger: Daily 7 AM
4. Automatic every day

### Option B: Cron (Mac/Linux)
```bash
# Edit crontab
crontab -e

# Add line for daily 7 AM
0 7 * * * /path/to/run_pipeline.sh
```

### Option C: Cloud Solutions
- AWS Lambda
- Google Cloud Functions
- Azure Functions
- Heroku

### Option D: Manual (No Automation)
Run manually whenever you want new articles

## Integration Checklist

- [ ] News Scanner configured with API key
- [ ] News Scanner tested (produces articles)
- [ ] Article Analyzer tested (produces analysis)
- [ ] articles_data.json appears on disk
- [ ] Thoughts page updated to fetch articles
- [ ] Articles appear on website
- [ ] Automation set up (if desired)
- [ ] Cross-referencing working correctly

## Monitoring & Maintenance

### Weekly Check
- [ ] Articles appearing on Thoughts page
- [ ] Tags are accurate
- [ ] Cross-references valid
- [ ] No errors in console

### Monthly Review
- [ ] Check article quality
- [ ] Remove outdated content
- [ ] Verify sector coverage balanced
- [ ] Update keywords if needed

### Quarterly Optimization
- [ ] Analyze which sectors get most interest
- [ ] Adjust keywords for better results
- [ ] Consider new data sources
- [ ] Review and refine themes

## Troubleshooting

**No articles appearing?**
1. Check news_scanner.py has valid API key
2. Verify articles_data.json is created
3. Check thoughts.html fetch() is working
4. Review browser console for errors

**Articles showing but not analyzing?**
1. Run article_analyzer.py manually
2. Check for errors in console
3. Verify articles_data.json format
4. Ensure read/write permissions

**Related articles not showing?**
1. Check tags are consistent
2. Verify existing articles have tags
3. Run analyzer on sample set
4. Check cross-reference logic

**Automation not running?**
1. Test scripts manually first
2. Check environment variables set
3. Verify task scheduler/cron setup
4. Check system logs for errors

## Performance Tips

- Run news_scanner daily (30-50 articles/day)
- Run analyzer after scanner completes
- Clean up very old articles monthly
- Keep articles_data.json < 10MB
- Archive older articles if needed

## Security Notes

- Store API keys in environment variables (not code)
- Don't commit API keys to git
- Use HTTPS for API calls (automatic with requests library)
- Validate article sources before publishing
- Review content before public display

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| News Scanner | Free | NewsAPI free tier (100 requests/day) |
| Article Analyzer | ~$0.01/article | Claude API for AI-enhanced analysis (enabled by default) |
| Thoughts Page | Free | Just HTML/JavaScript on website |
| Alternative | Free | Template-based articles if Claude API unavailable |
| Total Monthly | $0-20 | Depends on article volume and Claude API usage |

## Next Steps

1. **Immediate (Today):**
   - [ ] Get NewsAPI key
   - [ ] Configure news_scanner.py
   - [ ] Run first scan

2. **Short-term (This Week):**
   - [ ] Configure article_analyzer.py
   - [ ] Set up automation (optional)
   - [ ] Test full pipeline

3. **Long-term (Ongoing):**
   - [ ] Monitor article quality
   - [ ] Refine keywords and themes
   - [ ] Add more data sources
   - [ ] Consider Claude API enhancement

## File References

- `news_scanner.py` - Collects raw articles
- `article_analyzer.py` - Analyzes and enhances
- `NEWS_SCANNER_SETUP.md` - News scanner guide
- `ANALYZER_SETUP.md` - Analyzer guide
- `PIPELINE_COMPLETE.md` - This file
- `thoughts.html` - Display website
- `articles_data.json` - Data interchange format

## Support

For issues or questions:
1. Check relevant setup guide
2. Review troubleshooting section
3. Test components individually
4. Check system logs
5. Verify file permissions

---

**Status:** Ready for production
**Last Updated:** January 2026
**Version:** 1.0

You now have a complete, automated content pipeline!
