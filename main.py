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

def logging_init(level = logging.INFO):
    """Create a logger and return filepath"""
    logger_fname = 'log_{}.txt'.format(datetime.now().strftime('%d_%m_%Y:%H_%M_%S'))
    # Create the logs folder if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger_filepath = os.path.join('logs', logger_fname)

    # Create logger
    logging.basicConfig(filename=logger_filepath, encoding="utf-8", level=level, format='%(asctime)s:%(levelname)s:%(message)s')

    return logger_filepath

logger_filepath = logging_init()

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
            # Basically because Curses is a little bitch and whines when you overflow even if you DON'T overflow
            # logging.warning(f"State failed to render: {state.__class__.__name__}")
            # logging.warning(e)
            exit(1)

        # Refresh the screen
        stdscr.refresh()
        curses.doupdate()

        sleep(sleep_interval)


if __name__ == '__main__':
    main()
