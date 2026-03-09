#!/usr/bin/env python3
"""
Preprocess ALL White House speeches with lemmatization
"""

import pandas as pd
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
for resource in ['punkt_tab', 'stopwords', 'wordnet', 'omw-1.4']:
    try:
        nltk.data.find(f'corpora/{resource}') if resource in ['wordnet', 'omw-1.4'] else nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        nltk.download(resource)

# Load data
df = pd.read_csv('whitehouse_speeches_raw.csv')

# Parse dates - White House uses ISO format or various formats
df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
# If that didn't work, try other formats
if df['date_parsed'].isna().sum() > len(df) * 0.5:
    df['date_parsed'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')

df['total_words'] = df['content'].str.split().str.len()

print(f"\n=== PREPROCESSING ALL WHITE HOUSE SPEECHES ===")
print(f"Total speeches: {len(df)}")
print(f"Date range: {df['date_parsed'].min()} to {df['date_parsed'].max()}")
print(f"Speech length range: {df['total_words'].min()} to {df['total_words'].max()} words\n")

# Stopwords - adapted for US context
english_stopwords = set(stopwords.words('english'))
custom_stopwords = {
    'said', 'says', 'saying', 'say', 'told', 'tell', 'asked', 'ask',
    'going', 'go', 'goes', 'went', 'come', 'came', 'comes',
    'see', 'saw', 'seen', 'look', 'looked', 'looking',
    'know', 'knew', 'known', 'knows', 'knowing',
    'think', 'thought', 'thinks', 'thinking',
    'want', 'wanted', 'wants', 'wanting',
    'make', 'made', 'makes', 'making',
    'get', 'got', 'gets', 'getting',
    'take', 'took', 'taken', 'takes', 'taking',
    'give', 'gave', 'given', 'gives', 'giving',
    'good', 'well', 'very', 'really', 'quite',
    'also', 'just', 'now', 'then', 'there', 'here',
    'yes', 'no', 'okay', 'ok',
    'applause', 'laughter', 'inaudible', 'crosstalk',
    'question', 'answer', 'comment', 'remarks',
    'speech', 'address', 'statement', 'transcript',
    'president', 'biden', 'trump', 'obama', 'bush', 'clinton',
    'he', 'she', 'they', 'them', 'their', 'his', 'her',
    'the', 'a', 'an',
    'today', 'yesterday', 'tomorrow', 'year', 'month', 'day',
    'mr', 'ms', 'mrs', 'dr',
    'would', 'could', 'should', 'might', 'must', 'can', 'may', 'will', 'shall',
    'and', 'but', 'or', 'so', 'because', 'since', 'for', 'in', 'on', 'at',
    'secretary', 'senator', 'representative', 'congressman', 'congresswoman',
    'house', 'senate', 'white', 'administration'
}
all_stopwords = english_stopwords.union(custom_stopwords)

# Country/demonym mapping
country_normalizations = {
    'russian': 'russia',
    'russians': 'russia',
    'chinese': 'china',
    'american': 'america',
    'americans': 'america',
    'ukrainian': 'ukraine',
    'ukrainians': 'ukraine',
    'german': 'germany',
    'germans': 'germany',
    'french': 'france',
    'british': 'britain',
    'japanese': 'japan',
    'indian': 'india',
    'european': 'europe',
    'europeans': 'europe',
    'asian': 'asia',
    'asians': 'asia',
    'iranian': 'iran',
    'iranians': 'iran',
    'north korean': 'north korea',
    'south korean': 'south korea',
    'korean': 'korea',
    'koreans': 'korea',
    'israeli': 'israel',
    'israeli': 'israel',
    'palestinian': 'palestine',
    'palestinians': 'palestine',
    'syrian': 'syria',
    'syrians': 'syria',
    'iraqi': 'iraq',
    'iraqis': 'iraq',
    'afghan': 'afghanistan',
    'afghans': 'afghanistan',
}

lemmatizer = WordNetLemmatizer()

def clean_and_lemmatize(text):
    if pd.isna(text):
        return ""
    
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    
    tokens = word_tokenize(text)
    
    cleaned_tokens = []
    for token in tokens:
        if token.isalpha() and len(token) > 2 and token not in all_stopwords:
            if token in country_normalizations:
                cleaned_tokens.append(country_normalizations[token])
            else:
                lemma = lemmatizer.lemmatize(token)
                cleaned_tokens.append(lemma)
    
    return ' '.join(cleaned_tokens)

print("Cleaning and lemmatizing ALL speeches...")
df['content_lemmatized'] = df['content'].apply(clean_and_lemmatize)
df['total_words_lemmatized'] = df['content_lemmatized'].str.split().str.len()

# Calculate reduction
total_orig = df['total_words'].sum()
total_lemma = df['total_words_lemmatized'].sum()
reduction_pct = (1 - total_lemma / total_orig) * 100

print(f"\n=== RESULTS ===")
print(f"Speeches processed: {len(df)}")
print(f"Original total words: {total_orig:,}")
print(f"Lemmatized total words: {total_lemma:,}")
print(f"Reduction: {reduction_pct:.1f}%\n")

# Save
df.to_csv('whitehouse_speeches_lemmatized.csv', index=False)
print(f"✓ Saved to: whitehouse_speeches_lemmatized.csv")

# Check for quarters with no speeches
df['year_quarter'] = pd.to_datetime(df['date_parsed']).dt.to_period('Q')
quarterly_counts = df.groupby('year_quarter').size()

print(f"\n=== COVERAGE CHECK ===")
print(f"Total quarters covered: {len(quarterly_counts)}")
if len(df[df['date_parsed'].notna()]) > 0:
    print(f"Date range: {df['date_parsed'].min().strftime('%Y-%m-%d')} to {df['date_parsed'].max().strftime('%Y-%m-%d')}")

# Find any gaps
if len(quarterly_counts) > 0:
    all_quarters = pd.period_range(start=df['year_quarter'].min(), end=df['year_quarter'].max(), freq='Q')
    missing_quarters = set(all_quarters) - set(quarterly_counts.index)
    
    if len(missing_quarters) > 0:
        print(f"\nWARNING: {len(missing_quarters)} missing quarters:")
        for q in sorted(missing_quarters):
            print(f"  {q}")
    else:
        print("\n✓ NO GAPS - Complete quarterly coverage!")
