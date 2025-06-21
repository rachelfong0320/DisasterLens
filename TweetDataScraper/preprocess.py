import re
import emoji
from langdetect import detect
from deep_translator import GoogleTranslator
import spacy
import nltk
from nltk.corpus import stopwords
import os

"""
Tweet Text Preprocessing Utilities for Disaster Tweet Analysis

Overview:
This script provides functions for cleaning, translating, and tokenizing tweet text to prepare it for further analysis or storage.

Key Features:
1. **clean_text(text)**:
   - Removes URLs, mentions (@user), emojis, and special characters.
   - Strips and normalizes whitespace.
   - Outputs clean, alphanumeric-only text.

2. **translate_to_english(text)**:
   - Detects the language of the input text using `langdetect`.
   - Translates non-English text to English using `deep_translator` and Google Translate.
   - Falls back to original text if detection or translation fails.

3. **tokenize_and_clean(text)**:
   - Uses spaCy for tokenization.
   - Converts text to lowercase and removes stopwords (both English and Bahasa Melayu).
   - Returns a list of clean, meaningful tokens.

Dependencies:
- `emoji`, `langdetect`, `deep-translator`, `spacy`, `nltk`
- English and BM stopwords are included.
- Downloads NLTK stopwords and ensures the `en_core_web_sm` spaCy model is available.

Usage:
These functions are intended to be used in a tweet scraping pipeline to preprocess text before analysis, filtering, or database insertion.
"""

# Ensure stopwords are available
try:
    english_stopwords = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords')
    english_stopwords = set(stopwords.words('english'))

# Load BM stopwords manually
bm_stopwords = set(['dan', 'yang', 'untuk', 'dari', 'pada', 'adalah', 'ini', 'itu'])
    
try:
    nlp = spacy.load(os.getenv("SPACY_MODEL", "en_core_web_sm"))
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def clean_text(text):
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r"[^A-Za-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()

def translate_to_english(text):
    try:
        lang = detect(text)
        if lang != "en":
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

def tokenize_and_clean(text):
    doc = nlp(text.lower())
    return [token.text for token in doc if token.is_alpha and token.text not in english_stopwords and token.text not in bm_stopwords]
