"""Preprocess 1TV translated data into JSON files for the GitHub Pages dashboard."""

import json
import re
from collections import Counter
from datetime import datetime, timezone
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

# ── Unified Category Taxonomy ──────────────────────────────────────────────────

UNIFIED_CATEGORIES = [
    "Politics & Government",
    "Economy & Business",
    "Military & Security",
    "International Affairs",
    "Society & Culture",
    "Science & Health",
    "Sports",
]

# 1TV native category → unified
OTV_CATEGORY_MAP = {
    "Economy": "Economy & Business",
    "Culture": "Society & Culture",
    "Politics": "Politics & Government",
    "Sports": "Sports",
    "Moscow": "Society & Culture",
    "Incidents": "Military & Security",
    "World": "International Affairs",
    "Weather": "Society & Culture",
    "Health": "Science & Health",
    "Society": "Society & Culture",
}

# TASS native category → unified
TASS_CATEGORY_MAP = {
    "world": "International Affairs",
    "politics": "Politics & Government",
    "economy": "Economy & Business",
    "defense": "Military & Security",
    "society": "Society & Culture",
    "sports": "Sports",
    "emergencies": "Military & Security",
    "science": "Science & Health",
    "pressreview": "Politics & Government",
    "russia": "Politics & Government",
}

# RT section-based category → unified (geographic sections use keyword fallback)
RT_CATEGORY_MAP = {
    "business": "Economy & Business",
    "sport": "Sports",
    "pop-culture": "Society & Culture",
    "op-ed": "Politics & Government",
}
RT_GEO_SECTIONS = {"news", "russia", "usa", "uk", "africa", "india"}

# Keyword rules for classification (checked in priority order)
KEYWORD_RULES = [
    ("Military & Security", [
        "military", "army", "soldier", "weapon", "missile", "drone",
        "defense", "defence", "nato", "war ", "combat", "troops",
        "attack", "bomb", "artillery", "tank ", "navy",
        "nuclear", "warhead", "battalion", "brigade", "special operation",
        "terrorist", "terrorism", "extremis", "ceasefire", "offensive",
        "frontline", "armed force",
    ]),
    ("Economy & Business", [
        "economy", "economic", "gdp", "inflation", "trade", "export",
        "import", "sanction", "tariff", "oil ", "gas ", "energy",
        "ruble", "rouble", "bank", "finance", "invest", "market",
        "business", "company", "corporation", "stock",
        "budget", "debt", "growth", "recession",
    ]),
    ("Science & Health", [
        "science", "scientist", "research", "space ", "roscosmos",
        "satellite", "technology", "innovation", "artificial intelligence",
        "covid", "pandemic", "vaccine", "health", "hospital", "medical",
        "disease", "virus", "pharma",
    ]),
    ("Sports", [
        "sport", "football", "soccer", "hockey", "olympic",
        "championship", "tournament", "athlete", "medal", "fifa",
        "league", "coach",
    ]),
    ("International Affairs", [
        "diplomat", "embassy", "summit", "bilateral", "multilateral",
        "united nations", "treaty", "foreign minister", "foreign affair",
        "international", "g20 ", "brics", "shanghai cooperation",
    ]),
    ("Society & Culture", [
        "culture", "cultural", "museum", "film ", "movie",
        "music", "theater", "theatre", "education", "school",
        "university", "religion", "church", "orthodox", "mosque",
        "holiday", "festival", "tradition", "heritage",
        "demograph", "population", "migration",
    ]),
    ("Politics & Government", [
        "president", "putin", "government", "parliament", "duma",
        "election", "vote", "governor", "minister", "decree",
        "legislation", "law ", "policy", "political",
        "kremlin", "federation council",
    ]),
]


def classify_by_keywords(text: str) -> str:
    """Classify text into unified category using keyword matching."""
    if not text:
        return "Politics & Government"
    text_lower = str(text).lower()
    scores = {}
    for cat, keywords in KEYWORD_RULES:
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return "Politics & Government"


