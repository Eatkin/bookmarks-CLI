import requests
from bs4 import BeautifulSoup
from scripts.database_utils import Database

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

# Insert the descriptions into the database
db.insert_page_content(page_contents)
