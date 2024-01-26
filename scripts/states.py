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
from scripts.scraping_utils import main as scrape_data
from scripts.scraping_utils import get_null_description_bookmarks

# BUG: Trying to load as list of bookmarks by tag now crshes with an out of bounds error for some reason lol I am a bad programmer and I should feel bad
# Seriously it was working this morniung and now it's broken fml

# TODO: a by="tag" method for bookmark viewer state

# TODO: Implement the search function (by title, url, folder, date added, etc)
# TODO: Can add a menu with a number next to it to show results like categories (3)
# TODO: Query the database for the search results and pass them to a new state

# TODO: Setup page_content scraping in the build database state
# TODO: We can go to another state because it might take a while and we should track progress

# TODO: Build recommender engine using cosine similarity

# TODO: We'll add a state for this and it'll have a nice progress bar and shit like that, it'll be cool
# TODO: The scraping utils does everything but we should do it one at a time so we can show a progress bar using a for loop

# TODO: I dunno setup an option so we can browse from Lynx or something

# BUG: Trying to explore bookmarks without a database crashes the program
# BUG: Probably same thing happens trying to generate descriptions and tags

# Some semantical sugar
state_history = []

# Globals
database = None
month_names = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December"
}

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
                    logging.warning(f"Menu function failed to perform")
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
        menu_items = ["Load Bookmarks Database", "Build Bookmarks Database", "Generate Bookmark Descriptions and Tags", "Exit"]
        menu_functions = [
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkExplorerIndex),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateSelectBookmarksFile),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateGenerateDescriptionsAndTags),
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
        menu_items = ["Random Bookmark", "View By Category", "View By Date Added", "View By Tag", "Search", "Back"]
        menu_functions = [
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkViewer, args=[self.random_bookmark()]),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkExplorerByCategory),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkExplorerByYear),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkExplorerByTag),
            MenuFunction(FunctionType.ADVANCE_STATE, state=StateExit),
            MenuFunction(FunctionType.REGRESS_STATE)
            ]

        self.menu = Menu(self.stdscr, menu_items, menu_functions, "Google Chrome Bookmarks Explorer")

    def random_bookmark(self):
        """Select a random bookmark"""
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
        menu_functions = [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarksList, args=[database.get_bookmarks_by_category(category[0]), f"{category[0]} Bookmarks", "category"]) for category in categories]

        # Add on the back option
        menu_items.append("Back")
        menu_functions.append(MenuFunction(FunctionType.REGRESS_STATE))

        self.menu = MenuList(self.stdscr, menu_items, menu_functions, "Bookmarks by Category")

class StateBookmarkExplorerByTag(State):
    """Display each tag as a menu item"""
    def __init__(self, stdscr):
        super().__init__(stdscr)
        tags = database.get_all_tags()
        menu_items = [tag for tag in tags]
        meun_functions = [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarksList, args=[database.get_bookmarks_by_tag(tag), f"Bookmarks with tag {tag}", "tag"]) for tag in tags]

        # Back option
        menu_items.append("Back")
        meun_functions.append(MenuFunction(FunctionType.REGRESS_STATE))

        self.menu = MenuList(self.stdscr, menu_items, meun_functions, "Bookmarks by Tag")

class StateBookmarkExplorerByYear(State):
    """Display every year as a menu item"""
    def __init__(self, stdscr):
        super().__init__(stdscr)

        # Get a list of all the years
        years = database.get_distinct_years()
        # Create a list menu from the years
        menu_items = [year for year in years]
        # Functions are just advance state to the bookmark list state
        menu_functions = [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkExplorerByMonth, args=[year]) for year in years]

        # Append a back option
        menu_items.append("Back")
        menu_functions.append(MenuFunction(FunctionType.REGRESS_STATE))

        # Create the list menu
        self.menu = MenuList(self.stdscr, menu_items, menu_functions, "Bookmarks by Year")

