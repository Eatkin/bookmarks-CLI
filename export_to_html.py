import scripts.database_utils as db

# Instantiate the database
database = db.Database()
database.open_database()

# Now query to get bookmarks joined to descriptions table and ordered by date
query = """SELECT * FROM bookmarks
           JOIN descriptions
           ON bookmarks.id = descriptions.bookmark_id
           ORDER BY add_date DESC"""

results = database.query(query)

# Now we can do some boilerplate HTML stuff
html = """<html>
<head>
<title>Bookmarks</title>
</head>
<body>
<h1>Bookmarks</h1>
<table>
"""

# Now we can iterate over the results and add them to the HTML
# The results are returned as id, title, url, add_date, folder (category), description_id, content, relevant_content, description, tags
for row in results:
    title = row[1]
    url = row[2]
    date = row[3]
    category = row[4]
    description = row[8]
    tags = row[9]

    # Format tags
    if tags:
        tags = tags.split(',')
        tags = ', '.join(tags)
    else:
        tags = ''

    # Format description (replace with empty string if None)
    if description is None:
        description = ''
    else:
        description = description.replace('\n', '<br>')

    # Format date
    date = date.split(' ')[0]

    # Now construct a table row
    html += """<tr>
                <td><a href="{0}">{1}</a></td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td>{5}</td>
                </tr>
                """.format(url, title, date, category, description, tags)

# Now we can finish off the HTML
html += """</table>
</body>
</html>"""

# Now we can write the HTML to a file
with open('bookmarks.html', 'w') as f:
    f.write(html)
