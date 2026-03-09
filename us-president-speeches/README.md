# White House Speeches Analysis: Russia Mentions

This project scrapes and analyzes White House briefings and statements to track mentions of Russia and other adversary nations, paralleling the analysis conducted on Kremlin speeches.

## Overview

The analysis examines how frequently US presidential communications mention Russia, China, Iran, and North Korea, comparing these patterns over time. This mirrors the methodology used in the parent `kremlin-speeches` project, which analyzes how Russian presidential speeches mention the United States and Asian countries.

## Pipeline

### 1. Data Collection
**Script:** `scrape_whitehouse.py`

Scrapes all briefings and statements from https://www.whitehouse.gov/briefings-statements/

```bash
python scrape_whitehouse.py
```

**Output:** `whitehouse_speeches_raw.csv`

### 2. Preprocessing
**Script:** `preprocess_whitehouse_speeches.py`

Cleans and lemmatizes speech content, applies stopword removal, and normalizes country/demonym references.

```bash
python preprocess_whitehouse_speeches.py
```

**Output:** `whitehouse_speeches_lemmatized.csv`

### 3. Geographic Classification
**Script:** `classify_whitehouse_geography.py`

Classifies speeches by location (where delivered) and participants (who involved) at regional/continental level.

```bash
python classify_whitehouse_geography.py
```

**Output:** `whitehouse_speeches_classified.csv`

### 4. Analysis

#### Python Analysis (2021-Present)
**Script:** `analyze_russia_mentions.py`

Generates 4-panel comparison plot showing mentions of Russia, China, North Korea, and Iran.

```bash
python analyze_russia_mentions.py
```

**Outputs:**
- `whitehouse_russia_comparison.png`
- `whitehouse_russia_comparison.pdf`

#### R Temporal Analysis
**Script:** `full_temporal_analysis_whitehouse.R`

Creates comprehensive temporal visualizations with key event markers.

```bash
Rscript full_temporal_analysis_whitehouse.R
```

**Outputs:**
- `whitehouse_adversaries_timeline.png/pdf` - All adversary nations over time
- `whitehouse_russia_timeline.png/pdf` - Russia mentions with key events
- `whitehouse_regional_focus.png/pdf` - Regional focus comparison
- `whitehouse_full_temporal_analysis.png/pdf` - Combined plot

## Requirements

### Python
```bash
pip install selenium webdriver-manager beautifulsoup4 pandas nltk matplotlib tqdm lxml
```

### R
```R
install.packages(c("tidyverse", "ggthemes", "lubridate", "patchwork"))
```

## Key Differences from Kremlin Analysis

1. **Subject Focus**: Analyzes mentions OF Russia (not BY Russia)
2. **Comparison**: Compares Russia mentions to China (not US to Asia)
3. **Time Period**: Focuses on 2021-present to capture Ukraine war period
4. **Keywords**: Adapted for US political context and adversary nations

## Methodology

Following the Kremlin speeches methodology:

- **Keyword counting**: Counts mentions of country names, cities, leaders
- **Proportion estimation**: Assumes 5 words per mention context
- **Monthly aggregation**: Groups speeches by month for temporal trends
- **Thematic visualization**: Uses Tufte principles via `theme_tufte()`

## Analysis Questions

1. How has Russia's prominence in US presidential communications changed since the 2022 Ukraine invasion?
2. How do Russia mentions compare to mentions of China, Iran, and North Korea?
3. What are the temporal patterns around key geopolitical events?
4. How does the US executive's rhetorical focus compare to Russia's focus on the US?

## File Structure

```
us-president-speeches/
├── README.md                                  # This file
├── scrape_whitehouse.py                       # Web scraper
├── preprocess_whitehouse_speeches.py          # Preprocessing pipeline
├── classify_whitehouse_geography.py           # Geographic classifier
├── analyze_russia_mentions.py                 # Python analysis (4-panel plot)
├── full_temporal_analysis_whitehouse.R        # R temporal analysis
├── whitehouse_speeches_raw.csv                # Raw scraped data
├── whitehouse_speeches_lemmatized.csv         # Preprocessed data
├── whitehouse_speeches_classified.csv         # Classified data
└── *.png/pdf                                  # Generated visualizations
```

## Notes

- The scraper respects whitehouse.gov with rate limiting (1-2 second delays)
- Headless Chrome is used for JavaScript-rendered content
- All visualizations follow Tufte's principles for clean, professional figures
- Data and visualizations are generated at 300 DPI for publication quality

## Comparison with Kremlin Project

This mirrors the kremlin-speeches parent directory:
- **Kremlin project**: "How often does Russia mention the US/Asia?"
- **White House project**: "How often does the US mention Russia/adversaries?"

Both use identical methodological approaches for direct comparison of rhetorical focus.
