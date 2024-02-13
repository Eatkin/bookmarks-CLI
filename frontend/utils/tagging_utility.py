import firebase_admin
from firebase_admin import credentials, firestore
import os
from string import ascii_letters, digits
from google.cloud.firestore_v1 import FieldFilter

def tag_loop():
    tags = []
    tagging = True
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

    return tags

# Get the service worker from the environment variable
service_worker = os.environ.get("SERVICE_WORKER")
# Get the parent directory
parent_dir = os.path.dirname(__file__)
parent_parent_dir = os.path.dirname(parent_dir)
service_worker = os.path.join(parent_parent_dir, service_worker)
firebase_admin.initialize_app(credentials.Certificate(service_worker))
db = firestore.client()

# We can query the database for tags with nothing in them
untagged_docs = db.collection("data").where(filter=FieldFilter("tags", "array_contains", "UNTAGGED")).stream()

# Loop through the untagged documents
for doc in untagged_docs:
    # Get the title
    title = doc.to_dict()["title"]
    print(f"Title: {title}")
    tags = tag_loop()

    # Get the document reference
    doc_ref = db.collection("data").document(doc.id)
    # Update the document
    doc_ref.update({"tags": tags})

print("All done!")
