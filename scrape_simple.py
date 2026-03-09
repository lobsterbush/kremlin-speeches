"""
Simple scraper for ALL Russian Presidential Transcripts - no regex
Uses basic string matching to find links
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleKremlinScraper:
    """Simple scraper using string matching instead of regex"""
    
    def __init__(self):
        self.categories = [
            "speeches",
            "statements", 
            "transcripts",
            "news-conferences",
            "press-statements"
        ]
        self.all_data = []
        
    def get_driver(self):
        """Create a fresh driver instance"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(120)
        return driver
    
    def get_all_links(self, category, max_pages=50):
        """Get all links for a category using simple string matching"""
        base_url = f"http://en.kremlin.ru/events/president/transcripts/{category}"
        all_links = set()
        
        driver = self.get_driver()
        
        try:
            for page in range(1, max_pages + 1):
                if page == 1:
                    url = base_url
                else:
                    url = f"{base_url}?page={page}"
                
                try:
                    logger.info(f"[{category}] Loading page {page}...")
                    driver.get(url)
                    time.sleep(2)
                    
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    
                    # Find all links that contain the category path and end with a number
                    page_links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        
                        # Simple string checks instead of regex
                        if href.startswith('/events/president/transcripts/'):
                            if f'/{category}/' in href:
                                # Check if ends with a number
                                parts = href.rstrip('/').split('/')
                                if parts and parts[-1].isdigit():
                                    full_url = f"http://en.kremlin.ru{href}"
                                    page_links.append(full_url)
                    
                    if not page_links:
                        logger.info(f"[{category}] No links found on page {page}, stopping")
                        break
                    
                    all_links.update(page_links)
                    logger.info(f"[{category}] Page {page}: {len(page_links)} links (total: {len(all_links)})")
                    
                except Exception as e:
                    logger.error(f"[{category}] Error on page {page}: {e}")
                    break
                    
        finally:
            driver.quit()
        
        return list(all_links)
    
    def scrape_page(self, url):
        """Scrape a single page - creates fresh driver each time"""
        driver = self.get_driver()
        
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Extract data
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
    
    def scrape_all(self, max_pages=50):
        """Main scraping orchestration"""
        
        # Step 1: Collect all links from all categories
        logger.info("\n" + "="*60)
        logger.info("STEP 1: COLLECTING ALL LINKS")
        logger.info("="*60 + "\n")
        
        all_links = []
        for category in self.categories:
            logger.info(f"\n--- Category: {category.upper()} ---")
            category_links = self.get_all_links(category, max_pages=max_pages)
            logger.info(f"[{category}] Collected {len(category_links)} links")
            all_links.extend(category_links)
        
        # Remove duplicates
        unique_links = list(set(all_links))
        logger.info(f"\n{'='*60}")
        logger.info(f"TOTAL UNIQUE LINKS: {len(unique_links)}")
        logger.info(f"{'='*60}\n")
        
        # Step 2: Scrape each page
        logger.info("\n" + "="*60)
        logger.info("STEP 2: SCRAPING CONTENT")
        logger.info("="*60 + "\n")
        
        for url in tqdm(unique_links, desc="Scraping pages"):
            data = self.scrape_page(url)
            if data:
                self.all_data.append(data)
            time.sleep(1)  # Be respectful
        
        logger.info(f"\nSuccessfully scraped {len(self.all_data)} pages")
        return self.all_data
    
    def save_to_csv(self, filename="kremlin_all_simple.csv"):
        """Save to CSV"""
        if not self.all_data:
            logger.warning("No data to save")
            return None
        
        df = pd.DataFrame(self.all_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} transcripts to {filename}")
        return df


if __name__ == "__main__":
    scraper = SimpleKremlinScraper()
    
    # Scrape all
    data = scraper.scrape_all(max_pages=50)
    
    # Save
    df = scraper.save_to_csv("kremlin_all_simple.csv")
    
    print(f"\n{'='*60}")
    print(f"Scraping complete!")
    print(f"Total transcripts: {len(data)}")
    print(f"Saved to: kremlin_all_simple.csv")
    print(f"{'='*60}")
