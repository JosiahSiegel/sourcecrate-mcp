"""Offline regression coverage for HTTP boundaries, transport adapters and stream isolation."""

import asyncio
import json
import socket
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from fastmcp import Client

from source_crate import http_server
from source_crate.core import research
from source_crate.core.status import get_help_core
from source_crate.server import mcp
from source_crate.utils import public_download
from source_crate.utils.fuzzy_matching import FuzzyPaperMatcher
from source_crate.utils.result_streaming import create_streaming_search


@pytest.fixture
def http_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("SOURCECRATE_HTTP_TOKEN", "test-secret")
    monkeypatch.setenv("SOURCECRATE_HTTP_ROOT", str(tmp_path))
    return tmp_path


@pytest.mark.asyncio
async def test_http_authentication(monkeypatch, http_environment):
    monkeypatch.setattr(
        http_server, "get_help_core", AsyncMock(return_value={"help": "ok"})
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=http_server.app), base_url="http://test"
    ) as client:
        assert (await client.get("/health")).status_code == 200
        assert (await client.get("/api/v1/help")).status_code == 401
        assert (
            await client.get("/api/v1/help", headers={"Authorization": "Bearer wrong"})
        ).status_code == 401
        response = await client.get(
            "/api/v1/help",
            headers={
                "Authorization": "Bearer test-secret",
                "Origin": "https://untrusted.example",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers
        schema = (await client.get("/openapi.json")).json()
        assert schema["paths"]["/api/v1/help"]["get"]["security"] == [
            {"HTTPBearer": []}
        ]
        monkeypatch.delenv("SOURCECRATE_HTTP_TOKEN")
        assert (await client.get("/api/v1/help")).status_code == 503


@pytest.mark.asyncio
async def test_http_file_confinement_and_default_outputs(monkeypatch, http_environment):
    root = http_environment
    (root / "paper.pdf").write_bytes(b"%PDF-1.4 test")
    convert = AsyncMock(return_value={"success": True})
    monkeypatch.setattr(http_server, "convert_pdf_to_text_core", convert)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=http_server.app),
        base_url="http://test",
        headers={"Authorization": "Bearer test-secret"},
    ) as client:
        for body in [
            {"file_path": "../private.pdf"},
            {"file_path": "paper.pdf", "output_path": "../private.txt"},
            {"file_path": str(root.parent / "private.pdf")},
        ]:
            assert (
                await client.post("/api/v1/convert/pdf-to-text", json=body)
            ).status_code == 400
        convert.assert_not_called()
        response = await client.post(
            "/api/v1/convert/pdf-to-text", json={"file_path": "paper.pdf"}
        )
        assert response.status_code == 200
        assert Path(convert.call_args.kwargs["output_path"]).parent == root
        assert Path(convert.call_args.kwargs["file_path"]) == root / "paper.pdf"
        assert (
            await client.get(
                "/api/v1/search/stream", params={"query": "test", "limit": 999}
            )
        ).status_code == 422


@pytest.mark.asyncio
async def test_http_rejects_link_escape(http_environment):
    target = http_environment.parent / "outside.pdf"
    target.write_bytes(b"%PDF-1.4")
    link = http_environment / "link.pdf"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("This Windows account cannot create symlinks")
    with pytest.raises(http_server.HTTPException):
        http_server.confined_path("link.pdf", pdf=True)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "::1",
        "::ffff:127.0.0.1",
        "224.0.0.1",
    ],
)
async def test_download_rejects_nonpublic_dns(monkeypatch, address):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))],
    )
    with pytest.raises(public_download.UnsafeDownloadError):
        await public_download.resolve_public_host(
            httpx.URL("https://papers.example/paper.pdf")
        )


@pytest.mark.asyncio
async def test_download_pins_dns_and_rechecks_redirects(monkeypatch):
    calls = []

    def dns(host, *args, **kwargs):
        address = "127.0.0.1" if host == "internal.example" else "93.184.215.14"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]

    def handler(request):
        calls.append(request)
        assert request.url.host == "93.184.215.14"
        assert request.headers["host"] == "papers.example"
        assert request.extensions["sni_hostname"] == "papers.example"
        return httpx.Response(
            302, headers={"location": "https://internal.example/private"}
        )

    original_client = httpx.AsyncClient
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs, transport=httpx.MockTransport(handler)
        ),
    )
    with pytest.raises(public_download.UnsafeDownloadError):
        await public_download.fetch_public("https://papers.example/paper.pdf", {})
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_download_enforces_streamed_size(monkeypatch):
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        public_download, "resolve_public_host", AsyncMock(return_value="93.184.215.14")
    )
    monkeypatch.setattr(public_download, "MAX_DOWNLOAD_BYTES", 10)
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(
                lambda req: httpx.Response(
                    200, stream=httpx.ByteStream(b"%PDF-" + b"x" * 20)
                )
            ),
        ),
    )
    with pytest.raises(public_download.UnsafeDownloadError, match="exceeds"):
        await public_download.fetch_public("https://papers.example/paper.pdf", {})


