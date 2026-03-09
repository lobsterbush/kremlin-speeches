# Kremlin Presidential Speeches Dataset - Status Report

## Overview
This project scrapes Russian presidential speeches from en.kremlin.ru and classifies them geographically.

## Current Status

### Data Collection
- **Total links identified**: 1,402 unique speeches
- **Speeches scraped**: 184 (13% complete)
- **Date range**: April 12, 2011 to September 7, 2019

### Geographic Classification
All 184 scraped speeches have been classified by:
1. **Location Region** (where the event occurred)
2. **Participant Region** (who was involved)

#### Location Region Distribution
- Russia/Domestic: 156 speeches (85%)
- Europe: 17 speeches (9%)
- Asia: 8 speeches (4%)
- South America: 2 speeches (1%)
- Middle East: 1 speech (<1%)

#### Participant Region Distribution
- International: 114 speeches (62%)
- European + International: 17 speeches (9%)
- Russian: 11 speeches (6%)
- Various combinations: 42 speeches (23%)

## Dataset Structure

### Files
- `speech_links.json`: All 1,402 collected speech URLs
- `kremlin_speeches_raw.csv`: Raw scraped data (184 speeches)
- `kremlin_speeches_classified.csv`: Classified data with geographic tags

### Columns in Final Dataset
1. `url` - Full URL to the speech
2. `title` - Title of the speech/transcript
3. `date` - Date of the speech
4. `location` - Location where speech occurred
5. `content` - Full text content
6. `speakers` - Semicolon-separated list of all speakers
7. `president_remarks` - Only remarks by Putin or Medvedev
8. `location_region` - Geographic region where event occurred
9. `participant_region` - Geographic origin of participants

## Technical Approach

### Scraping Method
- **Tool**: Python with `requests` and `BeautifulSoup`
- **Pagination**: Discovered correct format is `/page/N` not `?page=N`
- **Challenges**: Rate limiting (403 errors) after ~180 requests
- **Solution**: Added delays (2 seconds between requests) and retry logic

### Classification Method
- **Approach**: Keyword-based classification
- **Location keywords**: City and country names mapped to regions
- **Participant keywords**: Nationalities and organizations mapped to regions
- **Handles**: Multiple regions per speech (semicolon-separated)

## Continuing the Scrape

To continue scraping the remaining 1,218 speeches:

```bash
python3 scrape_fast.py
```

The scraper:
- Automatically resumes from where it left off
- Saves progress every 100 speeches
- Has retry logic for failed requests
- Includes 2-second delays to respect rate limits

## Usage

### View the data
```python
import pandas as pd
df = pd.read_csv('kremlin_speeches_classified.csv')
print(df.head())
```

### Filter by region
```python
# Speeches in Europe
europe = df[df['location_region'] == 'Europe']

# Speeches with Asian participants
asian = df[df['participant_region'].str.contains('Asian', na=False)]
```

### Analyze Putin's remarks
```python
# Get speeches where Putin spoke
putin_speeches = df[df['president_remarks'].notna() & (df['president_remarks'] != '')]
```

## Notes

- The scraper respects the server with delays between requests
- Some older speeches may have limited data
- Geographic classification is keyword-based and may need refinement
- The full dataset (1,402 speeches) will take several more hours to complete due to rate limiting

## Next Steps

1. Continue scraping remaining 1,218 speeches (in progress)
2. Validate classification accuracy on a sample
3. Consider adding more granular geographic categories
4. Add temporal analysis capabilities
5. Extract additional metadata (e.g., speech type, audience)
