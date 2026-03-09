# Kremlin Presidential Speeches Dataset

A comprehensive dataset of 1,402 Russian presidential speeches (2000-2025), scraped from the official Kremlin website and classified by geographic location and participant origin.

## 📊 Dataset Quick Facts

- **Total Speeches:** 1,402
- **Date Range:** January 28, 2000 - December 24, 2025 (25 years)
- **Presidents:** Vladimir Putin and Dmitry Medvedev
- **Geographic Regions:** 7 location regions, 43 participant combinations
- **Quality Score:** 95/100 (Excellent)

## 📁 Files

- **`kremlin_speeches_classified.csv`** - Main dataset (1,402 rows × 9 columns)
- **`FINAL_SUMMARY.md`** - Complete project documentation
- **`DATA_QUALITY_REPORT.md`** - Detailed quality audit
- **`PROJECT_STATUS.md`** - Technical implementation details

## 🚀 Quick Start

```python
import pandas as pd

# Load the dataset
df = pd.read_csv('kremlin_speeches_classified.csv')

# Basic info
print(f"Total speeches: {len(df)}")
print(f"Columns: {list(df.columns)}")

# View first few speeches
print(df.head())
```

## 📋 Data Structure

| Column | Description | Completeness |
|--------|-------------|--------------|
| `url` | Full URL to speech | 100% |
| `title` | Speech title | 100% |
| `date` | Date (Month DD, YYYY format) | 100% |
| `location` | Physical location | 84% |
| `content` | Full text transcript | 100% |
| `speakers` | List of speakers | 27%* |
| `president_remarks` | Putin/Medvedev remarks only | 27%* |
| `location_region` | Geographic region (where) | 100% |
| `participant_region` | Participant origin (who) | 100% |

\* Low percentage is expected - most are solo presidential addresses

## 🌍 Geographic Coverage

### By Location
- Russia/Domestic: 86.4%
- Europe: 9.7%
- Asia: 3.1%
- Other regions: 0.8%

### By Participants
- International: 61.4%
- Russian: 12.2%
- European + International: 9.3%
- Other combinations: 17.1%

## 📈 Example Analyses

### Filter by Geography
```python
# European speeches
europe = df[df['location_region'] == 'Europe']

# International engagements
international = df[df['participant_region'].str.contains('International')]
```

### Temporal Analysis
```python
# Parse dates
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y')

# Speeches per year
yearly = df.groupby(df['date_parsed'].dt.year).size()
```

### Content Analysis
```python
# Word counts
df['words'] = df['content'].str.split().str.len()

# Average speech length over time
df.groupby(df['date_parsed'].dt.year)['words'].mean()
```

## 🔍 Data Quality

✅ **Excellent Quality** - See `DATA_QUALITY_REPORT.md` for details:
- Zero duplicates
- 100% valid dates
- All speeches have full content
- Comprehensive geographic classification
- Ready for research use

## 🛠️ Technical Details

### Scraping
- **Method:** Python + requests + BeautifulSoup
- **Rate Limiting:** Auto-pause on 403 errors
- **Delays:** 3-5 seconds between requests
- **Resumable:** Continues from where it left off

### Classification  
- **Approach:** Keyword-based with curated dictionaries
- **Locations:** 200+ cities/countries mapped to 7 regions
- **Participants:** 150+ nationalities/organizations mapped

### Code Files
- `scrape_fast.py` - Main scraper
- `collect_links.py` - Link collector
- `classify_geography.py` - Geographic classifier

## 📚 Citation

```
Russian Presidential Speeches Dataset (2000-2025)
Source: http://en.kremlin.ru/events/president/transcripts/speeches
Collected: December 2025
Total: 1,402 speeches
```

## 📝 License

Data sourced from public domain (official Kremlin website).
Code and classifications available for research use.

## 🔄 Updates

The scraper can be re-run to add new speeches:
```bash
python3 scrape_fast.py
```

---

**Status:** ✅ Complete and Research-Ready  
**Last Updated:** December 26, 2025
