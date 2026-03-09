#!/usr/bin/env python3
"""
Analyze top Asian countries mentioned in Russian presidential speeches over time
"""

import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')
df['year'] = df['date_parsed'].dt.year

# Count total words
df['total_words'] = df['content'].str.split().str.len()

# Define Asian countries with their keywords
asian_countries = {
    'China': ['China', 'Chinese', 'Beijing', 'Shanghai', 'PRC'],
    'Japan': ['Japan', 'Japanese', 'Tokyo'],
    'India': ['India', 'Indian', 'Delhi', 'New Delhi'],
    'Korea': ['Korea', 'Korean', 'Seoul'],
    'Vietnam': ['Vietnam', 'Vietnamese', 'Hanoi'],
    'Kazakhstan': ['Kazakhstan', 'Kazakh', 'Astana', 'Nur-Sultan'],
    'Uzbekistan': ['Uzbekistan', 'Uzbek', 'Tashkent'],
    'Thailand': ['Thailand', 'Thai', 'Bangkok'],
    'Indonesia': ['Indonesia', 'Indonesian', 'Jakarta'],
    'Singapore': ['Singapore', 'Singaporean'],
    'Pakistan': ['Pakistan', 'Pakistani', 'Islamabad'],
    'Afghanistan': ['Afghanistan', 'Afghan', 'Kabul'],
    'Iran': ['Iran', 'Iranian', 'Tehran'],
    'Turkey': ['Turkey', 'Turkish', 'Ankara'],
    'Mongolia': ['Mongolia', 'Mongolian', 'Ulaanbaatar'],
    'Kyrgyzstan': ['Kyrgyzstan', 'Kyrgyz', 'Bishkek'],
    'Tajikistan': ['Tajikistan', 'Tajik', 'Dushanbe'],
    'Turkmenistan': ['Turkmenistan', 'Turkmen', 'Ashgabat'],
    'Philippines': ['Philippines', 'Philippine', 'Filipino', 'Manila'],
    'Malaysia': ['Malaysia', 'Malaysian', 'Kuala Lumpur'],
    'Bangladesh': ['Bangladesh', 'Bengali', 'Dhaka'],
    'Myanmar': ['Myanmar', 'Burma', 'Burmese'],
    'Cambodia': ['Cambodia', 'Cambodian', 'Phnom Penh'],
    'Laos': ['Laos', 'Lao', 'Vientiane'],
    'Israel': ['Israel', 'Israeli', 'Jerusalem', 'Tel Aviv'],
    'Saudi Arabia': ['Saudi', 'Arabia', 'Riyadh']
}

# Calculate mentions for each country
for country, keywords in asian_countries.items():
    pattern = '|'.join([re.escape(kw) for kw in keywords])
    df[f'{country}_mentions'] = df['content'].str.count(pattern, flags=re.IGNORECASE)
    df[f'{country}_words_estimate'] = df[f'{country}_mentions'] * 5
    df[f'{country}_proportion'] = df[f'{country}_words_estimate'] / df['total_words'].clip(lower=1)

# Overall totals
print('\n=== TOP ASIAN COUNTRIES (ALL TIME: 2000-2025) ===\n')
print('Rank | Country          | Total Mentions | Speeches | % of Speeches | Avg Word %')
print('-' * 85)

country_stats = []
for country in asian_countries.keys():
    total_mentions = df[f'{country}_mentions'].sum()
    speeches_with = (df[f'{country}_mentions'] > 0).sum()
    pct_speeches = speeches_with / len(df) * 100
    avg_proportion = df[f'{country}_proportion'].mean() * 100
    
    country_stats.append({
        'country': country,
        'mentions': total_mentions,
        'speeches': speeches_with,
        'pct_speeches': pct_speeches,
        'avg_proportion': avg_proportion
    })

country_stats = sorted(country_stats, key=lambda x: x['mentions'], reverse=True)

for i, stat in enumerate(country_stats[:15], 1):
    print(f"{i:2}   | {stat['country']:16} | {stat['mentions']:14,} | {stat['speeches']:8} | {stat['pct_speeches']:13.1f}% | {stat['avg_proportion']:10.3f}%")

