from nltk.tokenize import word_tokenize as word_tokenise
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer as WordNetLemmatiser
from nltk import FreqDist
import string

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
    # Rename the lemmatize method to lemmatise because I'm British lol
    lemmatizer.lemmatise = lemmatizer.lemmatize
    words = [lemmatizer.lemmatise(word) for word in words]
    return words

def get_tags(words, n_tags=5):
    """Use frequency distribution to get the most common words"""
    freq_dist = FreqDist(words)
    most_common = freq_dist.most_common(n_tags)
    return most_common if most_common else None