class StateBookmarkExplorerByMonth(State):
    """Display all months within a year as a menu item"""
    def __init__(self, stdscr, year):
        global month_names
        super().__init__(stdscr)
        self.year = year

        # We can get all the distinct months in a year
        months = database.get_distinct_months(year)

        # Now make our menu
        menu_items = [month_names[month] for month in months]

        # Functions are just advance state to the bookmark list state
        menu_functions = [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarksList, args=[database.get_bookmarks_by_year_month(self.year, month), f"Bookmarks {month_names[month]} {year}", "month"]) for month in months]

        # Append the back option
        menu_items.append("Back")
        menu_functions.append(MenuFunction(FunctionType.REGRESS_STATE))

        # Create the menu
        self.menu = MenuList(self.stdscr, menu_items, menu_functions, "Bookmarks by Month")

class StateBookmarksList(State):
    """Display a list of bookmarks that are passed to the state"""
    def __init__(self, stdscr, bookmarks, menu_title="Remember to set a title", by="category"):
        super().__init__(stdscr)
        logging.info("Initialising StateBookmarksList")
        # Bookmarks should be passed as a list of bookmark object
        self.bookmarks = bookmarks
        # Here we will create a list menu from the bookmarks - also include a randomise option at the top
        menu_items = ["Randomise"] + [bookmark.title for bookmark in self.bookmarks]
        category = self.bookmarks[0].folder
        logging.info(f"Category: {category}")

        # Set restrictions based on by attribute
        restrictions = None
        if by == "category":
            restrictions = f"folder = \"{category}\""
        elif by == "month":
            # Get the year and month from the first bookmark (they should all be the same)
            restrictions = f"strftime('%Y', add_date) = '{self.bookmarks[0].year}' AND strftime('%m', add_date) = '{self.bookmarks[0].month}'"
        elif by == "tag":
            # We can actually extract the tag from the menu title which is a bit stupid but whatever
            tag = menu_title.split(' ')[-1]
            logging.info(f"Tag: {tag}")
            restrictions = f"tags LIKE '%{tag}%'"

        menu_functions = [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkViewer, args=[self.random_bookmark(), True, restrictions])]
        # Disable randomisation for viewing a single bookmark
        menu_functions += [MenuFunction(FunctionType.ADVANCE_STATE, state=StateBookmarkViewer, args=[bookmark, False]) for bookmark in self.bookmarks]

        # If there's only one bookmark in the bookmarks list pop off the randomise option
        if len(self.bookmarks) == 1:
            menu_items.pop(0)
            menu_functions.pop(0)

        # Add the back option
        menu_items.append("Back")
        menu_functions.append(MenuFunction(FunctionType.REGRESS_STATE))

        self.menu = MenuList(self.stdscr, menu_items, menu_functions, menu_title)

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
        logging.info("Walking current directory")
        logging.info(f"Current directory: {os.getcwd()}")
        for path, dir, files in os.walk(os.getcwd()):
            # Save the filename and path to the dictionary
            if len(files) != 0:
                for file in files:
                    if file.endswith('.html'):
                        self.html_files[file] = os.path.join(path, file)

        # Sort the dictionary by key, reverse=True for descending order
        # Should show most recent bookmarks first by Chrome's naming convention
        self.html_files = dict(sorted(self.html_files.items(), reverse=True))

        menu_options = list(self.html_files.keys()) + ["Delete database", "Exit"]
        menu_functions = [MenuFunction(FunctionType.FUNCTION, self.select_file, [file]) for file in list(self.html_files.keys())]
        menu_functions += [MenuFunction(FunctionType.FUNCTION, self.delete_database), MenuFunction(FunctionType.REGRESS_STATE)]

        # Create a list style menu
        self.menu = MenuList(self.stdscr, menu_options, menu_functions, "Select Bookmarks File")
        logging.info("StateSelectBookmarksFile initialised")

        self.deleted_database_timer_max = 2
        self.deleted_database_timer = 0
        self.t = datetime.now()

    def delete_database(self):
        """Delete the database"""
        if self.database_exists():
            os.remove(os.path.join(os.getcwd(), 'bookmarks.db'))

        self.deleted_database_timer = self.deleted_database_timer_max
        self.t = datetime.now()

    def draw_deleted_message(self):
        """Draw a message to the screen when the database is deleted"""
        yy, xx = self.stdscr.getmaxyx()
        self.stdscr.addstr(int(yy/2), int(xx/2)-int(len("Database deleted successfully")/2), "Database deleted successfully", self.colours.get_colour('white_on_red') | curses.A_ITALIC)

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
        # Count down the timer if necessary
        if self.deleted_database_timer > 0:
            dt = datetime.now() - self.t
            self.deleted_database_timer -= dt.total_seconds()
            self.t = datetime.now()
            if self.deleted_database_timer <= 0:
                self.deleted_database_timer = 0
            return None

        return super().update()

    def render(self):
        """Render the state"""
        if self.html_files == {}:
            self.stdscr.addstr("No .html files found in current directory\n", self.colours.get_colour('red_on_black'))
        elif self.database_exists():
                self.stdscr.addstr("Database already exists, new bookmarks will be added to existing database\n", self.colours.get_colour('red_on_black'))

        super().render()

        if self.deleted_database_timer > 0:
            self.draw_deleted_message()
            self.stdscr.addstr("\n")

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

