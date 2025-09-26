#!/usr/bin/env python3
"""
Example client usage for the Enhanced Scholarly MCP Server

This script demonstrates how to use all the enhanced features of the
scholarly MCP server, including full-text retrieval capabilities.
"""

import asyncio
import json
from fastmcp import Client
from typing import Dict, Any, List

# Server configuration
SERVER_URL = "https://your-project.fastmcp.app/mcp"  # Replace with your deployed URL

class ScholarlyClient:
    """Enhanced client wrapper for scholarly MCP server"""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = None

    async def __aenter__(self):
        self.client = Client(self.server_url)
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def search_authors(self, name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for authors by name"""
        result = await self.client.call_tool("search_author", {"name": name, "limit": limit})
        return result.data if hasattr(result, 'data') else result

    async def search_publications(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for publications by keywords"""
        result = await self.client.call_tool("search_publications", {"query": query, "limit": limit})
        return result.data if hasattr(result, 'data') else result

    async def get_full_text_by_doi(self, doi: str, extract_text: bool = True) -> Dict[str, Any]:
        """Get full text of a paper using its DOI"""
        result = await self.client.call_tool("get_full_text_by_doi", {
            "doi": doi,
            "extract_text": extract_text
        })
        return result.data if hasattr(result, 'data') else result

    async def get_full_text_by_title(self, title: str, extract_text: bool = True) -> Dict[str, Any]:
        """Get full text of a paper using its title"""
        result = await self.client.call_tool("get_full_text_by_title", {
            "title": title,
            "extract_text": extract_text
        })
        return result.data if hasattr(result, 'data') else result

    async def find_open_access_versions(self, title: str, doi: str = "") -> Dict[str, Any]:
        """Find open access versions of a paper"""
        result = await self.client.call_tool("find_open_access_versions", {
            "title": title,
            "doi": doi
        })
        return result.data if hasattr(result, 'data') else result

    async def search_with_full_text(self, query: str, limit: int = 3, extract_text: bool = False) -> List[Dict[str, Any]]:
        """Search for papers and optionally include full text"""
        result = await self.client.call_tool("search_with_full_text", {
            "query": query,
            "limit": limit,
            "extract_text": extract_text
        })
        return result.data if hasattr(result, 'data') else result

    async def extract_pdf_text(self, pdf_url: str) -> Dict[str, Any]:
        """Extract text from a PDF URL"""
        result = await self.client.call_tool("extract_pdf_text_from_url", {"pdf_url": pdf_url})
        return result.data if hasattr(result, 'data') else result

def print_json(data: Any, title: str = ""):
    """Pretty print JSON data"""
    if title:
        print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))

async def example_author_search():
    """Example: Search for authors and get detailed information"""
    print("🔍 AUTHOR SEARCH EXAMPLE")
    print("-" * 40)

    async with ScholarlyClient(SERVER_URL) as client:
        # Search for authors
        authors = await client.search_authors("Steven Cholewiak", limit=2)
        print_json(authors, "Author Search Results")

        if authors and not authors[0].get("error"):
            # Get detailed author information
            author_id = authors[0].get("scholar_id")
            if author_id:
                detailed = await client.client.call_tool("get_author_details", {
                    "author_id": author_id,
                    "sections": ["basics", "indices", "coauthors"]
                })
                print_json(detailed.data if hasattr(detailed, 'data') else detailed,
                          "Detailed Author Information")

async def example_publication_search():
    """Example: Search for publications with metadata"""
    print("\n📄 PUBLICATION SEARCH EXAMPLE")
    print("-" * 40)

    async with ScholarlyClient(SERVER_URL) as client:
        # Search for publications
        papers = await client.search_publications("machine learning neural networks", limit=3)
        print_json(papers, "Publication Search Results")

        # Get BibTeX citation for first paper
        if papers and papers[0].get("title") and not papers[0].get("error"):
            title = papers[0]["title"]
            bibtex = await client.client.call_tool("get_bibtex_citation", {
                "publication_title": title
            })
            print_json(bibtex.data if hasattr(bibtex, 'data') else bibtex,
                      "BibTeX Citation")

async def example_open_access_detection():
    """Example: Find open access versions of papers"""
    print("\n🔓 OPEN ACCESS DETECTION EXAMPLE")
    print("-" * 40)

    async with ScholarlyClient(SERVER_URL) as client:
        # Check for open access versions
        oa_versions = await client.find_open_access_versions(
            title="Attention Is All You Need",
            doi="10.48550/arXiv.1706.03762"
        )
        print_json(oa_versions, "Open Access Versions Found")

