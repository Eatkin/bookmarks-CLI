import os
import readline
from getch import getch
from bs4 import BeautifulSoup
import re
from datetime import datetime as dt
import requests
import pandas as pd
from google.cloud import bigquery

def get_bigquery_client():
    """Returns a bigquery client object."""
    project_id = 'bookmarks-414106'
    client = bigquery.Client(project=project_id)
    return client

def get_latest_date():
    """Returns the latest datetime from the bookmarks table."""
    dataset_id = 'bookmarks_data'
    table_id = 'bookmarks'
    client = get_bigquery_client()

    query = f"""
    SELECT MAX(Date_Added) FROM {dataset_id}.{table_id}
    """

    job = client.query(query)
    result = job.result()

    # Returns a datetime object
    latest_date = next(result)[0]
    return latest_date

def get_all_urls():
    """Returns a list of all URLs from the bookmarks table."""
    dataset_id = 'bookmarks_data'
    table_id = 'bookmarks'
    client = get_bigquery_client()

    query = f"""
    SELECT URL FROM {dataset_id}.{table_id}
    """

    job = client.query(query)
    result = job.result()

    urls = []
    for row in result:
        urls.append(row[0])
    return urls

def get_tags():
    """Returns a list of tags from the tags table."""
    dataset_id = 'bookmarks_data'
    table_id = 'tags'
    client = get_bigquery_client()

    query = f"""
    SELECT Name FROM {dataset_id}.{table_id}
    """

    job = client.query(query)
    result = job.result()

    tags = []
    for row in result:
        tags.append(row[0])
    return tags

def get_categories():
    """Returns a list of categories from the categories table."""
    dataset_id = 'bookmarks_data'
    table_id = 'categories'
    client = get_bigquery_client()

    query = f"""
    SELECT Name FROM {dataset_id}.{table_id}
    """

    job = client.query(query)
    result = job.result()

    categories = []
    for row in result:
        categories.append(row[0])
    return categories

def parse_bookmarks(file, max_tags=None):
    """Parses the bookmarks.html file and returns a list of dictionaries as long as bookmarks are added after the latest date."""
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()
    latest_date = get_latest_date()
    print(f"Getting bookmarks added after {latest_date}")
    # Do stuff with the html
    soup = BeautifulSoup(html, 'html.parser')

    # Append dummy header to the end of the soup
    soup.append(BeautifulSoup('<h3>dummy</h3>', 'html.parser'))

    # Find h3 tags
    h3_tags = soup.find_all('h3')
    bookmarks = {}
    failures = []
    for i in range(0, len(h3_tags)-1):
        heading = h3_tags[i].text

        # Make pattern to find content between h3 tags
        pattern = re.compile(r'{}(.+?){}'.format(re.escape(str(h3_tags[i])), re.escape(str(h3_tags[i + 1]))), re.DOTALL)

        try:
            bookmarks[heading] = pattern.search(str(soup)).group(1).strip()
        except AttributeError:
            bookmarks[heading] = ''
            failures.append(heading)

    # Assign bookmarks to bookmark_dict
    bookmark_dict = bookmarks

    # Now get a list of dictionaries
    all_bookmark_urls = get_all_urls()
    bookmarks = []
    for folder, html in bookmark_dict.items():
        s = BeautifulSoup(html, 'html.parser')
        # Find all the a tags
        a_tags = s.find_all('a')
        for a in a_tags:
            add_date = a['add_date']
            # Convert add_date to datetime (it's in unix time)
            add_date = dt.fromtimestamp(int(add_date))
            # Skip if add_date is lower than the latest date because we only want to add bookmarks that are new
            if latest_date >= add_date:
                continue

            print(f"Processing bookmark {a.text} added on {add_date}")

            title = a.text
            url = a['href']


            # Append the bookmark
            bookmarks.append({
                'title': title,
                'url': url,
                'add_date': add_date,
                'folder': folder,
                'tags': []
            })


    num_bookmarks = len(bookmarks)
    if num_bookmarks == 0:
        print("No new bookmarks, goodbye!")
        exit(1)

    print(f"Found {num_bookmarks} bookmarks")


    # Order bookmarks by add_date (oldest first)
    bookmarks = sorted(bookmarks, key=lambda x: x['add_date'])

    if max_tags is not None and num_bookmarks > max_tags:
        bookmarks = bookmarks[:max_tags]
        print(f"Only processing {max_tags} bookmarks due to max_tags limit")

    bookmarks = get_descriptions(bookmarks)

    bookmarks = tag_bookmarks(bookmarks)

    return bookmarks

