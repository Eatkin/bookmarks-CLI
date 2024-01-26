import sqlite3
import os
import logging
from scripts.components import Bookmark

class Database():
    def __init__(self, db_path='bookmarks.db'):
        self.db_path = db_path
        self.db = None
        self.cursor = None

    def database_exists(self):
        """Returns true if the database exists"""
        return os.path.exists(self.db_path)

    def open_database(self):
        """Loads the database"""
        self.db = sqlite3.connect(self.db_path)
        self.cursor = self.db.cursor()

    def close_database(self):
        """Closes the database"""
        self.db.close()
        self.cursor = None
        self.db = None

    def database_is_connected(self):
        """Returns true if the database is connected"""
        return self.db is not None

    def create_tables(self):
        """Creates the tables for the database"""
        try:
            self.create_bookmarks_table()
        except Exception as e:
            logging.error(f"Failed to create bookmarks table: {e}")
        try:
            self.create_description_table()
        except Exception as e:
            logging.error(f"Failed to create descriptions table: {e}")

    def create_bookmarks_table(self):
        """Creates the primary table containing bookmarks"""
        # Open database if not already open
        if not self.database_is_connected():
            self.open_database()

        #--------------------------------------------------------------------------------#
        # Create the table if it doesn't exist
        # Schema: id (primary key), title, url, add_date, folder
        #--------------------------------------------------------------------------------#
        query = """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            add_date TEXT,
            folder TEXT,
            CONSTRAINT unique_bookmark UNIQUE (title, url, add_date, folder)
        )
        """
        self.cursor.execute(query)

        # Commit changes and close database
        self.db.commit()
        self.close_database()

    def create_description_table(self):
        """Creates the description table"""
        # Open database if not already open
        if not self.database_is_connected():
            self.open_database()

        #--------------------------------------------------------------------------------#
        # Create the table if it doesn't exist
        # Schema: bookmark_id (foreign key), content, relevant_content, description, tags
        # Content is the entire page content
        # Relevant content is the content that is relevant to the page
        # Description is the description of the page
        # Tags are the tags for the page
        #--------------------------------------------------------------------------------#
        query = """
        CREATE TABLE IF NOT EXISTS descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            relevant_content TEXT,
            description TEXT,
            tags TEXT,
            bookmark_id INTEGER,  -- Foreign key referencing bookmarks table
            FOREIGN KEY (bookmark_id) REFERENCES bookmarks (id),
            CONSTRAINT unique_description UNIQUE (bookmark_id)
        )
        """
        self.cursor.execute(query)

        # Commit changes and close database
        self.db.commit()
        self.close_database()

    def export_bookmarks(self, bookmarks):
        """Creates the primary table containing bookmarks"""
        # Setup tables
        self.create_tables()

        # Open database if not already open
        if not self.database_is_connected():
            self.open_database()

        # Insert UNIQUE bookmarks using window title, url, and add_date
        # The ids are autoincremented so won't necessarily be unique
        query = """
        INSERT OR IGNORE INTO bookmarks (title, url, add_date, folder)
        VALUES (?, ?, ?, ?)
        """
        self.cursor.executemany(query, bookmarks)

        # Commit changes and close database
        self.db.commit()
        self.close_database()

    def insert_descriptions(self, descriptions):
        """Exports the descriptions to the database
        Input is list of tuples of the form (bookmark_id, content, relevant_content, description, tags)"""
        # Open database if not already open
        if not self.database_is_connected():
            self.open_database()

        # Insert UNIQUE descriptions using title and description
        query = """
        INSERT OR REPLACE INTO descriptions (bookmark_id, content, relevant_content, description, tags)
        VALUES (?, ?, ?, ?, ?)
        """
        self.cursor.executemany(query, descriptions)

        # Commit changes and close database
        self.db.commit()
        self.close_database()

    def query(self, query, params=None):
        """Generic method for arbitrary queries"""
        # Open database if not already open
        close = False
        if not self.database_is_connected():
            close = True
            self.open_database()

        if params is None:
            self.cursor.execute(query)
        else:
            if len(params) == 1:
                self.cursor.execute(query, params)
            else:
                self.cursor.executemany(query, params)

        results = self.cursor.fetchall()

        self.db.commit()

        # Close database if it was closed before
        if close:
            self.close_database()

        return results

    def get_categories(self):
        query = """
        SELECT DISTINCT folder FROM bookmarks
        ORDER BY folder ASC
        """

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_random_bookmark(self, restrictions=None):
        """Return a random bookmark"""
        query = """
        SELECT * FROM bookmarks
        JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
        """

        # Pass in restrictions here, should be a where statement or list of where statements
        if restrictions is not None:
            if type(restrictions) is str:
                query += "WHERE " + restrictions
            else:
                query += "WHERE "
                for restriction in restrictions:
                    query += restriction + ' AND '
                # Remove the last AND
                query = query[:-5]


        query += """
        ORDER BY RANDOM()
        LIMIT 1
        """

        self.cursor.execute(query)
        return Bookmark(self.cursor.fetchone())

    def get_description(self, bookmark_id):
        """Returns the description for a bookmark"""
        query = """
        SELECT description FROM descriptions
        WHERE bookmark_id = ?
        """

        self.cursor.execute(query, (bookmark_id,))
        return self.cursor.fetchone()[0]

    def get_tags(self, bookmark_id):
        """Returns the tags for a bookmark"""
        query = """
        SELECT tags FROM descriptions
        WHERE bookmark_id = ?
        """

        self.cursor.execute(query, (bookmark_id,))
        return self.cursor.fetchone()[0]

    def get_all_tags(self):
        """Returns all tags"""
        query = """
        SELECT DISTINCT tags FROM descriptions
        WHERE tags IS NOT NULL
        """

        self.cursor.execute(query)

        results = self.cursor.fetchall()

        # Tags are separated by commas, so split them
        # No duplicates
        tags = []
        for result in results:
            tags.extend([t for t in result[0].split(',') if t not in tags])
        return sorted(tags)

    def get_bookmarks_by_tag(self, tag):
        """Returns all bookmarks with a tag"""
        query = """
        SELECT * FROM bookmarks
        JOIN descriptions ON bookmarks.id = descriptions.bookmark_id
        WHERE tags LIKE ?
        OR tags LIKE ?
        OR tags LIKE ?
        """

        self.cursor.execute(query, ('%,'+tag,'%,'+tag+',%',tag+',%'))
        return [Bookmark(record) for record in self.cursor.fetchall()]

    def get_bookmarks_by_category(self, category):
        """Returns all bookmarks in a category"""
        query = """
        SELECT * FROM bookmarks
        WHERE folder = ?
        ORDER BY title ASC
        """

        self.cursor.execute(query, (category,))
        return [Bookmark(record) for record in self.cursor.fetchall()]

    def get_all_bookmarks(self):
        """Returns all bookmarks"""
        query = """
        SELECT * FROM bookmarks
        ORDER BY title ASC
        """

        self.cursor.execute(query)
        return [Bookmark(record) for record in self.cursor.fetchall()]

    def get_distinct_years(self):
        """Returns a list of distinct years"""
        query = """
        SELECT DISTINCT strftime('%Y', add_date) FROM bookmarks
        ORDER BY strftime('%Y', add_date) DESC
        """

        self.cursor.execute(query)
        return [year[0] for year in self.cursor.fetchall()]

    def get_distinct_months(self, year):
        """Returns a list of distinct months for a year"""
        query = """
        SELECT DISTINCT strftime('%m', add_date) FROM bookmarks
        WHERE strftime('%Y', add_date) = ?
        ORDER BY strftime('%m', add_date) ASC
        """

        self.cursor.execute(query, (year,))
        return [month[0] for month in self.cursor.fetchall()]


    def get_bookmarks_by_year_month(self, year, month):
        """Returns all bookmarks in a year - most recent first"""
        query = """
        SELECT * FROM bookmarks
        WHERE strftime('%Y', add_date) = ?
        AND strftime('%m', add_date) = ?
        ORDER BY strftime(add_date) DESC
        """

        self.cursor.execute(query, (year,month))
        return [Bookmark(record) for record in self.cursor.fetchall()]
