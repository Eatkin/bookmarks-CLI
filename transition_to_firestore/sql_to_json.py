import scripts.database_utils as db

# Get all database tables
db = db.Database()
db.open_database()

# Query to join main table to description table
query = """
SELECT bookmarks.id, bookmarks.title, bookmarks.url, bookmarks.add_date, bookmarks.folder,
descriptions.description
FROM bookmarks
LEFT JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
"""

results = db.cursor.execute(query).fetchall()

# now make a list of dictionaries
bookmarks = []
for result in results:
    bookmark = {
        "id": result[0],
        "title": result[1],
        "url": result[2],
        "add_date": result[3],
        "folder": result[4],
        "description": result[5]
    }
    bookmarks.append(bookmark)

# Write to file
import json
with open('bookmarks.json', 'w') as f:
    json.dump(bookmarks, f, indent=4)


db.close_database()
