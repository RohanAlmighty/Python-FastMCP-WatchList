"""HTML templates for the Movie Watchlist MCP Server."""

from importlib import resources

def _load_health_template() -> str:
    """Load the health template from package data."""
    template = resources.files("mcp_server_watchlist").joinpath("templates/health.html")
    return template.read_text(encoding="utf-8")


def get_health_html(data):
    """Return a lightweight HTML page showing server health status.
    
    Loads the health.html template and renders it with the provided data.
    
    Args:
        data: Dict with keys: status, service, tools, prompts, resources
    """
    html_template = _load_health_template()
    
    # Render data into template
    tools_html = "".join(f'<div class="item">{tool}</div>' for tool in data.get("tools", []))
    prompts_html = "".join(f'<div class="item">{prompt}</div>' for prompt in data.get("prompts", []))
    resources_html = "".join(f'<div class="item">{resource}</div>' for resource in data.get("resources", []))
    
    return (
        html_template
        .replace("{tools_html}", tools_html)
        .replace("{prompts_html}", prompts_html)
        .replace("{resources_html}", resources_html)
    )
