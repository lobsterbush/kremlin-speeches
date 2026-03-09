"""Daily incremental update: scrape new 1TV articles, translate, append.

Designed to run in CI (GitHub Actions) or locally.  Scrapes the last N days
from the 1TV API, translates new articles via Argos Translate, appends them
to the main translated CSV, then re-runs classification and dashboard
preprocessing.

Usage:
    python3 update_daily.py              # scrape yesterday
    python3 update_daily.py --days 3     # scrape last 3 days
"""

import argparse
import csv
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).parent
TRANSLATED_CSV = BASE / "1tv_news_2000_2026_translated.csv"

# ── 1TV API ────────────────────────────────────────────────────────────────────

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


def extract_category(url: str) -> str:
    """Extract category slug from article URL."""
    m = re.search(r"/news/([a-z][a-z_]+)/\d{4}-\d{2}-\d{2}", url)
    if m and m.group(1) != "issue":
        return m.group(1)
    return ""


def scrape_date(date_str: str, session: requests.Session) -> list[dict]:
    """Fetch all articles for a single date from the 1TV API."""
    url = f"{API_URL}?date={date_str}"
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                articles = []
                for group in data.get("newslist", []):
                    for item in group.get("news", []):
                        article = {
                            "url": item.get("link", ""),
                            "title": item.get("title", ""),
                            "date_extracted": date_str,
                            "content": item.get("lead", ""),
                            "category": extract_category(item.get("link", "")),
                        }
                        if article["url"] and article["content"]:
                            articles.append(article)
                return articles
            elif resp.status_code in (403, 429):
                time.sleep(5 * (attempt + 1))
            else:
                return []
        except requests.exceptions.RequestException:
            time.sleep(5)
    return []


# ── Translation ────────────────────────────────────────────────────────────────

def setup_translator():
    """Install Argos ru→en model and return translator."""
    import argostranslate.package
    import argostranslate.translate

    installed = argostranslate.translate.get_installed_languages()
    lang_codes = {lang.code for lang in installed}

    if "ru" not in lang_codes or "en" not in lang_codes:
        print("Downloading Russian→English model...")
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = next(
            (p for p in available if p.from_code == "ru" and p.to_code == "en"),
            None,
        )
        if pkg is None:
            print("ERROR: ru→en package not found.")
            sys.exit(1)
        argostranslate.package.install_from_path(pkg.download())

    installed = argostranslate.translate.get_installed_languages()
    ru = next(lang for lang in installed if lang.code == "ru")
    en = next(lang for lang in installed if lang.code == "en")
    return ru.get_translation(en)


def translate_text(translator, text: str) -> str:
    """Translate a single Russian text to English."""
    if not text or not isinstance(text, str) or not text.strip():
        return ""
    try:
        return translator.translate(text)
    except Exception:
        return ""


# ── Main pipeline ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Daily 1TV update")
    parser.add_argument(
        "--days", type=int, default=1,
        help="Number of past days to scrape (default: 1 = yesterday)",
    )
    parser.add_argument(
        "--skip-classify", action="store_true",
        help="Skip re-running the classifier",
    )
    parser.add_argument(
        "--skip-dashboard", action="store_true",
        help="Skip regenerating dashboard data",
    )
    args = parser.parse_args()

    # 1. Load existing URLs to deduplicate
    print("Loading existing data...")
    if TRANSLATED_CSV.exists():
        existing = pd.read_csv(TRANSLATED_CSV, low_memory=False)
        existing_urls = set(existing["url"].values)
        print(f"  Existing: {len(existing):,} articles")
    else:
        existing = pd.DataFrame()
        existing_urls = set()

    # 2. Scrape recent days
    session = requests.Session()
    session.headers.update(HEADERS)
    new_articles = []
    today = datetime.now().date()

    for d in range(1, args.days + 1):
        target = today - timedelta(days=d)
        date_str = target.strftime("%Y-%m-%d")
        articles = scrape_date(date_str, session)
        day_new = [a for a in articles if a["url"] not in existing_urls]
        new_articles.extend(day_new)
        for a in day_new:
            existing_urls.add(a["url"])
        print(f"  {date_str}: {len(articles)} scraped, {len(day_new)} new")
        time.sleep(1.5)

    if not new_articles:
        print("\nNo new articles found. Nothing to update.")
        return

    print(f"\n{len(new_articles)} new articles to translate.")

    # 3. Translate
    print("Setting up translator...")
    translator = setup_translator()
    print("Translating...")
    for i, art in enumerate(new_articles):
        art["title_en"] = translate_text(translator, art["title"])
        art["content_en"] = translate_text(translator, art["content"])
        if (i + 1) % 50 == 0:
            print(f"  Translated {i + 1}/{len(new_articles)}")

    print(f"  Translated {len(new_articles)} articles.")

    # 4. Append to translated CSV
    new_df = pd.DataFrame(new_articles)
    cols = ["url", "title", "date_extracted", "content", "category",
            "title_en", "content_en"]
    for c in cols:
        if c not in new_df.columns:
            new_df[c] = ""
    new_df = new_df[cols]

    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.to_csv(TRANSLATED_CSV, index=False)
    print(f"\nAppended to {TRANSLATED_CSV.name}: {len(combined):,} total articles")

    # 5. Re-run classifier
    if not args.skip_classify:
        print("\nRe-running classifier...")
        subprocess.run(
            [sys.executable, str(BASE / "01_classify_categories.py")],
            check=True,
        )

    # 6. Regenerate dashboard data
    if not args.skip_dashboard:
        print("\nRegenerating dashboard data...")
        subprocess.run(
            [sys.executable, str(BASE / "preprocess_dashboard.py")],
            check=True,
        )

    print("\nDaily update complete!")


if __name__ == "__main__":
    main()
