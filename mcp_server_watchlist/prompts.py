
"""Prompt functions for the Movie Watchlist MCP server."""

# Prompt functions
def prompt_add_movie(watchlist_key: str, title: str, year: int) -> str:
    """Prompt to add a movie to a specific watchlist."""
    return f"Add '{title}' ({year}) to watchlist '{watchlist_key}'?"

def prompt_unwatch_movie(watchlist_key: str, title: str) -> str:
    """Prompt to mark a movie as unwatched in a specific watchlist."""
    return f"Mark '{title}' as unwatched in watchlist '{watchlist_key}'?"

def prompt_delete_movie(watchlist_key: str, title: str) -> str:
    """Prompt to delete a movie from a specific watchlist."""
    return f"Delete '{title}' from watchlist '{watchlist_key}'?"

def prompt_mark_watched(watchlist_key: str, title: str) -> str:
    """Prompt to mark a movie as watched in a specific watchlist."""
    return f"Mark '{title}' as watched in watchlist '{watchlist_key}'?"


def prompt_show_watchlist(watchlist_key: str) -> str:
    """Prompt to show a specific watchlist."""
    return f"Show full watchlist '{watchlist_key}'?"
