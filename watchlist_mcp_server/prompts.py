# Prompt functions
def prompt_add_movie(title: str, year: int) -> str:
	"""Prompt to add a movie"""
	return f"Add '{title}' ({year}) to your watchlist?"

def prompt_unwatch_movie(title: str) -> str:
	"""Prompt to mark a movie as unwatched"""
	return f"Mark '{title}' as unwatched?"

def prompt_delete_movie(title: str) -> str:
	"""Prompt to delete a movie from the watchlist"""
	return f"Delete '{title}' from your watchlist?"

def prompt_mark_watched(title: str) -> str:
	"""Prompt to mark a movie as watched"""
	return f"Mark '{title}' as watched?"
