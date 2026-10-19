"""Verify a real installed stdio server, outside the repository, without network calls."""

import asyncio
import os
import sys
import tempfile

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main():
    with tempfile.TemporaryDirectory(prefix="sourcecrate-smoke-") as cwd:
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        transport = StdioTransport(
            command=sys.executable,
            args=["-m", "source_crate.cli"],
            cwd=cwd,
            env=env,
            keep_alive=False,
        )
        async with Client(transport, timeout=30) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools} == {
                "browse_papers",
                "browse_papers_streaming",
                "download_papers",
                "convert_pdf_to_text",
                "convert_pdf_to_markdown",
                "batch_convert_pdfs",
                "get_status",
                "get_help",
            }
            result = await client.call_tool("get_help", {})
            assert not result.is_error and result.content, result
            print("Installed MCP handshake, all 8 tools and get_help passed.")


if __name__ == "__main__":
    asyncio.run(main())
