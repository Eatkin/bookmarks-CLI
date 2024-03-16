import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

service_worker = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

firebase_admin.initialize_app(credentials.Certificate(service_worker))
fs_client = firestore.client()

# Get all documents from the bookmarks collection
bookmarks = fs_client.collection("data").stream()

df = pd.DataFrame(columns=["Bookmark_ID", "Title", "Category", "URL", "Description", "Date_Added", "Tags"])

for b in bookmarks:
    bookmark = b.to_dict()
    # Convert keys to the correct column names
    mapping = {
        "id": "Bookmark_ID",
        "description": "Description",
        "folder": "Category",
        "add_date": "Date_Added",
        "tags": "Tags",
        "title": "Title",
        "url": "URL",
    }
    for old, new in mapping.items():
        bookmark[new] = bookmark.pop(old)

    # Convert the tags to a string
    bookmark["Tags"] = ", ".join(bookmark["Tags"])

    df_dict = pd.DataFrame(bookmark, index=[0])
    df = pd.concat([df, df_dict], ignore_index=True)

# Output to CSV
output = os.path.join(os.path.dirname(__file__), "bookmarks.csv")
df.to_csv(output, index=False)
