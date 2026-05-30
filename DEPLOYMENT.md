# O'Dwyer Capital - Deployment & Automation Guide

## Overview
This guide sets up automated daily article publishing to odwyercapital.com with the following workflow:
- **Monday-Friday at 8am UTC**: Automatically fetch articles, create briefs, and publish
- **Monday**: Analyzes articles from Friday 5pm through Monday 8am
- **Tuesday-Friday**: Analyzes articles from previous day's 8am post to current time
- **No weekend publishing**

## Prerequisites
- GitHub account
- NewsAPI key (get free at https://newsapi.org)
- Vercel account (free tier available)
- Domain: odwyercapital.com

## Step 1: Set Up GitHub Repository

1. Create a new GitHub repository:
   - Go to https://github.com/new
   - Name: `odwyercapital` (or similar)
   - Make it public
   - Add a README

2. Initialize and push your local code:
   ```bash
   cd /path/to/O'Dwyer Capital
   git init
   git add .
   git commit -m "Initial commit: O'Dwyer Capital website"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/odwyercapital.git
   git push -u origin main
   ```

## Step 2: Add NewsAPI Secret to GitHub

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `NEWSAPI_KEY`
5. Value: Your NewsAPI key from https://newsapi.org
6. Click "Add secret"

## Step 3: Set Up Vercel Hosting

1. Go to https://vercel.com and sign up/log in
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure:
   - Framework: "Other"
   - Root Directory: `./`
   - Build Command: (leave empty - we don't need to build)
   - Output Directory: (leave empty)
5. Click "Deploy"

## Step 4: Connect Your Domain

In Vercel project settings:
1. Go to "Domains"
2. Add your domain: `odwyercapital.com`
3. Follow Vercel's instructions to update your domain's DNS:
   - Point your domain nameservers to Vercel
   - OR add Vercel's DNS records to your registrar

## Step 5: Verify Automation

1. The workflow is configured to run:
   - **Every Monday-Friday at 8am UTC**
   - Manually anytime via "Run workflow"

2. To test manually:
   - Go to GitHub Actions tab
   - Click "Daily Article Publisher"
   - Click "Run workflow"

3. Monitor runs:
   - Go to Actions tab in GitHub
   - Watch the workflow execute
   - Check "Deployments" in Vercel to see site updates

## File Structure

```
odwyercapital/
├── .github/
│   └── workflows/
│       └── publish.yml          # GitHub Actions schedule
├── .gitignore
├── requirements.txt             # Python dependencies
├── article_analyzer.py          # Main analyzer script
├── article_analyzer_simple.py   # Backup simple version
├── articles_data.json           # Persistent article archive
├── emerging-tech.html           # Template
├── energy-transition.html       # Template
├── materials.html               # Template
├── thoughts.html                # Archive view
├── index.html                   # Homepage
├── favicon.png
├── odwyer_capital_logo_primary.png
└── ARCHIVE_SYSTEM.md            # Archive docs
```

## How It Works

### Daily Schedule (Monday-Friday)

**Monday 8am:**
1. Fetches articles from Friday 5pm → Monday 8am (UTC)
2. Analyzes and categorizes into: Energy, Technology, Innovation
3. Creates 3 analytical briefs
4. Generates dated HTML files: `emerging-tech-2026-01-13.html`, etc.
5. Updates `articles_data.json` (now has ~600+ articles)
6. GitHub Action commits and pushes changes
7. Vercel automatically re-deploys
8. New briefs appear on odwyercapital.com/thoughts.html

**Tuesday-Friday 8am:**
1. Fetches articles from previous day's 8am → current time
2. Same process (fewer articles, more focused)

### Archive System

- **articles_data.json**: Grows indefinitely, contains all briefs ever published
- **Dated HTML files**: Daily snapshots (emerging-tech-2026-01-13.html, etc.)
- **thoughts.html**: Dynamic index showing all briefs with filters by topic and theme
- **Sidebar**: Browse articles by month/year

## Monitoring & Maintenance

### Check Automation Health
1. GitHub Actions: https://github.com/YOUR_USERNAME/odwyercapital/actions
2. Vercel Deployments: https://vercel.com/dashboard (Your Project)
3. Live site: https://odwyercapital.com/thoughts.html

### Troubleshooting

**Workflow failed to run:**
- Check GitHub Actions tab for error messages
- Verify NEWSAPI_KEY secret is set correctly
- Check that newsapi.org API is accessible

**No articles fetched:**
- May indicate time window caught no new articles
- This is normal on low-traffic days
- Workflow still succeeds but no briefs created

**Deployment failed:**
- Check Vercel deployment logs
- Verify GitHub has permission to push commits
- Ensure no merge conflicts in articles_data.json

### Manual Testing

To test the analyzer locally:
```bash
export NEWSAPI_KEY="your_api_key_here"
python article_analyzer.py
```

This will:
1. Fetch today's articles
2. Create briefs
3. Update articles_data.json
4. Generate dated HTML files
5. All without committing to GitHub

## Time Zone Notes

- Cron schedules run in **UTC**
- 8am UTC = 3am EST / 12am PST
- To change publish time, edit `.github/workflows/publish.yml`:
  ```yaml
  - cron: '0 13 * * 1-5'  # 1pm UTC = 8am EST
  ```

## Customization

### Change Article Categories
Edit `article_analyzer.py`:
- Modify `queries` list for different search terms
- Adjust `categorize_article()` to change keyword detection
- Add new categories to `create_brief()`

### Change Publish Time
Edit `.github/workflows/publish.yml`:
- Modify cron expression (https://crontab.guru for help)
- Example: `0 13 * * 1-5` = 1pm UTC on weekdays

### Change Time Window Logic
Edit `get_time_window()` in `article_analyzer.py`:
- Adjust how far back Monday reaches
- Change time window for Tue-Fri

## Support

For issues:
1. Check GitHub Actions logs for error details
2. Verify NEWSAPI_KEY is set and valid
3. Test locally with `python article_analyzer.py`
4. Check Vercel deployment logs for build issues
