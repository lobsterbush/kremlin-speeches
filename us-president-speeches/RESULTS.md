# White House Speeches Analysis - Results Summary

**Data Collection Date**: January 12, 2026  
**Analysis Period**: January 2025 - January 2026 (Trump Administration 47)

## Dataset Overview

- **Total Speeches Scraped**: 265
- **Date Range**: January 20, 2025 - January 8, 2026
- **Total Words**: 128,165 (original), 67,589 (after lemmatization)
- **Speeches ≥500 words**: 64 (used for temporal analysis)
- **Word Reduction from Preprocessing**: 47.3%

## Geographic Distribution

### Location
- **US/Domestic**: 248 speeches (93.6%)
- **Europe**: 5 speeches
- **Middle East**: 5 speeches
- **Asia**: 4 speeches
- **North America** (non-US): 2 speeches
- **South America**: 1 speech

### Participants
Most speeches involve international organizations and North American topics (80 speeches), reflecting diplomatic communications.

## Adversary Nation Mentions

### Overall Statistics (All 265 speeches)

| Country | Total Mentions | Speeches Mentioning | % of Speeches | Avg. Word Proportion |
|---------|---------------|---------------------|---------------|---------------------|
| **Russia** | 30 | 12 | 4.5% | 0.178% |
| **China** | 40 | 10 | 3.8% | 0.104% |
| **Iran** | 10 | 6 | 2.3% | 0.130% |
| **North Korea** | 11 | 3 | 1.1% | 0.030% |

### Analysis for Longer Speeches (≥500 words, n=64)

| Country | Avg. Proportion |
|---------|----------------|
| **Russia** | 0.07% |
| **China** | 0.12% |
| **Iran** | 0.00% |
| **North Korea** | 0.08% |

## Key Findings

1. **Very Low Adversary Mentions**: The current administration's first year shows remarkably low mentions of traditional adversary nations, with all four countries mentioned in less than 5% of speeches.

2. **China Most Prominent**: Despite fewer speeches mentioning China (10 vs 12 for Russia), China has slightly more total mentions (40 vs 30), suggesting more repeated references when discussed.

3. **Domestic Focus**: 93.6% of speeches are categorized as US/Domestic, indicating a strong focus on internal issues during the first year of the administration.

4. **Minimal Russia-Ukraine Discussion**: Only 12 speeches (4.5%) mention Russia, suggesting reduced focus on the Ukraine conflict compared to the previous administration.

5. **Limited Middle East Focus**: Iran appears in only 2.3% of speeches, with minimal discussion of Middle East issues overall.

## Comparison to Expected Patterns

This data represents the **beginning of the Trump 47 administration** (January 2025 - January 2026). For a meaningful comparison with the Kremlin speeches analysis:

- **Kremlin analysis**: Covers 2000-2025, showing Russia's sustained focus on the US and growing Asia focus
- **White House data**: Only covers first year of one administration
- **Temporal Context**: Captures a specific political moment rather than long-term trends

## Visualizations Generated

1. **whitehouse_russia_comparison.png/pdf**: 4-panel comparison of Russia, China, North Korea, and Iran mentions
2. **whitehouse_adversaries_timeline.png/pdf**: Temporal trends of all adversary nations
3. **whitehouse_russia_timeline.png/pdf**: Russia mentions with key event markers
4. **whitehouse_regional_focus.png/pdf**: Comparison of Europe/NATO, Middle East, and China focus
5. **whitehouse_full_temporal_analysis.png/pdf**: Combined visualization of all three plots

## Data Limitations

1. **Short Time Period**: Only 1 year of data vs. 25 years for Kremlin analysis
2. **Administration Change**: Data captures transition period and early administration
3. **Communication Style**: Reflects current administration's communication patterns
4. **Recent Events**: May not capture major geopolitical shifts yet

## Methodology

- Followed identical methodology to kremlin-speeches project
- Keyword-based mention counting with 5-word context estimation
- Monthly aggregation for temporal trends
- Geographic classification by location and participants
- Tufte-style visualizations for professional presentation

## Next Steps for Longitudinal Analysis

To make this directly comparable to the Kremlin analysis, consider:

1. Scraping historical speeches from previous administrations (Biden, Trump 45, Obama)
2. Extending data collection through 2026-2028
3. Comparing across presidential administrations
4. Analyzing response patterns to specific geopolitical events

---

*Analysis completed: January 12, 2026*  
*Scripts available in: `/Users/f00421k/Documents/GitHub/kremlin-speeches/us-president-speeches/`*
