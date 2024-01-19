import curses
import logging
import os
import atexit
from enum import Enum
from scripts.database_utils import Database
from scripts.chrome_bookmarks_parser import parse
from scripts.components import Menu, MenuList
from scripts.colours import Colours

# Some semantical sugar
state_history = []

# Globals
database = None

# Register cleanup function
@atexit.register
def cleanup():
    """Shutdown the database"""
    if database:
        database.close_database()

# Enums
class FunctionType(Enum):
    """Types of menu functions"""
    ADVANCE_STATE = 1
    REGRESS_STATE = 2
    FUNCTION = 3

# Class for defining menu functions
class MenuFunction():
    """Base class for menu functions
    Define function type from enum
    If type is FUNCTION then pass a function to the function argument along with any args
    If type is ADVANCE_STATE then pass a state to the state argument
    If type is REGRESS_STATE then nothing is needed other than the type"""
    def __init__(self, function_type, function=None, args=None, state=None):
        self.type = function_type
        self.function = function
        self.args = args
        self.state = state

class State():
    """Base class for all states"""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        # Add the state to the history
        global state_history
        state_history.append(self)
        # Callbacks for when we regress to a prior state
        self.on_regress = None
        # Set menu to None by default
        self.menu = None

        # Set up colours
        self.colours = Colours()

    def update(self):
        """Update the state"""
        # These are one time functions that are called when we regress to a prior state
        # Useful for passing data between states
        if self.on_regress:
            self.on_regress()
            self.on_regress = None

        if self.menu:
            callback = self.menu.update()
            if callback:
                logging.info(f"Menu function called: {callback}")
                logging.info(f"Menu function type: {callback.type}")
                logging.info(f"Caller: {self.__class__.__name__}")
                try:
                    return self.perform_menu_function(callback)
                except Exception as e:
                    logging.warning(f"Menu function failed to perform: {callback}")
                    logging.warning(e)
                    exit(1)

    def perform_menu_function(self, function):
        """Perform a menu function"""
        # Check the function type
        if function.type == FunctionType.ADVANCE_STATE:
            # Advance to the new state
            if not function.args:
                function.args = []
            return self.advance_state(function.state, function.args)
        elif function.type == FunctionType.REGRESS_STATE:
            # Regress to the previous state
            return self.regress_state()
        elif function.type == FunctionType.FUNCTION:
            # Call the function
            function.function(*function.args)
            return None

    def render(self):
        """Render the state"""
        # Draw menu if it exists
        if self.menu:
            self.menu.render()
        pass

    def advance_state(self, state, args=[]):
        """Advance to a new state"""
        # This just needs to return state, logic is handled in update() to pass the new state to the main loop
        # Create new state object
        return state(self.stdscr, *args)

    def regress_state(self, on_regress=None):
        """Regress to the previous state"""
        global state_history
        # Remove the current state
        state_history.pop()
        # Get the previous state
        state = state_history[-1]
        # Set the callback for when we regress
        state.on_regress = on_regress
        return state

class StateSetup(State):
    """State for parsing or loading a database"""
    def __init__(self, stdscr):
        logging.info("Initialising StateSetup")
        super().__init__(stdscr)
        # Create a blank menu for now
        menu_items = ["Build Bookmarks Database", "Load Bookmarks Database", "Exit"]
        menu_functions = [
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateSelectBookmarksFile),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateExit),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateExit)
            ]
        self.menu = Menu(self.stdscr, menu_items, menu_functions)

    def update(self):
        """Update the state"""
        return super().update()
        pass

    def render(self):
        """Render the state"""
        super().render()
        pass

class StateSelectBookmarksFile(State):
    """State for selecting a bookmarks .html file
    Used for creating a new database"""
    def __init__(self, stdscr):
        super().__init__(stdscr)
        self.stdscr = stdscr
        self.filepath = None

        # Get a list of all .html files in the current directory
        # Also crawl subdirectories
        self.html_files = {}
        for path, dir, files in os.walk('.'):
            # Save the filename and path to the dictionary
            if len(files) > 0:
                for file in files:
                    if file.endswith('.html'):
                        self.html_files[file] = os.path.join(path, file)


        menu_options = list(self.html_files.keys()) + ["Exit"]
        menu_functions = [MenuFunction(FunctionType.FUNCTION, self.select_file, [file]) for file in list(self.html_files.keys())] + [MenuFunction(FunctionType.REGRESS_STATE)]

        # Create a list style menu
        self.menu = MenuList(self.stdscr, menu_options, menu_functions)
        logging.info("StateSelectBookmarksFile initialised")

    def select_file(self, file):
        """Create a database from the selected file"""
        self.filepath = self.html_files[file]

        # Create the database
        self.create_database(self.filepath)

    def update(self):
        return super().update()

    def render(self):
        """Render the state"""
        if self.html_files == {}:
            self.stdscr.addstr("No .html files found in current directory", self.colours.get_colour('red_on_black'))
        else:
            if self.database_exists():
                self.stdscr.addstr("Database already exists, it will be overwritten if you build a new database\n", self.colours.get_colour('red_on_black'))
            self.stdscr.addstr("Select a bookmarks file", self.colours.get_colour('white_on_black'))

        self.stdscr.addstr("\n")

        super().render()

    def create_database(self, html_filepath, db_path='bookmarks.db'):
        """Create a new database"""
        global database
        # Parse the bookmarks
        bookmarks, failures = parse(html_filepath)
        if len(failures) > 0:
            logging.warning(f'Bookmarks folders failed to parse: {failures}')
        else:
            logging.info('Bookmarks parsed successfully')

        self.database = Database(db_path=db_path)
        self.database.export_bookmarks(bookmarks)
        # Establish the database connection
        self.database.open_database()

        # Make the database globally accessible
        database = self.database

    def database_exists(self, db_path='bookmarks.db'):
        """Check if a database exists"""
        return os.path.isfile(os.path.join(os.getcwd(), db_path))

class StateExit(State):
    """State for exiting the program"""
    def __init__(self, stdscr):
        logging.info("Exiting via StateExit")
        exit(1)
