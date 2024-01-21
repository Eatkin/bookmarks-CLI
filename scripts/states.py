import curses
import logging
import os
import atexit
import webbrowser
from random import choice
from datetime import datetime
from enum import Enum
from scripts.database_utils import Database
from scripts.chrome_bookmarks_parser import parse
from scripts.components import Menu, MenuList, Bookmark
from scripts.colours import Colours

# TODO: Add a 'dyanmic' position option to the menu which will appear centred in AVAILABLE space
# TODO: ^ Not useful for bookmark viewer cause we don't want it to jump around like seizure inducing
# TODO: Probably should allow escape to go back to the previous state
# TODO: ^ We can basically see if there's a back option in the menu and if so activate the associated function
# TODO: Reorder the main menu cause we probably want to view the database more than we want to build it
# TODO: Randomise in the bookmark viewer randomises ALL but should maybe have restrictions
# TODO: Should be able to pick random category
# TODO: Bookmarks list state should have a heading with the category name or whatever
# TODO: We already have a title for the menus so we can just use that and render differently in list style
# TODO: Make list style menu centre in available space (horizontally)

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
    def __init__(self, function_type, function=None, args=[], state=None):
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

        # update_function is a function that is called when the state is updated
        # We can set the value of update_function to a function that will be called (e.g. to regress to a prior state)
        # It can return a new state to switch to or None
        self.update_function = None
        self.update_function_args = []

        # Set up colours
        self.colours = Colours()

    def update(self):
        """Update the state"""
        # These are one time functions that are called when we regress to a prior state
        # Useful for passing data between states
        if self.on_regress:
            self.on_regress()
            self.on_regress = None

        if self.update_function:
            val = self.update_function(*self.update_function_args)
            self.update_function = None
            self.update_function_args = []
            if val:
                return val

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
            return self.advance_state(function.state, function.args)
        elif function.type == FunctionType.REGRESS_STATE:
            # Regress to the previous state
            return self.regress_state(*function.args)
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
        old_state = state_history.pop()
        # Delete it
        del old_state
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
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkExplorerIndex),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateExit)
            ]
        self.menu = Menu(self.stdscr, menu_items, menu_functions, "Google Chrome Bookmarks Explorer")

        self.display_message = None
        self.timer_max = 3
        self.timer = 0
        self.t = datetime.now()

    def update(self):
        """Update the state"""
        # Update timer if necessary
        if self.timer > 0:
            dt = datetime.now() - self.t
            self.timer -= dt.total_seconds()
            self.t = datetime.now()
            if self.timer <= 0:
                self.display_message = None

        return super().update()


    def render(self):
        """Render the state"""
        # Display a message if necessary
        if self.display_message:
            self.stdscr.addstr(self.display_message, self.colours.get_colour('yellow_on_black') | curses.A_ITALIC)
            self.stdscr.addstr("\n")

        super().render()


    def on_db_update(self):
        """Callback for when the database is updated - used to display a message to the user"""
        self.timer = self.timer_max
        self.t = datetime.now()
        self.display_message = "Database updated successfully"

class StateBookmarkExplorerIndex(State):
    """This state will load the database and display a menu for exploring bookmarks
    It will give the user options for viewing bookmarks by folder, date added, etc
    It should also check if the database exists and if not, throw an error"""
    def __init__(self, stdscr):
        """Open database connection if it isn't already open"""
        super().__init__(stdscr)

        global database

        if not database:
            database = Database()
            # Check if database exists
            if not database.database_exists():
                # Do something
                pass

            # Open the database if it isn't already open
            if not database.database_is_connected():
                database.open_database()

        # Create our menu which should display our options for viewing bookmarks
        # We'll start with a random and a back option
        menu_items = ["Random Bookmark", "View By Category", "View By Date Added", "Search", "Back"]
        menu_functions = [
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkViewer, args=[self.random_bookmark()]),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkExplorerByCategory),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkExplorerByYear),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateExit),
            MenuFunction(FunctionType.REGRESS_STATE)
            ]

        self.menu = Menu(self.stdscr, menu_items, menu_functions, "Google Chrome Bookmarks Explorer")

    def random_bookmark(self):
        """Select a random bookmark"""
        logging.info("Getting random bookmark")
        result = database.get_random_bookmark()

        return result

    def reroll_random_bookmark(self):
        """Reroll the random bookmark"""
        logging.info("Rerolling random bookmark")
        # Update the menu function to use the new bookmark
        self.menu.functions[0].args[0] = self.random_bookmark()

class StateBookmarkExplorerByCategory(State):
    """Display each bookmark category as a menu item"""
    def __init__(self, stdscr):
        super().__init__(stdscr)
        categories = database.get_categories()
        # Unpack the tuples
        menu_items = [category[0] for category in categories]
        # Functions are just advance state to the bookmark list state
        menu_functions = [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarksList, args=[database.get_bookmarks_by_category(category[0])]) for category in categories]

        # Add on the back option
        menu_items.append("Back")
        menu_functions.append(MenuFunction(FunctionType.REGRESS_STATE))

        self.menu = MenuList(self.stdscr, menu_items, menu_functions, "Bookmarks by Category")


