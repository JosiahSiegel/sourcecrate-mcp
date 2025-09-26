#!/usr/bin/env python3
"""
Test script for full PDF text extraction to markdown.

This script demonstrates how to use the enhanced MCP server
to extract complete text from academic papers and convert
them to markdown with 100k+ characters.

Usage:
    python test_full_extraction.py

Requirements:
    - MCP server running with updated scholarly_enhanced_server.py
    - PyMuPDF, pdfplumber dependencies installed
    - Local PDF files in articles/ directory
"""

import asyncio
import os
import sys

# Test papers in the repository
TEST_PAPERS = [
    {
        "file": "articles/resnet_paper.pdf",
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "expected_pages": 12,
        "expected_min_chars": 50000
    },
    {
        "file": "articles/bert_paper.pdf",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        "expected_pages": 16,
        "expected_min_chars": 80000
    },
    {
        "file": "articles/gan_paper.pdf",
        "title": "Generative Adversarial Networks",
        "authors": ["Ian J. Goodfellow", "Jean Pouget-Abadie", "Mehdi Mirza", "Bing Xu"],
        "expected_pages": 9,
        "expected_min_chars": 40000
    },
    {
        "file": "articles/vit_paper.pdf",
        "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
        "authors": ["Alexey Dosovitskiy", "Lucas Beyer", "Alexander Kolesnikov"],
        "expected_pages": 22,
        "expected_min_chars": 120000
    },
    {
        "file": "articles/stable_diffusion_paper.pdf",
        "title": "High-Resolution Image Synthesis with Latent Diffusion Models",
        "authors": ["Robin Rombach", "Andreas Blattmann", "Dominik Lorenz"],
        "expected_pages": 26,
        "expected_min_chars": 150000
    }
]

def test_file_exists():
    """Test that all required PDF files exist."""
    print("Testing file existence...")

    missing_files = []
    for paper in TEST_PAPERS:
        file_path = paper["file"]
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            size = os.path.getsize(file_path)
            print(f"✓ {file_path} exists ({size:,} bytes)")

    if missing_files:
        print("✗ Missing files:")
        for file in missing_files:
            print(f"  - {file}")
        return False

    return True

async def test_mcp_tools():
    """Test MCP tool availability (requires running server)."""
    print("\nTesting MCP tool availability...")

    # This would need to be adapted to actually call the MCP server
    # For now, just show what should be available

    expected_tools = [
        "extract_pdf_text_from_local_file",
        "convert_pdf_to_markdown",
        "extract_pdf_text_from_url",
        "comprehensive_search"
    ]

    print("Expected MCP tools:")
    for tool in expected_tools:
        print(f"  - mcp__scholarly-enhanced__{tool}")

    return True

async def simulate_extraction(paper):
    """Simulate the extraction process for a paper."""
    print(f"\nSimulating extraction for: {paper['title']}")
    print(f"File: {paper['file']}")

    if not os.path.exists(paper['file']):
        print(f"✗ File not found: {paper['file']}")
        return False

    file_size = os.path.getsize(paper['file'])
    print(f"File size: {file_size:,} bytes")

    # Simulate what the MCP tool would do:
    print("Simulated MCP call:")
    print(f"  mcp__scholarly-enhanced__convert_pdf_to_markdown(")
    print(f"    file_path='{paper['file']}',")
    print(f"    title='{paper['title']}',")
    print(f"    authors={paper['authors']}")
    print(f"  )")

    # Expected results
    print("Expected results:")
    print(f"  - Pages extracted: {paper['expected_pages']}")
    print(f"  - Minimum characters: {paper['expected_min_chars']:,}")
    print(f"  - Markdown file: articles_markdown/{os.path.basename(paper['file']).replace('.pdf', '_full.md')}")

    return True

async def main():
    """Main test function."""
    print("Enhanced PDF Extraction Test")
    print("=" * 50)

    # Test 1: File existence
    if not test_file_exists():
        print("\n✗ File existence test failed")
        return False

    # Test 2: MCP tools
    if not await test_mcp_tools():
        print("\n✗ MCP tool test failed")
        return False

    # Test 3: Simulate extraction for each paper
    print("\n" + "=" * 50)
    print("SIMULATION: PDF to Markdown Conversion")
    print("=" * 50)

    success_count = 0
    for paper in TEST_PAPERS:
        if await simulate_extraction(paper):
            success_count += 1

    print(f"\nSimulation Results:")
    print(f"  Papers processed: {success_count}/{len(TEST_PAPERS)}")

    if success_count == len(TEST_PAPERS):
        print("\n✓ All simulations successful!")
        print("\nTo run actual extraction with MCP server:")
        print("1. Ensure MCP server is running with updated code")
        print("2. Ensure PyMuPDF and dependencies are installed")
        print("3. Call the MCP tools for each paper")
        print("4. Verify markdown files have 100k+ characters")

        return True
    else:
        print(f"\n✗ {len(TEST_PAPERS) - success_count} simulations failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)