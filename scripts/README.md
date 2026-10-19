# Validation scripts

Install the locked environment with `uv sync --locked --extra dev --extra http`.

- `uv run --locked python scripts/validate_code_quality.py`: syntax, Ruff, MyPy, Black.
- `uv run --locked pytest -q`: offline regression suite, including HTTP and MCP adapters.
- `uv run --locked python scripts/smoke_installed_mcp.py`: launch a real stdio server
  outside the checkout, list all eight tools, and call `get_help`.

CI also builds and installs a wheel into an isolated environment before running the
stdio smoke test. Legacy validators for configuration, imports, dependencies and
PDF processing remain available; `validate_mcp_server.py` and `validate_all.py` may
contact external academic APIs, so they are manual diagnostics rather than CI gates.
