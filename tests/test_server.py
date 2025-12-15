
# Tests for server.py
def test_import_server():
    import mcp_server_watchlist.server as server
    assert hasattr(server, "main")
