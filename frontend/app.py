from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from random import choice

# Create the Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

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

def get_all_bookmarks(cursor):
    return cursor.fetchall()

def execute_query(cursor, query):
    cursor.execute(query)
    return cursor.fetchall()

cursor = get_db_connection()

# Fetch the bookmarks
bookmarks = get_all_bookmarks(cursor)

PER_PAGE = 10

# Define the index route
@app.route('/')
def index():
    # Get page number from the query string
    page = int(request.args.get('page', 1))

    # Calculate start and end indices for the current page
    start_index = (page - 1) * PER_PAGE
    end_index = start_index + PER_PAGE

    # Slice the list of bookmarks to get the current page
    current_bookmarks = bookmarks[start_index:end_index]

    # Calculate total number of pages
    total_pages = (len(bookmarks) + PER_PAGE - 1) // PER_PAGE

    # Render the template
    return render_template('html/index.html', bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by category
@app.route('/categories/<category>')
def category(category):
    return f'This is the page for {category}'

# Routes by tag
@app.route('/tags/<tag>')
def tag(tag):
    return f'This is the page for {tag}'

# Routes by year
@app.route('/years/<year>')
def year(year):
    return f'This is the page for {year}'

# Route by year/month
@app.route('/years/<year>/<month>')
def month(year, month):
    return f'This is the page for {year}/{month}'

# Routes by bookmark
@app.route('/bookmarks/<bookmark_id>')
def bookmark(bookmark_id):
    return f'This is the page for bookmark {bookmark_id}'

@app.route('/random')
def random():
    # Params for year/month/tag/category so we can randomise with restrictions
    year = request.args.get('year', None)
    month = request.args.get('month', None)
    tag = request.args.get('tag', None)
    category = request.args.get('category', None)

    # If there's no args then just pick a random bookmark
    if not any([year, month, tag, category]):
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
            where_clauses.append(f"category = '{category}'")
        # Join and complete the query
        if where_clauses:
            query += "WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY RANDOM() LIMIT 1;"

        # Execute the query
        bookmark = execute_query(cursor, query)[0]

    # TODO: Go to an error page if no bookmarks are found with the given restrictions

    # Redirect to the bookmark page
    return redirect(url_for('bookmark', bookmark_id=bookmark))
