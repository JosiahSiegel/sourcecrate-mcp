#!/usr/bin/env python3
"""
Shared PDF processing validation script for both precommit and CI workflow.
This ensures identical validation across environments.
"""

import sys


def test_pdf_processing_imports() -> bool:
    """Test that all PDF processing imports work correctly."""
    print("🔍 Testing PDF processing imports...")

    try:
        import pymupdf4llm  # noqa: F401

        print("  ✓ pymupdf4llm available")
    except ImportError as e:
        print(f"  ❌ pymupdf4llm missing: {e}")
        return False

    try:
        import fitz  # PyMuPDF is imported as fitz  # noqa: F401

        print("  ✓ PyMuPDF (fitz) available")
    except ImportError as e:
        print(f"  ❌ PyMuPDF (fitz) missing: {e}")
        return False

    print("✓ PDF processing dependencies available")
    return True


def test_pdf_processor_functions() -> bool:
    """Test that PDF processor functions are available."""
    print("🔍 Testing PDF processor functions...")

    try:
        from paperez_mcp.utils.pdf_processor import extract_pdf_text_from_local_file

        _ = extract_pdf_text_from_local_file  # Verify it's callable
        print("  ✓ extract_pdf_text_from_local_file imported")
    except ImportError as e:
        print(f"  ❌ Failed to import PDF processor functions: {e}")
        return False

    print("✓ PDF processor functions available")
    return True


def main() -> int:
    """Run PDF processing validation."""
    print("🧪 Running PDF processing validation...")
    print("=" * 60)

    all_good = True

    # Test PDF processing imports
    if not test_pdf_processing_imports():
        all_good = False

    print()

    # Test PDF processor functions
    if not test_pdf_processor_functions():
        all_good = False

    print()
    print("=" * 60)

    if all_good:
        print("🎉 All PDF processing validation passed!")
        return 0
    else:
        print("❌ PDF processing validation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
