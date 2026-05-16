"""Tests for templates.py in mcp_server_watchlist."""

from mcp_server_watchlist import templates


def test_get_health_html_renders_lists():
    """Test get_health_html renders tool/prompt/resource items into template."""
    data = {
        "status": "healthy",
        "service": "Movie Watchlist MCP Server",
        "database": "Database: Connected",
        "database_connected": True,
        "tools": ["tools/show_watchlist", "tools/mark_watched"],
        "prompts": ["prompts/prompt_add_movie"],
        "resources": ["resources/watchlist://all"],
    }

    html = templates.get_health_html(data)

    assert "tools/show_watchlist" in html
    assert "prompts/prompt_add_movie" in html
    assert "resources/watchlist://all" in html
    assert "Database" in html
    assert "Database: Connected" in html
    assert '<div class="item">tools/mark_watched</div>' in html


def test_get_health_html_uses_packaged_template():
    """Test get_health_html uses the packaged health.html template."""
    data = {
        "status": "healthy",
        "database": "Disconnected",
        "database_connected": False,
        "tools": ["tools/show_watchlist"],
        "prompts": ["prompts/prompt_add_movie"],
        "resources": ["resources/watchlist://all"],
    }

    html = templates.get_health_html(data)

    assert "Movie Watchlist MCP Server - Health" in html
    assert "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);" in html
    assert "tools/show_watchlist" in html
    assert "prompts/prompt_add_movie" in html
    assert "resources/watchlist://all" in html
    assert "Disconnected" in html
