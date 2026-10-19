import asyncio

import pytest

from source_crate.utils import result_streaming


@pytest.mark.asyncio
async def test_streaming_preserves_results_and_reports_timed_out_source(monkeypatch):
    monkeypatch.setattr(result_streaming, "SOURCE_TIMEOUT_SECONDS", 0.1)
    started = asyncio.Event()
    stopped = asyncio.Event()

    async def slow(query, limit):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    async def fast(query, limit):
        await started.wait()
        return [{"title": "Quantum transport", "doi": "10.1234/retained"}]

    async def collect():
        return [
            update
            async for update in result_streaming.create_streaming_search(
                {"slow": slow, "fast": fast}, "quantum transport", 2, {}
            )
        ]

    updates = await asyncio.wait_for(collect(), 3)
    assert stopped.is_set()
    errors = [update for update in updates if update.type == "error"]
    assert len(errors) == 1 and errors[0].source == "slow"
    assert "deadline" in errors[0].error
    final = next(update for update in updates if update.type == "final")
    assert final.results[0].data["doi"] == "10.1234/retained"
    assert final.progress["error_sources"] == 1
    assert final.progress["completed_sources"] == 1
