"""
Fixed scraper with improved link matching
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def get_driver():
    """Create a fresh driver"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(120)
    return driver


def extract_links_from_page(html, category):
    """Extract links using improved logic"""
    soup = BeautifulSoup(html, 'lxml')
    links = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Must contain the category path
        if f'/transcripts/{category}/' not in href:
            continue
            
        # Must start with /events/president
        if not href.startswith('/events/president'):
            continue
        
        # Extract the number ID
        # Pattern: /events/president/transcripts/{category}/{number}
        # May have trailing /photos or /videos which we ignore
        parts = href.split('/')
        
        # Find the part after category
        try:
            cat_idx = parts.index(category)
            if cat_idx + 1 < len(parts):
                id_part = parts[cat_idx + 1]
                # Check if it's a number
                if id_part.isdigit():
                    # Reconstruct clean URL
                    clean_url = f"http://en.kremlin.ru/events/president/transcripts/{category}/{id_part}"
                    links.append(clean_url)
        except (ValueError, IndexError):
            continue
    
    return list(set(links))


def scrape_category(category, max_pages=50):
    """Scrape all links from a category"""
    base_url = f"http://en.kremlin.ru/events/president/transcripts/{category}"
    all_links = set()
    
    driver = get_driver()
    
    try:
        for page in range(1, max_pages + 1):
            url = base_url if page == 1 else f"{base_url}?page={page}"
            
            try:
                logger.info(f"[{category}] Page {page}...")
                driver.get(url)
                time.sleep(2)
                
                page_links = extract_links_from_page(driver.page_source, category)
                
                if not page_links:
                    logger.info(f"[{category}] No links on page {page}, stopping")
                    break
                
                all_links.update(page_links)
                logger.info(f"[{category}] Page {page}: +{len(page_links)} links (total: {len(all_links)})")
                
            except Exception as e:
                logger.error(f"[{category}] Error on page {page}: {e}")
                break
    
    finally:
        driver.quit()
    
    return list(all_links)


def scrape_page_content(url):
    """Scrape content from a single page"""
    driver = get_driver()
    
    try:
        driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        title_elem = soup.select_one("h1.entry-title, .p-name")
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        date_elem = soup.select_one(".entry-date, time.dt-published")
        date_str = date_elem.get_text(strip=True) if date_elem else ""
        
        location_elem = soup.select_one(".entry-info__place, .p-location")
        location = location_elem.get_text(strip=True) if location_elem else ""
        
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
        logger.error(f"Error scraping {url}: {e}")
        return None
    finally:
        driver.quit()


if __name__ == "__main__":
    categories = ["speeches", "statements", "transcripts", "news-conferences", "press-statements"]
    
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
    pd.DataFrame({'url': unique_links}).to_csv('kremlin_all_links.csv', index=False)
    logger.info(f"Links saved to kremlin_all_links.csv")
    
    # Phase 2: Scrape content
    logger.info("\n" + "="*60)
    logger.info("PHASE 2: SCRAPING CONTENT")
    logger.info("="*60 + "\n")
    
    all_data = []
    for url in tqdm(unique_links, desc="Scraping"):
        data = scrape_page_content(url)
        if data:
            all_data.append(data)
        time.sleep(1)
    
    # Save data
    df = pd.DataFrame(all_data)
    df.to_csv('kremlin_all_fixed.csv', index=False)
    logger.info(f"\n{'='*60}")
    logger.info(f"SUCCESS: {len(df)} transcripts saved to kremlin_all_fixed.csv")
    logger.info(f"{'='*60}")