class StateGenerateDescriptionsAndTags(State):
    def __init__(self, stdscr):
        """State to generate descriptions and tags for the database"""
        super().__init__(stdscr)
        # Get the list of bookmarks to process
        self.bookmarks_to_process = get_null_description_bookmarks()
        self.bookmarks_processed = []
        self.bookmarks_total = len(self.bookmarks_to_process)
        self.failures = 0

    def update(self):
        """Update the state"""
        # We will go through the bookmarks to process and generate descriptions and tags
        try:
            # Pop the bookmark from the list and append it to the processed list
            # Do this first otherwise we'll get stuck on the same bookmark if we crash
            self.bookmarks_processed.append(self.bookmarks_to_process.pop(0))
            # Then scrape the data
            success = scrape_data(self.bookmarks_processed[-1])
            if not success:
                self.failures += 1
        except Exception as e:
            logging.warning("Failed to generate descriptions and tags")
            logging.warning(e)

        # Go back to the previous state if we're done
        if len(self.bookmarks_to_process) == 0:
            # Set the update function to regress to the previous state
            self.update_function = self.regress_state
            state_previous = state_history[-2]
            # This will set the on_regress callback
            self.update_function_args = [state_previous.on_db_update]

        return super().update()

    def draw_progress_bar(self, t_width, percentage_complete):
        """Draw a progress bar in [] brackets with # representing progress"""
        progress_count = int((t_width - 2) * int(percentage_complete[:-1]) / 100)
        self.stdscr.addstr("[", self.colours.get_colour('green_on_black') | curses.A_BOLD)
        self.stdscr.addstr("#" * progress_count, self.colours.get_colour('blue_on_black') | curses.A_BOLD)
        self.stdscr.addstr(" " * (t_width - 2 - progress_count), self.colours.get_colour('green_on_black') | curses.A_BOLD)
        self.stdscr.addstr("]", self.colours.get_colour('green_on_black') | curses.A_BOLD)


    def render(self):
        """Just draws some text"""
        _, t_width = self.stdscr.getmaxyx()
        self.stdscr.addstr("Generating descriptions and tags for the database\n", self.colours.get_colour('yellow_on_black') | curses.A_BOLD)
        self.stdscr.addstr("This may take a while\n", self.colours.get_colour('red_on_black') | curses.A_BOLD)
        self.stdscr.addstr("Here is a picture of a cat\n", self.colours.get_colour('green_on_black') | curses.A_BOLD)
        self.stdscr.addstr("=^._.^= ∫\n", self.colours.get_colour('white_on_black') | curses.A_BOLD)
        self.stdscr.addstr("\n")

        # Now we can draw a progress bar
        percentage_complete = int((self.bookmarks_total - len(self.bookmarks_to_process)) / self.bookmarks_total * 100)
        percentage_complete = str(percentage_complete) + "%"
        # Draw the percentage centred in green
        padding_left = int(t_width/2)-int(len(percentage_complete)/2)
        self.stdscr.addstr(" " * padding_left + percentage_complete, self.colours.get_colour('green_on_black') | curses.A_BOLD)
        self.stdscr.addstr("\n")
        self.draw_progress_bar(t_width, percentage_complete)

        # Display how many successes and failures we've had
        self.stdscr.addstr("\n")
        self.stdscr.addstr("\n")
        self.stdscr.addstr(f"Successes: {self.bookmarks_total - len(self.bookmarks_to_process) - self.failures}\n", self.colours.get_colour('green_on_black') | curses.A_BOLD)
        self.stdscr.addstr(f"Failures: {self.failures}\n", self.colours.get_colour('red_on_black') | curses.A_BOLD)

        super().render()

