# Dataset Column Descriptions

**File:** `kremlin_speeches_classified.csv`  
**Total Columns:** 10  
**Total Speeches:** 1,402

---

## Column Reference

### 1. `url` (TEXT)
- **Description:** Full URL to the speech on en.kremlin.ru
- **Format:** `http://en.kremlin.ru/events/president/transcripts/speeches/[ID]`
- **Completeness:** 100%
- **Example:** `http://en.kremlin.ru/events/president/transcripts/speeches/78853`

### 2. `title` (TEXT)
- **Description:** Title of the speech or event
- **Completeness:** 100%
- **Example:** `"Dmitry Medvedev addressed the World Economic Forum in Davos"`

### 3. `date` (TEXT)
- **Description:** Date of the speech
- **Format:** "Month DD, YYYY" (e.g., "January 26, 2011")
- **Completeness:** 100%
- **Note:** All dates are parseable with `pd.to_datetime(df['date'], format='%B %d, %Y')`

### 4. `president` (TEXT) ⭐ NEW
- **Description:** Russian president in office at the time of the speech
- **Completeness:** 100%
- **Values:**
  - `"Yeltsin"` - 3 speeches (0.2%)
  - `"Putin (2000-2008)"` - 131 speeches (9.3%) - First & second terms
  - `"Medvedev (2008-2012)"` - 213 speeches (15.2%)
  - `"Putin (2012-present)"` - 1,055 speeches (75.2%) - Third term onwards
- **Based on:** Official presidential terms (inauguration: May 7)

### 5. `location` (TEXT)
- **Description:** Physical location where the speech/event occurred
- **Completeness:** 84% (226 missing)
- **Example:** `"The Kremlin, Moscow"`, `"Davos, Switzerland"`
- **Note:** Missing for phone calls, video addresses, and general statements

### 6. `content` (TEXT)
- **Description:** Full text transcript of the speech
- **Completeness:** 100%
- **Format:** Plain text with newlines separating paragraphs
- **Length:** Varies from a few hundred to several thousand words

### 7. `speakers` (TEXT)
- **Description:** Semicolon-separated list of all speakers in the transcript
- **Completeness:** 27% (384 speeches)
- **Format:** `"Name1; Name2; Name3"`
- **Example:** `"Dmitry Medvedev; Klaus Schwab"`
- **Note:** Low percentage is expected - 73% are solo presidential addresses

### 8. `president_remarks` (TEXT)
- **Description:** Extracted remarks by Putin or Medvedev only
- **Completeness:** 27% (374 speeches)
- **Note:** Only populated for multi-speaker events where president spoke
- **Use Case:** Isolate what the president said without other speakers

### 9. `location_region` (TEXT) 🌍
- **Description:** Geographic region WHERE the event occurred
- **Completeness:** 100%
- **Values:**
  - `"Russia/Domestic"` - 1,212 speeches (86.4%)
  - `"Europe"` - 136 speeches (9.7%)
  - `"Asia"` - 44 speeches (3.1%)
  - `"Middle East"` - 5 speeches (0.4%)
  - `"South America"` - 3 speeches (0.2%)
  - `"North America"` - 1 speech (0.1%)
  - `"Africa"` - 1 speech (0.1%)
- **Method:** Keyword-based classification using location names

### 10. `participant_region` (TEXT) 🌍
- **Description:** Geographic origin of WHO was involved
- **Completeness:** 100%
- **Values:** 43 unique combinations including:
  - `"International"` - 861 speeches (61.4%)
  - `"Russian"` - 171 speeches (12.2%)
  - `"European; International"` - 130 speeches (9.3%)
  - Various multi-region combinations
- **Method:** Keyword-based classification from title, speakers, and content

---

## Usage Examples

### Load and explore
```python
import pandas as pd

df = pd.read_csv('kremlin_speeches_classified.csv')
print(df.columns)
print(df.head())
```

### Filter by president
```python
# Putin's first tenure
putin_early = df[df['president'] == 'Putin (2000-2008)']

# Medvedev years
medvedev = df[df['president'] == 'Medvedev (2008-2012)']

# Putin's return
putin_recent = df[df['president'] == 'Putin (2012-present)']
```

### Analyze by president and region
```python
# International engagement by president
df.groupby(['president', 'location_region']).size().unstack(fill_value=0)
```

### Parse dates for temporal analysis
```python
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y')
df['year'] = df['date_parsed'].dt.year
df['month'] = df['date_parsed'].dt.month

# Speeches per year by president
df.groupby(['year', 'president']).size()
```

---

## Data Types

When loading with pandas, recommended dtypes:
```python
df = pd.read_csv('kremlin_speeches_classified.csv', 
                 dtype={
                     'url': 'string',
                     'title': 'string',
                     'date': 'string',
                     'president': 'category',
                     'location': 'string',
                     'content': 'string',
                     'speakers': 'string',
                     'president_remarks': 'string',
                     'location_region': 'category',
                     'participant_region': 'category'
                 })
```

---

**Last Updated:** December 26, 2025
