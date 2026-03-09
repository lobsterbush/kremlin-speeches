"""
Scrape statements using curl instead of Selenium
Much faster and more reliable
"""

import subprocess
import re
import time
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_page(url):
    """Fetch page using curl"""
    try:
        result = subprocess.run(
            ['curl', '-s', url, '-H', 'User-Agent: Mozilla/5.0'],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def extract_links(html, category):
    """Extract statement links from HTML"""
    links = set()
    
    # Simple regex to find links - use raw string
    pattern = rf'href="/events/president/transcripts/{category}/(\d+)"'
    matches = re.findall(pattern, html)
    
    for match in matches:
        url = f"http://en.kremlin.ru/events/president/transcripts/{category}/{match}"
        links.add(url)
    
    return list(links)


def scrape_page_content(url):
    """Scrape content from a page using curl"""
    html = fetch_page(url)
    if not html:
        return None
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title
        title_elem = soup.select_one("h1.entry-title, .p-name")
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Extract date
        date_elem = soup.select_one(".entry-date, time.dt-published")
        date_str = date_elem.get_text(strip=True) if date_elem else ""
        
        # Extract location
        location_elem = soup.select_one(".entry-info__place, .p-location")
        location = location_elem.get_text(strip=True) if location_elem else ""
        
        # Extract content
        content_elem = soup.select_one(".entry-content, .read__content")
        content = content_elem.get_text(separator="\n", strip=True) if content_elem else ""
        
        return {
            'url': url,
            'title': title,
            'date': date_str,
            'location': location,
            'content': content
        }
    except Exception as e:
        logger.error(f"Error parsing {url}: {e}")
        return None


def scrape_category(category, max_pages=50):
    """Scrape all links from a category"""
    base_url = f"http://en.kremlin.ru/events/president/transcripts/{category}"
    all_links = set()
    
    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url}?page={page}"
        
        logger.info(f"[{category}] Fetching page {page}...")
        html = fetch_page(url)
        
        if not html:
            break
        
        page_links = extract_links(html, category)
        
        if not page_links:
            logger.info(f"[{category}] No links on page {page}, stopping")
            break
        
        all_links.update(page_links)
        logger.info(f"[{category}] Page {page}: +{len(page_links)} links (total: {len(all_links)})")
        
        time.sleep(1)  # Be polite
    
    return list(all_links)


if __name__ == "__main__":
    categories = ["statements", "speeches", "transcripts", "news-conferences", "press-statements"]
    
    # Phase 1: Collect links
    logger.info("\n" + "="*60)
    logger.info("PHASE 1: COLLECTING LINKS")
    logger.info("="*60)
    
    all_links = []
    for cat in categories:
        logger.info(f"\n--- {cat.upper()} ---")
        cat_links = scrape_category(cat, max_pages=50)
        logger.info(f"[{cat}] Total: {len(cat_links)} links")
        all_links.extend(cat_links)
    
    unique_links = list(set(all_links))
    logger.info(f"\n{'='*60}")
    logger.info(f"TOTAL UNIQUE LINKS: {len(unique_links)}")
    logger.info(f"{'='*60}\n")
    
    # Save links
    links_df = pd.DataFrame({'url': unique_links})
    links_df.to_csv('kremlin_all_links_curl.csv', index=False)
    logger.info(f"Links saved to kremlin_all_links_curl.csv\n")
    
    # Phase 2: Scrape content
    logger.info("="*60)
    logger.info("PHASE 2: SCRAPING CONTENT")
    logger.info("="*60 + "\n")
    
    all_data = []
    for url in tqdm(unique_links, desc="Scraping content"):
        data = scrape_page_content(url)
        if data:
            all_data.append(data)
        time.sleep(0.5)  # Be polite but faster than Selenium
    
    # Save
    df = pd.DataFrame(all_data)
    df.to_csv('kremlin_all_curl.csv', index=False)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"SUCCESS: {len(df)} transcripts scraped")
    logger.info(f"Saved to: kremlin_all_curl.csv")
    logger.info(f"{'='*60}")
    
    # Summary by category
    logger.info("\nBREAKDOWN BY CATEGORY:")
    for cat in categories:
        cat_count = sum(1 for url in df['url'] if f'/{cat}/' in url)
        logger.info(f"  {cat}: {cat_count}")
