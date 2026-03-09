"""
Collect all speech links with robust error handling
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def collect_links(max_pages=200):
    """Collect all speech links"""
    base_url = "http://en.kremlin.ru/events/president/transcripts/speeches"
    all_links = set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}/page/{page}"
        
        for retry in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=45)
                
                if response.status_code != 200:
                    logger.warning(f"Page {page} status {response.status_code}")
                    if response.status_code == 404:
                        logger.info("Reached end of pages")
                        return sorted(list(all_links))
                    time.sleep(5)
                    continue
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find speech links
                page_links = set()
                for a in soup.find_all('a', href=True):
                    href = a.get('href')
                    if re.match(r'^/events/president/transcripts/speeches/\d+$', href):
                        full_url = "http://en.kremlin.ru" + href
                        page_links.add(full_url)
                
                if not page_links:
                    consecutive_failures += 1
                    logger.warning(f"No speeches on page {page} (consecutive failures: {consecutive_failures})")
                    if consecutive_failures >= max_consecutive_failures:
                        logger.info(f"Stopping after {consecutive_failures} pages with no speeches")
                        return sorted(list(all_links))
                    break
                
                # Success - reset failure counter
                consecutive_failures = 0
                all_links.update(page_links)
                logger.info(f"Page {page}: +{len(page_links)} speeches (total: {len(all_links)})")
                
                # Save every 10 pages
                if page % 10 == 0:
                    with open('speech_links.json', 'w') as f:
                        json.dump(sorted(list(all_links)), f, indent=2)
                    logger.info(f"💾 Saved {len(all_links)} links")
                
                break  # Success, move to next page
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on page {page}, retry {retry + 1}/3")
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                time.sleep(10)
                if retry == 2:
                    # Save before potentially stopping
                    with open('speech_links.json', 'w') as f:
                        json.dump(sorted(list(all_links)), f, indent=2)
                    logger.info(f"💾 Saved {len(all_links)} links after error")
        
        time.sleep(1.5)  # Be respectful
    
    return sorted(list(all_links))


if __name__ == "__main__":
    logger.info("Starting link collection...")
    links = collect_links(max_pages=200)
    
    # Final save
    with open('speech_links.json', 'w') as f:
        json.dump(links, f, indent=2)
    
    logger.info(f"✓ Collection complete! Total: {len(links)} unique speeches")
    print(f"\n✓ Collected {len(links)} speech links")
