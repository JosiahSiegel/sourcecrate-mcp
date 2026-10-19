import asyncio
from unittest.mock import AsyncMock

import pytest

from source_crate.utils import smart_search


@pytest.mark.asyncio
async def test_browse_adapter_preserves_metadata_only_papers_and_reports_partial_search(monkeypatch):
    from source_crate.core import research

    papers = [
        {"title": "Quantum transport", "doi": "10.1234/one", "source": "fast"},
        {"title": "Quantum transport", "doi": "10.1234/two", "source": "fast"},
    ]
    search = AsyncMock(return_value=(papers, {"timed_out_sources": ["slow"]}))
    monkeypatch.setattr(research, "_lazy_import_utils", lambda: {"smart_downloadable_search": search})
    monkeypatch.setattr(research, "_lazy_import_search_functions", lambda: {})
    response = (await research.browse_papers("quantum transport", 2))[0]
    assert response["total_found"] == 2
    assert all(not paper["is_downloadable"] for paper in response["results"])
    assert response["partial"] is True
    assert response["timed_out_sources"] == ["slow"]


@pytest.mark.asyncio
async def test_metadata_search_keeps_completed_results_and_cancels_slow_sources(monkeypatch):
    monkeypatch.setattr(smart_search, "SEARCH_TIMEOUT_SECONDS", 0.1)
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def slow(query, limit):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    async def fast(query, limit):
        await started.wait()
        return [
            {"title": "Quantum transport", "doi": "10.1234/one", "source": "fast"},
            {"title": "Quantum transport", "doi": "10.1234/two", "source": "fast"},
        ]

    papers, log = await asyncio.wait_for(smart_search.smart_downloadable_search(
        "quantum transport", 2, {"slow": slow, "fast": fast}, {},
        {"slow": True, "fast": True}, metadata_only=True,
    ), 3)
    assert len(papers) == 2  # Metadata remains usable without PDFs; distinct DOIs survive.
    assert cancelled.is_set()
    assert log["timed_out_sources"] == ["slow"]
    assert log["results_per_source"]["fast"]["count"] == 2


@pytest.mark.asyncio
async def test_cancelling_search_cleans_up_source_tasks():
    started = asyncio.Event()
    stopped = asyncio.Event()

    async def source(query, limit):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    task = asyncio.create_task(smart_search.smart_downloadable_search(
        "quantum transport", 2, {"slow": source}, {}, {"slow": True}, metadata_only=True,
    ))
    await asyncio.wait_for(started.wait(), 3)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert stopped.is_set()
