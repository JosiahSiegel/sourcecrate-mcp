"""Bounded downloads from public HTTP endpoints, with DNS-pinned connections."""

import asyncio
import ipaddress
import socket

import httpx

MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
MAX_REDIRECTS = 5


class UnsafeDownloadError(ValueError):
    """The URL, redirect, or response violates the download boundary."""


async def resolve_public_host(url: httpx.URL) -> str:
    if (
        url.scheme not in ("http", "https")
        or not url.host
        or url.username
        or url.password
    ):
        raise UnsafeDownloadError(
            "Only public HTTP(S) URLs without credentials are allowed"
        )
    port = url.port or (443 if url.scheme == "https" else 80)
    if port not in (80, 443):
        raise UnsafeDownloadError("Only ports 80 and 443 are allowed")
    addresses = await asyncio.wait_for(
        asyncio.get_running_loop().getaddrinfo(url.host, port, type=socket.SOCK_STREAM),
        timeout=10,
    )
    if not addresses:
        raise UnsafeDownloadError("Download host has no addresses")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global or ip.is_multicast or ip.is_reserved:
            raise UnsafeDownloadError(
                "Download host must resolve only to public addresses"
            )
    return str(addresses[0][4][0])


async def fetch_public(url: str, headers: dict[str, str]) -> httpx.Response:
    """Validate every redirect and connect to the address that was validated.

    The original host is retained for HTTP routing and TLS certificate validation.
    Environment proxies are disabled so they cannot bypass the checked destination.
    """
    try:
        target = httpx.URL(url)
    except (ValueError, httpx.InvalidURL) as exc:
        raise UnsafeDownloadError("Invalid download URL") from exc
    async with asyncio.timeout(60):
        for hop in range(MAX_REDIRECTS + 1):
            address = await resolve_public_host(target)
            request_headers = {**headers, "Host": target.netloc.decode("ascii")}
            pinned = target.copy_with(host=address, fragment=None)
            async with httpx.AsyncClient(
                timeout=30, follow_redirects=False, trust_env=False
            ) as client:
                async with client.stream(
                    "GET",
                    pinned,
                    headers=request_headers,
                    extensions={"sni_hostname": target.host},
                ) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        if hop == MAX_REDIRECTS or "location" not in response.headers:
                            raise UnsafeDownloadError(
                                "Invalid or excessive download redirects"
                            )
                        target = target.join(response.headers["location"])
                        continue
                    size_header = response.headers.get("content-length")
                    if (
                        size_header
                        and size_header.isdigit()
                        and int(size_header) > MAX_DOWNLOAD_BYTES
                    ):
                        raise UnsafeDownloadError("Download exceeds 25 MiB")
                    chunks = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > MAX_DOWNLOAD_BYTES:
                            raise UnsafeDownloadError("Download exceeds 25 MiB")
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    if response.status_code == 200:
                        # Publisher login/challenge pages often return HTTP 200,
                        # sometimes even with an application/pdf content type.
                        if not body.lstrip().startswith(b"%PDF-"):
                            raise ValueError("Server returned a non-PDF response")
                        import pymupdf

                        try:
                            with pymupdf.open(stream=body, filetype="pdf") as document:
                                if not document.is_pdf or document.page_count < 1:
                                    raise ValueError("PDF contains no pages")
                        except Exception as exc:
                            raise ValueError(
                                "Server returned an invalid PDF document"
                            ) from exc
                    # The body is already decoded by httpx; remove encoding/length metadata.
                    response_headers = dict(response.headers)
                    response_headers.pop("content-encoding", None)
                    response_headers.pop("content-length", None)
                    return httpx.Response(
                        response.status_code,
                        headers=response_headers,
                        content=body,
                        request=httpx.Request("GET", target),
                    )
    raise UnsafeDownloadError("Download did not complete")
