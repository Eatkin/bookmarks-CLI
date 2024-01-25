from nltk.tokenize import word_tokenize as word_tokenise
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer as WordNetLemmatiser
from nltk import FreqDist
import string
import logging

def clean_text(text):
    tokens = word_tokenise(text)
    # Lowercase
    tokens = [w.lower() for w in tokens]
    # Remove punctuation
    table = str.maketrans('', '', string.punctuation)
    stripped = [w.translate(table) for w in tokens]
    # Remove non-alphabetic tokens
    words = [word for word in stripped if word.isalpha()]
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if not w in stop_words]
    # Lemmatize
    lemmatizer = WordNetLemmatiser()
    words = [lemmatizer.lemmatize(word) for word in words]
    return words

def get_tags(words, n_tags=5):
    """Use frequency distribution to get the most common words"""
    freq_dist = FreqDist(words)
    tags = freq_dist.most_common(n_tags)
    tags = [tag[0] for tag in tags]
    return tags if tags else None