# Top 10 for visualization
top10_countries = [s['country'] for s in country_stats[:10]]

# Yearly aggregation for top 10
print('\n\n=== YEARLY MENTIONS (TOP 10 COUNTRIES) ===\n')

yearly_data = []
for year in sorted(df['year'].dropna().unique()):
    year_df = df[df['year'] == year]
    year_dict = {'year': int(year), 'n_speeches': len(year_df)}
    
    for country in top10_countries:
        year_dict[country] = year_df[f'{country}_mentions'].sum()
    
    yearly_data.append(year_dict)

yearly_df = pd.DataFrame(yearly_data)

# Print table
print(yearly_df.to_string(index=False))

# Create visualization - time series of top 10
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))

# Panel 1: Top 5
colors = plt.cm.Set3(np.linspace(0, 1, 10))

for i, country in enumerate(top10_countries[:5]):
    ax1.plot(yearly_df['year'], yearly_df[country], 
             marker='o', linewidth=2.5, markersize=6, 
             label=country, color=colors[i], alpha=0.8)

ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Number of Mentions', fontsize=12)
ax1.set_title('Top 5 Asian Countries Mentioned in Russian Presidential Speeches', 
              fontsize=14, fontweight='bold')
ax1.legend(loc='upper left', fontsize=11, framealpha=0.95)
ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
ax1.set_xlim([yearly_df['year'].min() - 0.5, yearly_df['year'].max() + 0.5])

# Panel 2: Next 5
for i, country in enumerate(top10_countries[5:10]):
    ax2.plot(yearly_df['year'], yearly_df[country], 
             marker='o', linewidth=2.5, markersize=6, 
             label=country, color=colors[i+5], alpha=0.8)

ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('Number of Mentions', fontsize=12)
ax2.set_title('Asian Countries Ranked 6-10 in Russian Presidential Speeches', 
              fontsize=14, fontweight='bold')
ax2.legend(loc='upper left', fontsize=11, framealpha=0.95)
ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
ax2.set_xlim([yearly_df['year'].min() - 0.5, yearly_df['year'].max() + 0.5])

plt.suptitle(f'Asian Country Mentions Over Time (n = {len(df)} speeches, 2000-2025)', 
             fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('top_asian_countries_over_time.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('top_asian_countries_over_time.pdf', bbox_inches='tight', facecolor='white')

# Focus on 2021-present
print('\n\n=== TOP ASIAN COUNTRIES (2021-PRESENT) ===\n')
df_recent = df[df['date_parsed'] >= '2021-01-01']

print(f'Speeches: {len(df_recent)}')
print(f'Date range: {df_recent["date_parsed"].min().strftime("%B %Y")} - {df_recent["date_parsed"].max().strftime("%B %Y")}\n')

print('Rank | Country          | Total Mentions | Speeches | % of Speeches | Avg Word %')
print('-' * 85)

recent_stats = []
for country in asian_countries.keys():
    total_mentions = df_recent[f'{country}_mentions'].sum()
    speeches_with = (df_recent[f'{country}_mentions'] > 0).sum()
    pct_speeches = speeches_with / len(df_recent) * 100
    avg_proportion = df_recent[f'{country}_proportion'].mean() * 100
    
    recent_stats.append({
        'country': country,
        'mentions': total_mentions,
        'speeches': speeches_with,
        'pct_speeches': pct_speeches,
        'avg_proportion': avg_proportion
    })

recent_stats = sorted(recent_stats, key=lambda x: x['mentions'], reverse=True)

for i, stat in enumerate(recent_stats[:15], 1):
    print(f"{i:2}   | {stat['country']:16} | {stat['mentions']:14,} | {stat['speeches']:8} | {stat['pct_speeches']:13.1f}% | {stat['avg_proportion']:10.3f}%")

print('\n\nPlots saved:')
print('  - top_asian_countries_over_time.png')
print('  - top_asian_countries_over_time.pdf')
