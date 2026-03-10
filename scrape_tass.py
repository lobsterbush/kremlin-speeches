"""Scrape TASS English news articles via sitemaps and RSS.

Two modes:
  --mode sitemap   Download all TASS sitemaps, extract URLs, scrape article
                   pages for full text.  Resumable via tass_progress.json.
  --mode rss       Poll the RSS feed for the latest ~55 articles per category.
                   Appends only new articles (deduplicates by URL).

Output: tass_articles.csv

Usage:
    python3 scrape_tass.py --mode rss
    python3 scrape_tass.py --mode sitemap
    python3 scrape_tass.py --mode sitemap --max 500   # limit for testing
"""

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).parent
OUTPUT_CSV = BASE / "tass_articles.csv"
PROGRESS_FILE = BASE / "tass_progress.json"

SITEMAP_INDEX = "https://tass.com/sitemap.xml"
RSS_URL = "https://tass.com/rss/v2.xml"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}
REQUEST_DELAY = 1.0  # seconds between article requests
SAVE_EVERY = 100     # save progress every N articles


class TextExtractor(HTMLParser):
    """Strip HTML tags, keep text."""

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data: str):
        self.parts.append(data.strip())

    def get_text(self) -> str:
        return " ".join(p for p in self.parts if p)


# ── Progress tracking ──────────────────────────────────────────────────────────

def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"scraped_urls": [], "failed_urls": []}


def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


# ── Sitemap parsing ────────────────────────────────────────────────────────────

def fetch_sitemap_urls(session: requests.Session) -> list[str]:
    """Download all TASS news sitemaps and extract article URLs."""
    print("Fetching sitemap index...")
    resp = session.get(SITEMAP_INDEX, timeout=30)
    resp.raise_for_status()

    # Parse sitemap index for news sitemap URLs (namespace-agnostic)
    root = ET.fromstring(resp.text)
    sitemap_urls = [
        el.text
        for el in root.iter()
        if el.tag.endswith("loc") and el.text and "sitemap_news" in el.text
    ]
    print(f"Found {len(sitemap_urls)} news sitemaps")

    all_urls = []
    for sm_url in sorted(sitemap_urls):
        print(f"  Fetching {sm_url.split('/')[-1]}...", end=" ")
        try:
            r = session.get(sm_url, timeout=60)
            r.raise_for_status()
            sm_root = ET.fromstring(r.text)
            urls = [el.text for el in sm_root.iter() if el.tag.endswith("loc")]
            all_urls.extend(urls)
            print(f"{len(urls)} URLs")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(0.5)

    print(f"\nTotal article URLs from sitemaps: {len(all_urls):,}")
    return all_urls


# ── Article parsing ────────────────────────────────────────────────────────────

def extract_category_from_url(url: str) -> str:
    """Extract category from TASS URL like /politics/2098961."""
    m = re.search(r"tass\.com/(\w+)/\d+", url)
    return m.group(1) if m else ""


def extract_article_id(url: str) -> str:
    """Extract numeric ID from TASS URL."""
    m = re.search(r"/(\d+)$", url)
    return m.group(1) if m else ""


def scrape_article(url: str, session: requests.Session) -> dict:
    """Scrape a single TASS article page."""
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 404:
                return None
            if resp.status_code in (403, 429):
                time.sleep(5 * (attempt + 1))
                continue
            resp.raise_for_status()
            html = resp.text
            break
        except requests.exceptions.RequestException:
            time.sleep(3 * (attempt + 1))
    else:
        return None

    article = {
        "url": url,
        "article_id": extract_article_id(url),
        "category": extract_category_from_url(url),
    }

    # 1. JSON-LD
    for block in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    ):
        try:
            ld = json.loads(block)
            if isinstance(ld, dict) and ld.get("@type") in (
                "NewsArticle", "Article", "WebPage",
            ):
                article["title"] = ld.get("headline", "")
                article["date"] = ld.get("datePublished", "")[:10]
                article["lead"] = ld.get("description", "")
                if ld.get("articleSection"):
                    article["category"] = ld["articleSection"]
                break
        except (json.JSONDecodeError, KeyError):
            pass

    # 2. Full text from <div class="text-block">
    text_blocks = re.findall(
        r'<div class="text-block">(.*?)</div>', html, re.DOTALL
    )
    if text_blocks:
        extractor = TextExtractor()
        extractor.feed(text_blocks[0])
        article["content"] = extractor.get_text()
    else:
        article.setdefault("content", "")

    # 3. Fallback title from og:title
    if not article.get("title"):
        og = re.search(r'<meta property="og:title" content="(.*?)"', html)
        if og:
            article["title"] = og.group(1)

    # 4. Fallback date from og:url or meta
    if not article.get("date"):
        date_m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', html)
        if date_m:
            article["date"] = date_m.group(1)

    article.setdefault("title", "")
    article.setdefault("date", "")
    article.setdefault("lead", "")
    article.setdefault("content", "")

    # Skip articles with no meaningful content
    if not article["title"] and not article["content"]:
        return None

    return article


# ── RSS parsing ────────────────────────────────────────────────────────────────

