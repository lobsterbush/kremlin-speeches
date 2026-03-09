#!/usr/bin/env python3
"""
Comprehensive scraper for 1tv.ru - all news articles and broadcasts
Explores multiple sections and date-based archives
"""

import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveOneTVScraper:
    """Comprehensive scraper for all 1tv.ru news content"""
    
    def __init__(self):
        self.base_url = "https://www.1tv.ru"
        self.driver = None
        self.all_links = set()
        self.articles = []
        
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        chrome_options.page_load_strategy = 'eager'
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(180)
        self.driver.implicitly_wait(10)
        
    def close_driver(self):
        """Close driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def extract_links_from_page(self, page_source):
        """Extract article links from page"""
        soup = BeautifulSoup(page_source, 'lxml')
        links = set()
        
        # Try NEXT_DATA first
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        if next_data_script:
            try:
                data = json.loads(next_data_script.string)
                
                def find_urls(obj, depth=0):
                    if depth > 15:
                        return
                    if isinstance(obj, dict):
                        if 'url' in obj and isinstance(obj.get('url'), str):
                            url = obj['url']
                            if '/news/' in url:
                                links.add(self.base_url + url if url.startswith('/') else url)
                        for value in obj.values():
                            find_urls(value, depth + 1)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_urls(item, depth + 1)
                
                find_urls(data)
            except:
                pass
        
        # Traditional link extraction
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if '/news/' in href and href not in ['/news', '/news/', '/news/issue']:
                links.add(self.base_url + href if href.startswith('/') else href)
        
        return links
    
    def scrape_section(self, url, scroll_times=50):
        """Scrape a section with scrolling"""
        try:
            self.setup_driver()
            logger.info(f"Scraping section: {url}")
            
            self.driver.get(url)
            time.sleep(5)
            
            # Scroll
            for i in range(scroll_times):
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                    if (i + 1) % 20 == 0:
                        logger.info(f"  Scrolled {i + 1}/{scroll_times}")
                except:
                    break
            
            links = self.extract_links_from_page(self.driver.page_source)
            logger.info(f"  Found {len(links)} links")
            return links
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return set()
        finally:
            self.close_driver()
    
    def scrape_date_archives(self, start_date, end_date):
        """Try to find articles by exploring date-based URLs"""
        logger.info(f"\nExploring date archives from {start_date} to {end_date}")
        
        current = start_date
        links = set()
        
        while current <= end_date:
            # Try various date URL patterns
            date_patterns = [
                f"/news/{current.year}/{current.month:02d}/{current.day:02d}",
                f"/news/{current.year}-{current.month:02d}-{current.day:02d}",
                f"/news/issue/{current.year}/{current.month:02d}/{current.day:02d}",
            ]
            
            for pattern in date_patterns:
                url = self.base_url + pattern
                try:
                    self.setup_driver()
                    self.driver.get(url)
                    time.sleep(2)
                    
                    page_links = self.extract_links_from_page(self.driver.page_source)
                    if page_links:
                        logger.info(f"  {pattern}: found {len(page_links)} links")
                        links.update(page_links)
                    
                    self.close_driver()
                except:
                    self.close_driver()
                    continue
            
            current += timedelta(days=1)
            
            if len(links) % 100 == 0 and len(links) > 0:
                logger.info(f"  Total so far: {len(links)} links")
        
        return links
    
    def collect_all_links(self):
        """Collect links from all sections"""
        logger.info(f"\n{'='*60}")
        logger.info("PHASE 1: COLLECTING ALL ARTICLE LINKS")
        logger.info(f"{'='*60}\n")
        
        # Main sections to scrape
        sections = [
            ("/news", 100),  # Main news page
            ("/news/issue", 50),  # News broadcasts/issues
        ]
        
        for section_url, scroll_times in sections:
            url = self.base_url + section_url
            links = self.scrape_section(url, scroll_times)
            before = len(self.all_links)
            self.all_links.update(links)
            after = len(self.all_links)
            logger.info(f"Added {after - before} new links from {section_url} (total: {after})\n")
            time.sleep(3)
        
        # Try date archives from Jan 1, 2000 to present - maximize historical coverage
        end_date = datetime.now()
        start_date = datetime(2000, 1, 1)
        
        logger.info(f"\nTrying date-based archives...")
        date_links = self.scrape_date_archives(start_date, end_date)
        before = len(self.all_links)
        self.all_links.update(date_links)
        after = len(self.all_links)
        logger.info(f"Added {after - before} new links from archives (total: {after})\n")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TOTAL UNIQUE LINKS: {len(self.all_links)}")
        logger.info(f"{'='*60}\n")
        
        return list(self.all_links)
    
    def extract_article_data(self, url):
        """Extract article data"""
        try:
            if not self.driver:
                self.setup_driver()
            
            self.driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Extract data
            title = ""
            title_elem = soup.select_one("h1, .article-title, .news-title")
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            date_str = ""
            date_elem = soup.select_one("time, .date")
            if date_elem:
                date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            
            content = ""
            content_elem = soup.select_one(".article-text, .news-text, .content, article")
            if content_elem:
                for elem in content_elem.find_all(['script', 'style']):
                    elem.decompose()
                content = content_elem.get_text(separator="\n", strip=True)
            
            category = ""
            category_elem = soup.select_one(".category, .tag, .rubric")
            if category_elem:
                category = category_elem.get_text(strip=True)
            
            # Try NEXT_DATA if missing
            if not content or not title:
                next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
                if next_data_script:
                    try:
                        data = json.loads(next_data_script.string)
                        
                        def find_text(obj, depth=0):
                            results = {'title': '', 'text': '', 'lead': ''}
                            if depth > 10:
                                return results
                            if isinstance(obj, dict):
                                for key in ['title', 'text', 'lead']:
                                    if key in obj and not results[key]:
                                        results[key] = str(obj[key])
                                for value in obj.values():
                                    sub = find_text(value, depth + 1)
                                    for k in results:
                                        if sub[k] and not results[k]:
                                            results[k] = sub[k]
                            elif isinstance(obj, list):
                                for item in obj:
                                    sub = find_text(item, depth + 1)
                                    for k in results:
                                        if sub[k] and not results[k]:
                                            results[k] = sub[k]
                            return results
                        
                        article_data = find_text(data)
                        if not title:
                            title = article_data['title']
                        if not content:
                            content = (article_data['lead'] + "\n\n" + article_data['text']).strip()
                    except:
                        pass
            
            return {
                'url': url,
                'title': title,
                'date': date_str,
                'content': content,
                'category': category,
            }
            
        except Exception as e:
            logger.error(f"Error extracting {url}: {e}")
            return None
    
    def scrape_articles(self, links):
        """Scrape all articles"""
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 2: SCRAPING {len(links)} ARTICLES")
        logger.info(f"{'='*60}\n")
        
        try:
            self.setup_driver()
            
            for i, link in enumerate(tqdm(links, desc="Scraping")):
                article_data = self.extract_article_data(link)
                if article_data and article_data['content']:
                    self.articles.append(article_data)
                
                time.sleep(1)
                
                # Restart every 100
                if (i + 1) % 100 == 0:
                    logger.info(f"\nRestarting driver after {i + 1}...")
                    self.close_driver()
                    time.sleep(2)
                    self.setup_driver()
            
        finally:
            self.close_driver()
        
        logger.info(f"\nSuccessfully scraped {len(self.articles)} articles with content")
        return self.articles
    
    def save_to_csv(self, filename="1tv_news_comprehensive.csv"):
        """Save to CSV"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        df = pd.DataFrame(self.articles)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} articles to {filename}")
        return df


if __name__ == "__main__":
    scraper = ComprehensiveOneTVScraper()
    
    # Collect all links
    links = scraper.collect_all_links()
    
    # Scrape articles
    articles = scraper.scrape_articles(links)
    
    # Save
    df = scraper.save_to_csv("1tv_news_comprehensive.csv")
    
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE SCRAPING COMPLETE!")
    print(f"{'='*60}")
    print(f"Total articles: {len(articles)}")
    print(f"Saved to: 1tv_news_comprehensive.csv")
    print(f"{'='*60}\n")
