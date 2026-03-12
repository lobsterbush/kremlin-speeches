"""Scrape RT (Russia Today) English news articles via RSS, sitemaps, and Wayback Machine.

Three modes:
  --mode rss       Poll RSS feed for latest ~100 articles with full text
                   from content:encoded. Appends only new articles.
  --mode sitemap   Download yearly sitemaps (gzipped), extract URLs,
                   scrape article pages. Resumable via rt_progress.json.
  --mode wayback   Use Internet Archive CDX API to recover articles from
                   years missing in sitemap data (2015-2024). Fetches archived
                   pages from web.archive.org.

Output: rt_articles.csv

Usage:
    python3 scrape_rt.py --mode rss
    python3 scrape_rt.py --mode sitemap --max 500
    python3 scrape_rt.py --mode wayback --years 2015-2024 --max 2000
"""

import argparse
import gzip
import io
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

BASE = Path(__file__).parent
OUTPUT_CSV = BASE / "rt_articles.csv"
PROGRESS_FILE = BASE / "rt_progress.json"

SITEMAP_INDEX = "https://www.rt.com/sitemap.xml"
RSS_URL = "https://www.rt.com/rss/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Encoding": "gzip, deflate",
}
REQUEST_DELAY = 1.0
SAVE_EVERY = 100

# Categories to skip (shows, podcasts, etc. — keep news/opinion/analysis)
SKIP_CATEGORIES = {"shows", "podcast", "tags"}


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
    """Load scraping progress from JSON file."""
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"scraped_urls": [], "failed_urls": []}


def save_progress(progress: dict):
    """Save scraping progress to JSON file."""
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


# ── URL helpers ────────────────────────────────────────────────────────────────

def extract_category(url: str) -> str:
    """Extract category from RT URL like rt.com/news/634363-..."""
    m = re.search(r"rt\.com/(\w[\w-]*)/\d+", url)
    if m:
        return m.group(1)
    return ""


def should_skip_url(url: str) -> bool:
    """Skip non-article URLs (shows, podcasts, tag pages)."""
    cat = extract_category(url)
    if cat in SKIP_CATEGORIES:
        return True
    # Skip URLs that don't have article IDs
    if not re.search(r"/\d+-", url):
        return True
    return False


# ── RSS parsing (with full text from content:encoded) ──────────────────────────

def scrape_rss(session: requests.Session) -> list[dict]:
    """Scrape articles from RT RSS feed. RSS includes full article text."""
    print("Fetching RT RSS feed...")
    resp = session.get(RSS_URL, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    ns = {
        "content": "http://purl.org/rss/1.0/modules/content/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    items = root.findall(".//item")
    print(f"RSS items: {len(items)}")

    articles = []
    for item in items:
        link = item.findtext("link", "")
        if not link:
            continue
        # Clean CDATA/tracking params from link
        link = re.sub(r"\?utm_.*$", "", link.strip())

        if should_skip_url(link):
            continue

        title = item.findtext("title", "").strip()
        pub_date = item.findtext("pubDate", "")

        # Extract full text from content:encoded (RT provides this)
        content_encoded = item.findtext("content:encoded", "", ns)
        content = ""
        if content_encoded:
            ext = TextExtractor()
            ext.feed(content_encoded)
            content = ext.get_text()

        # Fallback: description (usually just lead)
        desc = item.findtext("description", "")
        lead = ""
        if desc:
            ext2 = TextExtractor()
            ext2.feed(desc)
            lead = ext2.get_text()
            if lead.endswith("Read Full Article at RT.com"):
                lead = lead.replace("Read Full Article at RT.com", "").strip()

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
            "title": title,
            "date": date,
            "lead": lead,
            "content": content,
            "category": extract_category(link),
        })

    return articles


# ── Sitemap parsing ────────────────────────────────────────────────────────────