@pytest.mark.asyncio
async def test_concurrent_streams_are_isolated():
    both_started = asyncio.Event()
    count = 0

    async def source(query, limit):
        nonlocal count
        count += 1
        if count == 2:
            both_started.set()
        await both_started.wait()
        return [{"title": query, "doi": f"10.1234/{query}", "source": "mock"}]

    async def collect(query):
        final = None
        async for update in create_streaming_search({"mock": source}, query, 5, {}):
            if update.type == "final":
                final = update.results
        return [result.data["title"] for result in final]

    assert await asyncio.wait_for(
        asyncio.gather(collect("galaxies"), collect("diabetes")), 3
    ) == [["galaxies"], ["diabetes"]]


@pytest.mark.asyncio
async def test_core_does_not_depend_on_decorator_wrappers(monkeypatch):
    monkeypatch.setattr(research, "get_help", AsyncMock(return_value={"ok": True}))
    assert await get_help_core() == {"ok": True}


@pytest.mark.asyncio
async def test_mcp_lists_and_calls_registered_tools():
    async with Client(mcp) as client:
        names = {tool.name for tool in await client.list_tools()}
        assert names == {
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
        assert not result.is_error
        assert result.content


def test_shared_paper_identity_contract():
    contract = json.loads(
        (Path(__file__).parent / "fixtures/paper-contract.json").read_text(
            encoding="utf-8"
        )
    )
    matcher = FuzzyPaperMatcher()
    for case in contract["identity_cases"]:
        score = matcher.calculate_match_score(case["a"], case["b"])
        assert score.is_match(matcher.match_threshold) == case["duplicate"], case[
            "name"
        ]


def test_shared_relevance_scale():
    from source_crate.utils.relevance_scorer import RelevanceScorer

    contract = json.loads(
        (Path(__file__).parent / "fixtures/paper-contract.json").read_text(
            encoding="utf-8"
        )
    )
    filtered = RelevanceScorer().filter_low_relevance(
        contract["filter_cases"], min_threshold=35
    )
    assert [paper["title"] for paper in filtered] == ["Strong match"]


@pytest.mark.asyncio
async def test_sse_final_snapshot_replaces_provisional_duplicates(
    monkeypatch, http_environment
):
    async def fast(query, limit):
        return [
            {"title": query, "doi": "10.1234/shared", "source": "fast"}
            for _ in range(3)
        ]

    async def slow(query, limit):
        await asyncio.sleep(0.05)
        return [{"title": query, "doi": "10.1234/shared", "source": "slow"}]

    monkeypatch.setattr(
        research, "_lazy_import_search_functions", lambda: {"fast": fast, "slow": slow}
    )
    monkeypatch.setattr(research, "get_api_status", lambda: {})
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=http_server.app),
        base_url="http://test",
        headers={"Authorization": "Bearer test-secret"},
    ) as client:
        response = await client.get(
            "/api/v1/search/stream", params={"query": "quantum transport"}
        )
    assert response.status_code == 200
    data = [
        json.loads(line[6:])
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    snapshots = [event for event in data if event.get("replace")]
    assert len(snapshots) == 1
    assert len(snapshots[0]["papers"]) == 1
    assert data[-1]["total_results"] == 1
    assert {event["source"]: event["count"] for event in data if "count" in event} == {
        "fast": 3,
        "slow": 1,
    }


@pytest.mark.asyncio
async def test_closing_stream_cancels_outstanding_sources():
    cancelled = asyncio.Event()

    async def fast(query, limit):
        return [{"title": "Available result"}]

    async def slow(query, limit):
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    stream = create_streaming_search({"fast": fast, "slow": slow}, "test", 5, {})
    await anext(stream)
    await stream.aclose()
    await asyncio.wait_for(cancelled.wait(), 1)


@pytest.mark.asyncio
async def test_real_pdf_conversions_stay_inside_http_workspace(
    monkeypatch, http_environment
):
    import fitz

    root = http_environment
    working = root.parent / (root.name + "-cwd")
    working.mkdir()
    monkeypatch.chdir(working)
    with fitz.open() as pdf:
        pdf.new_page().insert_text((72, 72), "Quantum transport regression document.")
        pdf.save(root / "paper.pdf")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=http_server.app),
        base_url="http://test",
        headers={"Authorization": "Bearer test-secret"},
    ) as client:
        for endpoint, suffix in [("pdf-to-text", "txt"), ("pdf-to-markdown", "md")]:
            response = await client.post(
                f"/api/v1/convert/{endpoint}", json={"file_path": "paper.pdf"}
            )
            assert response.status_code == 200
            assert response.json()["success"], response.text
            assert "Quantum transport" in (root / f"paper_full.{suffix}").read_text(
                encoding="utf-8"
            )
        response = await client.post(
            "/api/v1/convert/batch",
            json={"directory": ".", "output_dir": "batch-output"},
        )
        assert response.status_code == 200
        assert (root / "batch-output/paper_full.md").is_file(), response.text
    assert not (working / ".sourcecrate").exists()
