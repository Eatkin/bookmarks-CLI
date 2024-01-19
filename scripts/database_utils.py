import sqlite3


class Database():
    def __init__(self, db_path='bookmarks.db'):
        self.db_path = db_path
        self.db = None
        self.cursor = None

    def open_database(self):
        """Loads the database"""
        self.db = sqlite3.connect(self.db_path)
        self.cursor = self.db.cursor()

    def close_database(self):
        """Closes the database"""
        self.db.close()

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
