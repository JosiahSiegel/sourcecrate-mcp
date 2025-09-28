#!/usr/bin/env python3
"""
Shared dependency validation script for both precommit and CI workflow.
This ensures identical validation across environments.
"""

import sys
import subprocess
from pathlib import Path


def check_pdf_dependencies():
    """Check that all PDF processing dependencies are available."""
    print("🔍 Checking PDF processing dependencies...")

    required_deps = [
        ("PyMuPDF", "fitz"),
        ("pymupdf4llm", "pymupdf4llm"),
        ("pdfplumber", "pdfplumber"),
        ("lxml", "lxml"),
        ("beautifulsoup4", "bs4")
    ]

    missing_deps = []

    for dep_name, import_name in required_deps:
        try:
            __import__(import_name)
            print(f"  ✓ {dep_name} available")
        except ImportError:
            print(f"  ❌ {dep_name} missing")
            missing_deps.append(dep_name)

    if missing_deps:
        print(f"\n❌ Missing required PDF dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False

    print("✓ All PDF processing dependencies available")
    return True


def check_core_dependencies():
    """Check that all core MCP dependencies are available."""
    print("🔍 Checking core MCP dependencies...")

    # Core dependencies that are absolutely required
    required_deps = [
        ("fastmcp", "fastmcp"),
        ("scholarly", "scholarly"),
        ("httpx", "httpx"),
        ("aiohttp", "aiohttp"),
        ("requests", "requests"),
        ("tenacity", "tenacity"),
        ("diskcache", "diskcache"),
        ("asyncio-throttle", "asyncio_throttle"),
        ("fake-useragent", "fake_useragent"),
        ("arxiv", "arxiv"),
        ("pymed", "pymed"),
        ("semanticscholar", "semanticscholar")
    ]

    # Optional dependencies that may not be available in all environments
    optional_deps = [
        ("free-proxy", "free_proxy")
    ]

    missing_deps = []

    # Check required dependencies
    for dep_name, import_name in required_deps:
        try:
            __import__(import_name)
            print(f"  ✓ {dep_name} available")
        except ImportError:
            print(f"  ❌ {dep_name} missing")
            missing_deps.append(dep_name)

    # Check optional dependencies (warn but don't fail)
    for dep_name, import_name in optional_deps:
        try:
            __import__(import_name)
            print(f"  ✓ {dep_name} available (optional)")
        except ImportError:
            print(f"  ⚠️  {dep_name} missing (optional - may affect some functionality)")

    if missing_deps:
        print(f"\n❌ Missing required core dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False

    print("✓ All core MCP dependencies available")
    return True


def check_dev_dependencies():
    """Check that all development dependencies are available."""
    print("🔍 Checking development dependencies...")

    # Essential dev dependencies needed for validation
    essential_deps = [
        ("ruff", "ruff"),
        ("mypy", "mypy")
    ]

    # Optional dev dependencies for full development workflow
    optional_deps = [
        ("pytest", "pytest"),
        ("pytest-asyncio", "pytest_asyncio"),
        ("black", "black"),
        ("types-PyYAML", None),  # Type stubs don't have importable modules
        ("types-requests", None),
        ("types-beautifulsoup4", None)
    ]

    missing_essential = []

    # Check essential dependencies
    for dep_name, import_name in essential_deps:
        try:
            __import__(import_name)
            print(f"  ✓ {dep_name} available")
        except ImportError:
            print(f"  ❌ {dep_name} missing")
            missing_essential.append(dep_name)

    # Check optional dependencies
    for dep_name, import_name in optional_deps:
        if import_name is None:
            # For type stubs, just check if they're installed via pip
            try:
                result = subprocess.run([sys.executable, "-c", f"import pkg_resources; pkg_resources.get_distribution('{dep_name}')"],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✓ {dep_name} available (optional)")
                else:
                    print(f"  ⚠️  {dep_name} missing (optional)")
            except Exception:
                print(f"  ⚠️  {dep_name} missing (optional)")
        else:
            try:
                __import__(import_name)
                print(f"  ✓ {dep_name} available (optional)")
            except ImportError:
                print(f"  ⚠️  {dep_name} missing (optional)")

    if missing_essential:
        print(f"\n❌ Missing essential dev dependencies: {', '.join(missing_essential)}")
        print("Install with: pip install " + " ".join(missing_essential))
        return False

    print("✓ All essential development dependencies available")
    return True


def main():
    """Run dependency validation."""
    print("🧪 Running comprehensive dependency validation...")
    print("=" * 60)

    all_good = True

    # Check core dependencies
    if not check_core_dependencies():
        all_good = False

    print()

    # Check PDF dependencies
    if not check_pdf_dependencies():
        all_good = False

    print()

    # Check dev dependencies
    if not check_dev_dependencies():
        all_good = False

    print()
    print("=" * 60)

    if all_good:
        print("🎉 All dependencies validated successfully!")
        return 0
    else:
        print("❌ Dependency validation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())