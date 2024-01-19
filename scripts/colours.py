import curses

class Colours():
    def __init__(self):
        # Define colour pairs
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(8, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(11, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        curses.init_pair(12, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(13, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
        curses.init_pair(14, curses.COLOR_WHITE, curses.COLOR_CYAN)

        # Save these to a dictionary
        self.colours = {
            'black_on_white': curses.color_pair(1),
            'white_on_black': curses.color_pair(2),
            'red_on_black': curses.color_pair(3),
            'green_on_black': curses.color_pair(4),
            'yellow_on_black': curses.color_pair(5),
            'blue_on_black': curses.color_pair(6),
            'magenta_on_black': curses.color_pair(7),
            'cyan_on_black': curses.color_pair(8),
            'white_on_red': curses.color_pair(9),
            'white_on_green': curses.color_pair(10),
            'white_on_yellow': curses.color_pair(11),
            'white_on_blue': curses.color_pair(12),
            'white_on_magenta': curses.color_pair(13),
            'white_on_cyan': curses.color_pair(14),
        }

    def get_colour(self, colour):
        """Returns a curses colour pair"""
        # Default to white on black
        return self.colours.get(colour, curses.color_pair(2))
