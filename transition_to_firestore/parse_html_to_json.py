import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

# Let's load up our json file
with open('bookmarks.json', 'r') as f:
    bookmarks_json = json.load(f)

# Let's make a soup object from the html
with open('bookmarks.html', 'r', encoding='utf-8') as f:
    html = f.read()

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

# Now we need to find URLs that are not in the json file
urls = [bookmark[1] for bookmark in bookmarks]
json_urls = [bookmark['url'] for bookmark in bookmarks_json]

# Get the maximum id from the json file
max_id = max([bookmark['id'] for bookmark in bookmarks_json])

# Make them into dictionaries of id, title, url, add_date, folder, description
for i, url in enumerate(urls):
    target_folder = bookmarks[i][3]
    if url in json_urls:
        # Skip the url but update the folder if necessary
        source_folder = bookmarks_json[json_urls.index(url)]['folder']
        # Set the folder in bookmarks_json to the target folder
        bookmarks_json[json_urls.index(url)]['folder'] = target_folder
        continue
    max_id += 1
    title = soup.find('a', href=url).text
    folder = target_folder
    add_date = bookmarks[i][2]
    description = ''
    bookmarks_json.append({'id': max_id, 'title': title, 'url': url, 'add_date': add_date, 'folder': folder, 'description': description})

    # Repair descriptions will be used for descriptions

# Repair the add dates
for i, bookmark in enumerate(bookmarks_json):
    if "add_date" not in bookmark:
        print("Repairing add date for", bookmarks_json[i]['title'])
        bookmarks_json[i]["add_date"] = str(bookmarks[i][2])

# Write the json file
with open('bookmarks.json', 'w') as f:
    json.dump(bookmarks_json, f, indent=4)
