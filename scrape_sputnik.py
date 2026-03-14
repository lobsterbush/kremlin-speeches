"""Scrape Sputnik International (sputnikglobe.com) English articles via sitemaps and RSS.

Two modes:
  --mode sitemap   Download monthly sitemaps from sitemap_article_index.xml,
                   extract URLs, scrape article pages. Resumable via
                   sputnik_progress.json. 267 monthly sitemaps (2004-2026).
  --mode rss       Poll RSS feed for latest ~100 articles. Appends only new
                   articles (deduplicates by URL).

Output: sputnik_articles.csv

Usage:
    python3 scrape_sputnik.py --mode rss
    python3 scrape_sputnik.py --mode sitemap
    python3 scrape_sputnik.py --mode sitemap --max 5000
    python3 scrape_sputnik.py --mode sitemap --sample 200  # per-month sample
"""

import argparse
import json
import random
import re
import sys
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).parent
OUTPUT_CSV = BASE / "sputnik_articles.csv"
PROGRESS_FILE = BASE / "sputnik_progress.json"

SITEMAP_INDEX = "https://sputnikglobe.com/sitemap_article_index.xml"
RSS_URL = "https://sputnikglobe.com/export/rss2/archive/index.xml"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}
REQUEST_DELAY = 1.0
SAVE_EVERY = 100


class TextExtractor(HTMLParser):
    """Strip HTML tags, keep text."""

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str):
        self.parts.append(data.strip())

    def get_text(self) -> str:
        return " ".join(p for p in self.parts if p)


# ── Progress tracking ──────────────────────────────────────────────────────────

def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"scraped_urls": [], "failed_urls": [], "completed_months": []}


def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


# ── URL helpers ────────────────────────────────────────────────────────────────

def extract_article_id(url: str) -> str:
    """Extract numeric article ID from Sputnik URL."""
    m = re.search(r"-(\d{8,})\.html", url)
    return m.group(1) if m else ""


