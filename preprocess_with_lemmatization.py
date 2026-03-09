#!/usr/bin/env python3
"""
Preprocess speeches with lemmatization to combine variants:
- russia/russian -> russia
- china/chinese -> china
- etc.
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
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')
df['total_words'] = df['content'].str.split().str.len()
df = df[df['total_words'] >= 500].copy()

print(f"\n=== PREPROCESSING WITH LEMMATIZATION ===")
print(f"Total speeches (>=500 words): {len(df)}\n")

# Stopwords
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
    'president', 'vladimir', 'putin', 'dmitry', 'medvedev',
    'he', 'she', 'they', 'them', 'their', 'his', 'her',
    'the', 'a', 'an',
    'today', 'yesterday', 'tomorrow', 'year', 'month', 'day',
    'mr', 'ms', 'mrs', 'dr',
    'would', 'could', 'should', 'might', 'must', 'can', 'may', 'will', 'shall',
    'and', 'but', 'or', 'so', 'because', 'since', 'for', 'in', 'on', 'at'
}
all_stopwords = english_stopwords.union(custom_stopwords)

# Country/demonym mapping for manual normalization
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
    'belarusian': 'belarus',
    'belarusians': 'belarus',
    'kazakh': 'kazakhstan',
    'kazakhs': 'kazakhstan',
    'kyrgyz': 'kyrgyzstan'
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
            # Apply country normalization first
            if token in country_normalizations:
                cleaned_tokens.append(country_normalizations[token])
            else:
                # Lemmatize
                lemma = lemmatizer.lemmatize(token)
                cleaned_tokens.append(lemma)
    
    return ' '.join(cleaned_tokens)

print("Cleaning and lemmatizing speeches...")
df['content_lemmatized'] = df['content'].apply(clean_and_lemmatize)
df['total_words_lemmatized'] = df['content_lemmatized'].str.split().str.len()

# Calculate reduction
total_orig = df['total_words'].sum()
total_lemma = df['total_words_lemmatized'].sum()
reduction_pct = (1 - total_lemma / total_orig) * 100

print(f"\n=== RESULTS ===")
print(f"Original total words: {total_orig:,}")
print(f"Lemmatized total words: {total_lemma:,}")
print(f"Reduction: {reduction_pct:.1f}%\n")

# Most common words in lemmatized corpus
print("\n=== TOP 50 LEMMATIZED WORDS ===\n")
all_words = ' '.join(df['content_lemmatized']).split()
word_counts = Counter(all_words)
most_common = word_counts.most_common(50)

for i, (word, count) in enumerate(most_common, 1):
    print(f"{i:2}. {word:20} {count:6,}")

# Save
df.to_csv('kremlin_speeches_lemmatized.csv', index=False)
top_words_df = pd.DataFrame(most_common, columns=['word', 'count'])
top_words_df['rank'] = range(1, len(top_words_df) + 1)
top_words_df.to_csv('top_words_lemmatized_corpus.csv', index=False)

print(f"\n\n✓ Lemmatized corpus saved to: kremlin_speeches_lemmatized.csv")
print(f"✓ Top words saved to: top_words_lemmatized_corpus.csv")

# Statistics by period
print("\n\n=== LEMMATIZED CORPUS BY PERIOD ===\n")

df['year'] = df['date_parsed'].dt.year

periods = {
    'Pre-Crimea (2000-2013)': (2000, 2013),
    'Crimea-2022 (2014-2021)': (2014, 2021),
    'Post-Invasion (2022-2025)': (2022, 2025)
}

for period_name, (start_year, end_year) in periods.items():
    period_df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    period_words = ' '.join(period_df['content_lemmatized']).split()
    period_counts = Counter(period_words)
    
    print(f"{period_name}:")
    print(f"  Speeches: {len(period_df)}")
    print(f"  Total words: {len(period_words):,}")
    print(f"  Unique words: {len(set(period_words)):,}")
    print(f"  Top 10 words: {', '.join([w for w, _ in period_counts.most_common(10)])}")
    print()

# Country comparison across periods
print("\n=== KEY COUNTRIES ACROSS PERIODS ===\n")

key_countries = ['russia', 'ukraine', 'china', 'america', 'europe', 'india', 'belarus']

for country in key_countries:
    print(f"{country.upper()}:")
    for period_name, (start_year, end_year) in periods.items():
        period_df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
        period_words = ' '.join(period_df['content_lemmatized']).split()
        count = period_words.count(country)
        pct = (count / len(period_words)) * 100 if len(period_words) > 0 else 0
        print(f"  {period_name:30} {count:5,} mentions ({pct:.3f}%)")
    print()
