import curses
from scripts.colours import Colours

class Menu():
    def __init__(self, stdscr, items, functions, menu_title='Menu'):
        """Initialise the menu"""
        # Define the menu items and selection
        self.menu_title = menu_title
        self.items = items
        self.functions = functions
        self.selected = 0

        # Use items to determine the width and height of the menu
        self.width = max([len(item) for item in self.items]) + 4
        self.height = len(self.items) + 4

        # Set up colours
        self.colours = Colours()

        # Create a new window
        self.window = curses.newwin(self.height, self.width, 0, 0)

        # Set the window to white on blue
        self.window.bkgd(' ', Colours().get_colour('white_on_blue'))

    def render(self):
        """Render the menu"""
        # Clear the window
        self.window.clear()

        # Draw the border
        self.window.border()

        # Draw the title
        self.window.addstr(0, 2, self.menu_title, self.colours.get_colour('white_on_blue'))

        # Draw the items
        for index, item in enumerate(self.items):
            offset = round((self.width - len(item)) * 0.5)
            if index == self.selected:
                self.window.addstr(index + 2, offset, item, self.colours.get_colour('white_on_black'))
            else:
                self.window.addstr(index + 2, offset, item)

        # Refresh the window
        self.window.refresh()
