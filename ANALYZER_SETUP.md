# O'Dwyer Capital Article Analyzer & Publisher

## Overview

The Article Analyzer Agent converts raw news articles from `news_scanner.py` into deeper analytical pieces that:

✅ Extract key themes and trends
✅ Assess investment relevance
✅ Cross-reference with existing Thoughts
✅ Generate comprehensive analysis
✅ Automatically publish to website

## How It Works

```
news_scanner.py (Raw Articles)
        ↓
article_analyzer.py (Analysis & Enhancement)
        ↓
articles_data.json (Published to Thoughts)
```

## Features

### 1. **Theme Extraction**
Identifies key themes from articles:
- Disruption / Innovation
- Growth / Expansion
- Risk / Challenge
- Consolidation / Partnership
- Regulation / Compliance
- Efficiency / Optimization

### 2. **Investment Assessment**
Evaluates relevance level:
- **High** - Direct investment implications
- **Medium** - Market/business impact
- **Low** - General interest

### 3. **Trend Identification**
Classifies trend type:
- **Emerging** - New/early stage
- **Accelerating** - Growing momentum
- **Consolidating** - M&A/partnerships
- **Maturing** - Established/saturation
- **Disrupting** - Competitive threat

### 4. **Cross-Reference**
Links to related Thoughts articles:
- Matches tags across articles
- Identifies thematic connections
- Creates knowledge web

### 5. **Analysis Generation**
Produces comprehensive articles:
- Synthesizes findings
- Provides sector context
- Notes investment implications
- Optional: AI-enhanced content (Claude API)

## Setup Instructions

### Step 1: Basic Setup (No AI Enhancement)
```bash
python article_analyzer.py
```

This runs the analyzer with template-based articles. Ready to use immediately!

### Step 2: Configure Claude API (Enabled by Default)

The article analyzer now uses Claude API by default for AI enhanced analysis.

#### Get Anthropic API Key
1. Visit https://console.anthropic.com/
2. Sign up for account
3. Create API key
4. Set environment variable:

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your_key_here", "User")
```

**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY="your_api_key_here"
```

#### How It Works
The analyzer automatically uses Claude API when available:
- Checks for ANTHROPIC_API_KEY environment variable
- Falls back to template format if API is unavailable
- Creates comprehensive analytical articles using AI
- Each article generation takes 1-2 seconds

No code changes needed: just set the environment variable!

## Workflow

### Pipeline Flow

**Step 1: Collect News**
```bash
python news_scanner.py
# Output: articles_data.json with raw articles
```

**Step 2: Analyze & Enhance**
```bash
python article_analyzer.py
# Reads: articles_data.json (from news_scanner)
# Output: articles_data.json (with analytical pieces added)
```

**Step 3: Publish**
Articles automatically appear on Thoughts page via existing JavaScript:
```javascript
fetch('articles_data.json')
    .then(r => r.json())
    .then(data => { articles = data; filterArticles('all'); })
```

## Analysis Process

### What Gets Analyzed

For each raw article, the analyzer:

1. **Extracts Themes**
   - Scans title and excerpt
   - Identifies 1-3 dominant themes
   - Tags with relevance

2. **Assesses Relevance**
   - Investment focus: HIGH
   - Market/business: MEDIUM
   - General interest: LOW

3. **Identifies Trends**
   - Emerging / Accelerating / Consolidating / Maturing / Disrupting
   - Helps categorize market position

4. **Finds Connections**
   - Matches tags with existing articles
   - Cross-references themes
   - Creates content relationships

5. **Generates Article**
   - Creates new analysis piece
   - Titles as "Analysis: [Original Title]"
   - Includes themes, relevance, connections

## Output Format

### Raw Article (from news_scanner.py)
```json
{
    "id": 1,
    "title": "Article Title",
    "date": "January 15, 2026",
    "excerpt": "Brief excerpt...",
    "tags": ["energy"],
    "link": "https://...",
    "source": "NewsAPI"
}
```

### Analytical Article (from article_analyzer.py)
```json
{
    "id": 2,
    "title": "Analysis: Article Title",
    "date": "January 15, 2026",
    "excerpt": "Analysis of Article Title with implications...",
    "tags": ["energy"],
    "source": "O'Dwyer Analysis",
    "analysis_type": "analytical",
    "themes": ["disruption", "growth"],
    "investment_relevance": "high",
    "trend_type": "emerging",
    "related_articles": [
        {"title": "Related Article", "tags": ["energy"], "id": 1}
    ],
    "full_content": "[Complete analytical article text]",
    "link": "#article-analysis"
}
```

## Automation Setup

### Option A: Sequential Processing (Recommended)
Run both scanners in sequence:

**Windows Batch Script:**
```batch
@echo off
echo Running News Scanner...
python news_scanner.py

echo Running Article Analyzer...
python article_analyzer.py

echo Complete!
```

**Linux/Mac Shell Script:**
```bash
#!/bin/bash
echo "Running News Scanner..."
python3 news_scanner.py

echo "Running Article Analyzer..."
python3 article_analyzer.py

echo "Complete!"
```

