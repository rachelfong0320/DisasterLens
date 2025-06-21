import emoji
import re
from langdetect import detect
from deep_translator import GoogleTranslator
from config import malaysia_locations

failed_translations = []

def safe_get(d, *keys):
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key)
        else:
            return None
    return d

def clean_caption(text):
    """Clean caption text by removing emojis, URLs, hashtags, and special characters"""
    if not isinstance(text, str):
        return ""

    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[@#]\w+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def clean_hashtag(tag):
    """Clean hashtag by removing special characters and formatting"""
    tag = tag.lower()
    tag = tag.lstrip('#')
    tag = tag.replace(' ', '')
    tag = re.sub(r'[^\w\s]', '', tag)
    return tag.strip()


def translate_caption(text):
    """Translate non-English text to English"""
    if not isinstance(text, str) or text.strip() == "":
        return ""
    
    try:
        lang = detect(text)
        if lang != "en":
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except Exception as e:
        print(f"Translation error: {e} | Text: {text}")
        failed_translations.append(text)  
        return text

def contains_malaysia_location(row, location_fields):
    """Check if any location field contains Malaysian location"""
    for field in location_fields:
        val = str(row[field]).lower()
        if any(loc in val for loc in malaysia_locations):
            return True
    return False