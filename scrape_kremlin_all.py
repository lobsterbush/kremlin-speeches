"""
Scraper for ALL Russian Presidential Transcripts from en.kremlin.ru
Scrapes speeches, statements, transcripts, news conferences, and press statements
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


class KremlinScraperAll:
    """Scraper for all Kremlin presidential transcripts"""
    
    def __init__(self, categories=None):
        # All transcript categories to scrape
        if categories is None:
            self.categories = [
                "speeches",
                "statements",
                "transcripts",
                "news-conferences",
                "press-statements"
            ]
        else:
            self.categories = categories
        self.driver = None
        self.transcripts = []
        
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
        self.driver.set_page_load_timeout(180)  # 3 minutes timeout
        self.driver.implicitly_wait(10)
        logger.info("WebDriver initialized")
        
    def load_category_content(self, category, max_pages=50):
        """Load all content from a specific category by paginating through pages"""
        base_url = f"http://en.kremlin.ru/events/president/transcripts/{category}"
        all_links = []
        
        page = 1
        while page <= max_pages:
            # Construct paginated URL
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}?page={page}"
            
            max_retries = 3
            page_source = None
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"[{category}] Loading page {page} (attempt {attempt + 1}/{max_retries})...")
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
            page_links = self.extract_transcript_links(page_source, category)
            
            if not page_links:
                logger.info(f"[{category}] No transcripts found on page {page}, stopping pagination")
                break
            
            all_links.extend(page_links)
            logger.info(f"[{category}] Page {page}: found {len(page_links)} transcripts (total: {len(all_links)})")
            
            page += 1
            time.sleep(2)  # Be respectful
        
        return list(set(all_links))  # Remove duplicates
    
    def extract_transcript_links(self, page_source, category):
        """Extract all transcript links from the main page"""
        soup = BeautifulSoup(page_source, 'lxml')
        links = []
        
        # Find all transcript links with numeric IDs for this category
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            # Match pattern /events/president/transcripts/{category}/[number]
            pattern = f'^/events/president/transcripts/{category}/\d+$'
            if re.match(pattern, href):
                full_url = "http://en.kremlin.ru" + href
                links.append(full_url)
        
        # Remove duplicates
        links = list(set(links))
        return links
    
    def extract_transcript_data(self, url):
        """Extract detailed data from a single transcript page"""
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
            title_elem = soup.select_one("h1.entry-title, .p-name")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract date
            date_elem = soup.select_one(".entry-date, time.dt-published")
            date_str = date_elem.get_text(strip=True) if date_elem else ""
            
            # Extract location
            location_elem = soup.select_one(".entry-info__place, .p-location")
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Extract full content
            content_elem = soup.select_one(".entry-content, .read__content")
            content = content_elem.get_text(separator="\n", strip=True) if content_elem else ""
            
            # Extract speakers
            speakers = self._extract_speakers(content_elem)
            
            # Extract Putin/Medvedev remarks
            president_remarks = self._extract_president_remarks(content_elem)
            
            return {
                'url': url,
                'title': title,
                'date': date_str,
                'location': location,
                'content': content,
                'speakers': '; '.join(speakers) if speakers else "",
                'president_remarks': president_remarks,
            }
            
        except Exception as e:
            logger.error(f"Error extracting data from {url}: {e}")
            return None
    
    def _extract_speakers(self, content_elem):
        """Extract list of speakers from content"""
        if not content_elem:
            return []
        
        speakers = set()
        # Look for speaker patterns like "Name:" or "Name (Title):"
        paragraphs = content_elem.find_all(['p', 'div'])
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Match patterns like "Vladimir Putin:", "Dmitry Medvedev:", etc.
            match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*\([^)]+\))?\s*:', text)
            if match:
                speakers.add(match.group(1))
        
        return sorted(list(speakers))
    
    def _extract_president_remarks(self, content_elem):
        """Extract only Putin or Medvedev's remarks"""
        if not content_elem:
            return ""
        
        remarks = []
        paragraphs = content_elem.find_all(['p', 'div'])
        current_speaker = None
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            
            # Check if this is a speaker attribution
            speaker_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*\([^)]+\))?\s*:\s*(.*)', text)
            
            if speaker_match:
                speaker = speaker_match.group(1)
                speech_text = speaker_match.group(2)
                
                # Check if speaker is Putin or Medvedev
                if 'Putin' in speaker or 'Medvedev' in speaker:
                    current_speaker = speaker
                    if speech_text:
                        remarks.append(speech_text)
                else:
                    current_speaker = None
            elif current_speaker:
                # Continue collecting text for current president speaker
                remarks.append(text)
        
        return "\n\n".join(remarks)
    
    def scrape_all(self, max_transcripts=None, max_pages=50):
        """Main scraping orchestration"""
        try:
            self.setup_driver()
            
            all_links = []
            
            # Load links from all categories
            for category in self.categories:
                logger.info(f"\n{'='*60}")
                logger.info(f"CATEGORY: {category.upper()}")
                logger.info(f"{'='*60}")
                
                category_links = self.load_category_content(category, max_pages=max_pages)
                logger.info(f"[{category}] Found {len(category_links)} total links")
                all_links.extend(category_links)
            
            # Remove duplicates across categories
            links = list(set(all_links))
            logger.info(f"\n{'='*60}")
            logger.info(f"TOTAL UNIQUE LINKS: {len(links)}")
            logger.info(f"{'='*60}\n")
            
            if max_transcripts:
                links = links[:max_transcripts]
            
            # Scrape each transcript
            logger.info(f"Scraping {len(links)} transcripts...")
            for link in tqdm(links, desc="Scraping transcripts"):
                transcript_data = self.extract_transcript_data(link)
                if transcript_data:
                    self.transcripts.append(transcript_data)
                time.sleep(1)  # Be respectful to the server
            
            logger.info(f"\nSuccessfully scraped {len(self.transcripts)} transcripts")
            return self.transcripts
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_csv(self, filename="kremlin_all_transcripts_raw.csv"):
        """Save scraped data to CSV"""
        if not self.transcripts:
            logger.warning("No transcripts to save")
            return
        
        df = pd.DataFrame(self.transcripts)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} transcripts to {filename}")
        return df


if __name__ == "__main__":
    scraper = KremlinScraperAll()
    
    # Scrape all transcripts from all categories
    transcripts = scraper.scrape_all(max_transcripts=None, max_pages=50)
    
    # Save raw data
    df = scraper.save_to_csv("kremlin_all_transcripts_raw.csv")
    
    print(f"\nScraping complete! Collected {len(transcripts)} transcripts across all categories.")
    print(f"Data saved to kremlin_all_transcripts_raw.csv")
