#!/usr/bin/env python3
"""
Investigate the China spike in 2021-2022
"""

import pandas as pd
import re

# Load data
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')
df['year_month'] = df['date_parsed'].dt.to_period('M')

# Filter to 2021-2022
df_focus = df[(df['date_parsed'] >= '2021-01-01') & (df['date_parsed'] <= '2022-12-31')].copy()

# Count total words
df_focus['total_words'] = df_focus['content'].str.split().str.len()

# Count China mentions
china_keywords = ['China', 'Chinese', 'Beijing', 'Shanghai', 'PRC']
pattern = '|'.join([re.escape(kw) for kw in china_keywords])
df_focus['china_mentions'] = df_focus['content'].str.count(pattern, flags=re.IGNORECASE)
df_focus['china_words_estimate'] = df_focus['china_mentions'] * 5
df_focus['china_proportion'] = df_focus['china_words_estimate'] / df_focus['total_words'].clip(lower=1)
df_focus['china_proportion_pct'] = df_focus['china_proportion'] * 100

# Find speeches with highest China content
high_china = df_focus[df_focus['china_proportion_pct'] > 0.5].sort_values('china_proportion_pct', ascending=False)

print('\n=== SPEECHES WITH HIGH CHINA CONTENT (2021-2022) ===\n')
print(f'Total speeches 2021-2022: {len(df_focus)}')
print(f'Speeches with >0.5% China content: {len(high_china)}\n')

for idx, row in high_china.head(20).iterrows():
    print(f"\nDate: {row['date']}")
    print(f"Title: {row['title'][:100]}...")
    print(f"China proportion: {row['china_proportion_pct']:.2f}%")
    print(f"China mentions: {row['china_mentions']}")
    print(f"Total words: {row['total_words']}")
    print(f"Location: {row['location']}")
    print(f"URL: {row['url']}")

# Monthly aggregation to see the pattern
monthly = df_focus.groupby('year_month').agg({
    'china_mentions': 'sum',
    'china_proportion_pct': 'mean',
    'title': 'count'
}).reset_index()
monthly.columns = ['year_month', 'total_mentions', 'avg_pct', 'n_speeches']

print('\n\n=== MONTHLY BREAKDOWN (2021-2022) ===\n')
print(monthly.to_string(index=False))

# Find the specific month with the spike
spike_month = monthly[monthly['avg_pct'] == monthly['avg_pct'].max()]['year_month'].values[0]
print(f'\n\n=== SPIKE MONTH: {spike_month} ===\n')

spike_speeches = df_focus[df_focus['year_month'] == spike_month]
print(f'Number of speeches: {len(spike_speeches)}')
print(f'Average China %: {spike_speeches["china_proportion_pct"].mean():.2f}%\n')

for idx, row in spike_speeches.sort_values('china_proportion_pct', ascending=False).iterrows():
    print(f"\n{row['date']}: {row['title'][:80]}...")
    print(f"  China: {row['china_proportion_pct']:.2f}% ({row['china_mentions']} mentions)")