class StateBookmarkViewer(State):
    """View details of a single bookmark"""
    def __init__(self, stdscr, bookmark, randomise=True, restrictions=None):
        logging.info("Initialising StateBookmarkViewer")
        super().__init__(stdscr)
        # This is a tuple of the bookmark data
        self.bookmark = bookmark
        self.restrictions = restrictions
        self.randomise = randomise

        # Set up a menu which will allow us to go back or open the bookmark
        menu_items = ["Open Bookmark", "Randomise", "Back"]
        # Set on_regress for prior state
        prev_state = state_history[-2]
        menu_functions = [
            MenuFunction(FunctionType.FUNCTION, self.open_bookmark),
            MenuFunction(FunctionType.FUNCTION, self.get_random_bookmark),
            MenuFunction(FunctionType.REGRESS_STATE, args=[prev_state.reroll_random_bookmark])
            ]

        # We can turn randomise off if we want
        if not self.randomise:
            # Just pop out value 1
            # Yes this is bad practice but also fuck off
            menu_items.pop(1)
            menu_functions.pop(1)

        self.menu = Menu(self.stdscr, menu_items, menu_functions, "Bookmark Viewer", position="bottom")

        # Find tags and description
        self.tags = database.get_tags(self.bookmark.id)
        self.description = database.get_description(self.bookmark.id)

    def get_random_bookmark(self):
        """Get a new random bookmark"""
        new_bookmark = database.get_random_bookmark(restrictions=self.restrictions)
        timeout = 100
        # We'll try loop until we get a new bookmark that isn't the same as the current one
        # Timeout incase I fuck anything up
        while new_bookmark.get_attributes() == self.bookmark.get_attributes() and timeout > 0:
            new_bookmark = database.get_random_bookmark(restrictions=self.restrictions)
            timeout -= 1

        if timeout == 0:
            logging.info("Failed to get a unique random bookmark, which seems pretty unlikely")

        self.bookmark = new_bookmark

        # Find tags and description
        self.tags = database.get_tags(self.bookmark.id)
        self.description = database.get_description(self.bookmark.id)

    def open_bookmark(self):
        """Open the bookmark"""
        webbrowser.open(self.bookmark.url)

    def render_bookmark(self, bookmark):
        """Draws the bookmark details"""
        # Draw the bookmark details
        self.stdscr.addstr(f"Category: {bookmark.folder}\n", self.colours.get_colour('green_on_black') | curses.A_BOLD)
        self.stdscr.addstr(f"Title: {bookmark.title}\n", self.colours.get_colour('yellow_on_black') | curses.A_BOLD)
        # Description if we have one
        if self.description:
            self.stdscr.addstr(f"Description: {self.description}\n", self.colours.get_colour('magenta_on_black') | curses.A_BOLD)
        self.stdscr.addstr(f"Date added: {bookmark.add_date_formatted}\n", self.colours.get_colour('blue_on_black') | curses.A_BOLD)
        # This isn't THAT useful so I'll miss it out, also sometimes it's wrong or blank or unknown
        # self.stdscr.addstr(f"Domain: {bookmark.domain}\n", self.colours.get_colour('cyan_on_black') | curses.A_BOLD)
        self.stdscr.addstr(f"URL: {bookmark.url}\n", self.colours.get_colour('white_on_black') | curses.A_BOLD)

        # Render tags
        if self.tags:
            self.stdscr.addstr(f"Tags: {', '.join(self.tags.split(','))}\n", self.colours.get_colour('cyan_on_black') | curses.A_BOLD)



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