### Option B: Scheduled Pipeline
Set up daily automation:

**Windows Task Scheduler:**
- Task: "O'Dwyer Analysis Pipeline"
- Trigger: Daily at 7 AM
- Action: Run batch script above

**Cron (Linux/Mac):**
```bash
# Run daily at 7 AM
0 7 * * * /path/to/analysis_pipeline.sh
```

### Option C: Cloud Automation
- AWS Lambda + CloudWatch
- Google Cloud Functions + Cloud Scheduler
- Azure Functions + Timer Trigger

## Analysis Output Example

### Input Article
```
Title: "New Quantum Computing Breakthrough Achieves Milestone"
Excerpt: "Leading research facility announces quantum processor with 1000 qubits..."
Tags: ["technology"]
```

### Generated Analysis
```
Title: "Analysis: New Quantum Computing Breakthrough"

Key Themes:
- Breakthrough/Innovation
- Technology Advancement
- Competitive Advantage

Investment Relevance: High

Trend Type: Emerging

Related Articles:
- Quantum Computing Market Expansion (id: 5)
- Semiconductor Innovation Trends (id: 12)

Summary:
This breakthrough represents a significant milestone in quantum computing development...
[Full 300-400 word analysis generated]
```

## Customization

### Add New Themes
Edit `extract_themes()` method:
```python
'your_theme': ['keyword1', 'keyword2', 'keyword3']
```

### Modify Relevance Scoring
Edit `assess_relevance()` method to adjust keyword weights

### Change Trend Types
Edit `identify_trend()` method to add/remove classifications

### Custom Analysis Prompts
Modify Claude API prompt in `generate_full_article()`:
```python
"content": f"""Your custom analysis prompt here...
Include article details: {article['title']}
Sector: {analysis['sector']}
Focus on: investment implications, trends, risks"""
```

## Integration with Thoughts Page

### Automatic Display
If you've updated thoughts.html with:
```javascript
fetch('articles_data.json')
    .then(r => r.json())
    .then(data => { articles = data; filterArticles('all'); })
```

Articles appear automatically! No manual updates needed.

### Manual Update
If using static articles array, copy JSON output into thoughts.html:
```javascript
const articles = [
    // Paste articles_data.json content here
];
```

## Quality Control

### Before Publishing

✅ Review analytical accuracy
✅ Check theme relevance
✅ Verify source attribution
✅ Confirm cross-references
✅ Test Thoughts page display

### Handling Duplicates
The analyzer automatically skips articles that match existing content by:
- Title similarity
- Tag overlap
- Theme intersection

### Managing Volume
Control article growth:
- Run scanner 1x daily → ~30-50 articles/week
- Run analyzer 2x week → ~15-25 analytical pieces/week
- Manually curate top articles for featured placement

## Troubleshooting

**Issue: No articles being analyzed**
- Verify articles_data.json exists from news_scanner.py
- Check file format is valid JSON
- Ensure read/write permissions

**Issue: Related articles not finding connections**
- Check existing articles have proper tags
- Verify tag names match exactly
- Add more articles for better cross-referencing

**Issue: AI-generated content appears incorrect**
- Adjust Claude API prompt for better results
- Check API key is set correctly
- Review ANTHROPIC_API_KEY environment variable

## Performance

- **Processing Speed:** ~0.1-0.2 seconds per article (template)
- **With Claude API:** ~1-2 seconds per article (AI-enhanced)
- **Memory Usage:** Minimal (loads articles into memory)
- **Output Size:** ~5KB per analytical article

## Future Enhancements

🚀 **Possible Additions:**
- Sentiment analysis
- Impact scoring
- Automated insight extraction
- Competitive analysis
- Portfolio impact assessment
- Anomaly detection
- Predictive trend analysis

## Cost Analysis

**News Scanner:**
- NewsAPI: Free (100 requests/day)

**Article Analyzer:**
- Claude API: ~$0.01 per analytical article (optional)
- Or: Free with template-based articles

**Total Monthly Cost:** $0-$20 (optional AI enhancement)

## File Structure

```
O'Dwyer Capital/
├── news_scanner.py              # Step 1: Collect news
├── article_analyzer.py          # Step 2: Analyze & enhance
├── articles_data.json           # Step 3: Publish to website
├── thoughts.html               # Display articles
├── NEWS_SCANNER_SETUP.md       # News scanner guide
├── ANALYZER_SETUP.md           # This file
└── PIPELINE_GUIDE.md           # Complete workflow
```

## Getting Started

1. ✅ Ensure `news_scanner.py` is configured and working
2. ✅ Run `python article_analyzer.py` first time
3. ✅ (Optional) Enable Claude API for enhanced analysis
4. ✅ Set up daily automation (scheduler, cron, etc.)
5. ✅ Monitor articles appearing on Thoughts page

---

**Last Updated:** January 2026
**Status:** Ready for production use
