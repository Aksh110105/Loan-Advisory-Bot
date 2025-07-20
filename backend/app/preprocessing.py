import re

def preprocess_text(text: str) -> str:
    # Basic NLP preprocessing
    text = text.lower()
    text = re.sub(r'\W+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
