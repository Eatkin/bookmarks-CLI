import requests
import logging
from bs4 import BeautifulSoup
from scripts.database_utils import Database
from scripts.nlp_utils import clean_text, get_tags

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

def scrape_data(results):
    """Scrapes the page contents and returns a list of tuples of the bookmark id and the page contents"""
    # Loop through the results and use the requests library to get the page contents
    description_rows = []

    for result in results:
        # Get the id and url
        bookmark_id, url = result
        # Get the description
        try:
            r = requests.get(url)
        except:
            logging.error(f"Failed to get url: {url}")
            continue

        if r.status_code == 200:
            # Make the soup
            soup = BeautifulSoup(r.text, 'html.parser')
            content_dump = soup.text
            relevant_content = parse_soup(soup)
            description = get_decription(soup)
            tags = get_tags(clean_text(relevant_content), ntags = 5)
            # Format tags for database
            tags = ','.join(tags)
            description_rows.append((bookmark_id, content_dump, relevant_content, description, tags))

    return description_rows

def parse_soup(soup):
    """Parses the soup and returns the page contents"""
    # We will try get the main content
    body = soup.find('body')
    # If we can't find the body, we will use the entire soup
    if body is None:
        body = soup

    tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ol', 'ul']
    # Find all the tags
    tags = body.find_all(tags)
    page_contents = ' '.join([tag.text for tag in tags])

    return page_contents if page_contents else None

def insert_data(page_contents):
    """This inserts page contents into database
    It will also generate summaries and tags for the database using the page contents
    Uses the NLTK library to generate summaries and tags"""
    # We can use the db insert_page_contents method to insert the page contents
    db = Database()
    db.insert_descriptions(page_contents)

def get_decription(soup):
    """Gets the meta description from the page content"""
    meta = soup.find('meta', attrs={'name':'description'})
    if meta:
        return meta['content']
    else:
        return None

def main():
    """Main function for scraping the page contents and inserting relevant info into the database"""
    # Get the bookmarks with null descriptions
    results = get_null_description_bookmarks()
    # Scrape the page contents
    page_contents = scrape_data(results)
    # Insert the page contents
    insert_data(page_contents)
