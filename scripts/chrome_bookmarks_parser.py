import re
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

def read_bookmarks_html(file_path):
    """Reads the bookmarks html file and returns the contents as a string"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def make_soup(html):
    """Makes a BeautifulSoup object from the html"""
    soup = BeautifulSoup(html, 'html.parser')
    # Add the dummy h3 to the end of the soup
    # We parse by getting the content between h3 tags so we need a dummy h3 at the end
    soup.append(BeautifulSoup('<h3>dummy</h3>', 'html.parser'))
    return soup

def parse_folders(soup):
    """Gets all the bookmark folders and their contents
    returns: dictionary of folders and their html contents, list of failures
    """
    # NOTE: I don't use subfolders, I'm not sure how Chrome handles them in the html
    # Find h3 tags
    h3_tags = soup.find_all('h3')
    bookmarks = {}
    failures = []
    for i in range(0, len(h3_tags)-1):
        heading = h3_tags[i].text
        # Make pattern to find content between h3 tags
        pattern = re.compile(r'{}(.+?){}'.format(re.escape(str(h3_tags[i])), re.escape(str(h3_tags[i + 1]))), re.DOTALL)

        try:
            bookmarks[heading] = pattern.search(str(soup)).group(1).strip()
        except AttributeError:
            bookmarks[heading] = ''
            failures.append(heading)

    return bookmarks, failures

def parse_bookmarks(bookmark_dict):
    """Gets all the bookmarks from the bookmark folders
    returns: list of tuples
    """
    bookmarks = []
    for folder, html in bookmark_dict.items():
        soup = BeautifulSoup(html, 'html.parser')
        # Find all the a tags
        a_tags = soup.find_all('a')
        for a in a_tags:
            title = a.text
            url = a['href']
            add_date = a['add_date']
            # Convert add_date to datetime (it's in unix time)
            add_date = datetime.fromtimestamp(int(add_date))
            # Append the bookmark to the list
            bookmarks.append((title, url, add_date, folder))

    return bookmarks

def export_bookmarks(bookmarks, db_path='bookmarks.db'):
    """Exports the bookmarks to a sql file"""
    db = sqlite3.connect(db_path)
    cursor = db.cursor()

    # Create the table if it doesn't exist
    query = """
    CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT,
        add_date TEXT,
        folder TEXT
    )
    """
    cursor.execute(query)

    # Insert the bookmarks
    query = """
    INSERT INTO bookmarks (title, url, add_date, folder)
    VALUES (?, ?, ?, ?)
    """
    cursor.executemany(query, bookmarks)
    db.commit()
    db.close()

def parse(bookmarks_filepath):
    """Parses the bookmarks file and exports to a database
    Returns any bookmark folders that failed to parse"""
    soup = make_soup(read_bookmarks_html(bookmarks_filepath))
    bookmarks, failures = parse_folders(soup)
    bookmarks = parse_bookmarks(bookmarks)
    export_bookmarks(bookmarks)
    return failures