def extract_date_from_url(url: str) -> str:
    """Extract date from URL like /20260314/..."""
    m = re.search(r"/(\d{4})(\d{2})(\d{2})/", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def extract_category_from_url(url: str) -> str:
    """Extract section from Sputnik URL path component after date."""
    # URLs like /20260314/title-with-section-info-123.html
    # Sputnik doesn't have a clean category in URL, use og:section instead
    return ""


# ── Sitemap parsing ────────────────────────────────────────────────────────────

def fetch_monthly_sitemaps(session: requests.Session) -> list[dict]:
    """Get all monthly sitemap URLs from the index."""
    print("Fetching Sputnik sitemap index...")
    resp = session.get(SITEMAP_INDEX, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    sitemaps = []
    for el in root.iter():
        if el.tag.endswith("loc") and el.text and "sitemap_article.xml" in el.text:
            url = el.text
            # Extract date range from URL
            m = re.search(r"date_start=(\d{8}).*?date_end=(\d{8})", url)
            if m:
                sitemaps.append({
                    "url": url,
                    "start": m.group(1),
                    "end": m.group(2),
                    "key": f"{m.group(1)}-{m.group(2)}",
                })

    print(f"Found {len(sitemaps)} monthly sitemaps")
    return sorted(sitemaps, key=lambda s: s["start"], reverse=True)


def fetch_urls_from_sitemap(url: str, session: requests.Session) -> list[str]:
    """Get all article URLs from a single monthly sitemap."""
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    return [
        el.text for el in root.iter()
        if el.tag.endswith("loc") and el.text and "/20" in el.text
    ]


# ── Article scraping ──────────────────────────────────────────────────────────

def scrape_article(url: str, session: requests.Session) -> dict | None:
    """Scrape a single Sputnik article page."""
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
        "date": extract_date_from_url(url),
    }

    # 1. og: meta tags (Sputnik uses these extensively)
    og_map = {
        "og:title": "title",
        "og:description": "lead",
        "article:section": "category",
        "article:published_time": "_pub_time",
    }
    for og_prop, field in og_map.items():
        m = re.search(
            rf'<meta property="{og_prop}" content="(.*?)"', html
        )
        if m:
            article[field] = m.group(1)

    # Parse published_time for more precise date
    if article.get("_pub_time"):
        date_m = re.search(r"(\d{4})(\d{2})(\d{2})", article["_pub_time"])
        if date_m:
            article["date"] = f"{date_m.group(1)}-{date_m.group(2)}-{date_m.group(3)}"
        del article["_pub_time"]

    # 2. Article body text
    # Sputnik uses <div class="article__text"> for content paragraphs
    text_blocks = re.findall(
        r'<div class="article__text">(.*?)</div>', html, re.DOTALL
    )
    if text_blocks:
        ext = TextExtractor()
        for block in text_blocks:
            ext.feed(block)
        article["content"] = ext.get_text()
    else:
        # Fallback: try article__body
        body = re.findall(
            r'<div class="article__body">(.*?)</div>', html, re.DOTALL
        )
        if body:
            ext = TextExtractor()
            ext.feed(body[0])
            article["content"] = ext.get_text()

    # 3. Keywords from news sitemap (already extracted in sitemap, but
    #    also available as meta keywords)
    kw_m = re.search(r'<meta name="keywords" content="(.*?)"', html)
    if kw_m:
        article["keywords"] = kw_m.group(1)

    article.setdefault("title", "")
    article.setdefault("date", "")
    article.setdefault("lead", "")
    article.setdefault("content", "")
    article.setdefault("category", "")
    article.setdefault("keywords", "")

    if not article["title"] and not article["content"]:
        return None

    return article


# ── RSS parsing ────────────────────────────────────────────────────────────────

def scrape_rss(session: requests.Session) -> list[dict]:
    """Scrape articles from Sputnik RSS feed."""
    print("Fetching Sputnik RSS feed...")
    resp = session.get(RSS_URL, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    items = root.findall(".//item")
    print(f"RSS items: {len(items)}")

    articles = []
    for item in items:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "")
        desc = item.findtext("description", "")

        if not link:
            continue

        # Parse date
        date = extract_date_from_url(link)
        if not date and pub_date:
            date_m = re.search(r"(\d{1,2}) (\w{3}) (\d{4})", pub_date)
            if date_m:
                months = {
                    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
                }
                d, m, y = date_m.groups()
                date = f"{y}-{months.get(m, '01')}-{d.zfill(2)}"

        # Clean description
        lead = ""
        if desc:
            ext = TextExtractor()
            ext.feed(desc)
            lead = ext.get_text()

        articles.append({
            "url": link,
            "article_id": extract_article_id(link),
            "title": title,
            "date": date,
            "lead": lead,
            "content": "",
            "category": "",
            "keywords": "",
        })

    return articles


# ── Main ───────────────────────────────────────────────────────────────────────

def load_existing() -> tuple:
    if OUTPUT_CSV.exists():
        df = pd.read_csv(OUTPUT_CSV, low_memory=False)
        return df, set(df["url"].values)
    return pd.DataFrame(), set()


def save_articles(articles: list[dict], existing_df: pd.DataFrame):
    new_df = pd.DataFrame(articles)
    cols = ["url", "article_id", "title", "date", "lead", "content",
            "category", "keywords"]
    for c in cols:
        if c not in new_df.columns:
            new_df[c] = ""
    combined = pd.concat([existing_df, new_df[cols]], ignore_index=True)
    combined.to_csv(OUTPUT_CSV, index=False)
    return combined


def main():
    parser = argparse.ArgumentParser(description="Scrape Sputnik International")
    parser.add_argument(
        "--mode", choices=["sitemap", "rss"], required=True,
        help="Scraping mode: sitemap (historical) or rss (daily)",
    )
    parser.add_argument(
        "--max", type=int, default=0,
        help="Maximum total articles to scrape (0 = unlimited)",
    )
    parser.add_argument(
        "--sample", type=int, default=0,
        help="Sample N articles per monthly sitemap (0 = all)",
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
        rss_articles = scrape_rss(session)
        new_articles = [a for a in rss_articles if a["url"] not in existing_urls]
        print(f"New from RSS: {len(new_articles)}")

        if args.full_text and new_articles:
            print("Fetching full text for new articles...")
            for i, art in enumerate(new_articles):
                full = scrape_article(art["url"], session)
                if full:
                    art.update({k: v for k, v in full.items() if v})
                if (i + 1) % 10 == 0:
                    print(f"  {i + 1}/{len(new_articles)}")
                time.sleep(REQUEST_DELAY)

        if new_articles:
            combined = save_articles(new_articles, existing_df)
            print(f"Saved {len(combined):,} total to {OUTPUT_CSV.name}")
        else:
            print("No new articles.")

    elif args.mode == "sitemap":
        progress = load_progress()
        scraped_set = set(progress.get("scraped_urls", []))
        completed_months = set(progress.get("completed_months", []))

        monthly_sitemaps = fetch_monthly_sitemaps(session)

        total_scraped = 0
        total_failed = 0
        new_articles = []
        failed = list(progress.get("failed_urls", []))
        start_time = time.time()

        for sm in monthly_sitemaps:
            if sm["key"] in completed_months:
                continue

            print(f"\n  Month {sm['start'][:6]}: ", end="", flush=True)
            try:
                urls = fetch_urls_from_sitemap(sm["url"], session)
            except Exception as e:
                print(f"ERROR fetching sitemap: {e}")
                continue

            # Filter already scraped
            urls = [u for u in urls if u not in existing_urls and u not in scraped_set]

            # Sample if requested
            if args.sample > 0 and len(urls) > args.sample:
                urls = random.sample(urls, args.sample)

            print(f"{len(urls)} new URLs", flush=True)

            for i, url in enumerate(urls):
                article = scrape_article(url, session)
                if article:
                    new_articles.append(article)
                    total_scraped += 1
                else:
                    failed.append(url)
                    total_failed += 1

                scraped_set.add(url)

                done = total_scraped + total_failed
                if done % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = done / elapsed if elapsed > 0 else 0
                    print(
                        f"  [{done}] {total_scraped} ok, "
                        f"{total_failed} fail | "
                        f"{rate:.1f}/sec"
                    )

                # Periodic save
                if done % SAVE_EVERY == 0:
                    progress["scraped_urls"] = list(scraped_set)
                    progress["failed_urls"] = failed
                    progress["completed_months"] = list(completed_months)
                    save_progress(progress)
                    if new_articles:
                        combined = save_articles(new_articles, existing_df)
                        existing_df = combined
                        existing_urls.update(a["url"] for a in new_articles)
                        new_articles = []

                if 0 < args.max <= (total_scraped + total_failed):
                    break

                time.sleep(REQUEST_DELAY)

            completed_months.add(sm["key"])

            if 0 < args.max <= (total_scraped + total_failed):
                print(f"Reached --max limit of {args.max}.")
                break

        # Final save
        progress["scraped_urls"] = list(scraped_set)
        progress["failed_urls"] = failed
        progress["completed_months"] = list(completed_months)
        save_progress(progress)
        if new_articles:
            combined = save_articles(new_articles, existing_df)
            existing_df = combined

        elapsed = time.time() - start_time
        print(
            f"\nDone. {total_scraped:,} scraped, "
            f"{total_failed:,} failed in {elapsed/60:.0f}m. "
            f"Total in CSV: {len(existing_df):,}."
        )


if __name__ == "__main__":
    main()
