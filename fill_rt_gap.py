"""Fill the RT 2015-2024 data gap by scraping article URLs from yearly sitemaps.

Samples up to --per-year articles from each gap year (default 2000),
fetches them from rt.com, and appends to rt_articles.csv.

Usage:
    python3 fill_rt_gap.py --per-year 2000
    python3 fill_rt_gap.py --per-year 500 --years 2020-2022
"""

import argparse
import gzip
import random
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

# Reuse scrape_article and helpers from the main scraper
from scrape_rt import (
    HEADERS,
    OUTPUT_CSV,
    TextExtractor,
    extract_category,
    load_existing,
    save_articles,
    should_skip_url,
)

SKIP_PATHS = {"/shows/", "/podcast/", "/tags/", "/in-vision/", "/in-motion/"}
SAVE_EVERY = 100
REQUEST_DELAY = 0.8


def fetch_sitemap_article_urls(session: requests.Session, year: int) -> list:
    """Fetch article URLs from a single yearly sitemap."""
    url = f"https://www.rt.com/sitemap_{year}.xml"
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    try:
        content = gzip.decompress(resp.content).decode("utf-8")
    except (gzip.BadGzipFile, OSError):
        content = resp.text
    root = ET.fromstring(content)
    locs = [el.text for el in root.iter() if el.tag.endswith("loc") and el.text]
    # Filter to article URLs only
    articles = []
    for u in locs:
        if any(s in u for s in SKIP_PATHS):
            continue
        if not re.search(r"/\d+-", u):
            continue
        articles.append(u)
    return articles


def scrape_article(url: str, session: requests.Session):
    """Scrape a single RT article page. Returns dict or None."""
    import json as _json

    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 404:
                return None
            if resp.status_code in (403, 429, 451):
                time.sleep(5 * (attempt + 1))
                continue
            resp.raise_for_status()
            html = resp.text
            break
        except requests.exceptions.RequestException:
            time.sleep(3 * (attempt + 1))
    else:
        return None

    article = {"url": url, "category": extract_category(url)}

    # JSON-LD extraction
    for block in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    ):
        try:
            ld = _json.loads(block)
            if isinstance(ld, dict) and ld.get("@type") in (
                "NewsArticle", "Article", "WebPage",
            ):
                article["title"] = ld.get("headline", "")
                article["date"] = ld.get("datePublished", "")[:10]
                article["lead"] = ld.get("description", "")
                if ld.get("articleSection"):
                    article["category"] = ld["articleSection"]
                break
        except (_json.JSONDecodeError, KeyError):
            pass

    # Full text
    body_match = re.search(
        r'<div class="article__text"[^>]*>(.*?)</div>\s*(?:<div class="article__|<footer)',
        html, re.DOTALL,
    )
    if not body_match:
        body_match = re.search(
            r'<div[^>]*class="[^"]*article[^"]*text[^"]*"[^>]*>(.*?)</div>',
            html, re.DOTALL,
        )
    if body_match:
        ext = TextExtractor()
        ext.feed(body_match.group(1))
        article["content"] = ext.get_text()
    else:
        article.setdefault("content", "")

    # Fallback title
    if not article.get("title"):
        og = re.search(r'<meta property="og:title" content="(.*?)"', html)
        if og:
            article["title"] = og.group(1)

    # Fallback date
    if not article.get("date"):
        dm = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', html)
        if dm:
            article["date"] = dm.group(1)

    article.setdefault("title", "")
    article.setdefault("date", "")
    article.setdefault("lead", "")
    article.setdefault("content", "")

    if not article["title"] and not article["content"]:
        return None
    return article


def main():
    parser = argparse.ArgumentParser(description="Fill RT 2015-2024 data gap")
    parser.add_argument("--per-year", type=int, default=2000,
                        help="Max articles to sample per year")
    parser.add_argument("--years", type=str, default="2015-2024",
                        help="Year range (e.g. 2015-2024)")
    args = parser.parse_args()

    parts = args.years.split("-")
    year_start = int(parts[0])
    year_end = int(parts[1]) if len(parts) > 1 else year_start

    session = requests.Session()
    session.headers.update(HEADERS)

    existing_df, existing_urls = load_existing()
    print(f"Existing articles: {len(existing_df):,}")

    # Collect and sample URLs per year
    all_to_scrape = []
    for year in range(year_start, year_end + 1):
        print(f"\nFetching sitemap for {year}...", end=" ", flush=True)
        try:
            urls = fetch_sitemap_article_urls(session, year)
            new_urls = [u for u in urls if u not in existing_urls]
            print(f"{len(urls):,} articles, {len(new_urls):,} new")
            if len(new_urls) > args.per_year:
                random.seed(year)  # Reproducible sampling
                sampled = random.sample(new_urls, args.per_year)
            else:
                sampled = new_urls
            all_to_scrape.extend(sampled)
            print(f"  Sampled {len(sampled):,} for scraping")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(0.5)

    print(f"\n{'=' * 60}")
    print(f"Total to scrape: {len(all_to_scrape):,}")
    print(f"Estimated time: {len(all_to_scrape) * REQUEST_DELAY / 3600:.1f} hours")
    print(f"{'=' * 60}\n")

    if not all_to_scrape:
        print("Nothing to scrape.")
        return

    # Shuffle to distribute years evenly (helps with rate limits)
    random.shuffle(all_to_scrape)

    new_articles = []
    failed = 0
    start_time = time.time()

    for i, url in enumerate(all_to_scrape):
        article = scrape_article(url, session)
        if article:
            new_articles.append(article)
        else:
            failed += 1

        done = i + 1

        if done % 50 == 0 or done == len(all_to_scrape):
            elapsed = time.time() - start_time
            rate = done / elapsed if elapsed > 0 else 0
            remaining = (len(all_to_scrape) - done) / rate if rate > 0 else 0
            print(
                f"  [{done:,}/{len(all_to_scrape):,}] "
                f"{len(new_articles):,} ok, {failed} fail | "
                f"{rate:.1f}/sec | ETA: {remaining/60:.0f}m"
            )

        if done % SAVE_EVERY == 0 and new_articles:
            combined = save_articles(new_articles, existing_df)
            existing_df = combined
            existing_urls.update(a["url"] for a in new_articles)
            new_articles = []

        time.sleep(REQUEST_DELAY)

    # Final save
    if new_articles:
        combined = save_articles(new_articles, existing_df)
        print(f"\nSaved {len(combined):,} total articles to {OUTPUT_CSV.name}")

    elapsed = time.time() - start_time
    print(f"\nDone! {done:,} processed, {failed} failed, {elapsed/60:.1f} minutes")


if __name__ == "__main__":
    main()