def get_descriptions(bookmarks):
    """Queries the meta API to get descriptions for the bookmarks."""
    meta_api = "https://api.turbosite.cloud/metatags"

    for bookmark in bookmarks:
        # Set a default description of nothing
        bookmark['description'] = ''
        url = bookmark['url']
        r = requests.get(meta_api, params={'url': url})

        print(f"Getting description for {url}")

        if r.status_code == 200:
            try:
                data = r.json()
                description = data['description']
                if data['description'] == "No description":
                    # Fall back to using the title
                    description = data['title']
                print(f"Description for {url} is {description}")
            except:
                print(f"No description in JSON for {url}")

        bookmark['description'] = description

    return bookmarks

def suggest_tags(base_tag, tags):
    """Suggests tags for the bookmarks."""
    return [t for t in tags if t.startswith(base_tag)]

def tag_bookmarks(bookmarks):
    """Tags the bookmarks with the user's input."""
    all_tags = get_tags()

    for bookmark in bookmarks:
        print("Enter tags for bookmark {}".format(bookmark["title"]))
        print(bookmark['url'])
        print(bookmark['description'])
        print("Press enter without typing to confirm tag")
        user_input = ""
        tags = []
        # Pretty ugly but it's for personal use so it's fine I don't care lol
        while True:
            new_input = getch()
            if new_input == "\n":
                if not user_input:
                    if not tags:
                        print("Please enter at least one tag")
                        continue
                    confirmation = input("Confirm tags '{}' (Y/N): ".format(", ".join(tags))).strip().lower()
                    if confirmation == 'y':
                        bookmark['tags'] = tags
                        break
                    continue

                # If the user presses Enter without typing anything, prompt for confirmation
                confirmation = input("Confirm tag '{}' (Y/N): ".format(user_input)).strip().lower()
                if confirmation == 'y':
                    tags.append(user_input)
                    print("Enter more tags:")
                    user_input = ""
                continue

            if new_input == '\x7f':  # Backspace
                user_input = user_input[:-1]
                print(user_input)
            # Detect tabs
            elif new_input == '\t':
                suggestions = suggest_tags(user_input, all_tags)
                if suggestions:
                    user_input = suggestions[0]
                    print(user_input)
            else:
                user_input += new_input.lower().replace(" ", "-")
                print(user_input)
                suggestions = suggest_tags(user_input, all_tags)
                print("Suggestions:", ", ".join(suggestions))

    return bookmarks

def update_tags(bookmarks):
    """Updates the tags table with any new tags."""
    print("Updating tags table")
    dataset_id = 'bookmarks_data'
    table_id = 'tags'
    client = get_bigquery_client()
    query = f"SELECT MAX(Tag_ID) from {dataset_id}.{table_id}"
    job = client.query(query)
    result = job.result()
    tag_id = next(result)[0] + 1

    all_tags = get_tags()
    tags = [t for b in bookmarks for t in b['tags']]
    tags = list(set(tags))

    new_tags = [t for t in tags if t not in all_tags]
    # Create a dictionary of tags
    tag_dict = [{"Tag_ID": tag_id + i, "Name": tag} for i, tag in enumerate(new_tags)]

    # Make a dataframe
    df = pd.DataFrame(tag_dict)

    if not df.empty:
        print(f"Adding {len(df)} new tags")
        # Upload the tags to the tags table
        job = client.load_table_from_dataframe(df, f"{dataset_id}.{table_id}")
        job.result()
    else:
        print("No new tags to add")

