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
    """Load classified CSV (with predicted categories)."""
    path = BASE / "1tv_news_classified.csv"
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
    """Year-sharded search index with titles, snippets, word count, category."""
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
            content_en = str(r.get("content_en", "")) if pd.notna(r.get("content_en")) else ""
            content_ru = str(r.get("content", "")) if pd.notna(r.get("content")) else ""
            cat = str(r.get("category_label", "")) if pd.notna(r.get("category_label")) else ""
            wc = len(content_en.split()) if content_en else 0
            rec = {
                "t": title_en[:150],
                "r": title_ru[:150],
                "d": str(r["date_extracted"])[:10] if pd.notna(r.get("date_extracted")) else "",
                "u": str(r["url"]) if pd.notna(r.get("url")) else "",
                "s": content_en[:120],
                "wc": wc,
            }
            if cat:
                rec["cat"] = cat
            records.append(rec)
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
    # Category distribution
    if "category_clean" in df.columns:
        cats = df["category_clean"].value_counts()
        stats["categories"] = [
            {"name": str(c), "count": int(n)} for c, n in cats.items()
        ]
    (DATA_DIR / "summary.json").write_text(json.dumps(stats))
    print(f"  summary.json: {stats}")


# ── TASS data generation ───────────────────────────────────────────────────────

def load_tass() -> pd.DataFrame:
    """Load TASS articles CSV if available."""
    path = BASE / "tass_articles.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["text"] = (
        df["title"].fillna("").astype(str)
        + " "
        + df["content"].fillna("").astype(str)
        + " "
        + df["lead"].fillna("").astype(str)
    ).str.lower()
    return df


def tass_stats(df: pd.DataFrame) -> None:
    """Generate TASS summary, volume, keywords, and category data."""
    tass_dir = DATA_DIR / "tass"
    tass_dir.mkdir(parents=True, exist_ok=True)

    # Summary
    stats = {
        "total_articles": len(df),
        "date_start": str(df["date"].min().date()) if len(df) else "",
        "date_end": str(df["date"].max().date()) if len(df) else "",
        "years_covered": int(df["year"].nunique()),
        "avg_content_len": round(df["content"].astype(str).str.len().mean(), 0),
        "categories": [
            {"name": str(c), "count": int(n)}
            for c, n in df["category"].value_counts().items()
        ],
    }
    (tass_dir / "summary.json").write_text(json.dumps(stats))
    print(f"  tass/summary.json: {stats['total_articles']} articles")

    # Monthly volume
    counts = df.groupby("month").size().reset_index(name="count")
    data = [{"month": r["month"], "count": int(r["count"])} for _, r in counts.iterrows()]
    (tass_dir / "monthly_volume.json").write_text(json.dumps(data))
    print(f"  tass/monthly_volume.json: {len(data)} months")

    # Keyword trends
    kw_results = {}
    for kw in TRACKED_KEYWORDS:
        pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
        monthly = (
            df.assign(has_kw=df["text"].str.contains(pattern, na=False))
            .groupby("month")["has_kw"]
            .mean()
            .reset_index()
        )
        kw_results[kw] = [
            {"month": r["month"], "pct": round(float(r["has_kw"]) * 100, 2)}
            for _, r in monthly.iterrows()
        ]
    (tass_dir / "keyword_trends.json").write_text(json.dumps(kw_results))
    print(f"  tass/keyword_trends.json: {len(kw_results)} keywords")

    # Country mentions
    co_results = {}
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
        co_results[country] = [
            {"month": r["month"], "pct": round(float(r["has"]) * 100, 2)}
            for _, r in monthly.iterrows()
        ]
    (tass_dir / "country_mentions.json").write_text(json.dumps(co_results))
    print(f"  tass/country_mentions.json: {len(co_results)} countries")


def cross_source_comparison(otv_df: pd.DataFrame, tass_df: pd.DataFrame) -> None:
    """Generate cross-source keyword comparison data."""
    compare_dir = DATA_DIR / "compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    # For each keyword, produce monthly pct for both sources
    results = {}
    for kw in TRACKED_KEYWORDS:
        pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
        entry = {}
        for label, df in [("1tv", otv_df), ("tass", tass_df)]:
            if len(df) == 0:
                continue
            monthly = (
                df.assign(has_kw=df["text"].str.contains(pattern, na=False))
                .groupby("month")["has_kw"]
                .mean()
                .reset_index()
            )
            entry[label] = [
                {"month": r["month"], "pct": round(float(r["has_kw"]) * 100, 2)}
                for _, r in monthly.iterrows()
            ]
        results[kw] = entry
    (compare_dir / "keyword_comparison.json").write_text(json.dumps(results))
    print(f"  compare/keyword_comparison.json: {len(results)} keywords")


def main():
    print("Loading 1TV data...")
    df = load_data()
    print(f"Loaded {len(df)} 1TV rows.\n")

    print("Generating 1TV JSON files:")
    summary_stats(df)
    monthly_volume(df)
    yearly_stats(df)
    keyword_trends(df)
    country_mentions(df)
    top_words_by_year(df)
    search_shards(df)

    print("\nLoading TASS data...")
    tass_df = load_tass()
    if len(tass_df) > 0:
        print(f"Loaded {len(tass_df)} TASS rows.\n")
        print("Generating TASS JSON files:")
        tass_stats(tass_df)
        print("\nGenerating cross-source comparison:")
        cross_source_comparison(df, tass_df)
    else:
        print("No TASS data found, skipping.\n")

    print("\nDone!")


if __name__ == "__main__":
    main()
