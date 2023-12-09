import sqlite3
import datetime

class SailorDB():
    db_filename = 'sailor.db'
    messages_queue = []

    def __init__(self, filename):
        self.db_filename = filename
        self.conn = sqlite3.connect(self.db_filename)
        self.conn.execute('CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, author TEXT NOT NULL, author_did INTEGER NOT NULL, message TEXT NOT NULL, created TIMESTAMP)')

        self.cur = self.conn.cursor()

    def add_query(self):
        if len(self.query_queue) >= 10:
            #execute many
            self.query_queue.clear()
        else:
            self.query_queue.append(query)

    def add_user_message(self, author, author_id, message):
        sql = 'INSERT INTO messages (author, author_did, message, created) VALUES(?, ?, ?, ?)'

        if len(self.messages_queue) >= 10:
            self.cur.executemany(sql, self.messages_queue)
            self.conn.commit()
            self.messages_queue.clear()
        else:
            self.messages_queue.append((author, author_id, message, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
