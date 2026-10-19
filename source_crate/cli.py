"""Small stdio entry point; package managers own dependency installation."""

import argparse

from source_crate import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sourcecrate",
        description="Academic research MCP server. Starts the MCP stdio transport by default.",
        epilog="Configure your agent to launch this command; no API key is required.",
    )
    parser.add_argument(
        "--version", action="version", version=f"SourceCrate {__version__}"
    )
    parser.parse_args()

    from source_crate.server import main as serve

    serve()


if __name__ == "__main__":
    main()
