#!/usr/bin/env python3
"""
Tabulate top 10 countries mentioned in Russian presidential speeches (2021-present, >=500 words)
"""

import pandas as pd
import re

# Load data
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')

# Filter to 2021-present
df_recent = df[df['date_parsed'] >= '2021-01-01'].copy()

# Count total words and filter out short speeches
df_recent['total_words'] = df_recent['content'].str.split().str.len()
df_recent = df_recent[df_recent['total_words'] >= 500].copy()

print(f"\n=== TOP 10 COUNTRIES IN RUSSIAN PRESIDENTIAL SPEECHES ===")
print(f"Period: 2021-present")
print(f"Speeches analyzed: {len(df_recent)} (filtered to >=500 words)\n")

# Define all countries with their keywords
countries = {
    'Russia': ['Russia', 'Russian', 'Moscow', 'Russians', 'Kremlin'],
    'Ukraine': ['Ukraine', 'Ukrainian', 'Kyiv', 'Kiev'],
    'China': ['China', 'Chinese', 'Beijing', 'Shanghai', 'PRC'],
    'United States': ['United States', 'America', 'American', 'Washington', 'U.S.', 'USA'],
    'Germany': ['Germany', 'German', 'Berlin'],
    'France': ['France', 'French', 'Paris'],
    'United Kingdom': ['Britain', 'British', 'UK', 'United Kingdom', 'London'],
    'Japan': ['Japan', 'Japanese', 'Tokyo'],
    'India': ['India', 'Indian', 'Delhi', 'New Delhi'],
    'Kazakhstan': ['Kazakhstan', 'Kazakh', 'Astana', 'Nur-Sultan'],
    'South Korea': ['South Korea', 'Seoul', 'ROK', 'Republic of Korea'],
    'North Korea': ['North Korea', 'DPRK', 'Pyongyang'],
    'Turkey': ['Turkey', 'Turkish', 'Ankara'],
    'Iran': ['Iran', 'Iranian', 'Tehran'],
    'Poland': ['Poland', 'Polish', 'Warsaw'],
    'Italy': ['Italy', 'Italian', 'Rome'],
    'Spain': ['Spain', 'Spanish', 'Madrid'],
    'Belarus': ['Belarus', 'Belarusian', 'Minsk'],
    'Kyrgyzstan': ['Kyrgyzstan', 'Kyrgyz', 'Bishkek'],
    'Mongolia': ['Mongolia', 'Mongolian', 'Ulaanbaatar'],
    'Vietnam': ['Vietnam', 'Vietnamese', 'Hanoi'],
    'Afghanistan': ['Afghanistan', 'Afghan', 'Kabul'],
    'Uzbekistan': ['Uzbekistan', 'Uzbek', 'Tashkent'],
    'Tajikistan': ['Tajikistan', 'Tajik', 'Dushanbe'],
    'Turkmenistan': ['Turkmenistan', 'Turkmen', 'Ashgabat'],
    'Armenia': ['Armenia', 'Armenian', 'Yerevan'],
    'Azerbaijan': ['Azerbaijan', 'Azerbaijani', 'Baku'],
    'Georgia': ['Georgia', 'Georgian', 'Tbilisi'],
    'Israel': ['Israel', 'Israeli', 'Jerusalem', 'Tel Aviv'],
    'Saudi Arabia': ['Saudi', 'Arabia', 'Riyadh'],
    'UAE': ['Emirates', 'UAE', 'Dubai', 'Abu Dhabi'],
    'Egypt': ['Egypt', 'Egyptian', 'Cairo'],
    'Brazil': ['Brazil', 'Brazilian', 'Brasilia'],
    'South Africa': ['South Africa', 'South African', 'Pretoria'],
    'Canada': ['Canada', 'Canadian', 'Ottawa'],
    'Mexico': ['Mexico', 'Mexican'],
    'Indonesia': ['Indonesia', 'Indonesian', 'Jakarta'],
    'Thailand': ['Thailand', 'Thai', 'Bangkok'],
    'Pakistan': ['Pakistan', 'Pakistani', 'Islamabad'],
    'Serbia': ['Serbia', 'Serbian', 'Belgrade'],
    'Hungary': ['Hungary', 'Hungarian', 'Budapest']
}

# Function to count keyword mentions
def count_keywords(text, keywords):
    if pd.isna(text):
        return 0
    pattern = '|'.join([re.escape(kw) for kw in keywords])
    return len(re.findall(r'\b(' + pattern + r')\b', text, flags=re.IGNORECASE))

# Calculate statistics for each country
results = []
for country, keywords in countries.items():
    df_recent[f'{country}_mentions'] = df_recent['content'].apply(lambda x: count_keywords(x, keywords))
    
    total_mentions = df_recent[f'{country}_mentions'].sum()
    speeches_with_mentions = (df_recent[f'{country}_mentions'] > 0).sum()
    pct_speeches = speeches_with_mentions / len(df_recent) * 100
    
    # Calculate average word proportion
    df_recent[f'{country}_words_est'] = df_recent[f'{country}_mentions'] * 5
    df_recent[f'{country}_proportion'] = df_recent[f'{country}_words_est'] / df_recent['total_words'].clip(lower=1) * 100
    avg_proportion = df_recent[f'{country}_proportion'].mean()
    
    results.append({
        'Country': country,
        'Total Mentions': total_mentions,
        'Speeches Mentioned': speeches_with_mentions,
        '% of Speeches': pct_speeches,
        'Avg Word %': avg_proportion
    })

# Sort by total mentions
results_df = pd.DataFrame(results).sort_values('Total Mentions', ascending=False)

# Display top 10
print("Rank | Country           | Total Mentions | In # Speeches | % of Speeches | Avg Word %")
print("-" * 95)

for i, row in results_df.head(10).iterrows():
    print(f"{results_df.index.get_loc(i)+1:4} | {row['Country']:17} | {row['Total Mentions']:14,} | {row['Speeches Mentioned']:13} | {row['% of Speeches']:13.1f}% | {row['Avg Word %']:10.3f}%")

print("\n\n=== FULL TOP 20 ===\n")
print(results_df.head(20).to_string(index=False))

# Save to CSV
results_df.to_csv('top_countries_2021_present.csv', index=False)
print("\n\n✓ Full results saved to: top_countries_2021_present.csv")
