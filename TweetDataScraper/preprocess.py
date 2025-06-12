import re
import emoji
from langdetect import detect
from deep_translator import GoogleTranslator
import spacy
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

nlp = spacy.load("en_core_web_sm")
english_stopwords = set(stopwords.words('english'))
bm_stopwords = set(['dan', 'yang', 'untuk', 'dari', 'pada', 'adalah', 'ini', 'itu'])

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
