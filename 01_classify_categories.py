"""Classify 142K unlabeled 1TV news segments into topic categories.

Uses 2,500 human-labeled segments as training data with TF-IDF features
and multinomial logistic regression. Small categories are merged into
semantically related larger ones before training.

Outputs:
  - 1tv_news_classified.csv: full dataset with predicted categories
  - docs/data/classification_report.json: model performance metrics
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score

BASE = Path(__file__).parent

# ── Category merging map ──
# Merge tiny / meta-categories into semantically related larger ones
MERGE_MAP = {
    "safety": "incidents",     # 4 items → security/safety incidents
    "army": "politika",        # 26 items → military = political
    "religion": "cultura",     # 27 items → religious = cultural
    "odnako": "politika",      # 199 items → political commentary show
    "time": "politika",        # 17 items → news program roundups
}

# Human-readable labels for dashboard
CATEGORY_LABELS = {
    "politika": "Politics",
    "ekonomika": "Economy",
    "cultura": "Culture",
    "sport": "Sport",
    "health": "Health",
    "moskva": "Moscow",
    "pogoda": "Weather",
    "mir": "World",
    "obschestvo": "Society",
    "incidents": "Incidents",
}


# Regex to strip section header boilerplate from labeled articles
# e.g. "News of the Politics section for December 2, 2000"
import re
SECTION_HEADER_RE = re.compile(
    r"^News of the.*?(?:section|column|rubric).*?for\b.*?\d{4}",
    re.IGNORECASE,
)


def load_data() -> pd.DataFrame:
    """Load translated CSV."""
    path = BASE / "1tv_news_2000_2026_translated.csv"
    df = pd.read_csv(path, low_memory=False)

    # Strip section headers from titles so classifier learns from content
    title_clean = df["title_en"].fillna("").astype(str).apply(
        lambda t: SECTION_HEADER_RE.sub("", t).strip()
    )
    # Use cleaned title + raw content as features
    df["text_en"] = (
        title_clean + " " + df["content_en"].fillna("").astype(str)
    )
    return df


def merge_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Apply category merging map."""
    df["category_clean"] = df["category"].map(
        lambda x: MERGE_MAP.get(x, x) if pd.notna(x) else x
    )
    return df


def train_and_predict(df: pd.DataFrame) -> pd.DataFrame:
    """Train TF-IDF + LogReg classifier, cross-validate, predict all."""
    labeled = df[df["category_clean"].notna()].copy()
    unlabeled = df[df["category_clean"].isna()].copy()

    print(f"Labeled: {len(labeled):,}")
    print(f"Unlabeled: {len(unlabeled):,}")
    print(f"\nCategory distribution (after merging):")
    print(labeled["category_clean"].value_counts().to_string())

    # ── TF-IDF features ──
    print("\nFitting TF-IDF vectorizer...")
    tfidf = TfidfVectorizer(
        max_features=15_000,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.95,
        sublinear_tf=True,
    )
    X_all = tfidf.fit_transform(df["text_en"])
    X_labeled = X_all[labeled.index]
    y_labeled = labeled["category_clean"].values

    # ── Cross-validation ──
    print("\nRunning 5-fold stratified cross-validation...")
    clf = LogisticRegression(
        C=5.0,
        max_iter=1000,
        solver="lbfgs",
        n_jobs=-1,
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_cv = cross_val_predict(clf, X_labeled, y_labeled, cv=cv)

    acc = accuracy_score(y_labeled, y_pred_cv)
    print(f"\nCross-validation accuracy: {acc:.3f}")
    report = classification_report(
        y_labeled, y_pred_cv, output_dict=True, zero_division=0
    )
    print(classification_report(y_labeled, y_pred_cv, zero_division=0))

    # ── Train on all labeled data and predict ──
    print("Training final model on all labeled data...")
    clf.fit(X_labeled, y_labeled)

    # Predict unlabeled
    X_unlabeled = X_all[unlabeled.index]
    y_pred = clf.predict(X_unlabeled)
    y_proba = clf.predict_proba(X_unlabeled)
    confidence = y_proba.max(axis=1)

    # Assign predictions
    df.loc[unlabeled.index, "category_clean"] = y_pred
    df.loc[unlabeled.index, "pred_confidence"] = confidence

    # Labeled items get confidence = 1.0 (ground truth)
    df.loc[labeled.index, "pred_confidence"] = 1.0

    # Add human-readable label
    df["category_label"] = df["category_clean"].map(CATEGORY_LABELS)

    # ── Summary stats ──
    print(f"\n=== PREDICTION SUMMARY ===")
    print(f"Mean confidence (unlabeled): {confidence.mean():.3f}")
    print(f"Median confidence: {np.median(confidence):.3f}")
    print(f"Low confidence (<0.5): {(confidence < 0.5).sum():,} ({100*(confidence<0.5).mean():.1f}%)")
    print(f"\nPredicted category distribution (all {len(df):,} items):")
    print(df["category_clean"].value_counts().to_string())

    # ── Save classification report ──
    report_data = {
        "cv_accuracy": round(acc, 4),
        "n_labeled": len(labeled),
        "n_unlabeled": len(unlabeled),
        "n_categories": len(df["category_clean"].unique()),
        "mean_confidence": round(float(confidence.mean()), 4),
        "per_class": {
            k: {
                "precision": round(v["precision"], 3),
                "recall": round(v["recall"], 3),
                "f1": round(v["f1-score"], 3),
                "support": int(v["support"]),
            }
            for k, v in report.items()
            if k not in ("accuracy", "macro avg", "weighted avg")
        },
        "category_labels": CATEGORY_LABELS,
    }
    out_path = BASE / "docs" / "data" / "classification_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report_data, indent=2))
    print(f"\nSaved classification report to {out_path}")

    return df


def main():
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df):,} rows.\n")

    df = merge_categories(df)
    df = train_and_predict(df)

    # ── Save augmented CSV ──
    out_cols = [
        "url", "title", "date_extracted", "content", "category",
        "title_en", "content_en",
        "category_clean", "category_label", "pred_confidence",
    ]
    out_path = BASE / "1tv_news_classified.csv"
    df[out_cols].to_csv(out_path, index=False)
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\nSaved {out_path.name} ({size_mb:.0f} MB)")


if __name__ == "__main__":
    main()
