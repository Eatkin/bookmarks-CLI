from random import choice
from flask import Flask, render_template, request, redirect, url_for

# Import bigquery
from google.cloud import bigquery

# Create a BigQuery client
project_id = 'bookmarks-414106'
dataset_id = 'bookmarks_data'
client = bigquery.Client(project=project_id)

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

def get_all_tags():
    """Get all unique tags and return a list of tuples containing the tag and the number of times it appears."""
    global client, project_id, dataset_id
    # Join bookmarktags on tags so we get the tag names and their counts
    query = f"""
    SELECT tags.Name, COUNT(tags.Name) as count
    FROM {project_id}.{dataset_id}.bookmarktags as bookmarktags
    JOIN {project_id}.{dataset_id}.tags as tags
    ON bookmarktags.Tag_ID = tags.Tag_ID
    GROUP BY tags.Name
    ORDER BY count DESC"""

    # Make the query
    query_job = client.query(query)
    # Get the results
    tags = query_job.result()
    tags = [(row.Name, row.count) for row in tags]

    return tags

def get_bookmark_page(page):
    """Get a list of bookmarks for a given page."""
    global PER_PAGE, project_id, dataset_id
    table_id = 'bookmarks'
    query = f"""
    SELECT bookmarks.Title, bookmarks.Description, bookmarks.URL, bookmarks.Date_Added,
    categories.Name as Category,
    STRING_AGG(tags.Name, ' ') AS Tags
    FROM {project_id}.{dataset_id}.{table_id} as bookmarks
    JOIN {project_id}.{dataset_id}.categories as categories
    ON bookmarks.Category_ID = categories.Category_ID
    JOIN {project_id}.{dataset_id}.bookmarktags as bookmarktags
    ON bookmarks.Bookmark_ID = bookmarktags.Bookmark_ID
    JOIN {project_id}.{dataset_id}.tags as tags
    ON bookmarktags.Tag_ID = tags.Tag_ID
    GROUP BY bookmarks.Title, bookmarks.Description, bookmarks.URL, bookmarks.Date_Added, categories.Name
    ORDER BY Date_Added DESC
    LIMIT {PER_PAGE}
    OFFSET {PER_PAGE * (page - 1)}"""

    # Now get it into a list of dictionaries
    query_job = client.query(query)
    bookmarks = query_job.result()
    bookmarks = [dict(row) for row in bookmarks]

    # Make the tags a list
    for bookmark in bookmarks:
        bookmark['Tags'] = bookmark['Tags'].split(' ')

    return bookmarks

def get_total_pages():
    """Query to count the total number of bookmarks and calculate the total number of pages."""
    global PER_PAGE, client, project_id, dataset_id
    table_id = 'bookmarks'
    query = f"""
    SELECT COUNT(*) as count
    FROM {project_id}.{dataset_id}.{table_id}"""

    # Make the query
    query_job = client.query(query)
    # Get the results
    count = query_job.result()
    count = [row.count for row in count][0]
    total_pages = (count + PER_PAGE - 1) // PER_PAGE
    return total_pages

def get_categories():
    """Query that gets all categories and number of entries for each category"""
    global client, project_id, dataset_id
    query = f"""
    SELECT categories.Name, COUNT(bookmarks.Bookmark_ID) as count
    FROM {project_id}.{dataset_id}.categories as categories
    JOIN {project_id}.{dataset_id}.bookmarks as bookmarks
    ON categories.Category_ID = bookmarks.Category_ID
    GROUP BY categories.Name
    ORDER BY count DESC"""

    # Make the query
    query_job = client.query(query)
    # Get the results
    categories = query_job.result()
    categories = [(row.Name, row.count) for row in categories]

    return categories

def get_bookmarks_by_category(category, page):
    global client, project_id, dataset_id, PER_PAGE
    query = f"""
    SELECT bookmarks.Title, bookmarks.Description, bookmarks.URL, bookmarks.Date_Added,
    categories.Name as Category,
    STRING_AGG(tags.Name, ' ') AS Tags
    FROM {project_id}.{dataset_id}.bookmarks as bookmarks
    JOIN {project_id}.{dataset_id}.categories as categories
    ON bookmarks.Category_ID = categories.Category_ID
    JOIN {project_id}.{dataset_id}.bookmarktags as bookmarktags
    ON bookmarks.Bookmark_ID = bookmarktags.Bookmark_ID
    JOIN {project_id}.{dataset_id}.tags as tags
    ON bookmarktags.Tag_ID = tags.Tag_ID
    WHERE categories.Name = '{category}'
    GROUP BY bookmarks.Title, bookmarks.Description, bookmarks.URL, bookmarks.Date_Added, categories.Name
    ORDER BY Date_Added DESC
    LIMIT {PER_PAGE}
    OFFSET {PER_PAGE * (page - 1)}"""

    # Now get it into a list of dictionaries
    query_job = client.query(query)
    bookmarks = query_job.result()
    bookmarks = [dict(row) for row in bookmarks]

    # Make the tags a list
    for bookmark in bookmarks:
        bookmark['Tags'] = bookmark['Tags'].split(' ')

    return bookmarks

