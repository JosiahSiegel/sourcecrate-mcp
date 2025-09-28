#!/usr/bin/env python3
"""
Shared code quality validation script for both precommit and CI workflow.
This ensures identical validation across environments.
"""

import py_compile
import subprocess
import sys
from pathlib import Path


def check_syntax():
    """Check Python syntax for all Python files."""
    print("🔍 Checking Python syntax...")

    python_files = [
        Path("paperez_mcp/server.py"),
        *list(Path("paperez_mcp").rglob("*.py")),
    ]

    failed_files = []

    for file_path in python_files:
        if file_path.exists():
            try:
                py_compile.compile(str(file_path), doraise=True)
                print(f"  ✓ {file_path}")
            except py_compile.PyCompileError as e:
                print(f"  ❌ {file_path}: {e}")
                failed_files.append(str(file_path))

    if failed_files:
        print(f"\n❌ Syntax errors in: {', '.join(failed_files)}")
        return False

    print("✓ All Python files have valid syntax")
    return True


def run_ruff():
    """Run Ruff linting."""
    print("🔍 Running Ruff linting...")

    try:
        result = subprocess.run(
            ["ruff", "check", "paperez_mcp/"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("✓ Ruff linting passed")
            return True
        else:
            print("❌ Ruff linting failed:")
            print(result.stdout)
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("❌ Ruff not found! Install with: pip install ruff")
        return False
    except Exception as e:
        print(f"❌ Ruff error: {e}")
        return False


def run_mypy():
    """Run MyPy type checking."""
    print("🔍 Running MyPy type checking...")

    try:
        result = subprocess.run(
            ["mypy", "paperez_mcp/", "--ignore-missing-imports"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("✓ MyPy type checking passed")
            return True
        else:
            print("❌ MyPy type checking failed:")
            print(result.stdout)
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("❌ MyPy not found! Install with: pip install mypy")
        return False
    except Exception as e:
        print(f"❌ MyPy error: {e}")
        return False


def run_black_check():
    """Check Black formatting."""
    print("🔍 Checking Black formatting...")

    try:
        result = subprocess.run(
            ["black", "--check", "paperez_mcp/", "scripts/"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("✓ Black formatting is correct")
            return True
        else:
            print("❌ Black formatting issues found:")
            print(result.stdout)
            print("Run 'black paperez_mcp/ scripts/' to fix formatting")
            return False

    except FileNotFoundError:
        print("❌ Black not found! Install with: pip install black")
        return False
    except Exception as e:
        print(f"❌ Black error: {e}")
        return False


def main():
    """Run code quality validation."""
    print("🧪 Running comprehensive code quality validation...")
    print("=" * 60)

    all_good = True

    # Check syntax
    if not check_syntax():
        all_good = False

    print()

    # Run Ruff linting
    if not run_ruff():
        all_good = False

    print()

    # Run MyPy type checking
    if not run_mypy():
        all_good = False

    print()

    # Check Black formatting
    if not run_black_check():
        all_good = False

    print()
    print("=" * 60)

    if all_good:
        print("🎉 All code quality checks passed!")
        return 0
    else:
        print("❌ Code quality validation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
