import json

# Bookmarks all have a unique ID but there are numbers missing. This script will repair the IDs so that they are all sequential.

with open("bookmarks.json", 'r') as file:
    data = json.load(file)

id_offset = 1
for i, item in enumerate(data):
    if item['id'] - id_offset != i:
        item['id'] = i + id_offset
        print(f"ID {item['id']} was repaired")

with open("bookmarks.json", 'w') as file:
    json.dump(data, file, indent=2)
