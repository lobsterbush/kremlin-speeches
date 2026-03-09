"""
Resumable scraper for Kremlin speeches
Can continue from where it left off if interrupted
"""

import json
import os
from scrape_kremlin import KremlinScraper
from classify_geography import GeographicClassifier
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def save_progress(links, output_file="speech_links.json"):
    """Save speech links to resume later"""
    with open(output_file, 'w') as f:
        json.dump(links, f, indent=2)
    logger.info(f"Saved {len(links)} links to {output_file}")


def load_progress(output_file="speech_links.json"):
    """Load saved speech links"""
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            links = json.load(f)
        logger.info(f"Loaded {len(links)} links from {output_file}")
        return links
    return None


def get_already_scraped_urls(csv_file="kremlin_speeches_raw.csv"):
    """Get URLs that have already been scraped"""
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        return set(df['url'].tolist())
    return set()


def scrape_with_resume(batch_size=50, max_pages=100):
    """Scrape speeches with periodic saving"""
    
    # Try to load existing links
    links = load_progress()
    
    if not links:
        # Get all links first
        logger.info("Fetching all speech links...")
        scraper = KremlinScraper()
        scraper.setup_driver()
        links = scraper.load_all_content(max_pages=max_pages)
        scraper.driver.quit()
        
        # Save links
        save_progress(links)
        logger.info(f"Found {len(links)} total speeches")
    
    # Check what's already been scraped
    already_scraped = get_already_scraped_urls()
    remaining_links = [link for link in links if link not in already_scraped]
    
    logger.info(f"Already scraped: {len(already_scraped)}")
    logger.info(f"Remaining: {len(remaining_links)}")
    
    if not remaining_links:
        logger.info("All speeches already scraped!")
        return
    
    # Scrape in batches, restarting browser for each batch
    for i in range(0, len(remaining_links), batch_size):
        batch = remaining_links[i:i+batch_size]
        logger.info(f"\nProcessing batch {i//batch_size + 1}/{(len(remaining_links)-1)//batch_size + 1}")
        logger.info(f"Speeches {i+1} to {min(i+batch_size, len(remaining_links))} of {len(remaining_links)}")
        
        # Start fresh browser for each batch
        scraper = KremlinScraper()
        scraper.setup_driver()
        
        try:
            batch_speeches = []
            for link in batch:
                speech_data = scraper.extract_speech_data(link)
                if speech_data:
                    batch_speeches.append(speech_data)
            
            # Append to CSV
            if batch_speeches:
                df_batch = pd.DataFrame(batch_speeches)
                
                if os.path.exists("kremlin_speeches_raw.csv"):
                    df_existing = pd.read_csv("kremlin_speeches_raw.csv")
                    df_combined = pd.concat([df_existing, df_batch], ignore_index=True)
                    df_combined.to_csv("kremlin_speeches_raw.csv", index=False, encoding='utf-8')
                else:
                    df_batch.to_csv("kremlin_speeches_raw.csv", index=False, encoding='utf-8')
                
                logger.info(f"Saved batch of {len(batch_speeches)} speeches")
                logger.info(f"Total scraped so far: {len(already_scraped) + i + len(batch_speeches)}")
        
        finally:
            scraper.driver.quit()
            logger.info("Browser closed for this batch")
    
    logger.info(f"\n✓ Scraping complete!")


if __name__ == "__main__":
    # Scrape all speeches in batches of 50
    scrape_with_resume(batch_size=50, max_pages=100)
    
    # Classify
    logger.info("\n\nStarting geographic classification...")
    classifier = GeographicClassifier()
    df = classifier.classify_dataset(
        input_file="kremlin_speeches_raw.csv",
        output_file="kremlin_speeches_classified.csv"
    )
    
    print("\n✓ Complete pipeline finished successfully!")
