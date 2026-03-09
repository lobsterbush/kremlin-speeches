#!/bin/bash
# Master script to run the complete White House speeches analysis pipeline

set -e  # Exit on error

echo "========================================="
echo "White House Speeches Analysis Pipeline"
echo "========================================="
echo ""

# Step 1: Scrape
echo "[1/5] Scraping White House speeches..."
python scrape_whitehouse.py
echo "✓ Scraping complete"
echo ""

# Step 2: Preprocess
echo "[2/5] Preprocessing speeches..."
python preprocess_whitehouse_speeches.py
echo "✓ Preprocessing complete"
echo ""

# Step 3: Classify
echo "[3/5] Classifying speeches geographically..."
python classify_whitehouse_geography.py
echo "✓ Classification complete"
echo ""

# Step 4: Python Analysis
echo "[4/5] Running Python analysis (Russia mentions)..."
python analyze_russia_mentions.py
echo "✓ Python analysis complete"
echo ""

# Step 5: R Analysis
echo "[5/5] Running R temporal analysis..."
Rscript full_temporal_analysis_whitehouse.R
echo "✓ R analysis complete"
echo ""

echo "========================================="
echo "Pipeline Complete!"
echo "========================================="
echo ""
echo "Generated files:"
echo "  Data:"
echo "    - whitehouse_speeches_raw.csv"
echo "    - whitehouse_speeches_lemmatized.csv"
echo "    - whitehouse_speeches_classified.csv"
echo ""
echo "  Visualizations:"
echo "    - whitehouse_russia_comparison.png/pdf"
echo "    - whitehouse_adversaries_timeline.png/pdf"
echo "    - whitehouse_russia_timeline.png/pdf"
echo "    - whitehouse_regional_focus.png/pdf"
echo "    - whitehouse_full_temporal_analysis.png/pdf"
echo ""
