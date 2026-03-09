#!/usr/bin/env python3
"""
Scrape Kremlin transcripts from Internet Archive Wayback Machine
"""

import requests
import re
import time
import json
from collections import defaultdict

def get_wayback_snapshot(url, max_retries=3):
    """Get closest available Wayback snapshot for a URL"""
    api_url = f"http://archive.org/wayback/available?url={url}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(api_url, timeout=30)
            data = response.json()
            
            if data.get('archived_snapshots', {}).get('closest', {}).get('available'):
                return data['archived_snapshots']['closest']['url']
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"Error getting snapshot for {url}: {e}")
            return None

def scrape_wayback_page(wayback_url):
    """Scrape links from a Wayback Machine archived page"""
    try:
        response = requests.get(wayback_url, timeout=30)
        html = response.text
        
        # Extract event IDs from links like /events/president/news/12345
        pattern = r'/events/president/[^/]+/(\d+)'
        matches = re.findall(pattern, html)
        
        return set(matches)
    except Exception as e:
        print(f"Error scraping {wayback_url}: {e}")
        return set()

def scrape_category(category, start_page=1, max_pages=100):
    """Scrape a category from Wayback Machine"""
    print(f"\n{'='*60}")
    print(f"Scraping category: {category}")
    print(f"{'='*60}\n")
    
    all_ids = set()
    base_url = f"http://en.kremlin.ru/events/president/transcripts/{category}/page"
    
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    for page in range(start_page, max_pages + 1):
        page_url = f"{base_url}/{page}"
        
        print(f"Page {page}: ", end="", flush=True)
        
        # Get Wayback snapshot URL
        wayback_url = get_wayback_snapshot(page_url)
        
        if not wayback_url:
            print("No snapshot")
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"\nStopping after {max_consecutive_failures} consecutive failures")
                break
            time.sleep(1)
            continue
        
        # Scrape the archived page
        page_ids = scrape_wayback_page(wayback_url)
        
        if not page_ids:
            print("No links found")
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"\nStopping after {max_consecutive_failures} consecutive failures")
                break
        else:
            new_ids = page_ids - all_ids
            all_ids.update(page_ids)
            print(f"Found {len(page_ids)} IDs ({len(new_ids)} new)")
            consecutive_failures = 0
        
        time.sleep(1)  # Be polite to Wayback Machine
    
    return all_ids

def main():
    categories = [
        'statements',
        'speeches',
        'transcripts',
        'news-conferences',
        'press-statements'
    ]
    
    results = {}
    
    for category in categories:
        ids = scrape_category(category, start_page=2, max_pages=50)
        results[category] = sorted([int(x) for x in ids])
        
        print(f"\n{category}: {len(results[category])} unique IDs")
        if results[category]:
            print(f"  Range: {min(results[category])} - {max(results[category])}")
    
    # Save results
    with open('wayback_scraped_ids.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for category, ids in results.items():
        print(f"{category:20s}: {len(ids):5d} IDs")
    print(f"\nResults saved to wayback_scraped_ids.json")

if __name__ == '__main__':
    main()
