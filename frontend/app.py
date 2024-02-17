import os
import firebase_admin
from datetime import datetime
from firebase_admin import credentials, firestore
from random import choice
from jinja2 import Environment
from flask import Flask, render_template, request, redirect, url_for

# Setup Firebase Admin SDK
cred = credentials.Certificate(os.environ.get("SERVICE_WORKER"))
firebase_admin.initialize_app(cred)

# Get a reference to the Firestore database
db = firestore.client()


# Create the Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

# Define custom filters
def get_max(a, b):
    return max(a, b)

def get_min(a, b):
    return min(a, b)

# Register custom filters with Jinja2 environment
app.jinja_env.filters['max'] = get_max
app.jinja_env.filters['min'] = get_min


# Function definitions
def get_all_bookmarks():
    collection_ref = db.collection("data")
    docs = collection_ref.stream()

    # Put the data into a list
    data = []
    for doc in docs:
        data.append(doc.to_dict())

    # Sort data by date with most recent first
    data.sort(key=lambda x: datetime.strptime(x['add_date'], '%Y-%m-%d %H:%M:%S'), reverse=True)

    return data

def get_all_categories(bookmarks):
    """Loop through the bookmarks and get all unique categories."""
    categories = set()
    for bookmark in bookmarks:
        categories.add(bookmark['folder'])

    # Sort
    categories = list(categories)
    categories = sorted(categories)
    return categories

def get_all_tags(bookmarks):
    """Loop through the bookmarks and get all unique tags."""
    tags = set()
    for bookmark in bookmarks:
        if bookmark['tags']:
            tags.update(bookmark['tags'])

    # Sort
    tags = list(tags)
    tags = sorted(tags)

    return tags

def get_by(bookmarks, key, value):
    """Get all bookmarks with a certain value in their key"""
    # Check if the key contains a list or a string
    type_of = type(bookmarks[0][key])
    if type_of == list:
        return [b for b in bookmarks if value in b[key]]
    else:
        return [b for b in bookmarks if b[key] == value]

# Globals
bookmarks = get_all_bookmarks()
unique_categories = get_all_categories(bookmarks)
unique_tags = get_all_tags(bookmarks)
PER_PAGE = 10

# TODO: Randomiser uses queries


def get_bookmarks_page_details(bookmarks):
    """Create a page of bookmarks from a list of bookmarks."""
    page = int(request.args.get('page', 1))

    start_index = (page - 1) * PER_PAGE
    end_index = start_index + PER_PAGE

    # Slice the list of bookmarks to get the current page
    current_bookmarks = bookmarks[start_index:end_index]

    # Calculate total number of pages
    total_pages = (len(bookmarks) + PER_PAGE - 1) // PER_PAGE

    return current_bookmarks, page, total_pages

# Define the index route
@app.route('/')
def index():
    global bookmarks

    current_bookmarks, page, total_pages = get_bookmarks_page_details(bookmarks)

    # Render the template
    return render_template('html/bookmarks.html', bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by category
@app.route('/categories')
def categories():
    global unique_categories, bookmarks

    # Query for all bookmarks in the category ordered by date IF we have a category parameter
    category = request.args.get('category', None)
    current_bookmarks = []
    page = 1
    total_pages = 1
    if category:
        category_bookmarks = get_by(bookmarks, 'folder', category)

        current_bookmarks, page, total_pages = get_bookmarks_page_details(category_bookmarks)

    # Render the template
    return render_template('html/categories.html', category=category, categories=unique_categories, bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by tag
@app.route('/tags')
def tags():
    global unique_tags, bookmarks

    tag = request.args.get('tag', None)
    current_bookmarks = []
    page = 1
    total_pages = 1
    if tag:
        tag_bookmarks = get_by(bookmarks, 'tags', tag)

        current_bookmarks, page, total_pages = get_bookmarks_page_details(tag_bookmarks)

    # Render the template
    return render_template('html/tags.html', tag=tag, tags=unique_tags, bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by bookmark
@app.route('/bookmarks/<bookmark_id>')
def bookmark(bookmark_id):
    global bookmarks
    # Get the bookmark with the given ID
    bookmark = get_by(bookmarks, 'id', int(bookmark_id))
    return render_template('html/bookmark_viewer.html', bookmarks=bookmark, page=1, total_pages=1)

@app.route('/randomiser')
def randomiser():
    return render_template('html/randomiser.html', categories=unique_categories, tags=unique_tags)

@app.route('/random')
def random():
    global bookmarks
    # Params are category/tag or lucky
    category = request.args.get('category', None)
    tag = request.args.get('tag', None)
    lucky = request.args.get('lucky', None)

    bookmarks_pool = bookmarks
    if category:
        bookmarks_pool = get_by(bookmarks, 'folder', category)
    elif tag:
        bookmarks_pool = get_by(bookmarks, 'tags', tag)

    bookmark = choice(bookmarks_pool)
    bookmark = [bookmark]

    # Show the random page which is just the bookmark viewer page with a re-roll button at the bottom
    return render_template('html/random.html', bookmarks=bookmark, page=None, total_pages=1, random=True, category=category, tag=tag, lucky=lucky)
