import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json

# DO NOT RUN THIS SCRIPT AGAIN UNLESS YOU WANT TO OVERWRITE THE DATA IN THE DATABASE
# exit(1)

# Initialize Firebase Admin SDK with the service account credentials
cred = credentials.Certificate(os.environ.get("SERVICE_WORKER"))
firebase_admin.initialize_app(cred)

# Get a reference to the Firestore database
db = firestore.client()

# Import the data from the JSON file
with open("bookmarks.json", "r") as file:
    data = json.load(file)

# Create a batch to upload the data
batch = db.batch()
for i, doc in enumerate(data[:11]):
    ref = db.collection("data").document(str(i))
    batch.set(ref, doc)

# Commit the batch
batch.commit()

print("Data uploaded successfully.")
