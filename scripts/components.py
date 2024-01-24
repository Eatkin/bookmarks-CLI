import curses
import logging
from scripts.colours import Colours
from math import floor, ceil
from datetime import datetime
import re

# A regex pattern for extracting the domain from a url
url_pattern = re.compile(r'(?:\w+)?(?:\://)?(?:w{3}\.)?([\w\d\._-]+)/?.*$')


class Menu():
    def __init__(self, stdscr, items, functions, menu_title='Menu', position="top"):
        """Initialise the menu"""
        # Define the menu items and selection
        self.menu_title = menu_title
        self.items = items
        self.functions = functions
        self.selected = 0

        # Use items to determine the width and height of the menu

        self.width = max([len(item) for item in self.items + [self.menu_title if self.menu_title else ""]]) + 4
        self.height = len(self.items) + 4
        self.h_padding = 4
        self.v_padding = 1
        # Add on the padding
        self.width += self.h_padding

        self.position = position

        # Set up colours
        self.colours = Colours()

        # Define scr
        self.stdscr = stdscr

        # Scroll behaviour (wrap or scroll)
        self.scroll_behaviour = 'wrap'

        # Min will be 2 but this will get updated in render
        self.menu_title_height = 2
        self.offset = 0

    def update(self):
        """Get keyboard input to navigate the menu,"""
        # Clear inputs
        self.stdscr.nodelay(True)
        key = self.stdscr.getch()
        vinput = 0
        if key == curses.KEY_UP:
            vinput -= 1
        if key == curses.KEY_DOWN:
            vinput += 1

        # Update the selected item
        self.selected += vinput

        # scrolling behaviour
        if self.scroll_behaviour == 'wrap':
            self.selected = self.wrap(self.selected, 0, len(self.items) - 1)
        elif self.scroll_behaviour == 'scroll':
            self.offset, self.selected = self.scroll(self.offset, self.selected, 0, len(self.items) - 1)

        # Check for enter key
        if key == curses.KEY_ENTER or key in [10, 13]:
            # Return the function for the state to call
            return self.functions[self.selected]

        return None

    def clamp(self, n, min, max):
        """Clamp a number between min and max"""
        if n < min:
            return min
        elif n > max:
            return max
        else:
            return n

    def wrap(self, selection, min, max):
        """Wrap a number between min and max"""
        if selection < min:
            return max
        elif selection > max:
            return min
        else:
            return selection

    def scroll(self, scroll, selection, min, max):
        """Scroll a number between min and max"""
        # Clamp selection
        selection = self.clamp(selection, min, max)

        # Adjust scroll if needed
        height, _ = self.stdscr.getmaxyx()

        if selection < scroll:
            scroll = selection
        elif selection >= scroll + height - 1 - self.menu_title_height:
            scroll += 1

        return scroll, selection

    def render(self):
        """Render the menu"""
        # Attributes
        t_height, t_width = self.stdscr.getmaxyx()
        col = self.colours.get_colour('white_on_blue')
        highlight_col = self.colours.get_colour('white_on_red')
        x = round((t_width - self.width) * 0.5)

        # Set y position based on position attribute
        if self.position == "top":
            y = round((t_height - self.height) * 0.25)
        elif self.position == "centre":
            y = round((t_height - self.height) * 0.5)
        elif self.position == "bottom":
            y = round((t_height - self.height) * 0.75)

        # Draw menu title (absolute fucking hell please god let me never have to touch this again)
        title_padding = (self.width - len(self.menu_title) - 2) // 2  # Padding on both sides
        title = f"+{'-' * title_padding}{self.menu_title}{'-' * title_padding}+"
        # Draw top vertical padding
        self.stdscr.addstr(y, x, title, col)
        for i in range(self.v_padding):
            self.stdscr.addstr(y + i + 1, x, "|" + " " * (self.width - 2) + "|", col)

        # Draw menu options
        for index, item in enumerate(self.items):
            # Define padding
            padding_left = (self.width - len(item) - 2) // 2
            padding_right = self.width - len(item) - padding_left - 2
            yy = y + index + self.v_padding + 1

            if index == self.selected:
                self.stdscr.addstr(yy, x, "| ", col)
                self.stdscr.addstr(yy, x + 2, f"{' '*(padding_left - 1)}{item}{' '*(padding_right + 1)}", highlight_col)
                self.stdscr.addstr(yy, x + self.width - 2, " |", col)
            else:
                item_str = f"|{' ' * padding_left}{item}{' ' * padding_right}|"
                self.stdscr.addstr(yy, x, item_str, col)

        # Draw bottom vertical padding
        for i in range(self.v_padding):
            self.stdscr.addstr(y + i + len(self.items) + self.v_padding + 1, x, "|" + " " * (self.width - 2) + "|", col)
        # Draw bottom border
        self.stdscr.addstr(y + len(self.items) + self.v_padding * 2 + 1, x, "+" + "-" * (self.width - 2) + "+", col)

