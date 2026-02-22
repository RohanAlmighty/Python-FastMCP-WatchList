"""Tests for prompts.py in mcp_server_watchlist."""

from mcp_server_watchlist import prompts


def test_prompt_add_movie():
    """Test prompt_add_movie returns correct string."""
    expected = "Add 'Inception' (2010) to your watchlist?"
    assert prompts.prompt_add_movie("Inception", 2010) == expected


def test_prompt_unwatch_movie():
    """Test prompt_unwatch_movie returns correct string."""
    expected = "Mark 'Inception' as unwatched?"
    assert prompts.prompt_unwatch_movie("Inception") == expected


def test_prompt_delete_movie():
    """Test prompt_delete_movie returns correct string."""
    expected = "Delete 'Inception' from your watchlist?"
    assert prompts.prompt_delete_movie("Inception") == expected


def test_prompt_mark_watched():
    """Test prompt_mark_watched returns correct string."""
    expected = "Mark 'Inception' as watched?"
    assert prompts.prompt_mark_watched("Inception") == expected
