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

    def export_bookmarks(self, bookmarks):
        """Exports the bookmarks to a sql file"""
        # Open database if not already open
        if not self.database_is_connected():
            self.open_database()

        # Create the table if it doesn't exist
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
