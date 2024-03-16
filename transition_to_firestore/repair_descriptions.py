import requests
import json

meta_api = "https://api.turbosite.cloud/metatags"

# Import the json file to get a list of dictionaries of bookmarks
with open('bookmarks.json') as f:
    bookmarks = json.load(f)

# Go through and find all the bookmarks that have no description
no_description = []
for bookmark in bookmarks:
    if bookmark['description'] is None or bookmark['description'] == "" or bookmark['description'] == "No description":
        # Make a request to the meta description API
        url = bookmark['url']
        r = requests.get(meta_api, params={'url': url})
        if r.status_code == 200:
            try:
                data = r.json()
                bookmark['description'] = data['description']
                if data['description'] == "No description":
                    # Fall back to using the title
                    bookmark['description'] = data['title']
                print(f"Description for {url} is {bookmark['description']}")
            except:
                no_description.append((bookmark['url'], "No description in JSON"))
                print(f"No description in JSON for {bookmark['url']}")
        else:
            no_description.append((bookmark['url'], r.status_code))

print(f"Summary of bookmarks with no description retrievable: {no_description}")
print(f"Number of bookmarks with no description retrievable: {len(no_description)}")

# Now write the updated bookmarks to the original file
with open('bookmarks.json', 'w') as f:
    json.dump(bookmarks, f, indent=4)
