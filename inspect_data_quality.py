#!/usr/bin/env python3
"""
Inspect data quality and potential keyword matching issues
"""

import pandas as pd
import re
from collections import Counter

# Load data
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')
df_recent = df[df['date_parsed'] >= '2021-01-01'].copy()

print(f"\n=== DATA QUALITY INSPECTION ===\n")
print(f"Total speeches (2021-present): {len(df_recent)}")
print(f"Date range: {df_recent['date_parsed'].min()} to {df_recent['date_parsed'].max()}\n")

# Check for potential keyword overlap issues
print("=== POTENTIAL KEYWORD OVERLAP ISSUES ===\n")

# Issue 1: "America" might catch "American" which is also in country names
test_cases = [
    ("america", ["Latin America", "North America", "South America", "American"]),
    ("russia", ["Russia", "Russian", "Russians"]),
    ("europe", ["Europe", "European"]),
    ("korea", ["Korea", "Korean", "North Korea", "South Korea"]),
    ("china", ["China", "Chinese"])
]

print("Testing keyword boundary matching:\n")
for keyword, test_phrases in test_cases:
    print(f"{keyword.upper()}:")
    for phrase in test_phrases:
        # Test if simple contains would match
        simple_match = keyword.lower() in phrase.lower()
        # Test word boundary match
        boundary_pattern = r'\b' + re.escape(keyword) + r'\b'
        boundary_match = bool(re.search(boundary_pattern, phrase, re.IGNORECASE))
        print(f"  '{phrase}': simple={simple_match}, boundary={boundary_match}")
    print()

# Issue 2: Check if "Korea" is catching both North and South Korea
print("\n=== KOREA DISAMBIGUATION CHECK ===\n")
korea_keywords = ['Korea', 'Korean', 'Seoul']
north_korea_keywords = ['North Korea', 'DPRK', 'Pyongyang']

for idx, row in df_recent.head(20).iterrows():
    korea_count = sum([row['content'].lower().count(kw.lower()) for kw in korea_keywords])
    nk_count = sum([row['content'].lower().count(kw.lower()) for kw in north_korea_keywords])
    
    if korea_count > 0 or nk_count > 0:
        print(f"{row['date']}: Korea={korea_count}, North Korea={nk_count}")
        print(f"  Title: {row['title'][:80]}...")

# Issue 3: Geographic classification vs keyword counting mismatch
print("\n\n=== GEOGRAPHIC CLASSIFICATION VS KEYWORD COUNTING ===\n")
print("Speeches classified as Asian location but with minimal Asia keywords:\n")

asia_locations = df_recent[df_recent['location_region'].str.contains('Asia', na=False)]
print(f"Speeches with Asian location_region: {len(asia_locations)}")

# Count Asia keywords in these
asia_keywords = ['China', 'Japan', 'India', 'Korea', 'Vietnam', 'Thailand', 'Singapore', 
                 'Malaysia', 'Indonesia', 'Philippines', 'Pakistan', 'Bangladesh', 'Myanmar',
                 'Cambodia', 'Laos', 'Mongolia', 'Afghanistan', 'Kazakhstan', 'Uzbekistan',
                 'Kyrgyzstan', 'Tajikistan', 'Turkmenistan', 'Asia', 'Asian']

for idx, row in asia_locations.head(10).iterrows():
    pattern = '|'.join([re.escape(kw) for kw in asia_keywords])
    mentions = len(re.findall(pattern, row['content'], flags=re.IGNORECASE))
    print(f"\n{row['date']} - {row['location']}")
    print(f"  Title: {row['title'][:70]}...")
    print(f"  Asia keyword mentions: {mentions}")

# Issue 4: Check for speeches with unusually high proportions
print("\n\n=== UNUSUALLY HIGH COUNTRY PROPORTIONS ===\n")
print("These might indicate data quality issues or very short speeches:\n")

df_recent['total_words'] = df_recent['content'].str.split().str.len()

