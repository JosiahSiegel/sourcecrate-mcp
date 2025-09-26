#!/usr/bin/env python3
"""
Simple MCP server validation for pre-commit hook.
Just checks syntax and basic imports.
"""

import py_compile
import sys
from pathlib import Path


def main():
    """Simple syntax and import check for MCP server."""
    server_file = "scholarly_enhanced_server.py"

    if not Path(server_file).exists():
        print(f"✗ {server_file} not found")
        sys.exit(1)

    try:
        # Check syntax
        py_compile.compile(server_file, doraise=True)
        print(f"✓ {server_file} syntax OK")

        # Try basic import test (will fail gracefully on missing deps)
        try:
            import scholarly_enhanced_server
            print("✓ MCP server imports successfully")
        except ImportError as e:
            if 'fastmcp' in str(e) or 'scholarly' in str(e):
                print("⚠ Optional dependencies missing (OK in CI)")
            else:
                print(f"✗ Import error: {e}")
                sys.exit(1)

        print("✅ MCP server validation passed")

    except py_compile.PyCompileError as e:
        print(f"✗ Syntax error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()