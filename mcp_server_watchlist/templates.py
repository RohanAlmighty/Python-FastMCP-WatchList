"""HTML templates for the Movie Watchlist MCP Server."""

import os


def get_health_html(data):
    """Return a lightweight HTML page showing server health status.
    
    Loads the health.html template and renders it with the provided data.
    
    Args:
        data: Dict with keys: status, service, tools, prompts, resources
    """
    # Load template file
    template_dir = os.path.dirname(__file__)
    template_path = os.path.join(template_dir, "templates", "health.html")
    
    with open(template_path, "r") as f:
        html_template = f.read()
    
    # Render data into template
    tools_html = "".join(f'<div class="item">{tool}</div>' for tool in data.get("tools", []))
    prompts_html = "".join(f'<div class="item">{prompt}</div>' for prompt in data.get("prompts", []))
    resources_html = "".join(f'<div class="item">{resource}</div>' for resource in data.get("resources", []))
    
    return html_template.format(
        tools_html=tools_html,
        prompts_html=prompts_html,
        resources_html=resources_html,
    )
