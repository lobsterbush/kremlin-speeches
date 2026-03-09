"""
Fast scraper using requests instead of Selenium
More reliable and faster for static content
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import json
import os
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def collect_all_links(base_url="http://en.kremlin.ru/events/president/transcripts/speeches", max_pages=200, save_file="speech_links.json"):
    """Collect all speech links using simple HTTP requests"""
    all_links = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}?page={page}"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Page {page} returned status {response.status_code}")
                break
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find speech links
            page_links = []
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                if re.match(r'^/events/president/transcripts/speeches/\d+$', href):
                    full_url = "http://en.kremlin.ru" + href
                    page_links.append(full_url)
            
            page_links = list(set(page_links))
            
            if not page_links:
                logger.info(f"No speeches found on page {page}, stopping")
                break
            
            all_links.extend(page_links)
            unique_links = list(set(all_links))
            logger.info(f"Page {page}: found {len(page_links)} speeches (total: {len(unique_links)})")
            
            # Save progress every 10 pages
            if page % 10 == 0:
                with open(save_file, 'w') as f:
                    json.dump(unique_links, f, indent=2)
                logger.info(f"Saved {len(unique_links)} links")
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error on page {page}: {e}")
            # Save what we have before breaking
            unique_links = list(set(all_links))
            if unique_links:
                with open(save_file, 'w') as f:
                    json.dump(unique_links, f, indent=2)
                logger.info(f"Saved {len(unique_links)} links before error")
            break
    
    return list(set(all_links))


def scrape_speech(url, headers):
    """Scrape a single speech using requests"""
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            logger.warning(f"Failed to load {url}: status {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract title
        title_elem = soup.select_one("h1.entry-title, .p-name, h1")
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Extract date
        date_elem = soup.select_one(".entry-date, time.dt-published, time")
        date_str = date_elem.get_text(strip=True) if date_elem else ""
        
        # Extract location
        location_elem = soup.select_one(".entry-info__place, .p-location")
        location = location_elem.get_text(strip=True) if location_elem else ""
        
        # Extract full content
        content_elem = soup.select_one(".entry-content, .read__content, .article__content")
        content = content_elem.get_text(separator="\n", strip=True) if content_elem else ""
        
        # Extract speakers
        speakers = extract_speakers(content_elem)
        
        # Extract Putin/Medvedev remarks
        president_remarks = extract_president_remarks(content_elem)
        
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
        logger.error(f"Error scraping {url}: {e}")
        return None


def extract_speakers(content_elem):
    """Extract list of speakers from content"""
    if not content_elem:
        return []
    
    speakers = set()
    paragraphs = content_elem.find_all(['p', 'div'])
    
    for p in paragraphs:
        text = p.get_text(strip=True)
        match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*\([^)]+\))?\s*:', text)
        if match:
            speakers.add(match.group(1))
    
    return sorted(list(speakers))


def extract_president_remarks(content_elem):
    """Extract only Putin or Medvedev's remarks"""
    if not content_elem:
        return ""
    
    remarks = []
    paragraphs = content_elem.find_all(['p', 'div'])
    current_speaker = None
    
    for p in paragraphs:
        text = p.get_text(strip=True)
        speaker_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*\([^)]+\))?\s*:\s*(.*)', text)
        
        if speaker_match:
            speaker = speaker_match.group(1)
            speech_text = speaker_match.group(2)
            
            if 'Putin' in speaker or 'Medvedev' in speaker:
                current_speaker = speaker
                if speech_text:
                    remarks.append(speech_text)
            else:
                current_speaker = None
        elif current_speaker:
            remarks.append(text)
    
    return "\n\n".join(remarks)