def update_categories(bookmarks):
    """Updates the categories table with any new categories."""
    print("Updating categories table")
    dataset_id = 'bookmarks_data'
    table_id = 'categories'
    client = get_bigquery_client()
    query = f"SELECT MAX(Category_ID) from {dataset_id}.{table_id}"
    job = client.query(query)
    result = job.result()
    category_id = next(result)[0] + 1

    all_categories = get_categories()
    categories = [b['folder'] for b in bookmarks]
    categories = list(set(categories))

    new_categories = [c for c in categories if c not in all_categories]
    # Create a dictionary of categories
    category_dict = [{"Category_ID": category_id + i, "Name": category} for i, category in enumerate(new_categories)]

    # Make a dataframe
    df = pd.DataFrame(category_dict)

    if not df.empty:
        print(f"Adding {len(df)} new categories")
        # Upload the categories to the categories table
        job = client.load_table_from_dataframe(df, f"{dataset_id}.{table_id}")
        job.result()
    else:
        print("No new categories to add")

def upload_bookmarks(bookmarks):
    """Uploads the bookmarks to the bookmarks table, the bookmarktags table, and updates the tags table."""
    # Update the tags table
    update_tags(bookmarks)

    # Update the categories table
    update_categories(bookmarks)

    dataset_id = 'bookmarks_data'
    client = get_bigquery_client()

    # Get the categories from the category tables
    query = f"SELECT * from {dataset_id}.categories"
    job = client.query(query)
    result = job.result()

    # Link the category names to the category IDs
    categories = {r[1]: r[0] for r in result}

    query = f"SELECT MAX(Bookmark_ID) from {dataset_id}.bookmarks"
    job = client.query(query)
    result = job.result()
    bookmark_id = next(result)[0] + 1

    print("Preparing to upload bookmarks to BigQuery")
    # Now we can form the bookmarks table
    bookmark_dict = [{
        "Bookmark_ID": bookmark_id + i,
        "Title": b["title"],
        "URL": b["url"],
        "Description": b["description"],
        "Date_Added": b["add_date"],
        "Category_ID": categories[b["folder"]],
        "Tags": b["tags"]
    } for i, b in enumerate(bookmarks)
    ]

    # Make a dataframe and upload
    # Tags aren't relevant here so we can remove them
    df = pd.DataFrame(bookmark_dict)
    df = df.drop(columns=["Tags"])

    job = client.load_table_from_dataframe(df, f"{dataset_id}.bookmarks")
    job.result()

    print(f"Uploaded {len(bookmark_dict)} bookmarks")

    # Now we need to update the bookmarktags table
    query = f"SELECT * from {dataset_id}.tags"
    job = client.query(query)
    result = job.result()

    # Link the tag names to the tag IDs
    tags = {r[1]: r[0] for r in result}

    # Now loop over the bookmarks i the bookmark dict
    tag_records = []
    for b in bookmark_dict:
        for tag in b["Tags"]:
            tag_records.append({
                "Bookmark_ID": b["Bookmark_ID"],
                "Tag_ID": tags[tag]
            })
    print(f"Preparing to upload {len(tag_records)} tags to BigQuery")

    # Make a dataframe and upload
    df = pd.DataFrame(tag_records)
    job = client.load_table_from_dataframe(df, f"{dataset_id}.bookmarktags")
    job.result()

    print(f"Uploaded {len(tag_records)} tags")


def main():
    # Get a list of any new bookmarks
    bookmarks_file = os.path.join(os.getcwd(), 'bookmarks.html')
    print(f"Reading bookmarks from {bookmarks_file}")

    # This returns a list of dictionaries with tagged and described bookmarks
    bookmarks = parse_bookmarks(bookmarks_file, max_tags=10)

    # Now upload the bookmarks to the database
    upload_bookmarks(bookmarks)

    print("All done!")
    print("Please check the database to ensure everything is correct")
    print("If there are any issues, please contact support")
    print("Thank you for using the service!")
    print("Goodbye!")
    print("")
    print("I hope you have a great day!")
    print("I don't want to kill myself anymore!")
    print("I'm so happy!")



if __name__ == '__main__':
    main()
