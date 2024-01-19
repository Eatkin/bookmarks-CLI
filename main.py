import os
import curses
import logging
import atexit
from datetime import datetime
from time import sleep
import scripts.chrome_bookmarks_parser as bookmarks_parser
from scripts.database_utils import Database

@atexit.register
def cleanup():
    """Cleanup the logger and close database connection"""
    logging.shutdown()
    if database:
        database.close_database()

def curses_init():
    """Initialize curses"""
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()

    return stdscr

def logging_init():
    """Create a logger and return filepath"""
    logger_fname = 'log_{}.txt'.format(datetime.now().strftime('%d_%m_%Y:%H_%M_%S'))
    # Create the logs folder if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger_filepath = os.path.join('logs', logger_fname)

    # Create logger
    logging.basicConfig(filename=logger_filepath, encoding="utf-8", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

    return logger_filepath

logger_filepath = logging_init()
database = None

def create_database(html_filepath, db_path='bookmarks.db'):
    """Create a new database"""
    # Parse the bookmarks
    bookmarks, failures = bookmarks_parser.parse(html_filepath)
    if len(failures) > 0:
        logging.warning(f'Bookmarks folders failed to parse: {failures}')
    else:
        logging.info('Bookmarks parsed successfully')

    db = Database(db_path=db_path)
    db.export_bookmarks(bookmarks)
    # Establish the database connection
    db.load_database()

    return db

def load_database(db_path='bookmarks.db'):
    """Load an existing database"""
    db = Database(db_path=db_path)
    db.load_database()

    return db
# --------------------------------------------------------------------------------
# THE PLAN:
# Use curses for the interface
# Use sqlite3 for the database
# Options - parse bookmarks (select a file) or view bookmarks
# Upon viewing bookmarks we have options for:
# - Random Bookmark
# - View By Folder (option for view all, and random pick from folder also)
# - Search (by title, url, folder)
# - View by date added
# - Explore by date (pick year, month, probably not day, not enough)
# --------------------------------------------------------------------------------

# Main loop
def main():
    # Initialize curses
    stdscr = curses_init()
    while True:
        pass


if __name__ == '__main__':
    main()
