"""Tests for importing the mcp_server_watchlist package."""

import mcp_server_watchlist


def test_import_package():
    """Test that the mcp_server_watchlist package can be imported and has a __file__ attribute."""
    assert hasattr(mcp_server_watchlist, "__file__")
