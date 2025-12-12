
# Tool functions
from pydantic import BaseModel, Field
from mcp_server_watchlist.db import get_db_connection
from mcp.server.fastmcp import Context

class RatingInput(BaseModel):
    """Schema for collecting rating input from user."""
    
    rating: float = Field(description="Rate the movie out of 10")

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
	# New movies have no rating by default
	return f"Added: Title: {title}, Year: {year}, Rating: N/A to watchlist."

async def mark_watched(title: str, ctx: Context) -> str:
	"""
	Mark a movie as watched.
    
	Args:
		title: Movie name (exclude year)
	Note:
		Pass only the movie name, not including the year. If the year is present, remove it before calling.
		Use elicitation to get rating from the user.
	"""
	conn = get_db_connection()
	c = conn.cursor()
	c.execute("SELECT year FROM watchlist WHERE title = ?", (title,))
	row = c.fetchone()

	if not row:
		conn.close()
		return f"Movie not found in watchlist: Title: {title}"

	# Use elicitation to get rating input from user
	result = await ctx.elicit(
		message="Great! Please provide your rating.",
		schema=RatingInput,
	)

	rating = None
	if getattr(result, "action", None) == "accept" and getattr(result, "data", None):
		rating = result.data.rating

	c.execute("UPDATE watchlist SET watched = 1, rating = ? WHERE title = ?", (rating, title))
	conn.commit()
	conn.close()
	year = row[0]
	return f"Marked as watched: Title: {title}, Year: {year}, Rating: {rating if rating is not None else 'N/A'}"

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
	c.execute("SELECT year, rating FROM watchlist WHERE title = ?", (title,))
	row = c.fetchone()
	if not row:
		conn.close()
		return f"Movie not found in watchlist: Title: {title}"
	c.execute("UPDATE watchlist SET watched = 0, rating = NULL WHERE title = ?", (title,))
	conn.commit()
	conn.close()
	year = row[0]
	rating = row[1] if row[1] is not None else 'N/A'
	return f"Marked as unwatched: Title: {title}, Year: {year}, Rating: {rating}"

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
	c.execute("SELECT year, rating FROM watchlist WHERE title = ?", (title,))
	row = c.fetchone()
	if not row:
		conn.close()
		return f"Movie not found in watchlist: Title: {title}"
	c.execute("DELETE FROM watchlist WHERE title = ?", (title,))
	conn.commit()
	conn.close()
	year = row[0]
	rating = row[1] if row[1] is not None else 'N/A'
	return f"Deleted: Title: {title}, Year: {year}, Rating: {rating} from watchlist."
