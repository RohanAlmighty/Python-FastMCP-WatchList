
# Tests for server.py

def test_import_server():
    import mcp_server_watchlist.server as server
    assert hasattr(server, "main")

def test_server_main(monkeypatch):
    import mcp_server_watchlist.server as server
    called = {}
    def fake_run(**kwargs):
        called['run'] = True
    server.mcp.run = fake_run
    server.main()
    assert called.get('run')

def test_server_main_block(monkeypatch):
    # Simulate __name__ == "__main__"
    import mcp_server_watchlist.server as server
    called = {}
    def fake_run(*a, **kw):
        called['run'] = True
    monkeypatch.setattr(server.mcp, "run", fake_run)
    server.main()
    assert called.get('run')
