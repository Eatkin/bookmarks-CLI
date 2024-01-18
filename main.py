import os
import scripts.chrome_bookmarks_parser as bookmarks_parser
import logging
from datetime import datetime

def logging_init():
    """Create a logger and return logger and filepath"""
    logger_fname = 'log_{}.txt'.format(datetime.now().strftime('%d_%m_%Y:%H_%M_%S'))
    # Create the logs folder if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger_filepath = os.path.join('logs', logger_fname)

    # Create logger
    logging.basicConfig(filename=logger_filepath, encoding="utf-8", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

    logger = logging.getLogger(__name__)

    return logger, logger_filepath

logger, logger_filepath = logging_init()


# Just testing being able to get the bookmarks at the moment
bookmarks_filepath = os.path.join(os.path.dirname(__file__), 'bookmarks_18_01_2024.html')

failures = bookmarks_parser.parse(bookmarks_filepath)

if len(failures) > 0:
    logger.warning(f'Bookmarks folders failed to parse: {failures}')
else:
    logger.info('Bookmarks parsed successfully')

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
