import pandas as pd
import json

# Read the json file into a dataframe
with open('bookmarks.json', 'r') as f:
    bookmarks_json = json.load(f)

df = pd.DataFrame(bookmarks_json)

# Check for duplicated urls
duplicates = df[df.duplicated(subset='url', keep=False)]

print(duplicates.to_string(index=False))
