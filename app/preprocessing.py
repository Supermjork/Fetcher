import re
import nltk
import spacy

stopwords = set(nltk.corpus.stopwords.words("english"))

lang_model = spacy.load("en_core_web_sm")

def regex_text(text: str) -> str:
    '''
    Cleans any passed string.
    Includes accented characters
    '''
    text = text.lower()

    regex_patterns = [
        (r"https?://\S+", ""),    # Remove http or https links
        (r"\S+@\S+\.\S+", " "),   # Remove email addresses
        (r"[^\w\sÀ-ÿ'’]", " "),   # Remove special characters, except accented ones
        (r"\s+", " "),            # Replace multiple spaces with a single space
        (r"^\s+|\s+$", "")        # Strip leading and trailing spaces
    ]

    for pattern, replacement in regex_patterns:
        text = re.sub(pattern, replacement, text)
    return text

def stopword_removal(text: str, stopwords_set: set) -> str:
    words = text.split()
    return " ".join([word for word in words if word not in stopwords_set])

def lemma(tokens, language_model):
    doc = language_model(tokens)

    return [token.lemma_ for token in doc]

def preprocess(text: str, remove_stopwords: bool = True) -> list[str]:
    text = regex_text(text)

    if remove_stopwords == True:
        stopword_removal(text, stopwords)

    return lemma(text , lang_model)
