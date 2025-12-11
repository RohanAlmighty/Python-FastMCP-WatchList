# Database logic
import sqlite3

DB_PATH = "watchlist.db"

def init_db():
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("""
		CREATE TABLE IF NOT EXISTS watchlist (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			title TEXT NOT NULL,
			year INTEGER,
			watched INTEGER DEFAULT 0
		)
	""")
	conn.commit()
	conn.close()

def get_db_connection():
	return sqlite3.connect(DB_PATH)
