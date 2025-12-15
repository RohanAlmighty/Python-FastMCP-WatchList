
# Resource functions
import urllib.parse
import aiosqlite
from typing import List
from mcp_server_watchlist import db

async def get_movie(title: str) -> str:
	"""Get details of a movie from the watchlist"""
	decoded_title = urllib.parse.unquote(title)
	async with aiosqlite.connect(db.DB_PATH) as conn:
		async with conn.execute("SELECT title, year, watched, rating FROM watchlist WHERE title = ?", (decoded_title,)) as cursor:
			row = await cursor.fetchone()
	if row:
		return format_movie_row(row)
	else:
		return "Movie not found in watchlist."

async def get_all_movies() -> List[str]:
	"""Get all movies in the watchlist"""
	async with aiosqlite.connect(db.DB_PATH) as conn:
		async with conn.execute("SELECT title, year, watched, rating FROM watchlist") as cursor:
			rows = await cursor.fetchall()
	return [format_movie_row(row) for row in rows]

async def get_unwatched_movies() -> List[str]:
	"""Get all unwatched movies in the watchlist"""
	async with aiosqlite.connect(db.DB_PATH) as conn:
		async with conn.execute("SELECT title, year, watched, rating FROM watchlist WHERE watched = 0") as cursor:
			rows = await cursor.fetchall()
	return [format_movie_row(row) for row in rows]

async def get_watched_movies() -> List[str]:
	"""Get all watched movies in the watchlist"""
	async with aiosqlite.connect(db.DB_PATH) as conn:
		async with conn.execute("SELECT title, year, watched, rating FROM watchlist WHERE watched = 1") as cursor:
			rows = await cursor.fetchall()
	return [format_movie_row(row) for row in rows]

def format_movie_row(row) -> str:
	"""Format a movie row as 'Title: abc, Year: xxxx, Watched: Yes/No, Rating: x'"""
	watched = "Yes" if row[2] else "No"
	rating = row[3] if row[3] is not None else "N/A"
	return f"Title: {row[0]}, Year: {row[1]}, Watched: {watched}, Rating: {rating}"
