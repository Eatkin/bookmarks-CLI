import sqlite3
import os
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

    def get_random_bookmark(self):
        """Return a random bookmark"""
        query = """
        SELECT * FROM bookmarks
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
