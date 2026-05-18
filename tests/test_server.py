"""Tests for server.py in mcp_server_watchlist."""

import pytest

from mcp_server_watchlist import server


def test_import_server():
    """Test that the server module can be imported and has a main function."""
    assert hasattr(server, "main")


def test_server_main(monkeypatch):
    """Test that server.main starts the ASGI app with uvicorn."""
    called = {}

    def fake_setup_server():
        called["setup_server"] = True

    def fake_build_http_app():
        called["build_http_app"] = True
        return object()

    def fake_uvicorn_run(app, host, port):
        called["uvicorn_run"] = (app, host, port)

    monkeypatch.setattr(server, "setup_server", fake_setup_server)
    monkeypatch.setattr(server, "build_http_app", fake_build_http_app)
    monkeypatch.setattr(server.uvicorn, "run", fake_uvicorn_run)
    server.main()
    assert called.get("setup_server")
    assert called.get("build_http_app")
    assert "uvicorn_run" in called


class _FakeMCP:
    """Minimal MCP test double for capturing registrations."""

    def __init__(self):
        self.tools = []

    def tool(self, name=None):
        """Capture tool registrations."""

        def decorator(func):
            self.tools.append((name or func.__name__, func.__name__))
            return func

        return decorator

    def resource(self, _uri):
        """No-op resource decorator."""

        def decorator(func):
            return func

        return decorator

    def prompt(self):
        """No-op prompt decorator."""

        def decorator(func):
            return func

        return decorator


def test_setup_server_registers_elicitation_and_sampling_variants(monkeypatch):
    """When flags are enabled, setup_server registers elicitation and sampling variants."""
    fake_mcp = _FakeMCP()
    monkeypatch.setattr(server, "mcp", fake_mcp)
    monkeypatch.setattr(server, "init_db", lambda: None)
    monkeypatch.setattr(server.asyncio, "run", lambda _coro: None)
    monkeypatch.setenv("ENABLE_ELICITATION", "true")
    monkeypatch.setenv("ENABLE_LLM_SAMPLING", "true")

    server.setup_server()

    registered = dict(fake_mcp.tools)
    assert "create_watchlist" in registered
    assert registered["mark_watched"] == "mark_watched_with_elicitation"
    assert registered["summarize_watchlist"] == "summarize_watchlist_with_sampling"


def test_setup_server_registers_direct_variants(monkeypatch):
    """When flags are disabled, setup_server registers direct-input variants."""
    fake_mcp = _FakeMCP()
    monkeypatch.setattr(server, "mcp", fake_mcp)
    monkeypatch.setattr(server, "init_db", lambda: None)
    monkeypatch.setattr(server.asyncio, "run", lambda _coro: None)
    monkeypatch.setenv("ENABLE_ELICITATION", "false")
    monkeypatch.setenv("ENABLE_LLM_SAMPLING", "false")

    server.setup_server()

    registered = dict(fake_mcp.tools)
    assert registered["mark_watched"] == "mark_watched_with_rating"
    assert registered["summarize_watchlist"] == "summarize_watchlist_without_sampling"


def test_is_enabled_parses_truthy_and_falsey(monkeypatch):
    """Test boolean env parsing helper for both truthy and falsey values."""
    monkeypatch.setenv("FEATURE_X", "YES")
    assert server._is_enabled("FEATURE_X", "false") is True

    monkeypatch.setenv("FEATURE_X", "off")
    assert server._is_enabled("FEATURE_X", "true") is False


def test_get_health_data_contains_expected_sections():
    """Test health payload includes tools, prompts, and resources metadata."""
    data = server.get_health_data(db_connected=True)
    assert data["status"] == "healthy"
    assert data["database"] == "Database: Connected"
    assert data["database_connected"] is True
    assert "tools/show_watchlist" in data["tools"]
    assert "prompts/prompt_add_movie" in data["prompts"]
    assert "resources/watchlist://{watchlist_key}/all" in data["resources"]


def test_setup_server_does_not_crash_when_init_db_fails(monkeypatch):
    """setup_server should continue registering handlers even if DB init fails."""
    fake_mcp = _FakeMCP()
    monkeypatch.setattr(server, "mcp", fake_mcp)

    async def failing_init_db():
        raise RuntimeError("db unavailable")

    def fake_run(_coro):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(server, "init_db", failing_init_db)
    monkeypatch.setattr(server.asyncio, "run", fake_run)

    # Should not raise.
    server.setup_server()

    registered = dict(fake_mcp.tools)
    assert "create_watchlist" in registered


@pytest.mark.asyncio
async def test_health_handler_returns_html(monkeypatch):
    """Test health_handler renders HTML using template data."""

    async def fake_check_database_connection():
        return False

    monkeypatch.setattr(
        server, "check_database_connection", fake_check_database_connection
    )
    monkeypatch.setattr(server, "get_health_html", lambda data: f"ok-{data['status']}")
    response = await server.health_handler(None)
    assert response.status_code == 200
    assert response.body == b"ok-degraded"


@pytest.mark.asyncio
async def test_health_json_handler_returns_json(monkeypatch):
    """Test health_json_handler returns JSON payload."""

    async def fake_check_database_connection():
        return False

    monkeypatch.setattr(
        server, "check_database_connection", fake_check_database_connection
    )
    response = await server.health_json_handler(None)

    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert '"status":"degraded"' in body
    assert '"database":"Database: Disconnected"' in body


def test_build_http_app_adds_routes_and_cors(monkeypatch):
    """Test build_http_app appends health routes and configures CORS middleware."""

    class DummyRouter:
        def __init__(self):
            self.routes = []

    class DummyApp:
        def __init__(self):
            self.router = DummyRouter()
            self.middleware_calls = []

        def add_middleware(self, middleware, **kwargs):
            self.middleware_calls.append((middleware, kwargs))

    class DummyMCP:
        def __init__(self):
            self.app = DummyApp()

        def streamable_http_app(self):
            return self.app

    dummy_mcp = DummyMCP()
    monkeypatch.setattr(server, "mcp", dummy_mcp)
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://a.example, https://b.example")

    app = server.build_http_app()

    assert app is dummy_mcp.app
    assert len(app.router.routes) == 2
    assert app.router.routes[0].path == "/health"
    assert app.router.routes[1].path == "/health/json"
    assert len(app.middleware_calls) == 1
    middleware, kwargs = app.middleware_calls[0]
    assert middleware is server.CORSMiddleware
    assert kwargs["allow_origins"] == ["https://a.example", "https://b.example"]
