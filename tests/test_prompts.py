
# Tests for prompts.py
from mcp_server_watchlist import prompts

def test_prompt_add_movie():
    assert prompts.prompt_add_movie("Inception", 2010) == "Add 'Inception' (2010) to your watchlist?"

def test_prompt_unwatch_movie():
    assert prompts.prompt_unwatch_movie("Inception") == "Mark 'Inception' as unwatched?"

def test_prompt_delete_movie():
    assert prompts.prompt_delete_movie("Inception") == "Delete 'Inception' from your watchlist?"

def test_prompt_mark_watched():
    assert prompts.prompt_mark_watched("Inception") == "Mark 'Inception' as watched?"
