"""
Scraper for ALL White House Briefings & Statements from whitehouse.gov
Scrapes speeches, statements, remarks, and other official communications
"""

import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WhiteHouseScraper:
    """Scraper for all White House briefings and statements"""
    
    def __init__(self):
        self.base_url = "https://www.whitehouse.gov/briefings-statements/"
        self.driver = None
        self.speeches = []
        
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        chrome_options.page_load_strategy = 'normal'
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(180)
        self.driver.implicitly_wait(10)
        logger.info("WebDriver initialized")
        
    def load_page_content(self, max_pages=100):
        """Load all content by paginating through pages"""
        all_links = []
        
        page = 1
        while page <= max_pages:
            # Construct paginated URL
            if page == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}page/{page}/"
            
            max_retries = 3
            page_source = None
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Loading page {page} (attempt {attempt + 1}/{max_retries})...")
                    self.driver.get(url)
                    time.sleep(3)
                    page_source = self.driver.page_source
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to load page {page} after {max_retries} attempts")
                        return all_links
                    time.sleep(10)
            
            if not page_source:
                break
            
            # Extract links from this page
            page_links = self.extract_speech_links(page_source)
            
            if not page_links:
                logger.info(f"No speeches found on page {page}, stopping pagination")
                break
            
            all_links.extend(page_links)
            logger.info(f"Page {page}: found {len(page_links)} speeches (total: {len(all_links)})")
            
            page += 1
            time.sleep(2)  # Be respectful
        
        return list(set(all_links))  # Remove duplicates
    
    def extract_speech_links(self, page_source):
        """Extract all speech links from the main page"""
        soup = BeautifulSoup(page_source, 'lxml')
        links = []
        
        # Find all links in the post template
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            # Match pattern /briefings-statements/YYYY/MM/slug or other briefing patterns
            if '/briefings-statements/' in href or '/briefing-room/' in href:
                # Make sure it's a full URL
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = "https://www.whitehouse.gov" + href
                
                # Avoid pagination links and the main category page
                if '/page/' not in full_url and full_url != self.base_url.rstrip('/'):
                    links.append(full_url)
        
        # Remove duplicates
        links = list(set(links))
        return links
    
    def extract_speech_data(self, url):
        """Extract detailed data from a single speech page"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                time.sleep(2)
                soup = BeautifulSoup(self.driver.page_source, 'lxml')
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to load {url} after {max_retries} attempts: {e}")
                    return None
                logger.warning(f"Attempt {attempt + 1} failed for {url}, retrying...")
                time.sleep(5)
        
        try:
            # Extract title
            title_elem = soup.select_one("h1, .post-title, .entry-title, h1.page-title")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract date
            date_elem = soup.select_one("time, .date, .post-date, .entry-date")
            date_str = ""
            if date_elem:
                # Try to get datetime attribute first
                date_str = date_elem.get('datetime', date_elem.get_text(strip=True))
            
            # Extract location if available
            location_elem = soup.select_one(".location, .post-location")
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Extract full content
            content_elem = soup.select_one(".post-content, .entry-content, .content, article")
            content = ""
            if content_elem:
                # Remove any script or style elements
                for elem in content_elem.find_all(['script', 'style']):
                    elem.decompose()
                content = content_elem.get_text(separator="\n", strip=True)
            
            # Extract category/type
            category_elem = soup.select_one(".post-category, .category, .post-type")
            category = category_elem.get_text(strip=True) if category_elem else ""
            
            return {
                'url': url,
                'title': title,
                'date': date_str,
                'location': location,
                'content': content,
                'category': category,
            }
            
        except Exception as e:
            logger.error(f"Error extracting data from {url}: {e}")
            return None
    
    def scrape_all(self, max_speeches=None, max_pages=100):
        """Main scraping orchestration"""
        try:
            self.setup_driver()
            
            # Load all links
            logger.info(f"\n{'='*60}")
            logger.info(f"SCRAPING WHITE HOUSE BRIEFINGS & STATEMENTS")
            logger.info(f"{'='*60}")
            
            links = self.load_page_content(max_pages=max_pages)
            logger.info(f"\n{'='*60}")
            logger.info(f"TOTAL UNIQUE LINKS: {len(links)}")
            logger.info(f"{'='*60}\n")
            
            if max_speeches:
                links = links[:max_speeches]
            
            # Scrape each speech
            logger.info(f"Scraping {len(links)} speeches...")
            for link in tqdm(links, desc="Scraping speeches"):
                speech_data = self.extract_speech_data(link)
                if speech_data:
                    self.speeches.append(speech_data)
                time.sleep(1)  # Be respectful to the server
            
            logger.info(f"\nSuccessfully scraped {len(self.speeches)} speeches")
            return self.speeches
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_csv(self, filename="whitehouse_speeches_raw.csv"):
        """Save scraped data to CSV"""
        if not self.speeches:
            logger.warning("No speeches to save")
            return
        
        df = pd.DataFrame(self.speeches)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} speeches to {filename}")
        return df


if __name__ == "__main__":
    scraper = WhiteHouseScraper()
    
    # Scrape all speeches
    speeches = scraper.scrape_all(max_speeches=None, max_pages=100)
    
    # Save raw data
    df = scraper.save_to_csv("whitehouse_speeches_raw.csv")
    
    print(f"\nScraping complete! Collected {len(speeches)} speeches.")
    print(f"Data saved to whitehouse_speeches_raw.csv")