def fetch_sitemap_urls(session: requests.Session) -> list[str]:
    """Download all RT yearly sitemaps and extract article URLs."""
    print("Fetching RT sitemap index...")
    resp = session.get(SITEMAP_INDEX, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    sitemap_urls = [
        el.text for el in root.iter()
        if el.tag.endswith("loc") and el.text
    ]
    print(f"Found {len(sitemap_urls)} yearly sitemaps")

    all_urls = []
    for sm_url in sorted(sitemap_urls, reverse=True):  # Recent years first
        name = sm_url.split("/")[-1]
        print(f"  Fetching {name}...", end=" ", flush=True)
        try:
            r = session.get(sm_url, timeout=60)
            r.raise_for_status()
            # Sitemaps may be gzipped
            try:
                content = gzip.decompress(r.content).decode("utf-8")
            except (gzip.BadGzipFile, OSError):
                content = r.text
            sm_root = ET.fromstring(content)
            urls = [
                el.text for el in sm_root.iter()
                if el.tag.endswith("loc") and el.text
            ]
            # Filter to article URLs only
            article_urls = [u for u in urls if not should_skip_url(u)]
            all_urls.extend(article_urls)
            print(f"{len(article_urls)} articles ({len(urls)} total)")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(0.5)

    print(f"\nTotal article URLs: {len(all_urls):,}")
    return all_urls


# ── Article scraping (for sitemap mode) ────────────────────────────────────────

def scrape_article(url: str, session: requests.Session) -> Optional[dict]:
    """Scrape a single RT article page."""
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

    article: dict = {
        "url": url,
        "category": extract_category(url),
    }

    # JSON-LD extraction
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

    # Full text from article body
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


# ── Data management ────────────────────────────────────────────────────────────

def load_existing() -> tuple:
    """Load existing CSV and return (df, url_set)."""
    if OUTPUT_CSV.exists():
        df = pd.read_csv(OUTPUT_CSV, low_memory=False)
        return df, set(df["url"].values)
    return pd.DataFrame(), set()


def save_articles(articles: list[dict], existing_df: pd.DataFrame):
    """Append new articles to CSV."""
    new_df = pd.DataFrame(articles)
    cols = ["url", "title", "date", "lead", "content", "category"]
    for c in cols:
        if c not in new_df.columns:
            new_df[c] = ""
    combined = pd.concat([existing_df, new_df[cols]], ignore_index=True)
    combined.to_csv(OUTPUT_CSV, index=False)
    return combined


# ── Main ───────────────────────────────────────────────────────────────────────

# ── Wayback Machine CDX API ─────────────────────────────────────────────────────

CDX_API = "https://web.archive.org/cdx/search/cdx"
WAYBACK_PREFIX = "https://web.archive.org/web"
# Sections known to contain articles
RT_SECTIONS = ["news", "russia", "usa", "uk", "business", "africa", "india", "op-ed"]


def query_cdx_year(session: requests.Session, year: int) -> list:
    """Query CDX API for RT article URLs archived in a given year.

    Returns list of (timestamp, original_url) tuples.
    """
    results = []
    for section in RT_SECTIONS:
        params = {
            "url": f"www.rt.com/{section}/*",
            "matchType": "prefix",
            "output": "json",
            "fl": "timestamp,original,statuscode",
            "filter": "statuscode:200",
            "from": f"{year}0101",
            "to": f"{year}1231",
            "collapse": "urlkey",
            "limit": "10000",
        }
        try:
            resp = session.get(CDX_API, params=params, timeout=120)
            if resp.status_code == 200 and resp.text.strip():
                rows = json.loads(resp.text)
                # First row is header ["timestamp", "original", "statuscode"]
                if len(rows) > 1:
                    for row in rows[1:]:
                        ts, url = row[0], row[1]
                        if not should_skip_url(url):
                            results.append((ts, url))
            print(f"  CDX {year}/{section}: {len(rows)-1 if resp.text.strip() and len(json.loads(resp.text)) > 1 else 0} URLs")
        except Exception as e:
            print(f"  CDX {year}/{section}: ERROR {e}")
        time.sleep(1)  # Be polite to IA
    return results


def scrape_wayback_article(url: str, timestamp: str, session: requests.Session) -> Optional[dict]:
    """Scrape an RT article from the Wayback Machine."""
    # id_ suffix gives raw page without Wayback toolbar
    wb_url = f"{WAYBACK_PREFIX}/{timestamp}id_/{url}"
    for attempt in range(3):
        try:
            resp = session.get(wb_url, timeout=45)
            if resp.status_code in (404, 403, 451, 522, 523):
                return None
            if resp.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            resp.raise_for_status()
            html = resp.text
            break
        except requests.exceptions.RequestException:
            time.sleep(5 * (attempt + 1))
    else:
        return None

    article: dict = {
        "url": url,
        "category": extract_category(url),
    }

    # JSON-LD extraction
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

    # Full text from article body
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

    # Fallback date from Wayback timestamp
    if not article.get("date") and len(timestamp) >= 8:
        article["date"] = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"

    article.setdefault("title", "")
    article.setdefault("date", "")
    article.setdefault("lead", "")
    article.setdefault("content", "")

    if not article["title"] and not article["content"]:
        return None

    return article


def main():
    parser = argparse.ArgumentParser(description="Scrape RT English news")
    parser.add_argument(
        "--mode", choices=["sitemap", "rss", "wayback"], required=True,
        help="Scraping mode: sitemap (historical), rss (daily), or wayback (gap recovery)",
    )
    parser.add_argument(
        "--max", type=int, default=0,
        help="Maximum articles to scrape (0 = unlimited)",
    )
    parser.add_argument(
        "--years", type=str, default="2015-2024",
        help="Year range for wayback mode (e.g. 2015-2024)",
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

        if new_articles:
            combined = save_articles(new_articles, existing_df)
            print(f"Saved {len(combined):,} total articles to {OUTPUT_CSV.name}")
        else:
            print("No new articles to add.")

    elif args.mode == "wayback":
        # Parse year range
        parts = args.years.split("-")
        year_start = int(parts[0])
        year_end = int(parts[1]) if len(parts) > 1 else year_start

        progress = load_progress()
        scraped_set = set(progress.get("scraped_urls", []))

        # Discover URLs via CDX API
        all_candidates = []
        for year in range(year_start, year_end + 1):
            print(f"\nQuerying CDX for {year}...")
            candidates = query_cdx_year(session, year)
            # Deduplicate: keep latest timestamp per URL
            url_map = {}
            for ts, url in candidates:
                if url not in url_map or ts > url_map[url]:
                    url_map[url] = ts
            all_candidates.extend(url_map.items())
            print(f"  {year}: {len(url_map)} unique article URLs")

        # Filter out already-scraped URLs
        to_scrape = [
            (url, ts) for url, ts in all_candidates
            if url not in existing_urls and url not in scraped_set
        ]
        if args.max > 0:
            to_scrape = to_scrape[:args.max]

        print(f"\nTotal candidates: {len(all_candidates):,}")
        print(f"Already have: {len(all_candidates) - len(to_scrape):,}")
        print(f"To scrape: {len(to_scrape):,}")

        if not to_scrape:
            print("Nothing new to scrape.")
            return

        new_articles = []
        failed = list(progress.get("failed_urls", []))
        start_time = time.time()

        for i, (url, ts) in enumerate(to_scrape):
            article = scrape_wayback_article(url, ts, session)
            if article:
                new_articles.append(article)
            else:
                failed.append(url)

            scraped_set.add(url)
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

            if done % SAVE_EVERY == 0:
                progress["scraped_urls"] = list(scraped_set)
                progress["failed_urls"] = failed
                save_progress(progress)
                if new_articles:
                    combined = save_articles(new_articles, existing_df)
                    existing_df = combined
                    existing_urls.update(a["url"] for a in new_articles)
                    new_articles = []

            time.sleep(REQUEST_DELAY * 1.5)  # Slower for Wayback

        progress["scraped_urls"] = list(scraped_set)
        progress["failed_urls"] = failed
        save_progress(progress)
        if new_articles:
            combined = save_articles(new_articles, existing_df)
            print(f"\nSaved {len(combined):,} total articles to {OUTPUT_CSV.name}")

        print(
            f"\nWayback done! Processed {len(scraped_set):,} URLs, "
            f"{len(new_articles)} new, {len(failed)} failures."
        )
        return

    elif args.mode == "sitemap":
        progress = load_progress()
        scraped_set = set(progress.get("scraped_urls", []))

        all_urls = fetch_sitemap_urls(session)
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

        progress["scraped_urls"] = list(scraped_set)
        progress["failed_urls"] = failed
        save_progress(progress)
        if new_articles:
            combined = save_articles(new_articles, existing_df)
            print(f"\nSaved {len(combined):,} total articles to {OUTPUT_CSV.name}")

        print(
            f"\nDone! Scraped {len(scraped_set):,} URLs, "
            f"{len(failed)} failures."
        )


if __name__ == "__main__":
    main()
