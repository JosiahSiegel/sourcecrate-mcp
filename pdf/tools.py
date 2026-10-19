# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx==0.28.1", "pymupdf==2.0", "pymupdf4llm==2.0"]
# ///
"""Local PDF operations only. Search and ranking belong to sourcecrate.org's engine."""
import asyncio
import contextlib
import hashlib
import json
from pathlib import Path
import re
import sys

from public_download import fetch_public


def convert(file_path, output_path=None, format="markdown"):
    import pymupdf

    source = Path(file_path).expanduser().resolve(strict=True)
    target = Path(output_path).expanduser().resolve() if output_path else source.with_suffix(".md" if format == "markdown" else ".txt")
    if target == source:
        raise ValueError("Output cannot replace the input PDF")
    with pymupdf.open(source) as document:
        if not document.is_pdf or document.page_count < 1:
            raise ValueError("Input must be a valid, nonempty PDF")
        pages = document.page_count
        if format == "text":
            text = "\n".join(page.get_text() for page in document)
        else:
            import pymupdf4llm
            text = pymupdf4llm.to_markdown(document)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as output:
        output.write(text)
    return {"success": True, "file_path": str(source), "output_path": str(target), "pages": pages, "characters": len(text)}


async def download(papers, output_dir, convert_to_markdown=True):
    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    # Bound work as well as each individual request. Try alternate PDF links when available.
    semaphore = asyncio.Semaphore(3)

    async def one(paper):
        async with semaphore:
            errors = []
            for link in [item for item in paper.get("access_links", []) if item["type"] == "pdf"][:3]:
                try:
                    response = await fetch_public(link["url"], {"User-Agent": "SourceCrate/3.0 (+https://sourcecrate.org)"})
                    response.raise_for_status()
                    title = re.sub(r'[^\w .-]', '_', paper.get("title") or "paper")[:100].strip(" .") or "paper"
                    digest = hashlib.sha256(response.content).hexdigest()[:12]
                    target = destination / f"paper-{title}-{digest}.pdf"
                    with target.open("xb") as output:
                        output.write(response.content)
                    result = {"success": True, "title": paper.get("title"), "url": link["url"], "pdf_path": str(target)}
                    if convert_to_markdown:
                        try:
                            result["conversion"] = convert(target)
                        except Exception as error:
                            result["conversion"] = {"success": False, "error": str(error)}
                    return result
                except Exception as error:
                    errors.append({"url": link["url"], "error": str(error)})
            return {"success": False, "title": paper.get("title"), "errors": errors}

    results = await asyncio.gather(*(one(paper) for paper in papers))
    return {"files": results, "downloaded": sum(item["success"] for item in results), "requested": len(papers)}


async def dispatch(request):
    operation = request.pop("operation")
    if operation == "convert":
        return convert(**request)
    if operation == "download":
        return await download(**request)
    if operation == "batch":
        directory = Path(request["directory"]).expanduser().resolve(strict=True)
        output = Path(request.get("output_dir") or directory).expanduser().resolve()
        format = request.get("format", "markdown")
        files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
        if len(files) > 100:
            raise ValueError("Batch limit is 100 PDFs; select a smaller directory")
        results = []
        for source in files:
            try:
                results.append(convert(source, output / (source.stem + (".md" if format == "markdown" else ".txt")), format))
            except Exception as error:
                results.append({"success": False, "file_path": str(source), "error": str(error)})
        return {"files": results, "converted": sum(item["success"] for item in results)}
    raise ValueError("Unknown PDF operation")


if __name__ == "__main__":
    # Third-party converters can print diagnostics; never corrupt the JSON response.
    with contextlib.redirect_stdout(sys.stderr):
        try:
            result = asyncio.run(dispatch(json.load(sys.stdin)))
        except Exception as error:
            result = {"success": False, "error": str(error)}
    print(json.dumps(result, ensure_ascii=False))
