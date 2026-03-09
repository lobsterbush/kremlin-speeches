#!/usr/bin/env python3
"""
Analyze mentions of China, North Korea, and Iran in Russian presidential speeches
Calculate word proportion for each country separately
"""

import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')
df['year_month'] = df['date_parsed'].dt.to_period('M').dt.to_timestamp()

# Count total words
df['total_words'] = df['content'].str.split().str.len()

# Define keywords for each country
country_keywords = {
    'China': ['China', 'Chinese', 'Beijing', 'Shanghai', 'PRC', 'People\'s Republic'],
    'North Korea': ['North Korea', 'DPRK', 'Pyongyang', 'Democratic People\'s Republic of Korea'],
    'Iran': ['Iran', 'Iranian', 'Tehran', 'Persia', 'Persian']
}

# Calculate word proportions for each country
for country, keywords in country_keywords.items():
    pattern = '|'.join([re.escape(kw) for kw in keywords])
    df[f'{country}_mentions'] = df['content'].str.count(pattern, flags=re.IGNORECASE)
    df[f'{country}_words_estimate'] = df[f'{country}_mentions'] * 5
    df[f'{country}_proportion'] = df[f'{country}_words_estimate'] / df['total_words'].clip(lower=1)
    df[f'{country}_proportion'] = df[f'{country}_proportion'].clip(upper=1.0)

# Monthly aggregation
monthly = df.groupby('year_month').agg({
    'China_proportion': 'mean',
    'North Korea_proportion': 'mean',
    'Iran_proportion': 'mean'
}).reset_index()

# Convert to percentages
for country in country_keywords.keys():
    monthly[f'{country}_pct'] = monthly[f'{country}_proportion'] * 100

# Create three-panel plot
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

colors = {'China': '#c0392b', 'North Korea': '#8e44ad', 'Iran': '#16a085'}

for idx, country in enumerate(['China', 'North Korea', 'Iran']):
    ax = axes[idx]
    
    # Plot data
    ax.plot(monthly['year_month'], monthly[f'{country}_pct'], 
            linewidth=2, color=colors[country], alpha=0.8)
    
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Proportion of Speech Content (%)', fontsize=12)
    ax.set_title(f'{country}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 20])  # 0-20% for better visibility
    ax.set_yticks(range(0, 21, 5))

plt.suptitle('Mentions of China, North Korea, and Iran in Russian Presidential Speeches\n(Estimated proportion of words)', 
             fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('country_specific_proportions.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('country_specific_proportions.pdf', bbox_inches='tight', facecolor='white')

# Print summary statistics
print('\n=== COUNTRY-SPECIFIC WORD PROPORTION ANALYSIS ===\n')

for country in country_keywords.keys():
    speeches_mentioning = (df[f'{country}_mentions'] > 0).sum()
    avg_proportion = df[f'{country}_proportion'].mean() * 100
    median_proportion = df[f'{country}_proportion'].median() * 100
    max_proportion = df[f'{country}_proportion'].max() * 100
    
    print(f'{country}:')
    print(f'  Speeches mentioning: {speeches_mentioning} ({speeches_mentioning/len(df)*100:.1f}%)')
    print(f'  Average word proportion: {avg_proportion:.3f}%')
    print(f'  Median word proportion: {median_proportion:.3f}%')
    print(f'  Max word proportion: {max_proportion:.2f}%')
    print(f'  Total mentions: {df[f"{country}_mentions"].sum():,}')
    print()

# Compare the three countries
print('=== COMPARISON ===\n')
print('Average word proportions:')
for country in country_keywords.keys():
    avg = df[f'{country}_proportion'].mean() * 100
    print(f'  {country:15} {avg:.3f}%')

print('\nSpeeches mentioning each country:')
for country in country_keywords.keys():
    count = (df[f'{country}_mentions'] > 0).sum()
    print(f'  {country:15} {count:4} speeches ({count/len(df)*100:.1f}%)')

print('\nPlots saved:')
print('  - country_specific_proportions.png')
print('  - country_specific_proportions.pdf')
