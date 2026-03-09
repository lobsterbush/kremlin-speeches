#!/usr/bin/env python3
"""
Enhanced scraper for 1tv.ru news articles with batch processing
Handles large-scale scraping with browser restarts to prevent crashes
"""

import time
import re
from datetime import datetime
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


class OneTVBatchScraper:
    """Enhanced scraper with batch processing for 1tv.ru"""
    
    def __init__(self):
        self.base_url = "https://www.1tv.ru"
        self.news_url = "https://www.1tv.ru/news"
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
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.page_load_strategy = 'eager'
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(180)
        self.driver.implicitly_wait(10)
        
    def close_driver(self):
        """Close and cleanup driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def load_and_extract_batch(self, scroll_times=50):
        """Load news page, scroll, and extract links in a batch"""
        try:
            self.setup_driver()
            logger.info(f"Loading news page and scrolling {scroll_times} times...")
            
            self.driver.get(self.news_url)
            time.sleep(5)
            
            # Scroll with progress
            for i in range(scroll_times):
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Scrolled {i + 1}/{scroll_times} times")
                except Exception as e:
                    logger.warning(f"Error during scroll {i + 1}: {e}")
                    break
            
            # Extract links
            page_source = self.driver.page_source
            links = self.extract_article_links(page_source)
            logger.info(f"Extracted {len(links)} article links in this batch")
            
            return links
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return []
        finally:
            self.close_driver()
    
    def extract_article_links(self, page_source):
        """Extract article links from the news page"""
        soup = BeautifulSoup(page_source, 'lxml')
        links = set()
        
        # Extract from NEXT_DATA
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        if next_data_script:
            try:
                data = json.loads(next_data_script.string)
                
                def find_articles_recursive(obj, depth=0):
                    if depth > 10:
                        return
                    
                    if isinstance(obj, dict):
                        if 'url' in obj and isinstance(obj.get('url'), str):
                            url = obj['url']
                            if '/news/' in url:
                                if url.startswith('http'):
                                    links.add(url)
                                else:
                                    links.add(self.base_url + url)
                        
                        for value in obj.values():
                            find_articles_recursive(value, depth + 1)
                    
                    elif isinstance(obj, list):
                        for item in obj:
                            find_articles_recursive(item, depth + 1)
                
                find_articles_recursive(data)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse __NEXT_DATA__: {e}")
        
        # Backup: traditional link extraction
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if '/news/' in href and href != '/news' and href != '/news/':
                if href.startswith('http'):
                    links.add(href)
                elif href.startswith('/'):
                    links.add(self.base_url + href)
        
        return list(links)
    
    def collect_all_links(self, total_scrolls=200, batch_size=50):
        """Collect all article links using multiple batches"""
        logger.info(f"\n{'='*60}")
        logger.info(f"COLLECTING ARTICLE LINKS IN BATCHES")
        logger.info(f"Total scrolls: {total_scrolls}, Batch size: {batch_size}")
        logger.info(f"{'='*60}\n")
        
        num_batches = (total_scrolls + batch_size - 1) // batch_size
        
        for batch_num in range(num_batches):
            logger.info(f"\n--- Batch {batch_num + 1}/{num_batches} ---")
            batch_links = self.load_and_extract_batch(scroll_times=batch_size)
            
            before = len(self.all_links)
            self.all_links.update(batch_links)
            after = len(self.all_links)
            new_links = after - before
            
            logger.info(f"Added {new_links} new unique links (total: {after})")
            
            # If we're not getting new links, stop early
            if new_links == 0:
                logger.info("No new links found. Stopping early.")
                break
            
            # Brief pause between batches
            time.sleep(3)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TOTAL UNIQUE ARTICLE LINKS: {len(self.all_links)}")
        logger.info(f"{'='*60}\n")
        
        return list(self.all_links)
    
    def extract_article_data(self, url):
        """Extract data from a single article page"""
        max_retries = 3
        soup = None
        
        for attempt in range(max_retries):
            try:
                if not self.driver:
                    self.setup_driver()
                
                self.driver.get(url)
                time.sleep(2)
                soup = BeautifulSoup(self.driver.page_source, 'lxml')
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to load {url} after {max_retries} attempts: {e}")
                    return None
                logger.warning(f"Attempt {attempt + 1} failed for {url}, retrying...")
                self.close_driver()
                time.sleep(5)
        
        if not soup:
            return None
        
        try:
            # Extract title
            title = ""
            title_elem = soup.select_one("h1, .article-title, .news-title")
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Extract date
            date_str = ""
            date_elem = soup.select_one("time, .date, .article-date, .news-date")
            if date_elem:
                date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            
            # Extract content
            content = ""
            content_elem = soup.select_one(".article-text, .news-text, .article-content, .text, article")
            if content_elem:
                for elem in content_elem.find_all(['script', 'style']):
                    elem.decompose()
                content = content_elem.get_text(separator="\n", strip=True)
            
            # Extract category
            category = ""
            category_elem = soup.select_one(".category, .tag, .rubric")
            if category_elem:
                category = category_elem.get_text(strip=True)
            
            # Try NEXT_DATA if content is missing
            if not content or not title:
                next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
                if next_data_script:
                    try:
                        data = json.loads(next_data_script.string)
                        
                        def find_article_text(obj, depth=0):
                            results = {'title': '', 'text': '', 'lead': ''}
                            if depth > 10:
                                return results
                            
                            if isinstance(obj, dict):
                                if 'title' in obj and not results['title']:
                                    results['title'] = str(obj['title'])
                                if 'text' in obj and not results['text']:
                                    results['text'] = str(obj['text'])
                                if 'lead' in obj and not results['lead']:
                                    results['lead'] = str(obj['lead'])
                                
                                for value in obj.values():
                                    sub_results = find_article_text(value, depth + 1)
                                    for key in results:
                                        if sub_results[key] and not results[key]:
                                            results[key] = sub_results[key]
                            
                            elif isinstance(obj, list):
                                for item in obj:
                                    sub_results = find_article_text(item, depth + 1)
                                    for key in results:
                                        if sub_results[key] and not results[key]:
                                            results[key] = sub_results[key]
                            
                            return results
                        
                        article_data = find_article_text(data)
                        if not title:
                            title = article_data['title']
                        if not content:
                            content = article_data['lead'] + "\n\n" + article_data['text']
                    
                    except json.JSONDecodeError:
                        pass
            
            return {
                'url': url,
                'title': title,
                'date': date_str,
                'content': content,
                'category': category,
            }
            
        except Exception as e:
            logger.error(f"Error extracting data from {url}: {e}")
            return None
    
    def scrape_articles(self, links, batch_size=100):
        """Scrape articles with periodic driver restarts"""
        logger.info(f"\n{'='*60}")
        logger.info(f"SCRAPING {len(links)} ARTICLES")
        logger.info(f"{'='*60}\n")
        
        try:
            self.setup_driver()
            
            for i, link in enumerate(tqdm(links, desc="Scraping articles")):
                article_data = self.extract_article_data(link)
                if article_data and article_data['content']:
                    self.articles.append(article_data)
                
                time.sleep(1)
                
                # Restart driver every batch_size articles
                if (i + 1) % batch_size == 0:
                    logger.info(f"\nRestarting driver after {i + 1} articles...")
                    self.close_driver()
                    time.sleep(2)
                    self.setup_driver()
            
        finally:
            self.close_driver()
        
        logger.info(f"\nSuccessfully scraped {len(self.articles)} articles with content")
        return self.articles
    
    def save_to_csv(self, filename="1tv_news_raw.csv"):
        """Save scraped data to CSV"""
        if not self.articles:
            logger.warning("No articles to save")
            return
        
        df = pd.DataFrame(self.articles)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} articles to {filename}")
        return df


if __name__ == "__main__":
    scraper = OneTVBatchScraper()
    
    # Phase 1: Collect all article links (200 scrolls in batches of 50)
    links = scraper.collect_all_links(total_scrolls=200, batch_size=50)
    
    # Phase 2: Scrape all articles
    articles = scraper.scrape_articles(links, batch_size=100)
    
    # Save data
    df = scraper.save_to_csv("1tv_news_raw.csv")
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE!")
    print(f"{'='*60}")
    print(f"Total articles collected: {len(articles)}")
    print(f"Data saved to: 1tv_news_raw.csv")
    print(f"{'='*60}\n")
