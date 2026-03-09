#!/usr/bin/env python3
"""
Scraper for 1tv.ru news articles (Channel One Russia)
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
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OneTVNewsScraper:
    """Scraper for 1tv.ru news articles"""
    
    def __init__(self):
        self.base_url = "https://www.1tv.ru"
        self.news_url = "https://www.1tv.ru/news"
        self.driver = None
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
        logger.info("WebDriver initialized")
        
    def load_news_page(self, scroll_times=20):
        """Load news page and scroll to load more articles"""
        logger.info(f"Loading news page: {self.news_url}")
        self.driver.get(self.news_url)
        time.sleep(5)  # Wait for initial load
        
        # Scroll down multiple times to load more articles
        logger.info(f"Scrolling to load more articles ({scroll_times} times)...")
        for i in range(scroll_times):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            if (i + 1) % 5 == 0:
                logger.info(f"Scrolled {i + 1}/{scroll_times} times")
        
        return self.driver.page_source
    
    def extract_article_links(self, page_source):
        """Extract article links from the news page"""
        soup = BeautifulSoup(page_source, 'lxml')
        links = set()
        
        # Try to find NEXT_DATA JSON with articles
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        if next_data_script:
            try:
                data = json.loads(next_data_script.string)
                # Navigate through the JSON structure to find articles
                # This structure may vary, so we'll be flexible
                logger.info("Found __NEXT_DATA__, extracting article URLs...")
                
                def find_articles_recursive(obj, depth=0):
                    """Recursively search for article URLs in nested JSON"""
                    if depth > 10:  # Prevent infinite recursion
                        return
                    
                    if isinstance(obj, dict):
                        # Look for URL patterns that indicate news articles
                        if 'url' in obj and isinstance(obj.get('url'), str):
                            url = obj['url']
                            if '/news/' in url:
                                if url.startswith('http'):
                                    links.add(url)
                                else:
                                    links.add(self.base_url + url)
                        
                        # Recurse through dictionary values
                        for value in obj.values():
                            find_articles_recursive(value, depth + 1)
                    
                    elif isinstance(obj, list):
                        # Recurse through list items
                        for item in obj:
                            find_articles_recursive(item, depth + 1)
                
                find_articles_recursive(data)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse __NEXT_DATA__: {e}")
        
        # Also try traditional link extraction as backup
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if '/news/' in href and href != '/news' and href != '/news/':
                if href.startswith('http'):
                    links.add(href)
                elif href.startswith('/'):
                    links.add(self.base_url + href)
        
        return list(links)
    
    def extract_article_data(self, url):
        """Extract data from a single article page"""
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
            title = ""
            title_elem = soup.select_one("h1, .article-title, .news-title")
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Extract date
            date_str = ""
            date_elem = soup.select_one("time, .date, .article-date, .news-date")
            if date_elem:
                date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            
            # Extract content/lead
            content = ""
            # Try multiple selectors for content
            content_elem = soup.select_one(".article-text, .news-text, .article-content, .text, article")
            if content_elem:
                # Remove scripts and styles
                for elem in content_elem.find_all(['script', 'style']):
                    elem.decompose()
                content = content_elem.get_text(separator="\n", strip=True)
            
            # Extract category/tags
            category = ""
            category_elem = soup.select_one(".category, .tag, .rubric")
            if category_elem:
                category = category_elem.get_text(strip=True)
            
            # If we couldn't find structured content, try to extract from NEXT_DATA
            if not content or not title:
                next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
                if next_data_script:
                    try:
                        data = json.loads(next_data_script.string)
                        # Try to find article data in the JSON
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
                                    if sub_results['title'] and not results['title']:
                                        results['title'] = sub_results['title']
                                    if sub_results['text'] and not results['text']:
                                        results['text'] = sub_results['text']
                                    if sub_results['lead'] and not results['lead']:
                                        results['lead'] = sub_results['lead']
                            
                            elif isinstance(obj, list):
                                for item in obj:
                                    sub_results = find_article_text(item, depth + 1)
                                    if sub_results['title'] and not results['title']:
                                        results['title'] = sub_results['title']
                                    if sub_results['text'] and not results['text']:
                                        results['text'] = sub_results['text']
                                    if sub_results['lead'] and not results['lead']:
                                        results['lead'] = sub_results['lead']
                            
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
    
    def scrape_all(self, max_articles=None, scroll_times=20):
        """Main scraping orchestration"""
        try:
            self.setup_driver()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"SCRAPING 1TV.RU NEWS ARTICLES")
            logger.info(f"{'='*60}")
            
            # Load news page and collect links
            page_source = self.load_news_page(scroll_times=scroll_times)
            links = self.extract_article_links(page_source)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"TOTAL UNIQUE ARTICLE LINKS: {len(links)}")
            logger.info(f"{'='*60}\n")
            
            if max_articles:
                links = links[:max_articles]
            
            # Scrape each article
            logger.info(f"Scraping {len(links)} articles...")
            for link in tqdm(links, desc="Scraping articles"):
                article_data = self.extract_article_data(link)
                if article_data and article_data['content']:  # Only save if we got content
                    self.articles.append(article_data)
                time.sleep(1)  # Be respectful to the server
            
            logger.info(f"\nSuccessfully scraped {len(self.articles)} articles with content")
            return self.articles
            
        finally:
            if self.driver:
                self.driver.quit()
    
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
    scraper = OneTVNewsScraper()
    
    # Scrape articles (scroll 200 times to load as much as possible)
    # This will take a long time but should collect all available articles
    articles = scraper.scrape_all(max_articles=None, scroll_times=200)
    
    # Save raw data
    df = scraper.save_to_csv("1tv_news_raw.csv")
    
    print(f"\nScraping complete! Collected {len(articles)} articles.")
    print(f"Data saved to 1tv_news_raw.csv")
