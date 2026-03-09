#!/usr/bin/env python3
"""
Save list of stopwords and filler words removed during preprocessing
"""

import nltk
from nltk.corpus import stopwords

# Download if needed
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

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
    
    # Generic pronouns and articles
    'he', 'she', 'they', 'them', 'their', 'his', 'her',
    'the', 'a', 'an',
    
    # Time/place that don't add meaning
    'today', 'yesterday', 'tomorrow', 'year', 'month', 'day',
    'mr', 'ms', 'mrs', 'dr',
    
    # Modal verbs
    'would', 'could', 'should', 'might', 'must', 'can', 'may', 'will', 'shall',
    
    # Conjunctions/prepositions
    'and', 'but', 'or', 'so', 'because', 'since', 'for', 'in', 'on', 'at'
}

# Combine all stopwords
all_stopwords = english_stopwords.union(custom_stopwords)

# Write to file
with open('stopwords_removed.txt', 'w') as f:
    f.write("STOPWORDS AND FILLER WORDS REMOVED DURING PREPROCESSING\n")
    f.write("=" * 60 + "\n\n")
    
    f.write(f"Total stopwords: {len(all_stopwords)}\n")
    f.write(f"  - English stopwords: {len(english_stopwords)}\n")
    f.write(f"  - Custom stopwords: {len(custom_stopwords)}\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("CUSTOM STOPWORDS (Speech-specific)\n")
    f.write("=" * 60 + "\n\n")
    
    for word in sorted(custom_stopwords):
        f.write(f"  {word}\n")
    
    f.write("\n" + "=" * 60 + "\n")
    f.write("STANDARD ENGLISH STOPWORDS\n")
    f.write("=" * 60 + "\n\n")
    
    for word in sorted(english_stopwords):
        f.write(f"  {word}\n")

print("✓ Stopwords list saved to: stopwords_removed.txt")
