# O'Dwyer Capital - Daily Archive System

## Overview

This system implements a sustainable daily-archive solution for investment briefs, with hyperlinked source articles and persistent accumulation of historical content.

## How It Works

### 1. Daily Brief Generation
- Three investment briefs are generated each day:
  - **Emerging Tech Investment Brief** 
  - **Energy Transition Investment Brief**
  - **Materials Investment Brief**

### 2. Archive System (Three Components)

#### A. Persistent JSON Archive (`articles_data.json`)
- **Purpose**: Accumulates ALL briefs indefinitely
- **Content**: Each entry includes:
  - Metadata (title, date, tags, source)
  - Full HTML content with embedded hyperlinks to source articles
  - Related article references with direct links
- **Behavior**: New briefs are prepended; file grows indefinitely
- **Format**: Standard JSON array sorted by date (newest first)

#### B. Dated HTML Files (`{brief-name}-{YYYY-MM-DD}.html`)
- **Purpose**: Preserves each day's briefs as separate, complete pages
- **Files Generated**:
  - `emerging-tech-2026-05-30.html`
  - `energy-transition-2026-05-30.html`
  - `materials-2026-05-30.html`
- **Content**: Full-featured HTML pages with styling, navigation, and source links
- **Renewal**: New files are created daily (overwriting previous day versions)

#### C. Thoughts Page Archive View (`thoughts.html`)
- **Purpose**: Dynamic archive index that lists all accumulated briefs
- **Functionality**:
  - Loads all articles from `articles_data.json`
  - Dynamically generates links to dated HTML files
  - Filters by category/tags
  - Shows newest briefs first
- **URL Generation**: 
  - Takes brief title (e.g., "Emerging Tech Investment Brief")
  - Extracts slug (e.g., "emerging-tech")
  - Combines with date (e.g., "2026-05-30")
  - Creates link: `emerging-tech-2026-05-30.html`

### 3. Source Attribution

Each brief contains hyperlinked references to source articles:
- **Format**: HTML anchor tags with `target="_blank"`
- **Example**: `<a href="URL" target="_blank">Article Title</a>`
- **Sources**: GlobeNewswire, PRNewswire, Fortune, and other industry publications

## Daily Workflow

1. **Generate Briefs**: Create three investment analyses from market research
2. **Publish to JSON**: Append new briefs to `articles_data.json`
3. **Archive to Files**: Run `article_analyzer_simple.py` to:
   - Create dated HTML files for today's briefs
   - Copy static HTML files and rename them with today's date
4. **View Archive**: Open `thoughts.html` to see all briefs with links to dated versions

## File Structure

```
O'Dwyer Capital/
├── articles_data.json              # Persistent accumulating archive
├── thoughts.html                   # Dynamic archive index
├── emerging-tech.html              # Static template (newest)
├── energy-transition.html          # Static template (newest)
├── materials.html                  # Static template (newest)
├── emerging-tech-2026-05-30.html   # Daily archive (May 30)
├── energy-transition-2026-05-30.html
├── materials-2026-05-30.html
├── emerging-tech-2026-05-29.html   # Daily archive (May 29)
├── energy-transition-2026-05-29.html
└── materials-2026-05-29.html
```

## Running the Archive Generator

```bash
python3 article_analyzer_simple.py
```

This creates dated HTML files for today's briefs, enabling:
- Historical access to any day's analysis
- Permanent links for sharing specific brief versions
- Complete audit trail of investment thinking over time

## Key Benefits

1. **Hyperlinked Sources**: Every claim is attributed to a specific source article
2. **Persistent History**: All briefs are accumulated in JSON for long-term reference
3. **Dated Archives**: Each day's analysis is preserved as a standalone HTML page
4. **Dynamic Indexing**: thoughts.html automatically links to dated versions
5. **No Manual Links**: URL generation is automatic based on title and date
6. **Accumulating Record**: `articles_data.json` grows indefinitely, creating institutional memory

## Maintenance

- **Daily**: Run `article_analyzer_simple.py` after generating briefs
- **Backup**: Periodically backup `articles_data.json` (core archive)
- **Links**: All internal links automatically route through `thoughts.html` for consistency
- **Search**: Filter articles by tag/category directly in `thoughts.html`
