"""Tests for server.py in mcp_server_watchlist."""

from mcp_server_watchlist import server


def test_import_server():
    """Test that the server module can be imported and has a main function."""
    assert hasattr(server, "main")


def test_server_main(monkeypatch):
    """Test that server.main starts the ASGI app with uvicorn."""
    called = {}

    def fake_build_http_app():
        called["build_http_app"] = True
        return object()

    def fake_uvicorn_run(app, host, port):
        called["uvicorn_run"] = (app, host, port)

    monkeypatch.setattr(server, "build_http_app", fake_build_http_app)
    monkeypatch.setattr(server.uvicorn, "run", fake_uvicorn_run)
    server.main()
    assert called.get("build_http_app")
    assert "uvicorn_run" in called


def test_server_main_block(monkeypatch):
    """Test that server.main can be called as if __name__ == '__main__'."""
    called = {}

    def fake_build_http_app():
        called["build_http_app"] = True
        return object()

    def fake_uvicorn_run(app, host, port):
        called["uvicorn_run"] = (app, host, port)

    monkeypatch.setattr(server, "build_http_app", fake_build_http_app)
    monkeypatch.setattr(server.uvicorn, "run", fake_uvicorn_run)
    server.main()
    assert called.get("build_http_app")
    assert "uvicorn_run" in called
