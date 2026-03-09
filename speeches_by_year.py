#!/usr/bin/env python3
"""
Tabulate Russian presidential speeches by year
"""

import pandas as pd

# Load data
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')
df['year'] = df['date_parsed'].dt.year
df['total_words'] = df['content'].str.split().str.len()

print("\n=== RUSSIAN PRESIDENTIAL SPEECHES BY YEAR (ALL SPEECHES) ===\n")

# Overall by year
yearly_all = df.groupby('year').agg({
    'title': 'count',
    'total_words': ['sum', 'mean', 'median']
}).reset_index()

yearly_all.columns = ['Year', 'Number of Speeches', 'Total Words', 'Avg Words per Speech', 'Median Words per Speech']
yearly_all = yearly_all[yearly_all['Year'].notna()].copy()
yearly_all['Year'] = yearly_all['Year'].astype(int)

print(yearly_all.to_string(index=False))
print(f"\nTotal speeches (all time): {len(df)}")
print(f"Total words (all time): {df['total_words'].sum():,}")

# Focus on 2021-present
print("\n\n=== SPEECHES BY YEAR (2021-PRESENT) ===\n")

df_recent = df[df['date_parsed'] >= '2021-01-01'].copy()

yearly_recent = df_recent.groupby('year').agg({
    'title': 'count',
    'total_words': ['sum', 'mean', 'median']
}).reset_index()

yearly_recent.columns = ['Year', 'Number of Speeches', 'Total Words', 'Avg Words per Speech', 'Median Words per Speech']
yearly_recent['Year'] = yearly_recent['Year'].astype(int)

print(yearly_recent.to_string(index=False))

# Break down by short vs long speeches
print("\n\n=== SPEECH LENGTH DISTRIBUTION (2021-PRESENT) ===\n")

length_categories = pd.cut(df_recent['total_words'], 
                           bins=[0, 500, 1000, 2000, 5000, float('inf')],
                           labels=['<500', '500-1000', '1000-2000', '2000-5000', '5000+'])

df_recent['length_category'] = length_categories

length_dist = df_recent.groupby(['year', 'length_category']).size().unstack(fill_value=0)
length_dist.index = length_dist.index.astype(int)

print(length_dist)
print(f"\nTotal speeches 2021-present: {len(df_recent)}")
print(f"Speeches >=500 words: {(df_recent['total_words'] >= 500).sum()}")
print(f"Speeches <500 words: {(df_recent['total_words'] < 500).sum()}")

# President breakdown (if available)
print("\n\n=== SPEECHES BY PRESIDENT ===\n")

if 'president' in df.columns:
    president_stats = df.groupby('president').agg({
        'title': 'count',
        'total_words': 'sum',
        'year': ['min', 'max']
    }).reset_index()
    
    president_stats.columns = ['President', 'Number of Speeches', 'Total Words', 'First Year', 'Last Year']
    print(president_stats.to_string(index=False))

# Monthly breakdown for 2021-present
print("\n\n=== MONTHLY SPEECH VOLUME (2021-PRESENT) ===\n")

df_recent['year_month'] = df_recent['date_parsed'].dt.to_period('M')
monthly = df_recent.groupby('year_month').agg({
    'title': 'count',
    'total_words': 'sum'
}).reset_index()

monthly.columns = ['Month', 'Speeches', 'Total Words']
monthly['Avg Words'] = (monthly['Total Words'] / monthly['Speeches']).round(0).astype(int)

print(f"Average speeches per month: {monthly['Speeches'].mean():.1f}")
print(f"Peak month: {monthly.loc[monthly['Speeches'].idxmax(), 'Month']} ({monthly['Speeches'].max()} speeches)")
print(f"Lowest month: {monthly.loc[monthly['Speeches'].idxmin(), 'Month']} ({monthly['Speeches'].min()} speeches)")

# Show months with most and least speeches
print("\n\nMonths with most speeches:")
print(monthly.nlargest(5, 'Speeches')[['Month', 'Speeches', 'Total Words']].to_string(index=False))

print("\n\nMonths with fewest speeches:")
print(monthly.nsmallest(5, 'Speeches')[['Month', 'Speeches', 'Total Words']].to_string(index=False))

# Save full results
yearly_all.to_csv('speeches_by_year_all.csv', index=False)
yearly_recent.to_csv('speeches_by_year_2021_present.csv', index=False)
monthly.to_csv('speeches_by_month_2021_present.csv', index=False)

print("\n\n✓ Tables saved:")
print("  - speeches_by_year_all.csv")
print("  - speeches_by_year_2021_present.csv")
print("  - speeches_by_month_2021_present.csv")