def apply_unified_categories(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Add unified_category column based on source type."""
    if source == "1tv":
        col = "category_label" if "category_label" in df.columns else "category_clean"
        if col in df.columns:
            df["unified_category"] = df[col].map(OTV_CATEGORY_MAP).fillna("Society & Culture")
        else:
            df["unified_category"] = df["text"].apply(classify_by_keywords)
    elif source == "tass":
        if "category" in df.columns:
            df["unified_category"] = df["category"].map(TASS_CATEGORY_MAP).fillna(
                df["text"].apply(classify_by_keywords)
            )
        else:
            df["unified_category"] = df["text"].apply(classify_by_keywords)
    elif source == "rt":
        if "category" in df.columns:
            mapped = df["category"].map(RT_CATEGORY_MAP)
            geo_mask = df["category"].isin(RT_GEO_SECTIONS) | mapped.isna()
            df["unified_category"] = mapped
            df.loc[geo_mask, "unified_category"] = (
                df.loc[geo_mask, "text"].apply(classify_by_keywords)
            )
        else:
            df["unified_category"] = df["text"].apply(classify_by_keywords)
    elif source in ("kremlin", "mfa"):
        df["unified_category"] = df["text"].apply(classify_by_keywords)
    return df


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
    df = apply_unified_categories(df, "1tv")
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
    """Year-sharded search index for 1TV."""
    _generic_search_shards(
        df,
        DATA_DIR / "search",
        title_col="title_en",
        title_ru_col="title",
        content_col="content_en",
        date_col="date_extracted",
        url_col="url",
        cat_col="unified_category",
    )


def _generic_search_shards(
    df: pd.DataFrame,
    out_dir: Path,
    title_col: str,
    content_col: str,
    date_col: str = "date",
    url_col: str = "url",
    cat_col: str = None,
    title_ru_col: str = None,
) -> None:
    """Year-sharded search index usable by any source."""
    out_dir.mkdir(parents=True, exist_ok=True)

    years_with_data = []
    total = 0
    for year in sorted(df["year"].dropna().unique()):
        ydf = df[df["year"] == year]
        records = []
        for _, r in ydf.iterrows():
            title = str(r.get(title_col, "")) if pd.notna(r.get(title_col)) else ""
            if not title:
                continue
            content = str(r.get(content_col, "")) if pd.notna(r.get(content_col)) else ""
            wc = len(content.split()) if content else 0
            date_val = r.get(date_col, r.get("date", ""))
            date_str = str(date_val)[:10] if pd.notna(date_val) else ""
            url_val = r.get(url_col, "")
            rec = {
                "t": title[:150],
                "d": date_str,
                "u": str(url_val) if pd.notna(url_val) else "",
                "s": content[:120],
                "wc": wc,
            }
            if title_ru_col:
                ru = str(r.get(title_ru_col, "")) if pd.notna(r.get(title_ru_col)) else ""
                if ru:
                    rec["r"] = ru[:150]
            if cat_col:
                cat = str(r.get(cat_col, "")) if pd.notna(r.get(cat_col)) else ""
                if cat:
                    rec["cat"] = cat
            records.append(rec)
        yr = str(int(year))
        (out_dir / f"{yr}.json").write_text(json.dumps(records, ensure_ascii=False))
        years_with_data.append(yr)
        total += len(records)
    (out_dir / "years.json").write_text(json.dumps(years_with_data))
    print(f"  search shards: {total} items across {len(years_with_data)} years")


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
    # Unified category distribution
    if "unified_category" in df.columns:
        cats = df["unified_category"].value_counts()
        stats["categories"] = [
            {"name": str(c), "count": int(n)} for c, n in cats.items()
        ]
    (DATA_DIR / "summary.json").write_text(json.dumps(stats))
    print(f"  summary.json: {stats}")


# ── Kremlin speeches data generation ───────────────────────────────────────────

def load_kremlin_speeches() -> pd.DataFrame:
    """Load Kremlin presidential speeches CSV."""
    import csv as _csv
    import sys as _sys
    _csv.field_size_limit(_sys.maxsize)

    path = BASE / "kremlin_speeches_all_lemmatized.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, engine="python")
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["text"] = (
        df["title"].fillna("").astype(str)
        + " "
        + df["content"].fillna("").astype(str)
    ).str.lower()
    df = apply_unified_categories(df, "kremlin")
    return df


def kremlin_stats(df: pd.DataFrame) -> None:
    """Generate Kremlin speeches summary, volume, keywords, country data."""
    kr_dir = DATA_DIR / "kremlin"
    kr_dir.mkdir(parents=True, exist_ok=True)

    # Summary
    pres_counts = (
        df["president"].value_counts()
        .reset_index()
        .rename(columns={"index": "president", "president": "name", "count": "count"})
    )
    top_locations = (
        df["location"].dropna()
        .value_counts()
        .head(10)
        .reset_index()
        .rename(columns={"index": "location", "location": "name", "count": "count"})
    )
    # Unified categories
    cats = df["unified_category"].value_counts() if "unified_category" in df.columns else pd.Series(dtype=int)
    stats = {
        "total_speeches": len(df),
        "date_start": str(df["date"].min().date()) if len(df) else "",
        "date_end": str(df["date"].max().date()) if len(df) else "",
        "years_covered": int(df["year"].nunique()),
        "avg_words": round(df["total_words"].mean(), 0) if "total_words" in df.columns else 0,
        "presidents": [
            {"name": str(r.get("name", r.get("president", ""))),
             "count": int(r["count"])}
            for _, r in pres_counts.iterrows()
        ],
        "top_locations": [
            {"name": str(r.get("name", r.get("location", ""))),
             "count": int(r["count"])}
            for _, r in top_locations.iterrows()
        ],
        "categories": [
            {"name": str(c), "count": int(n)} for c, n in cats.items()
        ],
    }
    (kr_dir / "summary.json").write_text(json.dumps(stats))
    print(f"  kremlin/summary.json: {stats['total_speeches']} speeches")

    # Monthly volume
    counts = df.groupby("month").size().reset_index(name="count")
    data = [{"month": r["month"], "count": int(r["count"])} for _, r in counts.iterrows()]
    (kr_dir / "monthly_volume.json").write_text(json.dumps(data))
    print(f"  kremlin/monthly_volume.json: {len(data)} months")

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
    (kr_dir / "keyword_trends.json").write_text(json.dumps(kw_results))
    print(f"  kremlin/keyword_trends.json: {len(kw_results)} keywords")

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
    (kr_dir / "country_mentions.json").write_text(json.dumps(co_results))
    print(f"  kremlin/country_mentions.json: {len(co_results)} countries")

    # Search shards
    _generic_search_shards(
        df, kr_dir / "search",
        title_col="title", content_col="content",
        url_col="url", cat_col="unified_category",
    )


# ── TASS data generation

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
    df = apply_unified_categories(df, "tass")
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
            for c, n in df["unified_category"].value_counts().items()
        ] if "unified_category" in df.columns else [],
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

    # Search shards
    _generic_search_shards(
        df, tass_dir / "search",
        title_col="title", content_col="content",
        url_col="url", cat_col="unified_category",
    )


def cross_source_comparison(
    otv_df: pd.DataFrame,
    tass_df: pd.DataFrame,
    kremlin_df: pd.DataFrame = None,
    mfa_df: pd.DataFrame = None,
    rt_df: pd.DataFrame = None,
) -> None:
    """Generate cross-source keyword comparison data."""
    compare_dir = DATA_DIR / "compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    sources = [("1tv", otv_df), ("tass", tass_df)]
    if kremlin_df is not None and len(kremlin_df) > 0:
        sources.append(("kremlin", kremlin_df))
    if mfa_df is not None and len(mfa_df) > 0:
        sources.append(("mfa", mfa_df))
    if rt_df is not None and len(rt_df) > 0:
        sources.append(("rt", rt_df))

    results = {}
    for kw in TRACKED_KEYWORDS:
        pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
        entry = {}
        for label, df in sources:
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
    print(f"  compare/keyword_comparison.json: {len(results)} keywords, {len(sources)} sources")


# ── MFA Telegram data generation ──────────────────────────────────────────────

def load_mfa() -> pd.DataFrame:
    """Load MFA Telegram messages CSV if available."""
    path = BASE / "mfa_telegram.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["text"] = df["text"].fillna("").astype(str).str.lower()
    df = apply_unified_categories(df, "mfa")
    return df


def mfa_stats(df: pd.DataFrame) -> None:
    """Generate MFA summary, volume, keywords, and country data."""
    mfa_dir = DATA_DIR / "mfa"
    mfa_dir.mkdir(parents=True, exist_ok=True)

    # Unified categories
    cats = df["unified_category"].value_counts() if "unified_category" in df.columns else pd.Series(dtype=int)
    stats = {
        "total_messages": len(df),
        "date_start": str(df["date"].min().date()) if len(df) else "",
        "date_end": str(df["date"].max().date()) if len(df) else "",
        "years_covered": int(df["year"].nunique()),
        "avg_text_len": round(df["text"].str.len().mean(), 0),
        "categories": [
            {"name": str(c), "count": int(n)} for c, n in cats.items()
        ],
    }
    (mfa_dir / "summary.json").write_text(json.dumps(stats))
    print(f"  mfa/summary.json: {stats['total_messages']} messages")

    # Monthly volume
    counts = df.groupby("month").size().reset_index(name="count")
    data = [{"month": r["month"], "count": int(r["count"])} for _, r in counts.iterrows()]
    (mfa_dir / "monthly_volume.json").write_text(json.dumps(data))
    print(f"  mfa/monthly_volume.json: {len(data)} months")

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
    (mfa_dir / "keyword_trends.json").write_text(json.dumps(kw_results))
    print(f"  mfa/keyword_trends.json: {len(kw_results)} keywords")

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
    (mfa_dir / "country_mentions.json").write_text(json.dumps(co_results))
    print(f"  mfa/country_mentions.json: {len(co_results)} countries")

    # Search shards
    _generic_search_shards(
        df, mfa_dir / "search",
        title_col="text", content_col="text",
        cat_col="unified_category",
    )


# ── RT data generation ─────────────────────────────────────────────────────────

def load_rt() -> pd.DataFrame:
    """Load RT articles CSV if available."""
    path = BASE / "rt_articles.csv"
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
    df = apply_unified_categories(df, "rt")
    return df


def rt_stats(df: pd.DataFrame) -> None:
    """Generate RT summary, volume, keywords, and category data."""
    rt_dir = DATA_DIR / "rt"
    rt_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "total_articles": len(df),
        "date_start": str(df["date"].min().date()) if len(df) else "",
        "date_end": str(df["date"].max().date()) if len(df) else "",
        "years_covered": int(df["year"].nunique()),
        "avg_content_len": round(df["content"].astype(str).str.len().mean(), 0),
        "categories": [
            {"name": str(c), "count": int(n)}
            for c, n in df["unified_category"].value_counts().items()
        ] if "unified_category" in df.columns else [],
    }
    (rt_dir / "summary.json").write_text(json.dumps(stats))
    print(f"  rt/summary.json: {stats['total_articles']} articles")

    # Monthly volume
    counts = df.groupby("month").size().reset_index(name="count")
    data = [{"month": r["month"], "count": int(r["count"])} for _, r in counts.iterrows()]
    (rt_dir / "monthly_volume.json").write_text(json.dumps(data))
    print(f"  rt/monthly_volume.json: {len(data)} months")

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
    (rt_dir / "keyword_trends.json").write_text(json.dumps(kw_results))
    print(f"  rt/keyword_trends.json: {len(kw_results)} keywords")

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
    (rt_dir / "country_mentions.json").write_text(json.dumps(co_results))
    print(f"  rt/country_mentions.json: {len(co_results)} countries")

    # Search shards
    _generic_search_shards(
        df, rt_dir / "search",
        title_col="title", content_col="content",
        url_col="url", cat_col="unified_category",
    )


def overview_summary(
    sources: dict,
) -> None:
    """Generate combined overview JSON for all sources."""
    overview_dir = DATA_DIR / "overview"
    overview_dir.mkdir(parents=True, exist_ok=True)

    src_list = []
    for name, df in sources.items():
        if df is None or len(df) == 0:
            continue
        src_list.append({
            "name": name,
            "count": len(df),
            "date_start": str(df["date"].min().date()),
            "date_end": str(df["date"].max().date()),
        })
    total = sum(s["count"] for s in src_list)
    (overview_dir / "summary.json").write_text(json.dumps({
        "total_items": total,
        "sources": src_list,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }))
    print(f"  overview/summary.json: {total} total items across {len(src_list)} sources")

    # Combined monthly volume per source
    combined = {}
    for name, df in sources.items():
        if df is None or len(df) == 0:
            continue
        counts = df.groupby("month").size().reset_index(name="count")
        combined[name] = [
            {"month": r["month"], "count": int(r["count"])}
            for _, r in counts.iterrows()
        ]
    (overview_dir / "volume_by_source.json").write_text(json.dumps(combined))
    print(f"  overview/volume_by_source.json: {len(combined)} sources")


def cross_source_category_comparison(
    sources: list,
) -> None:
    """Generate cross-source unified category comparison data."""
    compare_dir = DATA_DIR / "compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for label, df in sources:
        if df is None or len(df) == 0:
            continue
        if "unified_category" not in df.columns:
            continue
        cats = df["unified_category"].value_counts()
        total = len(df)
        results[label] = [
            {"name": str(c), "count": int(n), "pct": round(n / total * 100, 1)}
            for c, n in cats.items()
        ]
    (compare_dir / "category_comparison.json").write_text(json.dumps(results))
    print(f"  compare/category_comparison.json: {len(results)} sources")


def cross_source_country_comparison(
    sources: list,
) -> None:
    """Generate cross-source country comparison data."""
    compare_dir = DATA_DIR / "compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for country in COUNTRY_DISPLAY:
        terms = [country]
        for alias, canonical in COUNTRY_ALIASES.items():
            if canonical == country:
                terms.append(alias)
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b", re.IGNORECASE
        )
        entry = {}
        for label, df in sources:
            if len(df) == 0:
                continue
            monthly = (
                df.assign(has=df["text"].str.contains(pattern, na=False))
                .groupby("month")["has"]
                .mean()
                .reset_index()
            )
            entry[label] = [
                {"month": r["month"], "pct": round(float(r["has"]) * 100, 2)}
                for _, r in monthly.iterrows()
            ]
        results[country] = entry
    (compare_dir / "country_comparison.json").write_text(json.dumps(results))
    print(f"  compare/country_comparison.json: {len(results)} countries, {len(sources)} sources")


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

    print("\nLoading Kremlin speeches...")
    kremlin_df = load_kremlin_speeches()
    if len(kremlin_df) > 0:
        print(f"Loaded {len(kremlin_df)} Kremlin speeches.\n")
        print("Generating Kremlin JSON files:")
        kremlin_stats(kremlin_df)
    else:
        print("No Kremlin speeches data found, skipping.\n")

    print("\nLoading TASS data...")
    tass_df = load_tass()
    if len(tass_df) > 0:
        print(f"Loaded {len(tass_df)} TASS rows.\n")
        print("Generating TASS JSON files:")
        tass_stats(tass_df)
    else:
        print("No TASS data found, skipping.\n")

    print("\nLoading MFA Telegram data...")
    mfa_df = load_mfa()
    if len(mfa_df) > 0:
        print(f"Loaded {len(mfa_df)} MFA messages.\n")
        print("Generating MFA JSON files:")
        mfa_stats(mfa_df)
    else:
        print("No MFA data found, skipping.\n")

    print("\nLoading RT data...")
    rt_df = load_rt()
    if len(rt_df) > 0:
        print(f"Loaded {len(rt_df)} RT rows.\n")
        print("Generating RT JSON files:")
        rt_stats(rt_df)
    else:
        print("No RT data found, skipping.\n")

    all_sources = [("1tv", df), ("tass", tass_df), ("kremlin", kremlin_df), ("mfa", mfa_df), ("rt", rt_df)]

    print("\nGenerating cross-source comparison:")
    cross_source_comparison(df, tass_df, kremlin_df, mfa_df, rt_df)

    print("\nGenerating cross-source country comparison:")
    cross_source_country_comparison(all_sources)

    print("\nGenerating cross-source category comparison:")
    cross_source_category_comparison(all_sources)

    print("\nGenerating overview:")
    overview_summary({
        "1TV": df,
        "Kremlin": kremlin_df,
        "TASS": tass_df,
        "MFA": mfa_df,
        "RT": rt_df,
    })

    print("\nDone!")


if __name__ == "__main__":
    main()
