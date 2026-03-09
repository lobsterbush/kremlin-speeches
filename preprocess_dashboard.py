"""Preprocess 1TV translated data into JSON files for the GitHub Pages dashboard."""

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
DATA_DIR = BASE / "docs" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STOPWORDS = {
    "with", "from", "that", "this", "will", "have", "been", "were", "they",
    "their", "about", "which", "when", "what", "more", "also", "than", "into",
    "after", "between", "over", "most", "other", "only", "some", "said",
    "first", "year", "years", "time", "held", "took", "place", "made",
    "during", "before", "already", "there", "being", "very", "just", "well",
    "such", "part", "would", "could", "should", "where", "does", "each",
    "much", "under", "through", "even", "then", "them", "those", "these",
    "here", "same", "both", "many", "came", "come", "news", "program",
    "release", "channel", "today", "became", "according", "noted",
    "called", "told", "announced", "reported", "stated", "added",
}

TRACKED_KEYWORDS = [
    "ukraine", "military", "putin", "china", "sanctions", "nato",
    "syria", "crimea", "war", "economy", "nuclear", "election",
    "terrorism", "covid", "pandemic", "gas", "europe", "united",
    "security", "defense", "biden", "trump", "obama",
]

TRACKED_COUNTRIES = [
    "ukraine", "china", "united states", "america", "germany", "france",
    "syria", "turkey", "japan", "india", "belarus", "georgia",
    "iran", "israel", "britain", "poland", "kazakhstan",
]

COUNTRY_ALIASES = {
    "america": "united states",
    "american": "united states",
    "britain": "united kingdom",
    "british": "united kingdom",
    "chinese": "china",
    "turkish": "turkey",
    "german": "germany",
    "french": "france",
    "iranian": "iran",
    "israeli": "israel",
    "japanese": "japan",
    "indian": "india",
    "polish": "poland",
    "ukrainian": "ukraine",
    "syrian": "syria",
    "belarusian": "belarus",
    "georgian": "georgia",
}

COUNTRY_DISPLAY = [
    "ukraine", "china", "united states", "united kingdom", "germany",
    "france", "syria", "turkey", "japan", "india", "belarus",
    "georgia", "iran", "israel", "poland", "kazakhstan",
]