def get_bookmarks_by_tag(tag, page):
    global client, project_id, dataset_id, PER_PAGE
    query = f"""
    SELECT bookmarks.Title, bookmarks.Description, bookmarks.URL, bookmarks.Date_Added,
    categories.Name as Category,
    STRING_AGG(tags.Name, ' ') AS Tags
    FROM {project_id}.{dataset_id}.bookmarks as bookmarks
    JOIN {project_id}.{dataset_id}.categories as categories
    ON bookmarks.Category_ID = categories.Category_ID
    JOIN {project_id}.{dataset_id}.bookmarktags as bookmarktags
    ON bookmarks.Bookmark_ID = bookmarktags.Bookmark_ID
    JOIN {project_id}.{dataset_id}.tags as tags
    ON bookmarktags.Tag_ID = tags.Tag_ID
    WHERE bookmarks.Bookmark_ID IN (
        SELECT Bookmark_ID
        FROM {project_id}.{dataset_id}.bookmarktags as bookmarktags
        JOIN {project_id}.{dataset_id}.tags as tags
        ON bookmarktags.Tag_ID = tags.Tag_ID
        WHERE tags.Name = '{tag}')
    GROUP BY bookmarks.Title, bookmarks.Description, bookmarks.URL, bookmarks.Date_Added, categories.Name
    ORDER BY Date_Added DESC
    LIMIT {PER_PAGE}
    OFFSET {PER_PAGE * (page - 1)}"""

    # Now get it into a list of dictionaries
    query_job = client.query(query)
    bookmarks = query_job.result()
    bookmarks = [dict(row) for row in bookmarks]

    # Make the tags a list
    for bookmark in bookmarks:
        bookmark['Tags'] = bookmark['Tags'].split(' ')

    return bookmarks

def get_random_bookmark(by=None, category=None, tag=None):
    global client, project_id, dataset_id
    where_clause = ''
    if by == 'category':
        where_clause = f"WHERE categories.Name = '{category}'"
    elif by == 'tag':
        where_clause = f"WHERE tags.Name = '{tag}'"

    query = f"""
    SELECT bookmarks.Title, bookmarks.Description, bookmarks.URL, bookmarks.Date_Added,
    categories.Name as Category,
    STRING_AGG(tags.Name, ' ') AS Tags
    FROM {project_id}.{dataset_id}.bookmarks as bookmarks
    JOIN {project_id}.{dataset_id}.categories as categories
    ON bookmarks.Category_ID = categories.Category_ID
    JOIN {project_id}.{dataset_id}.bookmarktags as bookmarktags
    ON bookmarks.Bookmark_ID = bookmarktags.Bookmark_ID
    JOIN {project_id}.{dataset_id}.tags as tags
    ON bookmarktags.Tag_ID = tags.Tag_ID
    {where_clause}
    GROUP BY bookmarks.Title, bookmarks.Description, bookmarks.URL, bookmarks.Date_Added, categories.Name
    ORDER BY RAND()
    LIMIT 1"""

    # Now get it into a list of dictionaries
    query_job = client.query(query)
    bookmarks = query_job.result()
    bookmarks = [dict(row) for row in bookmarks]

    # Make the tags a list
    for bookmark in bookmarks:
        bookmark['Tags'] = bookmark['Tags'].split(' ')

    return bookmarks

# Globals
PER_PAGE = 10
unique_categories = get_categories()
unique_tags = get_all_tags()
total_pages = get_total_pages()

# Define the index route
@app.route('/')
def index():
    global total_pages

    page = int(request.args.get('page', 1))
    current_bookmarks = get_bookmark_page(page)

    # Render the template
    return render_template('html/bookmarks.html', bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by category
@app.route('/categories')
def categories():
    global unique_categories, client

    # Query for all bookmarks in the category ordered by date IF we have a category parameter
    category = request.args.get('category', None)
    # Get the page number
    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1

    # Get the bookmarks
    current_bookmarks = get_bookmarks_by_category(category, page)

    # Page count
    if category is None:
        total_pages = 1
    else:
        try:
            # Find the index of the category
            index = [x[0] for x in unique_categories].index(category)
            count = unique_categories[index][1]
            total_pages = (count + PER_PAGE - 1) // PER_PAGE
        except:
            total_pages = 1
            print('Category not found')

    # Render the template
    return render_template('html/categories.html', category=category, categories=unique_categories, bookmarks=current_bookmarks, page=page, total_pages=total_pages)

# Routes by tag
@app.route('/tags')
def tags():
    global unique_tags

    tag = request.args.get('tag', None)
    current_bookmarks = []
    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1
    if tag:
        current_bookmarks = get_bookmarks_by_tag(tag, page)
        try:
            index = [x[0] for x in unique_tags].index(tag)
            count = unique_tags[index][1]
            total_pages = (count + PER_PAGE - 1) // PER_PAGE
        except:
            total_pages = 1
            print('Tag not found')
    else:
        total_pages = 1

    # Render the template
    return render_template('html/tags.html', tag=tag, tags=unique_tags, bookmarks=current_bookmarks, page=page, total_pages=total_pages)

@app.route('/randomiser')
def randomiser():
    return render_template('html/randomiser.html', categories=unique_categories, tags=unique_tags)

@app.route('/random')
def random():
    # Params are category/tag or lucky
    category = request.args.get('category', None)
    tag = request.args.get('tag', None)
    lucky = request.args.get('lucky', None)

    if category:
        bookmark = get_random_bookmark(by='category', category=category)
    elif tag:
        bookmark = get_random_bookmark(by='tag', tag=tag)
    else:
        bookmark = get_random_bookmark()

    # Show the random page which is just the bookmark viewer page with a re-roll button at the bottom
    return render_template('html/random.html', bookmarks=bookmark, page=None, total_pages=1, random=True, category=category, tag=tag, lucky=lucky)
