"""
Scrape the Russian MFA English Telegram channel (@MFARussia) via the public
web preview at t.me/s/MFARussia.

Paginates backward through message history using the ?before=MSG_ID parameter.
Extracts message ID, date, text, embedded URLs.  Saves to mfa_telegram.csv.

Usage:
    python3 scrape_mfa_telegram.py               # scrape all available
    python3 scrape_mfa_telegram.py --max 2000     # scrape up to 2000 messages
"""

import argparse
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).parent
CSV_PATH = BASE / "mfa_telegram.csv"
PROGRESS_PATH = BASE / "mfa_telegram_progress.json"
CHANNEL = "MFARussia"
BASE_URL = f"https://t.me/s/{CHANNEL}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

FIELDNAMES = ["message_id", "date", "text", "urls", "has_photo", "views"]


def load_progress() -> dict:
    """Load scraping progress (lowest message ID seen so far)."""
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text())
    return {}


def save_progress(data: dict) -> None:
    PROGRESS_PATH.write_text(json.dumps(data, indent=2))


def load_existing_ids() -> set:
    """Load message IDs already in the CSV."""
    if not CSV_PATH.exists():
        return set()
    ids = set()
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.add(int(row["message_id"]))
    return ids


def parse_page(html: str) -> list[dict]:
    """Extract messages from a Telegram web preview page."""
    soup = BeautifulSoup(html, "html.parser")
    messages = []

    for widget in soup.select(".tgme_widget_message"):
        msg_id_attr = widget.get("data-post", "")
        # data-post format: "MFARussia/12345"
        parts = msg_id_attr.split("/")
        if len(parts) < 2:
            continue
        try:
            msg_id = int(parts[-1])
        except ValueError:
            continue

        # Date
        date_el = widget.select_one(".tgme_widget_message_date time")
        date_str = ""
        if date_el and date_el.get("datetime"):
            date_str = date_el["datetime"]

        # Text
        text_el = widget.select_one(".tgme_widget_message_text")
        text = ""
        if text_el:
            # Get text preserving newlines from <br> tags
            for br in text_el.find_all("br"):
                br.replace_with("\n")
            text = text_el.get_text(separator=" ").strip()
            # Collapse multiple spaces/newlines
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r" {2,}", " ", text)

        # Embedded URLs
        urls = []
        if text_el:
            for a in text_el.find_all("a", href=True):
                href = a["href"]
                if href and not href.startswith("tg://"):
                    urls.append(href)

        # Photo
        has_photo = bool(widget.select_one(".tgme_widget_message_photo"))

        # Views
        views_el = widget.select_one(".tgme_widget_message_views")
        views = views_el.get_text(strip=True) if views_el else ""

        if text or has_photo:
            messages.append({
                "message_id": msg_id,
                "date": date_str,
                "text": text,
                "urls": "|".join(urls),
                "has_photo": has_photo,
                "views": views,
            })

    return messages


def scrape(max_messages: int = 0) -> None:
    """Scrape MFA Telegram channel, paginating backward."""
    session = requests.Session()
    session.headers.update(HEADERS)

    existing_ids = load_existing_ids()
    progress = load_progress()
    min_id = progress.get("min_id")

    total_new = 0
    consecutive_empty = 0
    page = 0

    # Open CSV in append mode
    file_exists = CSV_PATH.exists() and CSV_PATH.stat().st_size > 0
    csvfile = open(CSV_PATH, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
    if not file_exists:
        writer.writeheader()

    try:
        while True:
            # Build URL
            if min_id:
                url = f"{BASE_URL}?before={min_id}"
            else:
                url = BASE_URL

            page += 1
            try:
                resp = session.get(url, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  Request error: {e}")
                time.sleep(5)
                consecutive_empty += 1
                if consecutive_empty > 5:
                    print("Too many consecutive failures, stopping.")
                    break
                continue

            messages = parse_page(resp.text)

            if not messages:
                consecutive_empty += 1
                if consecutive_empty > 3:
                    print("No more messages found, reached channel start.")
                    break
                time.sleep(2)
                continue

            consecutive_empty = 0
            new_count = 0

            for msg in messages:
                if msg["message_id"] not in existing_ids:
                    writer.writerow(msg)
                    existing_ids.add(msg["message_id"])
                    new_count += 1
                    total_new += 1

            # Update min_id to oldest message on this page
            page_min = min(m["message_id"] for m in messages)
            if min_id is None or page_min < min_id:
                min_id = page_min

            save_progress({"min_id": min_id, "total_scraped": len(existing_ids)})

            print(
                f"  Page {page}: {len(messages)} msgs, {new_count} new "
                f"(total: {len(existing_ids)}, min_id: {min_id})"
            )

            if 0 < max_messages <= total_new:
                print(f"Reached --max limit of {max_messages}.")
                break

            # Rate limit
            time.sleep(1.5)

    finally:
        csvfile.close()

    print(f"\nDone. {total_new} new messages scraped. Total in CSV: {len(existing_ids)}.")
    print(f"Saved to {CSV_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Scrape MFA Telegram channel")
    parser.add_argument(
        "--max", type=int, default=0,
        help="Maximum number of new messages to scrape (0 = unlimited)",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Reset progress and start from the latest messages",
    )
    args = parser.parse_args()

    if args.reset:
        if PROGRESS_PATH.exists():
            PROGRESS_PATH.unlink()
            print("Progress reset.")

    print(f"Scraping @{CHANNEL} Telegram channel...")
    print(f"  Output: {CSV_PATH}")
    if args.max > 0:
        print(f"  Max new messages: {args.max}")

    scrape(max_messages=args.max)


if __name__ == "__main__":
    main()
