import scripts.database_utils as db
import re

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
<link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
<h1>Bookmarks</h1>
"""

# Get the current year cause we'll use it for subheadings
current_year = results[0][3].split(' ')[0].split('-')[0]

html += '<h2 id="{0}">{0}</h2>'.format(current_year)

# Start the table
html += "<table>"

# Now we can iterate over the results and add them to the HTML
# The results are returned as id, title, url, add_date, folder (category), description_id, content, relevant_content, description, tags
for row in results:
    title = row[1]
    url = row[2]
    date = row[3]
    category = row[4]
    description = row[8]
    tags = row[9]

    # See if the year has changed
    year = date.split(' ')[0].split('-')[0]
    if year != current_year:
        html += '</table><h2 id="{0}">{0}</h2><table>'.format(year)
        current_year = year

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
                <td class="title"><a href="{0}">{1}</a></td>
                <td class="date">{2}</td>
                <td class="category">{3}</td>
                <td class="description">{4}</td>
                <td class="tags">{5}</td>
                </tr>
                """.format(url, title, date, category, description, tags)

# Now we can finish off the HTML
html += """</table>
</body>
</html>"""

# Clean up any empty <td> tags
pattern = re.compile('<td[a-z=" ]*></td>')
html = re.sub(pattern, '', html)

# Now we can write the HTML to a file
with open('bookmarks.html', 'w') as f:
    f.write(html)