async def example_full_text_retrieval():
    """Example: Retrieve full text of papers"""
    print("\n📖 FULL TEXT RETRIEVAL EXAMPLE")
    print("-" * 40)

    async with ScholarlyClient(SERVER_URL) as client:
        # Try to get full text by DOI (arXiv paper - should work)
        full_text = await client.get_full_text_by_doi(
            doi="10.48550/arXiv.1706.03762",  # "Attention Is All You Need"
            extract_text=True
        )

        if full_text.get("full_text"):
            # Show first 500 characters of the full text
            text_preview = full_text["full_text"][:500] + "..." if len(full_text["full_text"]) > 500 else full_text["full_text"]
            print(f"📄 Full text retrieved from {full_text.get('source', 'unknown source')}")
            print(f"📊 Number of pages: {full_text.get('num_pages', 'unknown')}")
            print(f"🔧 Extraction method: {full_text.get('extraction_method', 'unknown')}")
            print(f"\n📝 Text preview:\n{text_preview}")
        else:
            print_json(full_text, "Full Text Retrieval Result")

async def example_search_with_full_text():
    """Example: Search papers and include full text when available"""
    print("\n🔍📖 SEARCH WITH FULL TEXT EXAMPLE")
    print("-" * 40)

    async with ScholarlyClient(SERVER_URL) as client:
        # Search with full text extraction (can be slow)
        papers_with_text = await client.search_with_full_text(
            query="transformer architecture neural network",
            limit=2,
            extract_text=True  # Set to False for faster results
        )

        for i, paper in enumerate(papers_with_text):
            print(f"\n📄 Paper {i+1}: {paper.get('title', 'Unknown Title')}")
            print(f"👥 Authors: {', '.join(paper.get('author', []))}")
            print(f"📅 Year: {paper.get('year', 'Unknown')}")
            print(f"📊 Citations: {paper.get('num_citations', 0)}")

            if paper.get('full_text'):
                text_preview = paper['full_text'][:300] + "..." if len(paper['full_text']) > 300 else paper['full_text']
                print(f"📖 Full text source: {paper.get('full_text_source', 'unknown')}")
                print(f"📝 Text preview: {text_preview}")
            elif paper.get('open_access_urls'):
                print(f"🔗 Open access URLs available: {len(paper['open_access_urls'])}")
                for url in paper['open_access_urls'][:2]:  # Show first 2 URLs
                    print(f"   - {url}")
            else:
                print("❌ No full text or open access version found")

async def example_pdf_extraction():
    """Example: Extract text from a direct PDF URL"""
    print("\n📄 DIRECT PDF EXTRACTION EXAMPLE")
    print("-" * 40)

    async with ScholarlyClient(SERVER_URL) as client:
        # Example with an arXiv PDF (should work)
        pdf_url = "https://arxiv.org/pdf/1706.03762.pdf"  # "Attention Is All You Need"

        extracted = await client.extract_pdf_text(pdf_url)

        if extracted.get("text"):
            text_preview = extracted["text"][:500] + "..." if len(extracted["text"]) > 500 else extracted["text"]
            print(f"✅ Successfully extracted text from PDF")
            print(f"📊 Number of pages: {extracted.get('num_pages', 'unknown')}")
            print(f"🔧 Extraction method: {extracted.get('extraction_method', 'unknown')}")
            print(f"\n📝 Text preview:\n{text_preview}")
        else:
            print_json(extracted, "PDF Extraction Result")

async def run_all_examples():
    """Run all examples in sequence"""
    print("🚀 ENHANCED SCHOLARLY MCP SERVER - EXAMPLES")
    print("=" * 60)

    examples = [
        example_author_search,
        example_publication_search,
        example_open_access_detection,
        example_full_text_retrieval,
        example_search_with_full_text,
        example_pdf_extraction
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {str(e)}")

        print("\n" + "="*60)

async def main():
    """Main function to run examples"""
    print("Enhanced Scholarly MCP Server - Client Examples")
    print("Update SERVER_URL variable with your deployed server URL")
    print(f"Current URL: {SERVER_URL}")
    print()

    if "your-project" in SERVER_URL:
        print("⚠️  Please update SERVER_URL with your actual deployed server URL")
        return

    await run_all_examples()

if __name__ == "__main__":
    asyncio.run(main())