# Check China mentions
china_keywords = ['China', 'Chinese', 'Beijing', 'Shanghai', 'PRC']
pattern = '|'.join([re.escape(kw) for kw in china_keywords])
df_recent['china_mentions'] = df_recent['content'].str.count(pattern, flags=re.IGNORECASE)
df_recent['china_proportion'] = (df_recent['china_mentions'] * 5) / df_recent['total_words'].clip(lower=1) * 100

high_china = df_recent[df_recent['china_proportion'] > 5].sort_values('china_proportion', ascending=False)
print(f"Speeches with >5% China content: {len(high_china)}")
for idx, row in high_china.head(5).iterrows():
    print(f"\n{row['date']}: {row['title'][:70]}...")
    print(f"  China: {row['china_proportion']:.2f}% ({row['china_mentions']} mentions in {row['total_words']} words)")
    print(f"  URL: {row['url']}")

# Issue 5: Check for very short speeches
print("\n\n=== VERY SHORT SPEECHES ===\n")
print("Short speeches can have inflated proportions:\n")

short_speeches = df_recent[df_recent['total_words'] < 500].sort_values('total_words')
print(f"Speeches with <500 words: {len(short_speeches)}")
for idx, row in short_speeches.head(10).iterrows():
    print(f"\n{row['date']}: {row['total_words']} words")
    print(f"  Title: {row['title'][:70]}...")

# Issue 6: Verify Russia keyword counting
print("\n\n=== RUSSIA KEYWORD INTENSITY ===\n")
print("Russia references should be high but check for outliers:\n")

russia_keywords = ['Russia', 'Russian', 'Moscow', 'Russians', 'Kremlin']
pattern = '|'.join([re.escape(kw) for kw in russia_keywords])
df_recent['russia_mentions'] = df_recent['content'].str.count(pattern, flags=re.IGNORECASE)
df_recent['russia_proportion'] = (df_recent['russia_mentions'] * 5) / df_recent['total_words'].clip(lower=1) * 100

print(f"Average Russia proportion: {df_recent['russia_proportion'].mean():.2f}%")
print(f"Median Russia proportion: {df_recent['russia_proportion'].median():.2f}%")
print(f"Max Russia proportion: {df_recent['russia_proportion'].max():.2f}%")

unusual_russia = df_recent[df_recent['russia_proportion'] > 20].sort_values('russia_proportion', ascending=False)
print(f"\nSpeeches with >20% Russia content: {len(unusual_russia)}")
for idx, row in unusual_russia.head(5).iterrows():
    print(f"\n{row['date']}: {row['russia_proportion']:.2f}%")
    print(f"  Title: {row['title'][:70]}...")
    print(f"  {row['russia_mentions']} mentions in {row['total_words']} words")

# Issue 7: Check Europe keywords - might be too broad
print("\n\n=== EUROPE KEYWORD BREADTH CHECK ===\n")
europe_keywords = ['Europe', 'European', 'EU', 'Brussels', 'Germany', 'German', 'France', 
                   'French', 'Britain', 'British', 'UK', 'Italy', 'Italian', 'Spain', 
                   'Spanish', 'Poland', 'Polish', 'NATO']

# Sample speech analysis
sample = df_recent.sample(5, random_state=42)
for idx, row in sample.iterrows():
    print(f"\n{row['date']}:")
    europe_matches = {}
    for kw in europe_keywords:
        count = row['content'].lower().count(kw.lower())
        if count > 0:
            europe_matches[kw] = count
    if europe_matches:
        print(f"  Europe keywords: {europe_matches}")
    else:
        print(f"  No Europe keywords")

print("\n\n=== SUMMARY OF POTENTIAL ISSUES ===")
print("\n1. Word boundary matching: Check if implemented correctly")
print("2. Korea ambiguity: 'Korea' catches both North and South")
print("3. Short speeches: Can inflate proportions significantly")
print("4. Europe keywords: Very broad (includes NATO, individual countries)")
print("5. Russia self-references: Naturally high but should be consistent")
print("6. Geographic classification vs content: May not always align")
