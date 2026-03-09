#!/usr/bin/env python3
"""
1tv.ru news scraper using the public API (no Selenium required).
Suitable for running on Oz cloud agents.

Usage:
    python3 scrape_1tv_requests.py --start 2019-01-01 --end 2024-12-31
    python3 scrape_1tv_requests.py --start 2006-01-01 --end 2007-12-31
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

import requests
import pandas as pd

# ── Configuration ──────────────────────────────────────────────────────────────

API_URL = "https://api.1tv.ru/www/v1/news"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.1tv.ru/",
}
REQUEST_DELAY = 1.5  # seconds between requests
SAVE_EVERY = 50  # save progress every N days
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries


# ── Progress tracking ──────────────────────────────────────────────────────────

def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return json.load(f)
    return {"last_date_scraped": None, "total_articles": 0, "failed_dates": []}


def save_progress(progress_file, progress):
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


# ── API helpers ────────────────────────────────────────────────────────────────

def fetch_news_for_date(date_str, session):
    """Fetch all news articles for a given date via the 1tv API."""
    url = f"{API_URL}?date={date_str}"
    articles = []

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                newslist = data.get("newslist", [])
                for group in newslist:
                    for item in group.get("news", []):
                        article = {
                            "url": item.get("link", ""),
                            "title": item.get("title", ""),
                            "date_extracted": date_str,
                            "content": item.get("lead", ""),
                            "category": extract_category(item.get("link", "")),
                            "article_id": item.get("id"),
                            "time": item.get("time", ""),
                        }
                        if article["url"] and article["content"]:
                            articles.append(article)
                return articles
            elif resp.status_code == 403:
                print(f"  403 on {date_str}, waiting {RETRY_DELAY * (attempt + 1)}s...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            elif resp.status_code == 429:
                wait = RETRY_DELAY * (attempt + 2)
                print(f"  Rate limited on {date_str}, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  HTTP {resp.status_code} on {date_str}")
                return articles
        except requests.exceptions.Timeout:
            print(f"  Timeout on {date_str} (attempt {attempt + 1})")
            time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            print(f"  Error on {date_str}: {e}")
            time.sleep(RETRY_DELAY)

    return articles


def extract_category(url):
    """Extract category from URL path if present."""
    m = re.search(r"/news/([a-z][a-z_]+)/\d{4}-\d{2}-\d{2}", url)
    if m:
        cat = m.group(1)
        if cat not in ("issue",):
            return cat
    return ""


# ── Main scraper ───────────────────────────────────────────────────────────────

def scrape_date_range(start_date, end_date, output_csv, progress_file):
    """Scrape all news articles in the given date range."""
    progress = load_progress(progress_file)

    # Resume from last scraped date
    current = start_date
    if progress["last_date_scraped"]:
        resumed_from = datetime.strptime(progress["last_date_scraped"], "%Y-%m-%d").date()
        if resumed_from >= start_date:
            current = resumed_from + timedelta(days=1)
            print(f"Resuming from {current} (already scraped through {resumed_from})")

    if current > end_date:
        print("Already completed this date range.")
        return

    # Load existing articles if output CSV exists
    all_articles = []
    existing_urls = set()
    if os.path.exists(output_csv):
        existing_df = pd.read_csv(output_csv)
        all_articles = existing_df.to_dict("records")
        existing_urls = set(existing_df["url"].values)
        print(f"Loaded {len(all_articles)} existing articles from {output_csv}")

    total_days = (end_date - current).days + 1
    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"\nScraping {total_days} days: {current} to {end_date}")
    print(f"API endpoint: {API_URL}")
    print(f"Output: {output_csv}\n")

    days_scraped = 0
    new_articles = 0

    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        articles = fetch_news_for_date(date_str, session)

        day_new = 0
        for art in articles:
            if art["url"] not in existing_urls:
                all_articles.append(art)
                existing_urls.add(art["url"])
                day_new += 1
                new_articles += 1

        if day_new > 0:
            print(f"  {date_str}: +{day_new} articles (total new: {new_articles})")
        elif articles:
            print(f"  {date_str}: {len(articles)} articles (all duplicates)")

        progress["last_date_scraped"] = date_str
        progress["total_articles"] = len(all_articles)
        days_scraped += 1

        # Periodic save
        if days_scraped % SAVE_EVERY == 0:
            save_results(all_articles, output_csv, progress, progress_file)
            pct = days_scraped / total_days * 100
            print(f"\n  [Progress] {days_scraped}/{total_days} days ({pct:.1f}%), "
                  f"{new_articles} new articles, {len(all_articles)} total\n")

        current += timedelta(days=1)
        time.sleep(REQUEST_DELAY)

    # Final save
    save_results(all_articles, output_csv, progress, progress_file)
    print(f"\nDone! Scraped {days_scraped} days, {new_articles} new articles.")
    print(f"Total articles in {output_csv}: {len(all_articles)}")


def save_results(all_articles, output_csv, progress, progress_file):
    """Save articles to CSV and progress to JSON."""
    df = pd.DataFrame(all_articles)
    # Ensure consistent column order
    cols = ["url", "title", "date_extracted", "content", "category", "article_id", "time"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols]
    df.to_csv(output_csv, index=False, encoding="utf-8")
    save_progress(progress_file, progress)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scrape 1tv.ru news via API")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default=None, help="Output CSV path")
    parser.add_argument("--progress", default=None, help="Progress JSON path")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()

    if args.output:
        output_csv = args.output
    else:
        output_csv = f"1tv_news_{args.start}_{args.end}.csv"

    if args.progress:
        progress_file = args.progress
    else:
        progress_file = f"1tv_progress_{args.start}_{args.end}.json"

    print(f"1TV News Scraper (API-based)")
    print(f"  Date range: {start} to {end}")
    print(f"  Output:     {output_csv}")
    print(f"  Progress:   {progress_file}")

    scrape_date_range(start, end, output_csv, progress_file)


if __name__ == "__main__":
    main()
