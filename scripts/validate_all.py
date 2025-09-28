#!/usr/bin/env python3
"""
Master validation script that runs all checks.
Used by both precommit hooks and CI workflow to ensure consistency.
"""

import subprocess
import sys
from pathlib import Path


def run_validation_script(script_name: str, description: str) -> bool:
    """Run a validation script and return its result."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")

    script_path = Path(__file__).parent / script_name

    try:
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(script_path)], check=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run {script_name}: {e}")
        return False


def main() -> int:
    """Run all validation checks."""
    print("🚀 Starting comprehensive validation suite...")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")

    all_passed = True

    # Run dependency validation
    if not run_validation_script("validate_dependencies.py", "DEPENDENCY VALIDATION"):
        all_passed = False

    # Run import and functionality validation
    if not run_validation_script(
        "validate_imports.py", "IMPORT & FUNCTIONALITY VALIDATION"
    ):
        all_passed = False

    # Run code quality validation
    if not run_validation_script("validate_code_quality.py", "CODE QUALITY VALIDATION"):
        all_passed = False

    # Run configuration validation
    if not run_validation_script(
        "validate_configuration.py", "CONFIGURATION VALIDATION"
    ):
        all_passed = False

    # Run PDF processing validation
    if not run_validation_script(
        "validate_pdf_processing.py", "PDF PROCESSING VALIDATION"
    ):
        all_passed = False

    # Run MCP server validation
    if not run_validation_script("validate_mcp_server.py", "MCP SERVER VALIDATION"):
        all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL VALIDATION CHECKS PASSED! ✅")
        print("✅ Dependencies: GOOD")
        print("✅ Imports & Functionality: GOOD")
        print("✅ Code Quality: GOOD")
        print("✅ Configuration: GOOD")
        print("✅ PDF Processing: GOOD")
        print("✅ MCP Server: GOOD")
        print("🚀 Ready for commit/deployment!")
        return 0
    else:
        print("❌ VALIDATION FAILED! ❌")
        print("🛑 Fix the issues above before committing")
        return 1


if __name__ == "__main__":
    sys.exit(main())
