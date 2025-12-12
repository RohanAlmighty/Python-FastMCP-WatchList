
# Resource functions
import urllib.parse
from typing import List
from mcp_server_watchlist.db import get_db_connection

def get_movie(title: str) -> str:
	"""Get details of a movie from the watchlist"""
	decoded_title = urllib.parse.unquote(title)
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("SELECT title, year, watched, rating FROM watchlist WHERE title = ?", (decoded_title,))
	row = c.fetchone()
	conn.close()
	if row:
		return format_movie_row(row)
	else:
		return "Movie not found in watchlist."

def get_all_movies() -> List[str]:
	"""Get all movies in the watchlist"""
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("SELECT title, year, watched, rating FROM watchlist")
	rows = c.fetchall()
	conn.close()
	return [format_movie_row(row) for row in rows]

def get_unwatched_movies() -> List[str]:
	"""Get all unwatched movies in the watchlist"""
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("SELECT title, year, watched, rating FROM watchlist WHERE watched = 0")
	rows = c.fetchall()
	conn.close()
	return [format_movie_row(row) for row in rows]

def get_watched_movies() -> List[str]:
	"""Get all watched movies in the watchlist"""
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("SELECT title, year, watched, rating FROM watchlist WHERE watched = 1")
	rows = c.fetchall()
	conn.close()
	return [format_movie_row(row) for row in rows]

def format_movie_row(row) -> str:
	"""Format a movie row as 'Title: abc, Year: xxxx, Watched: Yes/No, Rating: x'"""
	watched = "Yes" if row[2] else "No"
	rating = row[3] if row[3] is not None else "N/A"
	return f"Title: {row[0]}, Year: {row[1]}, Watched: {watched}, Rating: {rating}"
