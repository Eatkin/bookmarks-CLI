from google.cloud import bigquery

bq_client = bigquery.Client()

"""SCHEMA:
Bookmarks DB:
- ID
- Title
- Category ID
- URL
- Description
Category DB:
- ID
- Name
Tags DB:
- Tag ID
- Tag Name
BookmarkTags DB:
- Bookmark ID
- Tag ID
"""

project_id = "bookmarks-414106"
dataset_id = "bookmarks_data"
table_id = "bookmarks"

tables = ["bookmarks", "categories", "tags", "bookmarktags"]

schemas = {}
schemas["bookmarks"] = [
    bigquery.SchemaField("Bookmark_ID", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("Title", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("Category_ID", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("URL", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("Description", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("Date_Added", "TIMESTAMP", mode="REQUIRED"),
]

schemas["categories"] = [
    bigquery.SchemaField("Category_ID", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("Name", "STRING", mode="REQUIRED"),
]

schemas["tags"] = [
    bigquery.SchemaField("Tag_ID", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("Name", "STRING", mode="REQUIRED"),
]

schemas["bookmarktags"] = [
    bigquery.SchemaField("Bookmark_ID", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("Tag_ID", "INT64", mode="REQUIRED"),
]

# Create dataset
dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
dataset.location = "europe-west2"
dataset = bq_client.create_dataset(dataset)
print(f"Created dataset {dataset_id}")

for table in tables:
    table_full_path = f"{project_id}.{dataset_id}.{table}"
    table = bigquery.Table(table_full_path, schema=schemas[table])
    table = bq_client.create_table(table)
    print(f"Created table {table_full_path}")
