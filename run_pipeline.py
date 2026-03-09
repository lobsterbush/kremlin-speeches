"""
Master pipeline script for scraping and classifying Kremlin speeches
"""

import sys
from scrape_kremlin import KremlinScraper
from classify_geography import GeographicClassifier


def main():
    print("=" * 60)
    print("Kremlin Presidential Speeches Scraper")
    print("=" * 60)
    
    # Step 1: Scraping
    print("\n[STEP 1/2] Scraping speeches from kremlin.ru...")
    print("This may take several hours. Progress will be logged.\n")
    
    try:
        scraper = KremlinScraper()
        speeches = scraper.scrape_all(max_speeches=None)
        df = scraper.save_to_csv("kremlin_speeches_raw.csv")
        
        print(f"\n✓ Scraping complete! Collected {len(speeches)} speeches.")
        
    except Exception as e:
        print(f"\n✗ Error during scraping: {e}")
        sys.exit(1)
    
    # Step 2: Geographic Classification
    print("\n[STEP 2/2] Classifying speeches geographically...")
    
    try:
        classifier = GeographicClassifier()
        df_classified = classifier.classify_dataset(
            input_file="kremlin_speeches_raw.csv",
            output_file="kremlin_speeches_classified.csv"
        )
        
        print(f"\n✓ Classification complete!")
        print(f"✓ Final dataset saved to kremlin_speeches_classified.csv")
        
    except Exception as e:
        print(f"\n✗ Error during classification: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Pipeline completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
