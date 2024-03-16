import json
from string import ascii_letters, digits
import atexit

# Save the data to the json file upon program end
@atexit.register
def save():
    with open("bookmarks.json", 'w') as file:
        json.dump(data, file, indent=2)

# Get the json file
with open("bookmarks.json", 'r') as file:
    data = json.load(file)

# Loop through
for i, item in enumerate(data):
    if item['tags'] == '':
        # Start the loop to get the tags
        tags = []
        tagging = True
        # Print title and url
        print("="*20)
        print(f"Title: {item['title']}")
        print(f"URL: {item['url']}")
        while tagging:
            tag = input(f"Enter a tag: ")
            if tag == '':
                print("Tags:", ', '.join(tags))
                response = ""
                while response.lower() not in ["yes", "no"]:
                    response = input("Is this correct? (yes/no) ")
                    if response.lower() == "yes":
                        tagging = False
                    if response.lower() == "no":
                        break
            else:
                # Clean the tag - replace spaces with hyphens, lowercase, and remove non-alphanumeric characters
                tag = tag.replace(' ', '-').lower()
                tag = ''.join(c for c in tag if c in ascii_letters or c in digits or c == '-')
                # Remove trailing hyphens
                tag = tag.strip('-')
                # Remove whitespace
                tag = tag.strip()
                tags.append(tag)

        # Add the tags to the item
        item['tags'] = tags

        # Update the data
        data[i]['tags'] = tags
