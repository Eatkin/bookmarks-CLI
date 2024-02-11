import sqlite3
import os
from random import choice
from jinja2 import Environment
from flask import Flask, render_template, request, redirect, url_for

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

# Get the database connection
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'bookmarks.db')
    conn = sqlite3.connect(db_path)
    query = """SELECT * FROM bookmarks
    JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
    ORDER BY strftime('%Y-%m-%d %H:%M:%S', bookmarks.add_date) DESC;"""
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor

def get_all_bookmarks():
    cursor = get_db_connection()
    return cursor.fetchall()

def execute_query(query):
    cursor = get_db_connection()
    cursor.execute(query)
    return cursor.fetchall()



PER_PAGE = 10

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
    bookmarks = get_all_bookmarks()

    current_bookmarks, page, total_pages = get_bookmarks_page_details(bookmarks)

    # Render the template
    return render_template('html/bookmarks.html', bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by category
@app.route('/categories')
def categories():
    # Query to get all unique categories
    query = """SELECT DISTINCT folder FROM bookmarks
    ORDER BY folder ASC;"""
    categories = execute_query(query)

    # Query for all bookmarks in the category ordered by date IF we have a category parameter
    category = request.args.get('category', None)
    current_bookmarks = []
    page = 1
    total_pages = 1
    if category:
        query = f"""SELECT * FROM bookmarks
        JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
        WHERE folder = '{category}'
        ORDER BY strftime('%Y-%m-%d %H:%M:%S', bookmarks.add_date) DESC;"""
        category_bookmarks = execute_query(query)

        current_bookmarks, page, total_pages = get_bookmarks_page_details(category_bookmarks)

    # Render the template
    return render_template('html/categories.html', category=category, categories=categories, bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by tag
@app.route('/tags')
def tags():
    query = """SELECT DISTINCT tags FROM bookmarks
    JOIN descriptions ON bookmarks.id = descriptions.bookmark_id;"""

    # The tags field contains 3 tags separated by commas so we need to create a set of all tags
    tags = set()
    for row in execute_query(query):
        if row[0]:
            tags.update(row[0].split(','))
    tags = list(tags)
    tags.sort()

    # Query for all bookmarks with the tag ordered by date IF we have a tag parameter
    # This is VERY similar to categories route so we could refactor this later
    # Going to move to firebase later so will all change anyway
    # Also this will eventually allow for multiple tags to be selected so we can filter by multiple tags
    tag = request.args.get('tag', None)
    current_bookmarks = []
    page = 1
    total_pages = 1
    if tag:
        query = f"""SELECT * FROM bookmarks
        JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
        WHERE tags LIKE '{tag},%' OR tags LIKE '%,{tag},%' OR tags LIKE '%,{tag}'
        ORDER BY strftime('%Y-%m-%d %H:%M:%S', bookmarks.add_date) DESC;"""
        tag_bookmarks = execute_query(query)

        current_bookmarks, page, total_pages = get_bookmarks_page_details(tag_bookmarks)

    # Render the template
    return render_template('html/tags.html', tag=tag, tags=tags, bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by bookmark
@app.route('/bookmarks/<bookmark_id>')
def bookmark(bookmark_id):
    # Get the bookmark info from the database
    query = f"""SELECT * FROM bookmarks
    JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
    WHERE bookmarks.id = {bookmark_id};"""
    result = execute_query(query)
    return f'This is the page for bookmark {bookmark_id} with info {result}'

@app.route('/random')
def random():
    # TODO: Set this up with some kind of form to select the restrictions
    # Then it gets passed to the bookmarks/<bookmark_id> route with URL parameters
    # From there we can re-randomise with the same restrictions

    # Params for year/month/tag/category so we can randomise with restrictions
    year = request.args.get('year', None)
    month = request.args.get('month', None)
    tag = request.args.get('tag', None)
    category = request.args.get('category', None)


    # If there's no args then just pick a random bookmark
    if not any([year, month, tag, category]):
        bookmarks = get_all_bookmarks()
        bookmark = choice(bookmarks)[0]
    else:
        # Construct a query
        query = """SELECT * FROM bookmarks
        JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
        """
        # Add where clauses
        where_clauses = []
        if year:
            where_clauses.append(f"strftime('%Y', bookmarks.add_date) = '{year}'")
        if month:
            where_clauses.append(f"strftime('%m', bookmarks.add_date) = '{month}'")
        if tag:
            where_clauses.append(f"tags LIKE '%{tag}%'")
        if category:
            where_clauses.append(f"folder = '{category}'")
        # Join and complete the query
        if where_clauses:
            query += "WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY RANDOM() LIMIT 1;"

        # Execute the query
        bookmark = execute_query(query)[0][0]

    # TODO: Go to an error page if no bookmarks are found with the given restrictions

    # Redirect to the bookmark page
    # TODO: Add query parameters to the redirect so we can keep the restrictions for generating another random bookmark
    return redirect(url_for('bookmark', bookmark_id=bookmark))
