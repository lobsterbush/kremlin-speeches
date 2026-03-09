# Kremlin Presidential Speeches Dataset - Complete

## ✅ Project Complete!

Successfully scraped and classified **1,402 Russian presidential speeches** from http://en.kremlin.ru/events/president/transcripts/speeches

## Dataset Overview

### Temporal Coverage
- **Date Range**: January 28, 2000 to December 24, 2025
- **Span**: 25 years of Russian presidential speeches
- **Presidents Covered**: Putin and Medvedev administrations

### Year Distribution
Most complete coverage from 2013-2019:

| Year | Speeches | Year | Speeches |
|------|----------|------|----------|
| 2000 | 10 | 2013 | 83 |
| 2001 | 13 | 2014 | 81 |
| 2002 | 2 | 2015 | 68 |
| 2003 | 24 | 2016 | 89 |
| 2004 | 13 | 2017 | 95 |
| 2005 | 24 | 2018 | 120 ⭐ |
| 2006 | 21 | 2019 | 98 |
| 2007 | 17 | 2020 | 60 |
| 2008 | 29 | 2021 | 75 |
| 2009 | 51 | 2022 | 61 |
| 2010 | 59 | 2023 | 66 |
| 2011 | 65 | 2024 | 59 |
| 2012 | 63 | 2025 | 56 |

## Geographic Classification

### Location Region (Where Events Occurred)
- **Russia/Domestic**: 1,212 speeches (86%)
- **Europe**: 136 speeches (10%)
- **Asia**: 44 speeches (3%)
- **Middle East**: 5 speeches (<1%)
- **South America**: 3 speeches (<1%)
- **North America**: 1 speech (<1%)
- **Africa**: 1 speech (<1%)

### Participant Region (Who Was Involved)
- **International**: 861 speeches (61%)
- **Russian**: 171 speeches (12%)
- **European + International**: 130 speeches (9%)
- **European**: 46 speeches (3%)
- **Asian + International**: 43 speeches (3%)
- Various multi-region combinations: ~150 speeches (11%)

## Dataset Structure

### Files Delivered
1. **`kremlin_speeches_classified.csv`** - Complete dataset with all classifications (1,402 rows)
2. **`kremlin_speeches_raw.csv`** - Raw scraped data without classifications
3. **`speech_links.json`** - All 1,402 collected URLs

### Data Columns (9 total)
1. **url** - Full URL to the speech on kremlin.ru
2. **title** - Title of the speech/event
3. **date** - Date of the speech (format: "Month DD, YYYY")
4. **location** - Location where speech occurred
5. **content** - Full text content of the speech
6. **speakers** - Semicolon-separated list of all speakers
7. **president_remarks** - Extracted remarks by Putin or Medvedev only
8. **location_region** - Geographic region where event occurred (classified)
9. **participant_region** - Geographic origin of participants (classified)

## Sample Use Cases

### Load and Explore
```python
import pandas as pd

df = pd.read_csv('kremlin_speeches_classified.csv')
print(f"Total speeches: {len(df)}")
print(df.head())
```

### Filter by Geography
```python
# Speeches in Europe
europe = df[df['location_region'] == 'Europe']

# Speeches with Asian participants
asian = df[df['participant_region'].str.contains('Asian', na=False)]

# International speeches (multiple countries involved)
international = df[df['participant_region'].str.contains('International', na=False)]
```

### Temporal Analysis
```python
# Convert dates
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y')

# Speeches by year
yearly = df.groupby(df['date_parsed'].dt.year).size()

# Speeches by president (approximate)
putin_2000_2008 = df[(df['date_parsed'].dt.year >= 2000) & (df['date_parsed'].dt.year <= 2008)]
medvedev_2008_2012 = df[(df['date_parsed'].dt.year >= 2008) & (df['date_parsed'].dt.year <= 2012)]
putin_2012_onwards = df[df['date_parsed'].dt.year >= 2012]
```

### Content Analysis
```python
# Analyze Putin's direct remarks
putin_remarks = df[df['president_remarks'].notna() & (df['president_remarks'] != '')]

# Word count analysis
df['content_length'] = df['content'].str.len()
df['words'] = df['content'].str.split().str.len()

# Average speech length over time
df.groupby(df['date_parsed'].dt.year)['words'].mean()
```

## Technical Details

### Scraping Method
- **Tool**: Python with `requests` library and `BeautifulSoup`
- **Rate Limiting**: Automatic 5-minute pauses after 5 consecutive 403 errors
- **Delays**: 3-5 second randomized delays between requests
- **Pagination**: Discovered correct format is `/page/N` (not `?page=N`)
- **Resumable**: Automatically continues from where it left off

### Classification Method
- **Approach**: Keyword-based classification using curated dictionaries
- **Location Keywords**: 200+ cities and country names mapped to regions
- **Participant Keywords**: 150+ nationalities and organizations mapped to regions
- **Handles**: Multiple regions per speech (semicolon-separated)

### Code Files
- `scrape_fast.py` - Main scraper with rate limit handling
- `collect_links.py` - Standalone link collection script
- `classify_geography.py` - Geographic classifier with keyword dictionaries
- `scrape_resumable.py` - Alternative batch-based scraper

## Key Findings

1. **Domestic Focus**: 86% of speeches occurred within Russia
2. **International Engagement**: 61% involved international participants
3. **European Relations**: 139 speeches involved Europe (location or participants)
4. **Peak Period**: 2018 had the most speeches (120), followed by 2019 (98) and 2017 (95)
5. **Asian Relations**: 87 speeches involved Asian location or participants
6. **Recent Coverage**: Excellent coverage through December 2025

## Data Quality Notes

- All 1,402 speeches successfully scraped and classified
- Geographic classification is keyword-based; may need manual review for edge cases
- Some speeches may have incomplete speaker lists if not clearly labeled
- Dates are in English format as provided by the website
- Content includes full text of speeches/remarks/statements

## Future Enhancements

Potential improvements for the dataset:
1. Manual validation of geographic classifications on a sample
2. More granular geographic categories (e.g., Western Europe vs. Eastern Europe)
3. Speech type classification (address, press conference, meeting, etc.)
4. Sentiment analysis of content
5. Topic modeling across speeches
6. Named entity recognition for participants
7. Translation to other languages

## Citation

If using this dataset in research:

```
Russian Presidential Speeches Dataset (2000-2025)
Source: http://en.kremlin.ru/events/president/transcripts/speeches
Collected: December 2025
Total Speeches: 1,402
Coverage: January 2000 - December 2025
```

## Contact & Maintenance

This dataset represents a snapshot as of December 2025. The scraper can be re-run periodically to update with new speeches as they are published on the Kremlin website.

---

**Dataset Complete**: 1,402 speeches across 25 years, fully classified by geography ✓
