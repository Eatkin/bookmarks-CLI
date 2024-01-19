import os
import curses
import logging
import atexit
from datetime import datetime
from time import sleep
from scripts.states import StateSetup

@atexit.register
def cleanup():
    """Cleanup the logger and cleanup after Curses"""
    logging.shutdown()
    # Clean up curses
    curses.nocbreak()
    curses.echo()
    curses.endwin()

def curses_init():
    """Initialize curses"""
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

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
# Additional components:
# Menu panels (consist of ascii art border, rectangle and options)
# Lists (long lists of items)
# --------------------------------------------------------------------------------

# Main loop
def main():
    # Initialize curses
    stdscr = curses_init()
    # Setup state
    state = StateSetup(stdscr)
    sleep_interval = 0.1
    while True:
        # Update and draw states
        try:
            # Update function can return a new state to switch to
            new_state = state.update()
            if new_state is not None:
                state = new_state
                logging.info(f"Switching to state: {state.__class__.__name__}")
        except Exception as e:
            logging.warning(f"State failed to update: {state.__class__.__name__}")
            logging.warning(e)
            exit(1)


        # Clear the screen
        stdscr.clear()

        try:
            state.render()
        except Exception as e:
            # Do no uncomment these unless needed cause they have the tendancy to spam the log file
            # logging.warning(f"State failed to render: {state.__class__.__name__}")
            # logging.warning(e)
            exit(1)

        # Refresh the screen
        stdscr.refresh()

        sleep(sleep_interval)


if __name__ == '__main__':
    main()
