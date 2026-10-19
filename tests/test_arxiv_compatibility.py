"""Exercise the installed arxiv library interface without live network requests."""

from datetime import datetime, timezone
from unittest.mock import patch

import arxiv
import pytest

from source_crate.builtin_functions import search_arxiv


@pytest.mark.asyncio
async def test_arxiv_search_uses_supported_client_interface():
    paper = arxiv.Result(
        entry_id="https://arxiv.org/abs/1706.03762v7",
        title="Attention Is All You Need",
        published=datetime(2017, 6, 12, tzinfo=timezone.utc),
        authors=[arxiv.Result.Author("Ashish Vaswani")],
        summary="The Transformer uses attention mechanisms.",
        categories=["cs.CL"],
        links=[arxiv.Result.Link("https://arxiv.org/pdf/1706.03762v7", title="pdf")],
    )
    # Search.results was removed in arxiv 4; use the real Search and Result types.
    with patch.object(
        arxiv.Client, "results", autospec=True, return_value=iter([paper])
    ) as fetch:
        results = await search_arxiv("attention", limit=3)
    assert len(results) == 1
    assert results[0]["title"] == paper.title
    assert results[0]["authors"] == ["Ashish Vaswani"]
    assert results[0]["year"] == 2017
    assert results[0]["pdf_url"] == "https://arxiv.org/pdf/1706.03762v7"
    assert results[0]["arxiv_id"] == "1706.03762v7"
    search = fetch.call_args.args[1]
    assert search.query == "attention"
    assert search.max_results == 3


@pytest.mark.asyncio
async def test_arxiv_network_failure_does_not_break_other_sources(caplog):
    with patch.object(
        arxiv.Client, "results", side_effect=ConnectionError("unavailable")
    ):
        assert await search_arxiv("attention") == []
    assert "unavailable" in caplog.text
