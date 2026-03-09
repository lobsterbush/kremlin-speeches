#!/usr/bin/env python3
"""
Historical scraper for 1tv.ru - covers 2000 to present
Includes resume capability and progress tracking
"""

import time
import re
import json
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import logging

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrape_1tv_historical.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HistoricalOneTVScraper:
    """Historical scraper for 1tv.ru from 2000 onwards"""
    
    def __init__(self, progress_file='1tv_progress.json'):
        self.base_url = "https://www.1tv.ru"
        self.driver = None
        self.all_links = set()
        self.articles = []
        self.progress_file = progress_file
        self.progress = self.load_progress()
        
    def load_progress(self):
        """Load scraping progress"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'links_collected': [],
            'last_date_scraped': None,
            'articles_scraped': 0
        }
    
    def save_progress(self):
        """Save scraping progress"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f)
        
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
    
    def scrape_date_archives(self, start_date, end_date):
        """Try to find articles by exploring date-based URLs"""
        logger.info(f"\n{'='*70}")
        logger.info(f"EXPLORING DATE ARCHIVES: {start_date.date()} to {end_date.date()}")
        logger.info(f"Total days to scan: {(end_date - start_date).days}")
        logger.info(f"{'='*70}\n")
        
        # Resume from last scraped date if available
        if self.progress['last_date_scraped']:
            last_date = datetime.fromisoformat(self.progress['last_date_scraped'])
            if last_date > start_date:
                start_date = last_date + timedelta(days=1)
                logger.info(f"Resuming from {start_date.date()}\n")
        
        current = start_date
        links = set(self.progress.get('links_collected', []))
        total_days = (end_date - start_date).days
        
        with tqdm(total=total_days, desc="Scanning dates", unit="day") as pbar:
            while current <= end_date:
                # Try various date URL patterns
                date_patterns = [
                    f"/news/{current.year}/{current.month:02d}/{current.day:02d}",
                    f"/news/{current.year}-{current.month:02d}-{current.day:02d}",
                    f"/news/issue/{current.year}/{current.month:02d}/{current.day:02d}",
                ]
                
                daily_links = 0
                for pattern in date_patterns:
                    url = self.base_url + pattern
                    try:
                        self.setup_driver()
                        self.driver.get(url)
                        time.sleep(2)
                        
                        page_links = self.extract_links_from_page(self.driver.page_source)
                        if page_links:
                            links.update(page_links)
                            daily_links += len(page_links)
                        
                        self.close_driver()
                    except Exception as e:
                        self.close_driver()
                        continue
                
                # Update progress
                self.progress['last_date_scraped'] = current.isoformat()
                self.progress['links_collected'] = list(links)
                
                # Save progress every 10 days
                if current.day % 10 == 0:
                    self.save_progress()
                
                if daily_links > 0:
                    pbar.set_postfix({'date': current.date().isoformat(), 
                                    'found': daily_links, 
                                    'total': len(links)})
                
                current += timedelta(days=1)
                pbar.update(1)
        
        # Final save
        self.save_progress()
        logger.info(f"\nTotal unique links collected: {len(links)}")
        return links
    
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
        logger.info(f"\n{'='*70}")
        logger.info(f"PHASE 2: SCRAPING {len(links)} ARTICLES")
        logger.info(f"{'='*70}\n")
        
        links = list(links)
        
        # Skip already scraped articles
        start_idx = self.progress.get('articles_scraped', 0)
        if start_idx > 0:
            logger.info(f"Resuming from article {start_idx}\n")
        
        try:
            self.setup_driver()
            
            for i in tqdm(range(start_idx, len(links)), desc="Scraping articles"):
                link = links[i]
                
                # Restart driver periodically
                if i > 0 and i % 100 == 0:
                    logger.info(f"\nRestarting driver after {i}...")
                    self.close_driver()
                    time.sleep(2)
                    self.setup_driver()
                
                article = self.extract_article_data(link)
                if article and article['content'] and len(article['content']) > 100:
                    self.articles.append(article)
                
                # Update progress
                self.progress['articles_scraped'] = i + 1
                
                # Save intermediate results every 500 articles
                if len(self.articles) % 500 == 0 and len(self.articles) > 0:
                    self.save_intermediate_results()
                    self.save_progress()
                
                time.sleep(0.5)
        
        finally:
            self.close_driver()
        
        return self.articles
    
    def save_intermediate_results(self):
        """Save intermediate results"""
        if self.articles:
            df = pd.DataFrame(self.articles)
            filename = f"1tv_news_historical_partial_{len(self.articles)}.csv"
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"\nSaved {len(self.articles)} articles to {filename}")
    
    def run(self):
        """Main execution"""
        try:
            # Phase 1: Collect links
            end_date = datetime.now()
            start_date = datetime(2000, 1, 1)  # Start from year 2000
            
            links = self.scrape_date_archives(start_date, end_date)
            self.all_links = links
            
            # Phase 2: Scrape articles
            articles = self.scrape_articles(links)
            
            # Final save
            if articles:
                df = pd.DataFrame(articles)
                df = df.drop_duplicates(subset=['url'])
                output_file = "1tv_news_historical_2000_2026.csv"
                df.to_csv(output_file, index=False, encoding='utf-8')
                
                logger.info(f"\n{'='*70}")
                logger.info(f"SCRAPING COMPLETE")
                logger.info(f"{'='*70}")
                logger.info(f"Total articles scraped: {len(df)}")
                logger.info(f"Output file: {output_file}")
                logger.info(f"Date range: 2000-01-01 to {datetime.now().date()}")
                
                return df
        
        except KeyboardInterrupt:
            logger.info("\n\nScraping interrupted. Progress saved. Run again to resume.")
            self.save_progress()
            if self.articles:
                self.save_intermediate_results()
        except Exception as e:
            logger.error(f"\n\nError during scraping: {e}")
            self.save_progress()
            if self.articles:
                self.save_intermediate_results()
            raise


if __name__ == "__main__":
    scraper = HistoricalOneTVScraper()
    scraper.run()