def main():
    # Step 1: Collect all links
    links_file = "speech_links.json"
    
    if os.path.exists(links_file):
        with open(links_file) as f:
            links = json.load(f)
        logger.info(f"Loaded {len(links)} links from {links_file}")
    else:
        logger.info("Collecting all speech links...")
        links = collect_all_links(max_pages=200)
        with open(links_file, 'w') as f:
            json.dump(links, f, indent=2)
        logger.info(f"Saved {len(links)} links to {links_file}")
    
    # Step 2: Scrape speeches
    csv_file = "kremlin_speeches_raw.csv"
    already_scraped = set()
    
    if os.path.exists(csv_file):
        df_existing = pd.read_csv(csv_file)
        already_scraped = set(df_existing['url'].tolist())
        logger.info(f"Already scraped: {len(already_scraped)}")
    
    remaining = [link for link in links if link not in already_scraped]
    logger.info(f"Remaining to scrape: {len(remaining)}")
    
    if not remaining:
        logger.info("All speeches already scraped!")
        return
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    speeches = []
    batch_size = 100
    
    consecutive_403s = 0
    max_consecutive_403s = 5
    
    for i, url in enumerate(tqdm(remaining, desc="Scraping speeches")):
        # Retry with backoff for 403 errors
        speech_data = None
        got_403 = False
        
        for retry in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code == 403:
                    got_403 = True
                    consecutive_403s += 1
                    logger.warning(f"403 error ({consecutive_403s} consecutive)")
                    
                    # If we hit too many 403s, take a long break
                    if consecutive_403s >= max_consecutive_403s:
                        pause_time = 300  # 5 minutes
                        logger.info(f"Rate limited! Pausing for {pause_time} seconds...")
                        time.sleep(pause_time)
                        consecutive_403s = 0
                    else:
                        time.sleep(10 * (retry + 1))
                    continue
                elif response.status_code == 200:
                    # Success - reset counter
                    consecutive_403s = 0
                    
                    soup = BeautifulSoup(response.text, 'lxml')
                    
                    # Extract title
                    title_elem = soup.select_one("h1.entry-title, .p-name, h1")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Extract date
                    date_elem = soup.select_one(".entry-date, time.dt-published, time")
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    
                    # Extract location
                    location_elem = soup.select_one(".entry-info__place, .p-location")
                    location = location_elem.get_text(strip=True) if location_elem else ""
                    
                    # Extract full content
                    content_elem = soup.select_one(".entry-content, .read__content, .article__content")
                    content = content_elem.get_text(separator="\n", strip=True) if content_elem else ""
                    
                    # Extract speakers
                    speakers = extract_speakers(content_elem)
                    
                    # Extract Putin/Medvedev remarks
                    president_remarks = extract_president_remarks(content_elem)
                    
                    speech_data = {
                        'url': url,
                        'title': title,
                        'date': date_str,
                        'location': location,
                        'content': content,
                        'speakers': '; '.join(speakers) if speakers else "",
                        'president_remarks': president_remarks,
                    }
                    break
                else:
                    logger.warning(f"Status {response.status_code} for {url}")
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                if retry < 2:
                    time.sleep(5 * (retry + 1))
        
        if speech_data:
            speeches.append(speech_data)
        elif got_403:
            # If we failed due to 403, add extra delay before next request
            time.sleep(5)
        
        # Save periodically
        if (i + 1) % batch_size == 0 or i == len(remaining) - 1:
            if speeches:
                df_batch = pd.DataFrame(speeches)
                
                if os.path.exists(csv_file):
                    df_existing = pd.read_csv(csv_file)
                    df_combined = pd.concat([df_existing, df_batch], ignore_index=True)
                    df_combined.to_csv(csv_file, index=False, encoding='utf-8')
                else:
                    df_batch.to_csv(csv_file, index=False, encoding='utf-8')
                
                logger.info(f"Saved batch, total: {len(already_scraped) + i + 1}")
                speeches = []
        
        # Base delay between requests (3-5 seconds randomized)
        import random
        time.sleep(random.uniform(3.0, 5.0))
    
    logger.info("✓ Scraping complete!")


if __name__ == "__main__":
    main()
