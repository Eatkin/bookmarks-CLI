# Google Chrome Bookmarks Explorer CLI

![Main Interface](https://github.com/Eatkin/bookmarks-CLI/blob/master/screens/main_interface.png?raw=true)

## Description

This utility is a command line interface based on Curses to parse your exported Google Chrome bookmarks and give you a means of exploring them by category or selecting random bookmarks to look at.

It aims to give a nice, user friendly interface to actually look at your bookmarks (I never look at mine and I'd like to).

There is functionality to generate tags and descriptions for your bookmarks.

Tags are based upon word frequency of scraped web pages and descriptions are based upon the meta description tag of the scraped web page. The tags and descriptions are not necessarily very good.

## Running From Source

### Requirements

* Built with Python 3.10.6
* Required packages are listed in `requirements.txt`
* (OPTIONAL) [Pyenv](https://github.com/pyenv/pyenv) for a virtual environment

### Using Make

1. Clone this repository
2. (OPTIONAL) Setup your virtual environment
3. `make all` will install required libraries
4. Run the CLI with `python main.py`

### Manually

1. Clone this repository
2. (OPTIONAL) Setup your virtual environment
3. Install required libraries with `pip install -r requirements.txt`
4. Run the CLI with `python main.py`

## Usage

* Run the CLI with `python main.py`
* You will need to provide an exported Google Chrome bookmarks file, it can be anywhere in the repository directory ([How to export bookmarks from Google Chrome](https://www.howtogeek.com/744989/how-to-export-chrome-bookmarks/))
* You will need to build the bookmarks database using the "Build Bookmarks Database" option in the main menu
* After building the bookmarks database you can use the "Load Bookmarks Database" option in the main menu to explore your bookmarks
* (Optional) You can generate tags and descriptions for your bookmarks using the "Generate Bookmark Descriptions and Tags" option in the main menu. This can be very slow. But there is a picture of a cat.

## Limitations

* Only parses bookmarks from Google Chrome
* This is based on a structure of bookmarks folders with NO subfolders

## TODO

* Add support for other browsers
* Add support for subfolders
* Add cosine similarity recommender system to suggest similar bookmarks
* Option to export bookmarks to a browsable HTML file instead of using the CLI

## Screenshots

![Bookmark Viewer](https://github.com/Eatkin/bookmarks-CLI/blob/master/screens/bookmark_viewer.png?raw=true)

![Generating Tags and Descriptions](https://github.com/Eatkin/bookmarks-CLI/blob/master/screens/loading_tags.png?raw=true)

![Viewing Bookmarks by Category](https://github.com/Eatkin/bookmarks-CLI/blob/master/screens/browse_by_category.png?raw=true)
