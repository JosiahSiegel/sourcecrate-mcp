from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pymupdf
import pytest

from source_crate import config
from source_crate.utils import public_download
from source_crate.utils.file_utils import download_pdf


def mock_publisher(monkeypatch, body):
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        config, "get_current_config", lambda: SimpleNamespace(sources={})
    )
    monkeypatch.setattr(
        public_download, "resolve_public_host", AsyncMock(return_value="93.184.215.14")
    )
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, content=body, headers={"content-type": "application/pdf"}
                )
            ),
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body", [b"<html>Publisher login required</html>", b"%PDF-1.4 broken document"]
)
async def test_download_rejects_html_and_invalid_pdf_without_writing(
    monkeypatch, tmp_path, body
):
    mock_publisher(monkeypatch, body)
    result = await download_pdf(
        "https://papers.example/sample.pdf", str(tmp_path), title="Sample"
    )
    assert result["success"] is False
    assert "PDF" in result["error"]
    assert not list(tmp_path.glob("*.pdf"))


@pytest.mark.asyncio
async def test_download_saves_valid_pdf_contents(monkeypatch, tmp_path):
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), "Verified downloaded paper content")
        body = document.tobytes()
    mock_publisher(monkeypatch, body)
    result = await download_pdf(
        "https://papers.example/sample.pdf", str(tmp_path), title="Sample"
    )
    assert result["success"] is True
    with pymupdf.open(result["pdf_path"]) as document:
        assert document.is_pdf
        assert "Verified downloaded paper content" in document[0].get_text()