def scrape_rss(session: requests.Session) -> list[dict]:
    """Scrape articles from TASS RSS feed."""
    print("Fetching TASS RSS feed...")
    resp = session.get(RSS_URL, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    items = root.findall(".//item")
    print(f"RSS items: {len(items)}")

    articles = []
    for item in items:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date = item.findtext("pubDate", "")
        desc = item.findtext("description", "")
        categories = [c.text for c in item.findall("category") if c.text]

        # Parse date
        date = ""
        if pub_date:
            date_m = re.search(r"(\d{1,2}) (\w{3}) (\d{4})", pub_date)
            if date_m:
                months = {
                    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
                }
                d, m, y = date_m.groups()
                date = f"{y}-{months.get(m, '01')}-{d.zfill(2)}"

        articles.append({
            "url": link,
            "article_id": extract_article_id(link),
            "title": title,
            "date": date,
            "lead": desc,
            "content": "",  # RSS only has lead; full text from article page
            "category": extract_category_from_url(link),
            "rss_categories": "; ".join(categories),
        })

    return articles


# ── Main ───────────────────────────────────────────────────────────────────────

def load_existing() -> tuple:
    """Load existing CSV and return (df, url_set)."""
    if OUTPUT_CSV.exists():
        df = pd.read_csv(OUTPUT_CSV, low_memory=False)
        return df, set(df["url"].values)
    return pd.DataFrame(), set()


def save_articles(articles: list[dict], existing_df: pd.DataFrame):
    """Append new articles to CSV."""
    new_df = pd.DataFrame(articles)
    cols = ["url", "article_id", "title", "date", "lead", "content", "category"]
    for c in cols:
        if c not in new_df.columns:
            new_df[c] = ""
    combined = pd.concat([existing_df, new_df[cols]], ignore_index=True)
    combined.to_csv(OUTPUT_CSV, index=False)
    return combined


def main():
    parser = argparse.ArgumentParser(description="Scrape TASS English news")
    parser.add_argument(
        "--mode", choices=["sitemap", "rss"], required=True,
        help="Scraping mode: sitemap (historical) or rss (daily)",
    )
    parser.add_argument(
        "--max", type=int, default=0,
        help="Maximum articles to scrape (0 = unlimited)",
    )
    parser.add_argument(
        "--full-text", action="store_true",
        help="In RSS mode, also scrape full article text from each page",
    )
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update(HEADERS)

    existing_df, existing_urls = load_existing()
    print(f"Existing articles: {len(existing_df):,}")

    if args.mode == "rss":
        # ── RSS mode ──
        rss_articles = scrape_rss(session)
        new_articles = [a for a in rss_articles if a["url"] not in existing_urls]
        print(f"New from RSS: {len(new_articles)}")

        if args.full_text and new_articles:
            print("Fetching full text for new articles...")
            for i, art in enumerate(new_articles):
                full = scrape_article(art["url"], session)
                if full and full.get("content"):
                    art["content"] = full["content"]
                if (i + 1) % 10 == 0:
                    print(f"  {i + 1}/{len(new_articles)}")
                time.sleep(REQUEST_DELAY)

        if new_articles:
            combined = save_articles(new_articles, existing_df)
            print(f"Saved {len(combined):,} total articles to {OUTPUT_CSV.name}")
        else:
            print("No new articles to add.")

    elif args.mode == "sitemap":
        # ── Sitemap mode ──
        progress = load_progress()
        scraped_set = set(progress.get("scraped_urls", []))

        # Get all URLs from sitemaps
        all_urls = fetch_sitemap_urls(session)

        # Filter out already scraped and existing
        to_scrape = [
            u for u in all_urls
            if u not in existing_urls and u not in scraped_set
        ]
        if args.max > 0:
            to_scrape = to_scrape[:args.max]

        print(f"URLs to scrape: {len(to_scrape):,}")
        if not to_scrape:
            print("Nothing new to scrape.")
            return

        new_articles = []
        failed = list(progress.get("failed_urls", []))
        start_time = time.time()

        for i, url in enumerate(to_scrape):
            article = scrape_article(url, session)
            if article:
                new_articles.append(article)
            else:
                failed.append(url)

            scraped_set.add(url)

            # Progress reporting
            done = i + 1
            if done % 50 == 0 or done == len(to_scrape):
                elapsed = time.time() - start_time
                rate = done / elapsed if elapsed > 0 else 0
                remaining = (len(to_scrape) - done) / rate if rate > 0 else 0
                print(
                    f"  [{done}/{len(to_scrape)}] "
                    f"{len(new_articles)} scraped, "
                    f"{len(failed)} failed | "
                    f"{rate:.1f}/sec | "
                    f"ETA: {remaining/60:.0f}m"
                )

            # Periodic save
            if done % SAVE_EVERY == 0:
                progress["scraped_urls"] = list(scraped_set)
                progress["failed_urls"] = failed
                save_progress(progress)
                if new_articles:
                    combined = save_articles(new_articles, existing_df)
                    existing_df = combined
                    existing_urls.update(a["url"] for a in new_articles)
                    new_articles = []

            time.sleep(REQUEST_DELAY)

        # Final save
        progress["scraped_urls"] = list(scraped_set)
        progress["failed_urls"] = failed
        save_progress(progress)
        if new_articles:
            combined = save_articles(new_articles, existing_df)
            print(f"\nSaved {len(combined):,} total articles to {OUTPUT_CSV.name}")

        print(f"\nDone! Scraped {len(scraped_set):,} URLs, "
              f"{len(failed)} failures.")


if __name__ == "__main__":
    main()
