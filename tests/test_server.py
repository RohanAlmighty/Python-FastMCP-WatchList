"""Tests for server.py in mcp_server_watchlist."""

from mcp_server_watchlist import server


def test_import_server():
    """Test that the server module can be imported and has a main function."""
    assert hasattr(server, "main")


def test_server_main(monkeypatch):
    """Test that server.main calls mcp.run."""
    called = {}

    def fake_run(**kwargs):
        called["run"] = True

    monkeypatch.setattr(server.mcp, "run", fake_run)
    server.main()
    assert called.get("run")


def test_server_main_block(monkeypatch):
    """Test that server.main can be called as if __name__ == '__main__'."""
    called = {}

    def fake_run(**kwargs):
        called["run"] = True

    monkeypatch.setattr(server.mcp, "run", fake_run)
    server.main()
    assert called.get("run")
