"""Tests for prompts.py in mcp_server_watchlist."""

from mcp_server_watchlist import prompts


def test_prompt_add_movie():
    """Test prompt_add_movie returns correct string."""
    expected = "Add 'Inception' (2010) to watchlist 'alpha-list'?"
    assert prompts.prompt_add_movie("alpha-list", "Inception", 2010) == expected


def test_prompt_unwatch_movie():
    """Test prompt_unwatch_movie returns correct string."""
    expected = "Mark 'Inception' as unwatched in watchlist 'alpha-list'?"
    assert prompts.prompt_unwatch_movie("alpha-list", "Inception") == expected


def test_prompt_delete_movie():
    """Test prompt_delete_movie returns correct string."""
    expected = "Delete 'Inception' from watchlist 'alpha-list'?"
    assert prompts.prompt_delete_movie("alpha-list", "Inception") == expected


def test_prompt_mark_watched():
    """Test prompt_mark_watched returns correct string."""
    expected = "Mark 'Inception' as watched in watchlist 'alpha-list'?"
    assert prompts.prompt_mark_watched("alpha-list", "Inception") == expected


def test_prompt_show_watchlist():
    """Test prompt_show_watchlist returns correct string."""
    expected = "Show full watchlist 'alpha-list'?"
    assert prompts.prompt_show_watchlist("alpha-list") == expected
