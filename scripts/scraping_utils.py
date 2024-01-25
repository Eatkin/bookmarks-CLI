import requests
import nltk
from bs4 import BeautifulSoup
from scripts.database_utils import Database

def get_null_description_bookmarks():
    """Returns a list of bookmarks with null descriptions"""
    # Create the database object
    db = Database()

    # Query the database to get all null descriptions joined with the bookmarks table
    # We want id and url
    query = """
    SELECT bookmarks.id, bookmarks.url
    FROM bookmarks
    JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
    WHERE descriptions.bookmark_id IS NULL
    """

    # Get the query results
    results = db.cursor.execute(query).fetchall()

    return results

def scrape_page_contents(results):
    """Scrapes the page contents and returns a list of tuples of the bookmark id and the page contents"""
    # Loop through the results and use the requests library to get the page contents
    page_contents = []

    for result in results:
        # Get the id and url
        bookmark_id, url = result
        # Get the description
        r = requests.get(url)

        if r == 200:
            # Make the soup
            soup = BeautifulSoup(r.text, 'html.parser')
            # Get a dump of the text
            text = soup.get_text()
            # Create a tuple of the id and the description
            page_contents.append((bookmark_id, text))

    return page_contents

def insert_data(page_contents):
    """This inserts page contents into database
    It will also generate summaries and tags for the database using the page contents
    Uses the NLTK library to generate summaries and tags"""
    # We can use the db insert_page_contents method to insert the page contents
    db = Database()
    db.insert_page_content(page_contents)

def generate_summary(page_content):
    """Generates a summary of the page content using transformers"""
    summary = "peeeeeeeeeeeee"

    return summary

def generate_tags(page_content):
    """Generates tags for the page content using NLTK"""
    # Tokenize the page content
    tokens = nltk.word_tokenize(page_content)
    # Get the frequency distribution
    fdist = nltk.FreqDist(tokens)
    # Get the most common words
    most_common = fdist.most_common(10)
    # Get the most common words
    tags = [word for word, _ in most_common]

    return tags
