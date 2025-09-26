#!/usr/bin/env python3
"""
Minimal MCP Server for Testing

Use this to verify MCP is working before trying the full enhanced server.
"""

from fastmcp import FastMCP

mcp = FastMCP("Minimal Test Server")

@mcp.tool
def hello(name: str) -> str:
    """Say hello to someone"""
    return f"Hello, {name}! MCP server is working!"

@mcp.tool
def test_search() -> dict:
    """Test search functionality"""
    return {
        "message": "MCP server is working correctly!",
        "status": "success",
        "tools_available": ["hello", "test_search"]
    }

if __name__ == "__main__":
    mcp.run()