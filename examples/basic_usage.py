#!/usr/bin/env python3
"""
Basic Usage Examples for Enhanced Scholarly MCP Server

Simple, focused examples for common use cases.
"""

import asyncio
from fastmcp import Client

# Replace with your deployed server URL
SERVER_URL = "https://your-project.fastmcp.app/mcp"

async def quick_author_search():
    """Quick example: Find an author and their papers"""
    async with Client(SERVER_URL) as client:
        # Search for an author
        result = await client.call_tool("search_author", {
            "name": "Geoffrey Hinton",
            "limit": 1
        })

        author = result.data[0] if hasattr(result, 'data') and result.data else result[0]
        print(f"Found: {author['name']}")
        print(f"Affiliation: {author['affiliation']}")
        print(f"Citations: {author['citedby']}")
        print(f"Research interests: {', '.join(author['interests'])}")

async def quick_paper_search():
    """Quick example: Search for papers on a topic"""
    async with Client(SERVER_URL) as client:
        # Search for papers
        result = await client.call_tool("search_publications", {
            "query": "deep learning",
            "limit": 3
        })

        papers = result.data if hasattr(result, 'data') else result

        print("Top papers on 'deep learning':")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['author'][:3])}{'...' if len(paper['author']) > 3 else ''}")
            print(f"   Year: {paper['year']} | Citations: {paper['num_citations']}")

async def quick_full_text_search():
    """Quick example: Get full text of a specific paper"""
    async with Client(SERVER_URL) as client:
        # Try to get full text of a well-known paper
        result = await client.call_tool("get_full_text_by_title", {
            "title": "Attention Is All You Need",
            "extract_text": True
        })

        paper = result.data if hasattr(result, 'data') else result

        print(f"Title: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'][:3])}")

        if paper.get('full_text'):
            # Show first 200 characters
            preview = paper['full_text'][:200] + "..."
            print(f"✅ Full text retrieved from {paper.get('source', 'unknown')}")
            print(f"Preview: {preview}")
        elif paper.get('open_access_sources'):
            print(f"📄 Open access versions found: {len(paper['open_access_sources'])}")
            for source in paper['open_access_sources'][:2]:
                print(f"   - {source['source']}: {source['url']}")
        else:
            print("❌ No full text or open access version found")

async def quick_open_access_check():
    """Quick example: Check if a paper has open access versions"""
    async with Client(SERVER_URL) as client:
        result = await client.call_tool("find_open_access_versions", {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "doi": "10.18653/v1/N19-1423"
        })

        oa_info = result.data if hasattr(result, 'data') else result

        print(f"Checking open access for: {oa_info['title']}")

        if oa_info['open_access_sources']:
            print(f"✅ {len(oa_info['open_access_sources'])} open access version(s) found:")
            for source in oa_info['open_access_sources']:
                print(f"   - {source['source']}: {source.get('url', 'URL not available')}")
        else:
            print("❌ No open access versions found")

async def main():
    """Run basic usage examples"""
    print("🚀 Enhanced Scholarly MCP Server - Basic Usage Examples")
    print("=" * 60)

    examples = [
        ("Author Search", quick_author_search),
        ("Paper Search", quick_paper_search),
        ("Full Text Retrieval", quick_full_text_search),
        ("Open Access Check", quick_open_access_check)
    ]

    for name, example_func in examples:
        print(f"\n📝 {name}")
        print("-" * 40)
        try:
            await example_func()
        except Exception as e:
            print(f"❌ Error: {str(e)}")

        print("\n" + "="*60)

if __name__ == "__main__":
    if "your-project" in SERVER_URL:
        print("⚠️  Please update SERVER_URL with your actual deployed server URL")
    else:
        asyncio.run(main())