"""Exercise real PDF files and the public download boundary without provider flakiness."""
import asyncio
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pdf"))
import httpx
import pymupdf
import public_download
from tools import convert, download, dispatch


class PdfTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        with pymupdf.open() as document:
            document.new_page().insert_text((72, 72), "SourceCrate PDF validation")
            self.body = document.tobytes()

    def publisher(self, callback):
        original = httpx.AsyncClient
        return patch.object(httpx, "AsyncClient", lambda **kw: original(**kw, transport=httpx.MockTransport(callback)))

    async def test_html_and_corrupt_pdf_are_rejected(self):
        for body in [b"<html>Login</html>", b"%PDF-1.4 invalid"]:
            with patch.object(public_download, "resolve_public_host", AsyncMock(return_value="93.184.215.14")), self.publisher(lambda _: httpx.Response(200, content=body)):
                result = await download([{"title": "Bad", "access_links": [{"type": "pdf", "url": "https://papers.example/a.pdf"}]}], self.root, False)
                self.assertEqual(result["downloaded"], 0)
                self.assertIn("PDF", result["files"][0]["errors"][0]["error"])
        self.assertEqual(list(self.root.iterdir()), [])

    async def test_real_pdf_download_conversion_and_no_overwrite(self):
        with patch.object(public_download, "resolve_public_host", AsyncMock(return_value="93.184.215.14")), self.publisher(lambda _: httpx.Response(200, content=self.body)):
            result = await download([{"title": "../CON: test", "access_links": [{"type": "pdf", "url": "https://papers.example/a.pdf"}]}], self.root)
        self.assertEqual(result["downloaded"], 1)
        item = result["files"][0]
        pdf = Path(item["pdf_path"])
        self.assertEqual(pdf.parent, self.root)
        self.assertIn("SourceCrate PDF validation", Path(item["conversion"]["output_path"]).read_text(encoding="utf-8"))
        text = convert(pdf, format="text")
        self.assertIn("SourceCrate PDF validation", Path(text["output_path"]).read_text())
        with self.assertRaises(FileExistsError):
            convert(pdf, format="text")
        with self.assertRaises(ValueError):
            convert(pdf, pdf)
        batch = await dispatch({"operation": "batch", "directory": str(self.root), "output_dir": str(self.root / "batch"), "format": "text"})
        self.assertEqual(batch["converted"], 1)

    async def test_private_mixed_dns_and_unsupported_urls(self):
        for address in ["127.0.0.1", "10.0.0.1", "::1", "169.254.169.254"]:
            records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 443)), (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]
            with patch.object(asyncio.get_running_loop(), "getaddrinfo", AsyncMock(return_value=records)):
                with self.assertRaises(public_download.UnsafeDownloadError):
                    await public_download.resolve_public_host(httpx.URL("https://papers.example/a.pdf"))
        for url in ["file:///tmp/test", "https://user:pass@papers.example/a.pdf", "https://papers.example:8080/a.pdf"]:
            with self.assertRaises(public_download.UnsafeDownloadError):
                await public_download.fetch_public(url, {})

    async def test_redirect_is_revalidated_and_connection_is_pinned(self):
        def response(request):
            self.assertEqual(request.url.host, "93.184.215.14")
            self.assertEqual(request.headers["host"], "papers.example")
            self.assertEqual(request.extensions["sni_hostname"], "papers.example")
            return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})
        resolver = AsyncMock(side_effect=["93.184.215.14", public_download.UnsafeDownloadError("private redirect")])
        with patch.object(public_download, "resolve_public_host", resolver), self.publisher(response):
            with self.assertRaisesRegex(ValueError, "private redirect"):
                await public_download.fetch_public("https://papers.example/a.pdf", {})
        self.assertEqual(resolver.await_count, 2)

    async def test_size_limit(self):
        with patch.object(public_download, "resolve_public_host", AsyncMock(return_value="93.184.215.14")), patch.object(public_download, "MAX_DOWNLOAD_BYTES", 20):
            for headers in [{"content-length": "999"}, {}]:
                with self.publisher(lambda _: httpx.Response(200, content=self.body, headers=headers)):
                    with self.assertRaisesRegex(ValueError, "exceeds"):
                        await public_download.fetch_public("https://papers.example/a.pdf", {})


if __name__ == "__main__":
    unittest.main()