def load_data() -> pd.DataFrame:
    """Load translated CSV."""
    path = BASE / "1tv_news_2000_2026_translated.csv"
    df = pd.read_csv(path, low_memory=False)
    df["date"] = pd.to_datetime(df["date_extracted"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["text"] = (
        df["title_en"].fillna("").astype(str)
        + " "
        + df["content_en"].fillna("").astype(str)
    ).str.lower()
    return df


def monthly_volume(df: pd.DataFrame) -> None:
    """Article count per month."""
    counts = df.groupby("month").size().reset_index(name="count")
    data = [{"month": r["month"], "count": int(r["count"])} for _, r in counts.iterrows()]
    (DATA_DIR / "monthly_volume.json").write_text(json.dumps(data))
    print(f"  monthly_volume.json: {len(data)} months")


def yearly_stats(df: pd.DataFrame) -> None:
    """Per-year aggregate stats."""
    df["content_en_len"] = df["content_en"].astype(str).str.len()
    df["title_en_len"] = df["title_en"].astype(str).str.len()
    stats = (
        df.groupby("year")
        .agg(
            count=("url", "size"),
            avg_content_len=("content_en_len", "mean"),
            avg_title_len=("title_en_len", "mean"),
        )
        .reset_index()
    )
    data = []
    for _, r in stats.iterrows():
        data.append({
            "year": int(r["year"]),
            "count": int(r["count"]),
            "avg_content_len": round(r["avg_content_len"], 1),
            "avg_title_len": round(r["avg_title_len"], 1),
        })
    (DATA_DIR / "yearly_stats.json").write_text(json.dumps(data))
    print(f"  yearly_stats.json: {len(data)} years")


def keyword_trends(df: pd.DataFrame) -> None:
    """Monthly frequency of tracked keywords."""
    results = {}
    for kw in TRACKED_KEYWORDS:
        pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
        monthly = (
            df.assign(has_kw=df["text"].str.contains(pattern, na=False))
            .groupby("month")["has_kw"]
            .mean()
            .reset_index()
        )
        results[kw] = [
            {"month": r["month"], "pct": round(float(r["has_kw"]) * 100, 2)}
            for _, r in monthly.iterrows()
        ]
    (DATA_DIR / "keyword_trends.json").write_text(json.dumps(results))
    print(f"  keyword_trends.json: {len(results)} keywords")


def country_mentions(df: pd.DataFrame) -> None:
    """Monthly mentions of countries in content."""
    results = {}
    for country in COUNTRY_DISPLAY:
        terms = [country]
        for alias, canonical in COUNTRY_ALIASES.items():
            if canonical == country:
                terms.append(alias)
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b", re.IGNORECASE
        )
        monthly = (
            df.assign(has=df["text"].str.contains(pattern, na=False))
            .groupby("month")["has"]
            .mean()
            .reset_index()
        )
        results[country] = [
            {"month": r["month"], "pct": round(float(r["has"]) * 100, 2)}
            for _, r in monthly.iterrows()
        ]
    (DATA_DIR / "country_mentions.json").write_text(json.dumps(results))
    print(f"  country_mentions.json: {len(results)} countries")


def top_words_by_year(df: pd.DataFrame) -> None:
    """Top 25 words per year from English titles+content."""
    results = {}
    for year in sorted(df["year"].dropna().unique()):
        ydf = df[df["year"] == year]
        words = Counter()
        for text in ydf["text"]:
            for w in re.findall(r"\b[a-zA-Z]{4,}\b", str(text)):
                wl = w.lower()
                if wl not in STOPWORDS:
                    words[wl] += 1
        top = [{"word": w, "count": c} for w, c in words.most_common(25)]
        results[str(int(year))] = top
    (DATA_DIR / "top_words_by_year.json").write_text(json.dumps(results))
    print(f"  top_words_by_year.json: {len(results)} years")


def search_shards(df: pd.DataFrame) -> None:
    """Year-sharded search index with both Russian and English titles."""
    search_dir = DATA_DIR / "search"
    search_dir.mkdir(parents=True, exist_ok=True)

    years_with_data = []
    total = 0
    for year in sorted(df["year"].dropna().unique()):
        ydf = df[df["year"] == year]
        records = []
        for _, r in ydf.iterrows():
            title_en = str(r.get("title_en", "")) if pd.notna(r.get("title_en")) else ""
            title_ru = str(r.get("title", "")) if pd.notna(r.get("title")) else ""
            if not title_en and not title_ru:
                continue
            records.append({
                "t": title_en[:150],
                "r": title_ru[:150],
                "d": str(r["date_extracted"])[:10] if pd.notna(r.get("date_extracted")) else "",
                "u": str(r["url"]) if pd.notna(r.get("url")) else "",
            })
        yr = str(int(year))
        (search_dir / f"{yr}.json").write_text(
            json.dumps(records, ensure_ascii=False)
        )
        years_with_data.append(yr)
        total += len(records)
    (search_dir / "years.json").write_text(json.dumps(years_with_data))
    print(f"  search shards: {total} articles across {len(years_with_data)} years")


def summary_stats(df: pd.DataFrame) -> None:
    """Overall summary for the hero section."""
    stats = {
        "total_articles": len(df),
        "date_start": str(df["date"].min().date()),
        "date_end": str(df["date"].max().date()),
        "years_covered": int(df["year"].nunique()),
        "avg_articles_per_day": round(len(df) / (df["date"].max() - df["date"].min()).days, 1),
        "avg_content_len": round(df["content_en"].astype(str).str.len().mean(), 0),
        "total_words_millions": round(
            df["content_en"].astype(str).str.split().str.len().sum() / 1_000_000, 1
        ),
    }
    (DATA_DIR / "summary.json").write_text(json.dumps(stats))
    print(f"  summary.json: {stats}")


def main():
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} rows.\n")

    print("Generating JSON files:")
    summary_stats(df)
    monthly_volume(df)
    yearly_stats(df)
    keyword_trends(df)
    country_mentions(df)
    top_words_by_year(df)
    search_shards(df)

    print("\nDone!")


if __name__ == "__main__":
    main()
