# Development container

Open this repository with VS Code's Dev Containers extension. The container installs
Python 3.12 and the locked development and optional HTTP dependencies.

Run `uv run --locked pytest -q` and `uv run --locked python scripts/validate_code_quality.py`.
Start MCP with `uv run --locked sourcecrate`. For the optional REST API, set
`SOURCECRATE_HTTP_TOKEN` and run `uv run --locked sourcecrate-http`; port 8000 is forwarded.

The website is maintained in the neighboring `sourcecrate` repository and deployed
through GitHub Pages. No cloud deployment tools or agent-specific CLI are required.
