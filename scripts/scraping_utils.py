from requests_html import HTMLSession
import logging
from bs4 import BeautifulSoup
from scripts.database_utils import Database
from scripts.nlp_utils import clean_text, get_tags

def get_null_description_bookmarks():
    """Returns a list of bookmarks with null descriptions"""
    # Create the database object
    db = Database()

    # Get all bookmark IDs that aren't in the descriptions table
    query = """
    SELECT bookmarks.id
    FROM bookmarks
    LEFT JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
    WHERE descriptions.bookmark_id IS NULL
    """

    results = db.query(query)

    # Now insert these into the descriptions table
    query = """
    INSERT INTO descriptions (bookmark_id)
    VALUES (?)
    """
    db.query(query, results)

    # Query the database to get all null descriptions joined with the bookmarks table
    # We want id and url
    query = """
    SELECT bookmarks.id, bookmarks.url
    FROM bookmarks
    JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
    WHERE descriptions.content IS NULL
    """

    # Get the query results
    results = db.query(query)

    return results

def scrape_data(bookmark_info):
    """Scrapes the page contents and returns a list of tuples of the bookmark id and the page contents"""
    # Loop through the results and use the requests library to get the page contents
    session = HTMLSession()

    # Get the id and url
    bookmark_id, url = bookmark_info
    # Get the description
    try:
        r = session.get(url)
        # Render for js content
        r.html.render()
    except:
        logging.error(f"Failed to get url: {url}")
        session.close()
        return (bookmark_id, None, None, None, None)

    if r.status_code == 200:
        # Make the soup
        soup = BeautifulSoup(r.text, 'html.parser')
        content_dump = soup.text
        try:
            relevant_content = parse_soup(soup)
        except Exception as e:
            logging.error(f"Failed to parse soup for url: {url}")
            session.close()
            return (bookmark_id, None, None, None, None)
        try:
            description = get_description(soup)
        except Exception as e:
            logging.error(f"Failed to get description for url: {url}")
            description = None
        try:
            # join description and relevant content
            if description:
                tag_content = description + ' ' + relevant_content
            cleaned_text = clean_text(tag_content)
            tags = get_tags(cleaned_text, n_tags = 3)
            # Format tags for database
            tags = ','.join(tags)
            logging.info(f"Tags for url: {url} are: {tags}")
        except Exception as e:
            logging.error(f"Failed to get tags for url: {url}")
            logging.info(f"Error: {e}")
            tags = None
    else:
        logging.error(f"Failed to get url: {url}")
        logging.info(f"Status code: {r.status_code}")
        session.close()
        # If status code is 404 then we can tag with 404
        if r.status_code == 404:
            tags = '404'
            description = '404 Error'
            # Also want content to be filled in because this is how we check if the bookmark has been scraped
            # Avoids re-scraping an error page
            content = '404 Error'
        else:
            tags = None
            description = None
            content = None
        return (bookmark_id, content, None, description, tags)

    # Return tuple
    session.close()
    return (bookmark_id, content_dump, relevant_content, description, tags)

def parse_soup(soup):
    """Parses the soup and returns the page contents"""
    # We will try get the main content
    body = soup.find('body')
    # If we can't find the body, we will use the entire soup
    if body is None:
        body = soup

    tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ol', 'ul']
    # Find all the tags
    tag_content = []
    for tag in tags:
        tag_content += [t.text for t in body.find_all(tag)]

    # Fall back to using the entire soup if we can't find any tags
    if not tag_content:
        tag_content = [body.text]

    # Join the tags
    page_contents = ' '.join(tag_content)

    return page_contents if page_contents else None

def insert_data(page_contents):
    """This inserts page contents into database
    It will also generate summaries and tags for the database using the page contents
    Uses the NLTK library to generate summaries and tags"""
    # We can use the db insert_page_contents method to insert the page contents
    db = Database()
    db.insert_descriptions(page_contents)

def get_description(soup):
    """Gets the meta description from the page content"""
    meta = soup.find('meta', attrs={'name':'description'})
    if meta:
        return meta['content']
    else:
        return None

def main(bookmark_info):
    """Main function for scraping the page contents and inserting relevant info into the database"""
    # Get the bookmarks with null descriptions
    # results = get_null_description_bookmarks()
    # logging.info(f"Got {len(results)} bookmarks with null descriptions")
    # Scrape the page contents
    page_contents = scrape_data(bookmark_info)

    # Check if the second value of the tuple is None
    if page_contents[1] is None:
        logging.info(f"Failed to scrape url: {bookmark_info[1]}")
        return False

    # Since we're doing 1 at a time put it in a list as that's how the insert_data method expects it
    page_contents = [page_contents]


    # Insert the page contents
    try:
        insert_data(page_contents)
        return True
    except Exception as e:
        logging.error(f"Failed to insert page contents into database: {e}")
        return False
