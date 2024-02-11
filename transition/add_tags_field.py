import json

# Import the json file, add a tags field, and write it back to the file
with open('bookmarks.json') as f:
    bookmarks = json.load(f)

for b in bookmarks:
    b['tags'] = ''

with open('bookmarks.json', 'w') as f:
    json.dump(bookmarks, f, indent=4)
