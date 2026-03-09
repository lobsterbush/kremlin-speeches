#!/usr/bin/env python3
"""
Preprocess Russian presidential speeches:
- Remove stopwords
- Remove common filler words specific to political speeches
- Create cleaned corpus for better signal
"""

import pandas as pd
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Load data
df = pd.read_csv('kremlin_speeches_classified.csv')
df['date_parsed'] = pd.to_datetime(df['date'], format='%B %d, %Y', errors='coerce')
df['total_words'] = df['content'].str.split().str.len()

# Filter to speeches >= 500 words
df = df[df['total_words'] >= 500].copy()

print(f"\n=== PREPROCESSING RUSSIAN PRESIDENTIAL SPEECHES ===")
print(f"Total speeches (>=500 words): {len(df)}\n")

# Standard English stopwords
english_stopwords = set(stopwords.words('english'))

# Custom stopwords specific to political speeches and transcripts
custom_stopwords = {
    # Common filler
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
    
    # Speech-specific
    'applause', 'laughter', 'inaudible', 'crosstalk',
    'question', 'answer', 'comment', 'remarks',
    'speech', 'address', 'statement', 'transcript',
    'president', 'vladimir', 'putin', 'dmitry', 'medvedev',
    
    # Generic pronouns and articles (already in standard stopwords but emphasizing)
    'he', 'she', 'they', 'them', 'their', 'his', 'her',
    'the', 'a', 'an',
    
    # Time/place that don't add meaning
    'today', 'yesterday', 'tomorrow', 'year', 'month', 'day',
    'mr', 'ms', 'mrs', 'dr',
    
    # Modal verbs
    'would', 'could', 'should', 'might', 'must', 'can', 'may', 'will', 'shall',
    
    # Conjunctions/prepositions (already in stopwords but emphasizing)
    'and', 'but', 'or', 'so', 'because', 'since', 'for', 'in', 'on', 'at'
}

# Combine all stopwords
all_stopwords = english_stopwords.union(custom_stopwords)

print(f"Total stopwords to remove: {len(all_stopwords)}")
print(f"English stopwords: {len(english_stopwords)}")
print(f"Custom stopwords: {len(custom_stopwords)}\n")

# Function to clean text
def clean_text(text):
    if pd.isna(text):
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords and keep only alphabetic tokens of length > 2
    cleaned_tokens = [
        token for token in tokens 
        if token.isalpha() 
        and len(token) > 2 
        and token not in all_stopwords
    ]
    
    return ' '.join(cleaned_tokens)

# Apply cleaning
print("Cleaning speeches...")
df['content_cleaned'] = df['content'].apply(clean_text)
df['total_words_cleaned'] = df['content_cleaned'].str.split().str.len()

# Calculate reduction
total_orig = df['total_words'].sum()
total_clean = df['total_words_cleaned'].sum()
reduction_pct = (1 - total_clean / total_orig) * 100

print(f"\n=== CLEANING RESULTS ===")
print(f"Original total words: {total_orig:,}")
print(f"Cleaned total words: {total_clean:,}")
print(f"Reduction: {reduction_pct:.1f}%\n")

print(f"Average words per speech:")
print(f"  Original: {df['total_words'].mean():.0f}")
print(f"  Cleaned: {df['total_words_cleaned'].mean():.0f}\n")

# Show example
print("=== EXAMPLE (First speech) ===\n")
example = df.iloc[0]
print(f"Date: {example['date']}")
print(f"Title: {example['title'][:80]}...\n")
print(f"Original ({example['total_words']} words, first 200 chars):")
print(f"{example['content'][:200]}...\n")
print(f"Cleaned ({example['total_words_cleaned']} words, first 200 chars):")
print(f"{example['content_cleaned'][:200]}...\n")

# Most common words in cleaned corpus
print("\n=== TOP 50 WORDS IN CLEANED CORPUS ===\n")
all_words = ' '.join(df['content_cleaned']).split()
word_counts = Counter(all_words)
most_common = word_counts.most_common(50)

for i, (word, count) in enumerate(most_common, 1):
    print(f"{i:2}. {word:20} {count:6,}")

# Save cleaned data
df.to_csv('kremlin_speeches_cleaned.csv', index=False)
print(f"\n\n✓ Cleaned corpus saved to: kremlin_speeches_cleaned.csv")

# Also save just the top words for analysis
top_words_df = pd.DataFrame(most_common, columns=['word', 'count'])
top_words_df['rank'] = range(1, len(top_words_df) + 1)
top_words_df.to_csv('top_words_cleaned_corpus.csv', index=False)
print(f"✓ Top words saved to: top_words_cleaned_corpus.csv")

# Statistics by period
print("\n\n=== CLEANED CORPUS STATISTICS BY PERIOD ===\n")

df['year'] = df['date_parsed'].dt.year

periods = {
    'Pre-Crimea (2000-2013)': (2000, 2013),
    'Crimea-2022 (2014-2021)': (2014, 2021),
    'Post-Invasion (2022-2025)': (2022, 2025)
}

for period_name, (start_year, end_year) in periods.items():
    period_df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    print(f"{period_name}:")
    print(f"  Speeches: {len(period_df)}")
    print(f"  Total words (cleaned): {period_df['total_words_cleaned'].sum():,}")
    print(f"  Avg words per speech (cleaned): {period_df['total_words_cleaned'].mean():.0f}")
    print(f"  Unique words: {len(set(' '.join(period_df['content_cleaned']).split())):,}")
    print()
