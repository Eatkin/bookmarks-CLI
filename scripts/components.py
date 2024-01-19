import curses
from scripts.colours import Colours
from math import floor, ceil

class Menu():
    def __init__(self, stdscr, items, functions, menu_title='Menu'):
        """Initialise the menu"""
        # Define the menu items and selection
        self.menu_title = menu_title
        self.items = items
        self.functions = functions
        self.selected = 0

        # Use items to determine the width and height of the menu
        self.width = max([len(item) for item in self.items + [self.menu_title]]) + 4
        self.height = len(self.items) + 4
        self.h_padding = 4
        self.v_padding = 1
        # Add on the padding
        self.width += self.h_padding

        # Set up colours
        self.colours = Colours()

        # Define scr
        self.stdscr = stdscr

    def update(self):
        """Get keyboard input to navigate the menu"""
        pass

    def render(self):
        """Render the menu"""
        # Attributes
        t_height, t_width = self.stdscr.getmaxyx()
        col = self.colours.get_colour('white_on_blue')
        highlight_col = self.colours.get_colour('white_on_red')
        x = round((t_width - self.width) * 0.5)
        # Add 1/4 of the height to the y position (looks better than central imo)
        y = round((t_height - self.height) * 0.25)

        # Draw menu title (absolute fucking hell please god let me never have to touch this again)
        title_padding = (self.width - len(self.menu_title) - 2) // 2  # Padding on both sides
        title = f"+{'-' * title_padding}{self.menu_title}{'-' * title_padding}+"
        # Draw top vertical padding
        self.stdscr.addstr(y, x, title, col)
        for i in range(self.v_padding):
            self.stdscr.addstr(y + i + 1, x, "|" + " " * (self.width - 2) + "|", col)

        # Draw menu options
        for index, item in enumerate(self.items):
            padding = (self.width - len(item) - 2) // 2  # Padding on both sides
            yy = y + index + self.v_padding + 1

            if index == self.selected:
                self.stdscr.addstr(yy, x, "|" + " ", col)
                padding = (self.width - len(item) - 4) // 2  # Padding on both sides
                self.stdscr.addstr(yy, x + 2, f"{' '*padding}{item}{' '*padding}", highlight_col)
                self.stdscr.addstr(yy, x + self.width - 2, " " + "|", col)
            else:
                item_str = f"|{' ' * padding}{item}{' ' * padding}|"
                self.stdscr.addstr(yy, x, item_str, col)

        # Draw bottom vertical padding
        for i in range(self.v_padding):
            self.stdscr.addstr(y + i + len(self.items) + self.v_padding + 1, x, "|" + " " * (self.width - 2) + "|", col)
        # Draw bottom border
        self.stdscr.addstr(y + len(self.items) + self.v_padding * 2 + 1, x, "+" + "-" * (self.width - 2) + "+", col)
