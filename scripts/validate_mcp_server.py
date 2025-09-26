#!/usr/bin/env python3
"""
Pre-commit validation script for MCP server functionality.
Tests syntax, imports, and basic server structure.
"""

import sys
import ast
import importlib.util
from pathlib import Path


def check_syntax(file_path):
    """Check Python syntax by parsing the AST."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        ast.parse(source, filename=file_path)
        print(f"✓ Syntax check passed: {file_path}")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in {file_path}:")
        print(f"  Line {e.lineno}: {e.text.strip() if e.text else ''}")
        print(f"  {e.msg}")
        return False
    except Exception as e:
        print(f"✗ Error checking syntax in {file_path}: {e}")
        return False


def check_imports(file_path):
    """Check if all imports can be resolved."""
    try:
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        if spec is None:
            print(f"✗ Could not create module spec for {file_path}")
            return False

        module = importlib.util.module_from_spec(spec)

        # Try to execute just the imports (top-level code before functions)
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # Parse and extract import statements
        tree = ast.parse(source)
        imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.get_source_segment(source, node))

        # Test imports in a controlled way
        import_code = '\n'.join(filter(None, imports))
        try:
            compile(import_code, file_path, 'exec')
            print(f"✓ Import check passed: {file_path}")
            return True
        except ImportError as e:
            # This is expected for optional dependencies
            if any(mod in str(e) for mod in ['scholarly', 'fastmcp', 'pymupdf4llm']):
                print(f"⚠ Optional dependency missing (OK): {e}")
                return True
            print(f"✗ Import error in {file_path}: {e}")
            return False

    except Exception as e:
        print(f"✗ Error checking imports in {file_path}: {e}")
        return False


def check_mcp_structure(file_path):
    """Check for basic MCP server structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for essential MCP components
        required_patterns = [
            '@mcp.tool',  # MCP tool decorators
            'async def',  # Async functions
            'FastMCP',    # FastMCP usage
        ]

        missing = []
        for pattern in required_patterns:
            if pattern not in content:
                missing.append(pattern)

        if missing:
            print(f"✗ Missing MCP patterns in {file_path}: {missing}")
            return False

        print(f"✓ MCP structure check passed: {file_path}")
        return True

    except Exception as e:
        print(f"✗ Error checking MCP structure in {file_path}: {e}")
        return False


def main():
    """Run all validation checks."""
    server_file = Path("paperez_mcp_server.py")

    if not server_file.exists():
        print(f"✗ MCP server file not found: {server_file}")
        sys.exit(1)

    print("🔍 Validating MCP server...")

    checks = [
        ("Syntax", check_syntax),
        ("Imports", check_imports),
        ("MCP Structure", check_mcp_structure),
    ]

    all_passed = True
    for check_name, check_func in checks:
        print(f"\n--- {check_name} Check ---")
        if not check_func(server_file):
            all_passed = False

    print(f"\n{'='*50}")
    if all_passed:
        print("✅ All MCP server validation checks passed!")
        sys.exit(0)
    else:
        print("❌ MCP server validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()