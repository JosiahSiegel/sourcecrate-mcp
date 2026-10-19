"""Verify a real installed stdio server, outside the repository, without network calls."""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pymupdf
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
            status = await client.call_tool("get_status", {})
            assert not status.is_error and status.data.get("api_status"), status

            root = Path(cwd)
            inputs = root / "inputs"
            inputs.mkdir()
            pdf_path = inputs / "sample.pdf"
            marker = "Installed SourceCrate conversion check."
            with pymupdf.open() as document:
                document.new_page().insert_text((72, 72), marker)
                document.save(pdf_path)

            for name, suffix in [
                ("convert_pdf_to_text", ".txt"),
                ("convert_pdf_to_markdown", ".md"),
            ]:
                output = root / f"sample{suffix}"
                result = await client.call_tool(
                    name, {"file_path": str(pdf_path), "output_path": str(output)}
                )
                assert not result.is_error and result.data["success"], result
                assert marker in output.read_text(encoding="utf-8")
            batch_dir = root / "batch"
            result = await client.call_tool(
                "batch_convert_pdfs",
                {"directory": str(inputs), "output_dir": str(batch_dir)},
            )
            assert (
                not result.is_error and result.data["successful_conversions"] == 1
            ), result
            assert any(
                marker in path.read_text(encoding="utf-8")
                for path in batch_dir.glob("*.md")
            )
            print(
                "Installed MCP handshake, 8 tools, help/status and all PDF conversions passed."
            )


if __name__ == "__main__":
    asyncio.run(main())