# WIP
class StateBookmarkExplorerByYear(State):
    """Display every year as a menu item"""
    def __init__(self, stdscr):
        super().__init__(stdscr)
        # Here we will get all the years from the database
        # Then create a list menu from it

# WIP
class StateBookmarkExplorerByMonth(State):
    """Display all bookmarks in a certain month and year"""
    def __init__(self, stdscr, year, month):
        super().__init__(stdscr)
        self.year = year
        self.month = month
        # Here we will get all the bookmarks in the month and year via query to the database
        # Then create a list menu from it

# WIP
class StateBookmarksList(State):
    """Display a list of bookmarks that are passed to the state"""
    def __init__(self, stdscr, bookmarks):
        super().__init__(stdscr)
        # Bookmarks should be passed as a list of bookmark object
        self.bookmarks = bookmarks
        # Here we will create a list menu from the bookmarks - also include a randomise option at the top
        menu_items = ["Randomise"] + [bookmark.title for bookmark in self.bookmarks]
        menu_functions = [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkViewer, args=[self.random_bookmark()])]
        menu_functions += [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkViewer, args=[bookmark]) for bookmark in self.bookmarks]

        # Add the back option
        menu_items.append("Back")
        menu_functions.append(MenuFunction(FunctionType.REGRESS_STATE))

        self.menu = MenuList(self.stdscr, menu_items, menu_functions, "Bookmarks List")

    def random_bookmark(self):
        """Get a new random bookmark"""
        # Update the menu function to use the new bookmark
        return choice(self.bookmarks)

    def reroll_random_bookmark(self):
        """Reroll the random bookmark"""
        self.menu.functions[0].args[0] = self.random_bookmark()


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

        # Set the update function to regress to the previous state
        self.update_function = self.regress_state
        state_previous = state_history[-2]
        # This will set the on_regress callback
        self.update_function_args = [state_previous.on_db_update]

    def update(self):
        return super().update()

    def render(self):
        """Render the state"""
        if self.html_files == {}:
            self.stdscr.addstr("No .html files found in current directory", self.colours.get_colour('red_on_black'))
        else:
            if self.database_exists():
                self.stdscr.addstr("Database already exists, it will be overwritten if you build a new database\n", self.colours.get_colour('red_on_black'))
            self.stdscr.addstr("Select a bookmarks file to build the database from", self.colours.get_colour('white_on_black'))

        self.stdscr.addstr("\n")

        super().render()

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


    def database_exists(self, db_path='bookmarks.db'):
        """Check if a database exists"""
        return os.path.isfile(os.path.join(os.getcwd(), db_path))

class StateBookmarkViewer(State):
    """View details of a single bookmark"""
    def __init__(self, stdscr, bookmark):
        logging.info("Initialising StateBookmarkViewer")
        super().__init__(stdscr)
        # This is a tuple of the bookmark data
        self.bookmark = bookmark

        # Set up a menu which will allow us to go back or open the bookmark
        menu_items = ["Open Bookmark", "Randomise", "Back"]
        # Set on_regress for prior state
        prev_state = state_history[-2]
        menu_functions = [
            MenuFunction(FunctionType.FUNCTION, self.open_bookmark),
            MenuFunction(FunctionType.FUNCTION, self.get_random_bookmark),
            MenuFunction(FunctionType.REGRESS_STATE, args=[prev_state.reroll_random_bookmark])
            ]

        self.menu = Menu(self.stdscr, menu_items, menu_functions, "Bookmark Viewer", position="bottom")

    def get_random_bookmark(self):
        """Get a new random bookmark"""
        self.bookmark = database.get_random_bookmark()

    def open_bookmark(self):
        """Open the bookmark"""
        webbrowser.open(self.bookmark[2])

    def render_bookmark(self, bookmark):
        """Draws the bookmark details"""
        # Draw the bookmark details
        self.stdscr.addstr(f"Category: {bookmark.folder}\n", self.colours.get_colour('green_on_black') | curses.A_BOLD)
        self.stdscr.addstr(f"Title: {bookmark.title}\n", self.colours.get_colour('yellow_on_black') | curses.A_BOLD)
        self.stdscr.addstr(f"Date added: {bookmark.add_date_formatted}\n", self.colours.get_colour('blue_on_black') | curses.A_BOLD)
        # This isn't THAT useful so I'll miss it out, also sometimes it's wrong or blank or unknown
        # self.stdscr.addstr(f"Domain: {bookmark.domain}\n", self.colours.get_colour('cyan_on_black') | curses.A_BOLD)
        self.stdscr.addstr(f"URL: {bookmark.url}\n", self.colours.get_colour('white_on_black') | curses.A_BOLD)



    def render(self):
        """Render bookmark details"""
        self.render_bookmark(self.bookmark)

        # Render menu
        super().render()

class StateExit(State):
    """State for exiting the program"""
    def __init__(self, stdscr):
        logging.info("Exiting via StateExit")
        exit(1)
