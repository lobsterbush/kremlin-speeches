#!/usr/bin/env python3
"""
Analyze mentions of Russia, China, Iran, and North Korea in US presidential speeches
Focus on 2021-present with 4-panel plot
"""

import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('whitehouse_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date_parsed'], errors='coerce', utc=True)

# Filter to 2021 onwards
df = df[df['date_parsed'] >= '2021-01-01'].copy()
df['year_month'] = df['date_parsed'].dt.to_period('M').dt.to_timestamp()

# Count total words
df['total_words'] = df['content'].str.split().str.len()

# Define keywords
keywords = {
    'Russia': ['Russia', 'Russian', 'Russians', 'Moscow', 'Putin', 'Kremlin', 'Soviet'],
    'China': ['China', 'Chinese', 'Beijing', 'Shanghai', 'PRC', "People's Republic", 'Xi Jinping'],
    'North Korea': ['North Korea', 'DPRK', 'Pyongyang', "Democratic People's Republic of Korea", 'Kim Jong'],
    'Iran': ['Iran', 'Iranian', 'Tehran', 'Persia', 'Persian', 'Ayatollah']
}

# Calculate word proportions for each country
for country, kw_list in keywords.items():
    pattern = '|'.join([re.escape(kw) for kw in kw_list])
    df[f'{country}_mentions'] = df['content'].str.count(pattern, flags=re.IGNORECASE)
    df[f'{country}_words_estimate'] = df[f'{country}_mentions'] * 5
    df[f'{country}_proportion'] = df[f'{country}_words_estimate'] / df['total_words'].clip(lower=1)
    df[f'{country}_proportion'] = df[f'{country}_proportion'].clip(upper=1.0)

# Monthly aggregation
agg_dict = {}
for country in keywords.keys():
    agg_dict[f'{country}_proportion'] = 'mean'

monthly = df.groupby('year_month').agg(agg_dict).reset_index()

# Convert to percentages
for country in keywords.keys():
    monthly[f'{country}_pct'] = monthly[f'{country}_proportion'] * 100

# Create four-panel plot
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()

countries = ['Russia', 'China', 'North Korea', 'Iran']
colors = {
    'Russia': '#c0392b',
    'China': '#e74c3c', 
    'North Korea': '#8e44ad',
    'Iran': '#16a085'
}

# Count speeches
n_speeches = len(df)

for idx, country in enumerate(countries):
    ax = axes[idx]
    
    # Plot country
    ax.plot(monthly['year_month'], monthly[f'{country}_pct'], 
            linewidth=2.5, color=colors[country], alpha=0.9, label=country)
    
    # Plot China comparison for non-China countries
    if country != 'China':
        ax.plot(monthly['year_month'], monthly['China_pct'], 
                linewidth=2.5, color='#34495e', alpha=0.7, linestyle='--', label='China')
    else:
        # For China, compare with Russia
        ax.plot(monthly['year_month'], monthly['Russia_pct'], 
                linewidth=2.5, color='#34495e', alpha=0.7, linestyle='--', label='Russia')
    
    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Proportion of Speech Content (%)', fontsize=11)
    ax.set_title(f'{country}', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
    ax.set_ylim([0, 15])
    ax.set_yticks(range(0, 16, 3))
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    
    # Format x-axis to show years clearly
    ax.tick_params(axis='both', labelsize=10)

plt.suptitle(f'US Presidential Speeches (2021-Present): Mentions of Adversary Nations\\n(Estimated proportion of words; n = {n_speeches} speeches)', 
             fontsize=15, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('whitehouse_russia_comparison.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('whitehouse_russia_comparison.pdf', bbox_inches='tight', facecolor='white')

# Print summary statistics
print('\\n=== COMPARISON ANALYSIS (2021-PRESENT) ===')
print(f'\\nTotal speeches: {n_speeches}')
print(f'Date range: {df["date_parsed"].min().strftime("%B %Y")} - {df["date_parsed"].max().strftime("%B %Y")}\\n')

print('Average word proportions:')
for country in countries:
    avg = df[f'{country}_proportion'].mean() * 100
    speeches_mentioning = (df[f'{country}_mentions'] > 0).sum()
    pct_speeches = speeches_mentioning / len(df) * 100
    print(f'  {country:15} {avg:.3f}%  (mentioned in {speeches_mentioning} speeches, {pct_speeches:.1f}%)')

print('\\nTotal mentions:')
for country in countries:
    total = df[f'{country}_mentions'].sum()
    print(f'  {country:15} {total:,}')

# Calculate average proportions by year
print('\\n=== YEARLY AVERAGES ===')
df['year'] = df['date_parsed'].dt.year
yearly = df.groupby('year').agg({
    f'{country}_proportion': 'mean' for country in countries
}).reset_index()

for country in countries:
    yearly[f'{country}_pct'] = yearly[f'{country}_proportion'] * 100

print('\\n', yearly[['year'] + [f'{country}_pct' for country in countries]].to_string(index=False))

print('\\nPlots saved:')
print('  - whitehouse_russia_comparison.png')
print('  - whitehouse_russia_comparison.pdf')
