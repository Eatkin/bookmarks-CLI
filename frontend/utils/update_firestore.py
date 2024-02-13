import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from bs4 import BeautifulSoup
import re
from datetime import datetime
import requests

"""Fucking stupidd gross script cause I couldn't be bothered to make it properly lol"""

# Get the service worker from the environment variable
service_worker = os.environ.get("SERVICE_WORKER")
# Get the parent directory
parent_dir = os.path.dirname(__file__)
parent_parent_dir = os.path.dirname(parent_dir)
service_worker = os.path.join(parent_parent_dir, service_worker)
firebase_admin.initialize_app(credentials.Certificate(service_worker))
db = firestore.client()

# Now we have a link to the Firestore database
# We'll use our cached data to update the database
with open('bookmarks.json', 'r') as f:
    bookmarks_json = json.load(f)

# Open bookmarks.html
with open('bookmarks.html', 'r', encoding='utf-8') as f:
    html = f.read()

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

# Now get a list of tuples
bookmarks = []
for folder, html in bookmark_dict.items():
    s = BeautifulSoup(html, 'html.parser')
    # Find all the a tags
    a_tags = s.find_all('a')
    for a in a_tags:
        title = a.text
        url = a['href']
        add_date = a['add_date']
        # Convert add_date to datetime (it's in unix time)
        add_date = datetime.fromtimestamp(int(add_date))
        # Append the bookmark to the list
        bookmarks.append((title, url, add_date, folder))

# Use the requests library to get the description
meta_api = "https://api.turbosite.cloud/metatags"

# Now we need to find URLs that are not in the json file
json_urls = [bookmark['url'] for bookmark in bookmarks_json]
all_urls = [bookmark[1] for bookmark in bookmarks]
urls = [bookmark[1] for bookmark in bookmarks if bookmark[1] not in json_urls]

print(f"Found {len(urls)} new URLs")

# Get the maximum id from the json file
max_id = max([bookmark['id'] for bookmark in bookmarks_json])

# Make them into dictionaries of id, title, url, add_date, folder, description
new_json = []
for i, url in enumerate(urls):
    bookmark_index = all_urls.index(url)
    target_folder = bookmarks[bookmark_index][3]
    max_id += 1
    title = soup.find('a', href=url).text
    folder = target_folder
    add_date = bookmarks[bookmark_index][2]
    description = ''
    # Request the description
    r = requests.get(meta_api, params={'url': url})
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
    new_json.append({'id': max_id, 'title': title, 'url': url, 'add_date': str(add_date), 'folder': folder, 'description': description, 'tags': ["UNTAGGED"]})

# Output as new json
# This is just for verification actually
with open('new_bookmarks.json', 'w') as f:
    json.dump(new_json, f, indent=4)

# Upload that shit to the firestore
batch = db.batch()
for doc in new_json:
    i = doc['id']
    ref = db.collection("data").document(str(i))
    batch.set(ref, doc)

# Commit the batch
batch.commit()

print("Data uploaded successfully.")
