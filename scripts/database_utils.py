import sqlite3
import os


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
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()

        # Create the table if it doesn't exist
        query = """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            add_date TEXT,
            folder TEXT
        )
        """
        cursor.execute(query)

        # Insert the bookmarks
        query = """
        INSERT INTO bookmarks (title, url, add_date, folder)
        VALUES (?, ?, ?, ?)
        """
        cursor.executemany(query, bookmarks)
        db.commit()
        db.close()

    def get_categories(self):
        query = """
        SELECT DISTINCT folder FROM bookmarks
        """

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_random_bookmark(self):
        query = """
        SELECT * FROM bookmarks
        ORDER BY RANDOM()
        LIMIT 1
        """

        self.cursor.execute(query)
        return self.cursor.fetchone()
