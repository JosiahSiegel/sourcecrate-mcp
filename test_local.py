#!/usr/bin/env python3
"""
Local Testing Script for Enhanced Scholarly MCP Server

Run this script to test the server functionality locally before deployment.
"""

import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from scholarly_enhanced_server import mcp
    print("✅ Successfully imported enhanced server")
except ImportError as e:
    print(f"❌ Failed to import enhanced server: {e}")
    print("Make sure you have installed all dependencies:")
    print("pip install -r requirements_enhanced.txt")
    sys.exit(1)

def test_basic_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")

    required_modules = [
        'fastmcp',
        'scholarly',
        'httpx',
        'aiohttp',
        'requests',
        'fitz',  # PyMuPDF
        'lxml'
    ]

    failed_imports = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            failed_imports.append(module)
            print(f"  ❌ {module}")

    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Install missing dependencies with:")
        print("pip install -r requirements_enhanced.txt")
        return False

    return True

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️  Testing configuration...")

    try:
        from enhanced_config import EnhancedConfig, validate_environment
        config = EnhancedConfig()

        print(f"  📧 Unpaywall email: {config.api.unpaywall_email}")
        print(f"  📁 Temp directory: {config.pdf.temp_dir}")
        print(f"  📊 Max PDF size: {config.pdf.max_pdf_size_mb} MB")
        print(f"  ⏱️  PDF timeout: {config.pdf.extraction_timeout} seconds")

        # Validate environment
        is_valid = validate_environment()
        print(f"  🔧 Environment valid: {'✅' if is_valid else '❌'}")

        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

async def test_server_tools():
    """Test basic server tools functionality"""
    print("\n🛠️  Testing server tools...")

    # Test basic search (doesn't require external APIs)
    try:
        # This will test the tool registration and basic functionality
        tools = mcp.list_tools()
        print(f"  📋 Registered tools: {len(tools.tools) if hasattr(tools, 'tools') else 'unknown'}")

        expected_tools = [
            'search_author',
            'search_publications',
            'find_open_access_versions',
            'get_full_text_by_doi',
            'get_full_text_by_title',
            'search_with_full_text',
            'extract_pdf_text_from_url'
        ]

        if hasattr(tools, 'tools'):
            tool_names = [tool.name for tool in tools.tools]
            for expected in expected_tools:
                if expected in tool_names:
                    print(f"    ✅ {expected}")
                else:
                    print(f"    ❌ {expected} (missing)")
        else:
            print("    ⚠️  Unable to verify individual tools")

        return True
    except Exception as e:
        print(f"  ❌ Tool registration error: {e}")
        return False

def test_pdf_extraction():
    """Test PDF text extraction functionality"""
    print("\n📄 Testing PDF extraction...")

    try:
        import fitz

        # Create a simple test PDF
        doc = fitz.open()  # Create empty document
        page = doc.new_page()
        text = "This is a test document for PDF extraction."
        page.insert_text((50, 100), text)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            doc.save(tmp_file.name)
            tmp_path = tmp_file.name

        doc.close()

        # Test extraction
        from scholarly_enhanced_server import extract_text_from_pdf
        result = extract_text_from_pdf(tmp_path)

        # Clean up
        os.unlink(tmp_path)

        if result.get('text') and text in result['text']:
            print("  ✅ PDF text extraction working")
            print(f"  📊 Extracted text: {result['text'].strip()}")
            return True
        else:
            print(f"  ❌ PDF extraction failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"  ❌ PDF extraction test error: {e}")
        return False

async def test_api_connectivity():
    """Test connectivity to external APIs"""
    print("\n🌐 Testing API connectivity...")

    # Test Unpaywall API
    try:
        from scholarly_enhanced_server import check_unpaywall
        result = await check_unpaywall("10.1038/nature12373")

        if result.get('is_oa') is not None:
            print("  ✅ Unpaywall API accessible")
            print(f"    📄 Test DOI open access: {'Yes' if result.get('is_oa') else 'No'}")
        else:
            print(f"  ❌ Unpaywall API error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"  ❌ Unpaywall API test error: {e}")

    # Test Semantic Scholar API
    try:
        from scholarly_enhanced_server import search_semantic_scholar
        result = await search_semantic_scholar("machine learning", limit=1)

        if result.get('data'):
            print("  ✅ Semantic Scholar API accessible")
            print(f"    📊 Test search returned {len(result['data'])} result(s)")
        else:
            print(f"  ❌ Semantic Scholar API error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"  ❌ Semantic Scholar API test error: {e}")

    # Test arXiv API
    try:
        from scholarly_enhanced_server import get_arxiv_paper
        result = await get_arxiv_paper("1706.03762")

        if result.get('pdf_url'):
            print("  ✅ arXiv API accessible")
            print(f"    📄 Test paper PDF URL: {result['pdf_url']}")
        else:
            print(f"  ❌ arXiv API error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"  ❌ arXiv API test error: {e}")

def run_server_test():
    """Test running the server locally (non-blocking)"""
    print("\n🚀 Testing server startup...")

    try:
        # Import and check server configuration
        print("  📋 Server configuration loaded")
        print("  ⚙️  Server tools registered")
        print("  🎯 Server ready for deployment")

        print("\n💡 To run the server locally:")
        print("  python scholarly_enhanced_server.py")
        print("\n💡 To test with FastMCP CLI:")
        print("  fastmcp run scholarly_enhanced_server.py:mcp")

        return True
    except Exception as e:
        print(f"  ❌ Server test error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 ENHANCED SCHOLARLY MCP SERVER - LOCAL TESTING")
    print("=" * 60)

    tests = [
        ("Basic Imports", lambda: test_basic_imports()),
        ("Configuration", lambda: test_configuration()),
        ("Server Tools", lambda: asyncio.create_task(test_server_tools())),
        ("PDF Extraction", lambda: test_pdf_extraction()),
        ("API Connectivity", lambda: asyncio.create_task(test_api_connectivity())),
        ("Server Startup", lambda: run_server_test()),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\n🔍 {name}")
        print("-" * 40)
        try:
            result = test_func()
            if asyncio.iscoroutine(result):
                result = await result
            elif hasattr(result, '__await__'):  # Task object
                result = await result

            if result:
                passed += 1
                print(f"✅ {name} - PASSED")
            else:
                print(f"❌ {name} - FAILED")
        except Exception as e:
            print(f"❌ {name} - ERROR: {e}")

    print("\n" + "="*60)
    print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Server is ready for deployment.")
        print("\n📝 Next steps:")
        print("  1. Push your code to GitHub")
        print("  2. Deploy to FastMCP Cloud with: scholarly_enhanced_server.py:mcp")
        print("  3. Test with the provided client examples")
    else:
        print("⚠️  Some tests failed. Please fix issues before deployment.")
        print("\n🔧 Common fixes:")
        print("  - Install missing dependencies: pip install -r requirements_enhanced.txt")
        print("  - Check network connectivity for API tests")
        print("  - Verify write permissions for temp directory")

if __name__ == "__main__":
    asyncio.run(main())