class MenuList(Menu):
    """This is the same as menu with different rendering logic"""
    def __init__(self, stdscr, items, functions, menu_title='Menu'):
        super().__init__(stdscr, items, functions, menu_title)

        self.scroll_behaviour = 'scroll'

    def render(self):
        """Draw the list of menu items"""
        # Get terminal size
        t_height, t_width = self.stdscr.getmaxyx()

        dy = 0

        # First draw menu title
        if self.menu_title is not None:
            # Get the y pos
            y, x = self.stdscr.getyx()
            # Draw menu title in italic yellow
            col = self.colours.get_colour('yellow_on_black')
            xoffset = round((t_width - len(self.menu_title)) * 0.5)
            self.stdscr.addstr(" " * xoffset + self.menu_title, col | curses.A_ITALIC)
            self.stdscr.addstr("\n")
            # Draw a line under the title
            self.stdscr.addstr("." * t_width, col)
            dy = self.stdscr.getyx()[0] - y

            # Update menu title height
            self.menu_title_height = dy

        # Call the scroll function to adjust the scroll if needed
        self.offset, self.selected = self.scroll(self.offset, self.selected, 0, len(self.items) - 1)

        # We slice items based on the offset
        items_to_render = self.items[self.offset:self.offset + t_height - dy]
        # Draw the items - this will except if it goes out of bounds
        for index, item in enumerate(items_to_render):
            try:
                col = self.colours.get_colour('white_on_black')
                if index + self.offset == self.selected:
                    col = self.colours.get_colour('black_on_white')

                # Centre the item
                if len(item) < t_width:
                    xoffset = floor((t_width - len(item)) * 0.5)
                    self.stdscr.addstr(" " * xoffset)
                    self.stdscr.addstr(item, col)
                else:
                    try:
                        # We need to do string slicing to get the item to fit
                        # Split string and add one word at a time until we overflow the terminal
                        words = item.split(" ")
                        lines = [""]
                        lines_index = 0
                        for word in words:
                            if len(lines[lines_index]) + len(word) + 1 < t_width:
                                lines[lines_index] += word + " "
                            else:
                                # Cut the last space
                                lines[lines_index] = lines[lines_index][:-1]
                                lines_index += 1
                                lines.append(word + " ")

                        # Now we can draw the lines centred
                        for i, line in enumerate(lines):
                            xoffset = floor((t_width - len(line)) * 0.5)
                            self.stdscr.addstr(" " * xoffset)
                            self.stdscr.addstr(line, col)
                            if i < len(lines) - 1:
                                self.stdscr.addstr("\n")
                    except Exception as e:
                        logging.warning(f"Failed to draw item: {item}")
                        logging.warning(e)
                        break

                try:
                    self.stdscr.addstr("\n")
                except:
                    break
            except Exception as e:
                # In this case we've gone out of bounds so ensure selection is within bounds
                # I don't think this ever happens
                y, _ = self.stdscr.getyx()
                if y > t_height:
                    # This will adjust the scroll if needed
                    if index - self.offset - dy <= self.selected:
                        logging.debug(f"Adjusting scroll up by {y - t_height - dy}")
                        self.offset -= (y - t_height - dy)
                        self.stdscr.clear()
                        self.stdscr.refresh()
                        self.render()
                    break

class Bookmark():
    def __init__(self, record):
        """Initialise the bookmark"""
        self.id = record[0]
        self.title = record[1]
        self.url = record[2]
        self.add_date = record[3]
        self.folder = record[4]

        # Also some alternative formatting for the date
        self.add_date_formatted = datetime.strptime(self.add_date, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")

        # Format the URL to get the domain name (including subdomains)
        try:
            self.domain = ".".join(url_pattern.match(self.url).group(1).split('.')[:-1])
            # .co.uk domains will include the .co
            if self.domain.endswith(".co"):
                self.domain = self.domain[:-3]
        except:
            logging.warning(f"Failed to extract domain from url: {self.url}")
            self.domain = "Unknown"

        # We should add a year and month attribute for filtering
        self.year = self.add_date_formatted.split("/")[2]
        self.month = self.add_date_formatted.split("/")[1]

    def get_attributes(self):
        """Return a list of attributes"""
        return [self.title, self.url, self.add_date_formatted, self.folder]
