

def test_import_package():
    import mcp_server_watchlist
    assert hasattr(mcp_server_watchlist, "__file__")
