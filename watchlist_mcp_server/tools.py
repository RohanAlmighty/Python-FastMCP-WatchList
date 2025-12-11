# Tool functions
from watchlist_mcp_server.db import get_db_connection

def add_movie(title: str, year: int) -> str:
	"""
	Add a movie to the watchlist.
    
	Args:
		title: Movie name (exclude year)
		year: Year of release
	"""
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("INSERT INTO watchlist (title, year) VALUES (?, ?)", (title, year))
	conn.commit()
	conn.close()
	return f"Added: Title: {title}, Year: {year} to watchlist."

def mark_watched(title: str) -> str:
	"""
	Mark a movie as watched.
    
	Args:
		title: Movie name (exclude year)
	Note:
		Pass only the movie name, not including the year. If the year is present, remove it before calling.
	"""
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("SELECT year FROM watchlist WHERE title = ?", (title,))
	row = c.fetchone()
	c.execute("UPDATE watchlist SET watched = 1 WHERE title = ?", (title,))
	conn.commit()
	conn.close()
	year = row[0] if row else "Unknown"
	return f"Marked as watched: Title: {title}, Year: {year}"

def unwatch_movie(title: str) -> str:
	"""
	Mark a movie as unwatched.
    
	Args:
		title: Movie name (exclude year)
	Note:
		Pass only the movie name, not including the year. If the year is present, remove it before calling.
	"""
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("SELECT year FROM watchlist WHERE title = ?", (title,))
	row = c.fetchone()
	c.execute("UPDATE watchlist SET watched = 0 WHERE title = ?", (title,))
	conn.commit()
	conn.close()
	year = row[0] if row else "Unknown"
	return f"Marked as unwatched: Title: {title}, Year: {year}"

def delete_movie(title: str) -> str:
	"""
	Delete a movie from the watchlist.
    
	Args:
		title: Movie name (exclude year)
	Note:
		Pass only the movie name, not including the year. If the year is present, remove it before calling.
	"""
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("SELECT year FROM watchlist WHERE title = ?", (title,))
	row = c.fetchone()
	c.execute("DELETE FROM watchlist WHERE title = ?", (title,))
	conn.commit()
	conn.close()
	year = row[0] if row else "Unknown"
	return f"Deleted: Title: {title}, Year: {year} from watchlist."
