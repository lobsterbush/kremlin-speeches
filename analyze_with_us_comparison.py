#!/usr/bin/env python3
"""
Analyze mentions of Asia, China, North Korea, and Iran vs US in Russian presidential speeches
Focus on 2021-present with 4-panel plot
"""

import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')

# Filter to 2021 onwards
df = df[df['date_parsed'] >= '2021-01-01'].copy()
df['year_month'] = df['date_parsed'].dt.to_period('M').dt.to_timestamp()

# Count total words
df['total_words'] = df['content'].str.split().str.len()

# Define keywords
keywords = {
    'Asia': ['China', 'Japan', 'India', 'Korea', 'Vietnam', 'Thailand', 'Singapore', 
             'Malaysia', 'Indonesia', 'Philippines', 'Pakistan', 'Bangladesh', 'Myanmar',
             'Cambodia', 'Laos', 'Mongolia', 'Afghanistan', 'Kazakhstan', 'Uzbekistan',
             'Kyrgyzstan', 'Tajikistan', 'Turkmenistan', 'Asia', 'Asian', 'Beijing',
             'Tokyo', 'Delhi', 'Seoul', 'Bangkok', 'Shanghai', 'ASEAN', 'SCO', 'APEC'],
    'China': ['China', 'Chinese', 'Beijing', 'Shanghai', 'PRC', 'People\'s Republic'],
    'North Korea': ['North Korea', 'DPRK', 'Pyongyang', 'Democratic People\'s Republic of Korea'],
    'Iran': ['Iran', 'Iranian', 'Tehran', 'Persia', 'Persian'],
    'US': ['United States', 'America', 'American', 'Washington', 'U.S.', 'USA']
}

# Calculate word proportions for each region/country
for region, kw_list in keywords.items():
    pattern = '|'.join([re.escape(kw) for kw in kw_list])
    df[f'{region}_mentions'] = df['content'].str.count(pattern, flags=re.IGNORECASE)
    df[f'{region}_words_estimate'] = df[f'{region}_mentions'] * 5
    df[f'{region}_proportion'] = df[f'{region}_words_estimate'] / df['total_words'].clip(lower=1)
    df[f'{region}_proportion'] = df[f'{region}_proportion'].clip(upper=1.0)

# Monthly aggregation
agg_dict = {}
for region in keywords.keys():
    agg_dict[f'{region}_proportion'] = 'mean'

monthly = df.groupby('year_month').agg(agg_dict).reset_index()

# Convert to percentages
for region in keywords.keys():
    monthly[f'{region}_pct'] = monthly[f'{region}_proportion'] * 100

# Create four-panel plot
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()

regions = ['Asia', 'China', 'North Korea', 'Iran']
colors = {
    'Asia': '#e74c3c',
    'China': '#c0392b', 
    'North Korea': '#8e44ad',
    'Iran': '#16a085',
    'US': '#2c3e50'
}

# Count speeches
n_speeches = len(df)

for idx, region in enumerate(regions):
    ax = axes[idx]
    
    # Plot region/country
    ax.plot(monthly['year_month'], monthly[f'{region}_pct'], 
            linewidth=2.5, color=colors[region], alpha=0.9, label=region)
    
    # Plot US comparison
    ax.plot(monthly['year_month'], monthly['US_pct'], 
            linewidth=2.5, color=colors['US'], alpha=0.9, linestyle='--', label='United States')
    
    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Proportion of Speech Content (%)', fontsize=11)
    ax.set_title(f'{region}', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
    ax.set_ylim([0, 25])
    ax.set_yticks(range(0, 26, 5))
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    
    # Format x-axis to show years clearly
    ax.tick_params(axis='both', labelsize=10)

plt.suptitle(f'Russian Presidential Speeches (2021-Present): Regional/Country Mentions vs United States\n(Estimated proportion of words; n = {n_speeches} speeches)', 
             fontsize=15, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('comparison_with_us_2021.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('comparison_with_us_2021.pdf', bbox_inches='tight', facecolor='white')

# Print summary statistics
print('\n=== COMPARISON ANALYSIS (2021-PRESENT) ===')
print(f'\nTotal speeches: {n_speeches}')
print(f'Date range: {df["date_parsed"].min().strftime("%B %Y")} - {df["date_parsed"].max().strftime("%B %Y")}\n')

print('Average word proportions:')
for region in regions + ['US']:
    avg = df[f'{region}_proportion'].mean() * 100
    speeches_mentioning = (df[f'{region}_mentions'] > 0).sum()
    pct_speeches = speeches_mentioning / len(df) * 100
    print(f'  {region:15} {avg:.3f}%  (mentioned in {speeches_mentioning} speeches, {pct_speeches:.1f}%)')

print('\nTotal mentions:')
for region in regions + ['US']:
    total = df[f'{region}_mentions'].sum()
    print(f'  {region:15} {total:,}')

# Calculate average proportions by year
print('\n=== YEARLY AVERAGES ===')
df['year'] = df['date_parsed'].dt.year
yearly = df.groupby('year').agg({
    f'{region}_proportion': 'mean' for region in regions + ['US']
}).reset_index()

for region in regions + ['US']:
    yearly[f'{region}_pct'] = yearly[f'{region}_proportion'] * 100

print('\n', yearly[['year'] + [f'{region}_pct' for region in regions + ['US']]].to_string(index=False))

print('\nPlots saved:')
print('  - comparison_with_us_2021.png')
print('  - comparison_with_us_2021.pdf')
