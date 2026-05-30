# O'Dwyer Capital - Automated Publishing Setup

## What's Included

✅ **article_analyzer.py** - Enhanced analyzer that:
  - Fetches from NewsAPI automatically
  - Categorizes articles into Energy, Technology, Innovation
  - Creates daily briefs
  - Updates articles_data.json (persistent archive)
  - Generates dated HTML files

✅ **GitHub Actions Workflow** - Automatically runs:
  - **Every Monday-Friday at 8am UTC**
  - Monday: Analyzes Fri 5pm through Mon 8am
  - Tue-Fri: Analyzes since previous day's 8am post
  - Commits changes back to GitHub
  - Vercel auto-deploys updates

✅ **Supporting Files**:
  - requirements.txt - Python dependencies
  - .gitignore - Git configuration
  - DEPLOYMENT.md - Full setup guide
  - .github/workflows/publish.yml - Scheduler config

## Quick Setup (5 steps)

### 1. Get NewsAPI Key
- Go to https://newsapi.org
- Sign up (free tier available)
- Copy your API key

### 2. Create GitHub Repository
```bash
cd "E:\Users\Steven\Documents\Claude\Projects\O'Dwyer Capital"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/odwyercapital.git
git push -u origin main
```

### 3. Add Secret to GitHub
- Go to https://github.com/YOUR_USERNAME/odwyercapital
- Settings → Secrets and variables → Actions
- New secret: `NEWSAPI_KEY` = your key from step 1

### 4. Deploy to Vercel
- Go to https://vercel.com
- Import your GitHub repo
- Deploy (takes ~30 seconds)

### 5. Connect Domain
- In Vercel, go to Settings → Domains
- Add odwyercapital.com
- Update your domain's DNS per Vercel instructions

## How It Works

**Every Monday-Friday at 8am UTC:**
1. GitHub Actions triggers automatically
2. Fetches articles from NewsAPI
3. Creates 3 analytical briefs (Energy, Technology, Innovation)
4. Updates articles_data.json
5. Generates dated HTML files
6. Commits changes
7. Vercel deploys to odwyercapital.com
8. New briefs appear on /thoughts.html

## File Descriptions

| File | Purpose |
|------|---------|
| article_analyzer.py | Main script that fetches, analyzes, and publishes |
| .github/workflows/publish.yml | Schedule & automation configuration |
| requirements.txt | Python dependencies (requests, etc.) |
| .gitignore | Tells Git which files to ignore |
| DEPLOYMENT.md | Detailed setup instructions |

## Next Steps

1. **Read DEPLOYMENT.md** - Full step-by-step guide
2. **Create GitHub repo** - Follow steps above
3. **Add NewsAPI key** - Set as GitHub secret
4. **Deploy to Vercel** - Connect your domain
5. **Test** - Manual workflow run from Actions tab

## Testing Without Live Site

To test locally before deployment:
```bash
set NEWSAPI_KEY=your_key_here
python article_analyzer.py
```

This will:
- Fetch today's articles
- Create briefs
- Update articles_data.json
- Generate dated HTML files

## Support

**Workflow times in other timezones:**
- 8am UTC = 3am EST / 12am PST
- Edit `.github/workflows/publish.yml` to change time

**Monitor automation:**
- GitHub Actions tab: See workflow runs
- Vercel Dashboard: See deployments
- odwyercapital.com/thoughts.html: See published briefs

## Architecture

```
Monday-Friday at 8am UTC
    ↓
GitHub Actions triggered
    ↓
article_analyzer.py runs
    ├─ Fetch from NewsAPI
    ├─ Categorize articles
    ├─ Create briefs
    ├─ Update articles_data.json
    └─ Generate dated HTML files
    ↓
Git commit & push
    ↓
Vercel auto-deploys
    ↓
odwyercapital.com updated
```

## Time Window Logic

**Monday 8am UTC:**
- Fetch: Friday 5pm → Monday 8am (captures weekend)

**Tuesday-Friday 8am UTC:**
- Fetch: Previous day 8am → Now (24-hour window)

This ensures no gaps or overlaps in coverage.

---

See DEPLOYMENT.md for complete detailed instructions.
