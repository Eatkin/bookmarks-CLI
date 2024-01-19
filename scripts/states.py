import curses
import logging
from scripts.database_utils import Database
from scripts.chrome_bookmarks_parser import parse

# Some semantical sugar
state_history = []

class State():
    """Base class for all states"""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        # Add the state to the history
        global state_history
        state_history.append(self)
        # Callbacks for when we regress to a prior state
        self.on_regress = None

    def update(self):
        """Update the state"""
        # These are one time functions that are called when we regress to a prior state
        # Useful for passing data between states
        if self.on_regress:
            self.on_regress()
            self.on_regress = None
        pass

    def render(self):
        """Render the state"""
        pass

class StateSetup(State):
    """State for parsing or loading a database"""
    def __init__(self, stdscr):
        super().__init__(stdscr)
        self.database = None

    def update(self):
        """Update the state"""
        super().update()
        pass

    def render(self):
        """Render the state"""
        super().render()
        pass

    def create_database(self, html_filepath, db_path='bookmarks.db'):
        """Create a new database"""
        # Parse the bookmarks
        bookmarks, failures = parse(html_filepath)
        if len(failures) > 0:
            logging.warning(f'Bookmarks folders failed to parse: {failures}')
        else:
            logging.info('Bookmarks parsed successfully')

        self.database = Database(db_path=db_path)
        self.database.export_bookmarks(bookmarks)
        # Establish the database connection
        self.database.load_database()

    def load_database(self, db_path='bookmarks.db'):
        """Load an existing database"""
        self.database = Database(db_path=db_path)
        self.database.load_database()

class StateSelectBookmarksFile(State):
    """State for selecting a bookmarks .html file
    Used for creating a new database"""
    def __init__(self, stdscr):
        super().__init__(stdscr)
        self.filepath = None

    def update(self):
        """Update the state"""
        super().update()
        pass

    def render(self):
        """Render the state"""
        super().render()
        pass
