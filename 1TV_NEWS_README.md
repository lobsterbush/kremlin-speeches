# 1tv.ru News Scraper

**Script**: `scrape_1tv_news.py`  
**Target**: https://www.1tv.ru/news (Channel One Russia - Первый канал)

## Overview

This scraper collects news articles from 1tv.ru, one of Russia's main state television channels. The site uses Next.js with dynamic loading, so Selenium is required to scroll and load additional articles.

## Usage

```bash
python3 scrape_1tv_news.py
```

## Data Collected (Latest Run)

- **Total Articles**: 101
- **Date**: January 12-13, 2026
- **Output**: `1tv_news_raw.csv`
- **Average Content Length**: 323 characters per article

## Sample Articles

- "Мощный шторм обрушился на Крым" (Powerful storm hits Crimea)
- "Расчеты ПВО за четыре часа сбили 56 дронов ВСУ" (Air defense shot down 56 Ukrainian drones in four hours)
- "Выпуск новостей в 15:00 от 12.01.2026" (News broadcast at 15:00 on 12.01.2026)
- "Убийства, погромы и поджоги в Иране..." (Murders, pogroms and arsons in Iran...)
- "Только пальцем погрозил: водитель в Оренбурге..." (Just wagged his finger: driver in Orenburg...)

## Data Structure

| Field | Description |
|-------|-------------|
| `url` | Full URL of the article |
| `title` | Article headline |
| `date` | Publication date (extracted from page) |
| `content` | Article text content |
| `category` | Category/tag if available |

## Methodology

1. **Page Loading**: Loads https://www.1tv.ru/news and scrolls 20 times to trigger lazy-loading of more articles
2. **Link Extraction**: Extracts article URLs from the `__NEXT_DATA__` JSON structure embedded in the page
3. **Article Scraping**: Visits each article URL and extracts:
   - Title from `<h1>` or similar elements
   - Date from `<time>` elements or JSON data
   - Content from article text elements or `__NEXT_DATA__`
   - Category/tags if available
4. **Content Filtering**: Only saves articles with non-empty content

## Technical Details

- **Framework**: Selenium WebDriver with Chrome (headless)
- **Parsing**: BeautifulSoup + JSON parsing for Next.js data
- **Rate Limiting**: 1-2 second delays between requests
- **Retry Logic**: Up to 3 attempts per article
- **Scroll Times**: Configurable (default: 20 scrolls, 2 seconds each)

## Customization

To scrape more or fewer articles, adjust the `scroll_times` parameter:

```python
scraper = OneTVNewsScraper()
articles = scraper.scrape_all(scroll_times=30)  # More scrolling = more articles
```

To limit the number of articles scraped:

```python
articles = scraper.scrape_all(max_articles=50, scroll_times=20)
```

## Potential Analysis

This data could be used for:

1. **News topic analysis**: What topics does Russian state TV cover?
2. **Sentiment analysis**: Tone and framing of news stories
3. **Comparative analysis**: Compare with other Russian or Western news sources
4. **Temporal trends**: How coverage changes over time
5. **Propaganda analysis**: Identify narrative patterns and recurring themes

## Integration with Kremlin Speeches

This news data could complement the Kremlin speeches analysis by:
- Comparing official presidential communications with state media coverage
- Analyzing how presidential messages are amplified or framed in news
- Identifying topics that appear in speeches vs. general news coverage
- Tracking temporal alignment between speeches and news cycles

## Notes

- 1tv.ru uses dynamic JavaScript loading via Next.js
- The site structure may change, requiring scraper updates
- Dates may need additional parsing depending on format variations
- Some articles may be video-only with minimal text content
- The scraper respects rate limits with deliberate delays

---

*Last updated: January 13, 2026*
