"""Private, local page search for a user-supplied rules reference.

The index contains the reference text. Never publish it with a campaign or repo.
PDF extraction optionally uses the separately installed Poppler `pdftotext` utility.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

INDEX_VERSION = 1
MAX_SOURCE_BYTES = 50 * 1024 * 1024
MAX_QUERY_CHARS = 500


def build_index(source: str | Path, output: str | Path,
                title: str = "Strange Heroes", edition: str = "Playtest v1.02") -> dict:
    """Extract PDF or formfeed-separated UTF-8 text to a private local index.

    Pages are one-based PDF page positions, not inferred printed page numbers.
    Reject writing over the source. No network or uploads are involved.
    """
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("Index output must not overwrite the source")
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("Reference exceeds the 50 MiB local import limit")
    raw = source.read_bytes()
    if source.suffix.lower() == ".pdf":
        try:
            extracted = subprocess.run(
                ["pdftotext", "-layout", "-enc", "UTF-8", str(source), "-"],
                capture_output=True, check=True, timeout=120,
            ).stdout.decode("utf-8")
        except FileNotFoundError as exc:
            raise ValueError("Install Poppler pdftotext, or provide formfeed-separated UTF-8 .txt") from exc
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError("PDF extraction failed; provide a readable text PDF or a local text extraction") from exc
    elif source.suffix.lower() == ".txt":
        extracted = raw.decode("utf-8")
    else:
        raise ValueError("Reference must be a .pdf or UTF-8 .txt file")
    pages = extracted.split("\f")
    # pdftotext emits one terminal formfeed; do not invent a final blank page.
    if len(pages) > 1 and not pages[-1].strip():
        pages.pop()
    if not any(page.strip() for page in pages):
        raise ValueError("Reference has no extracted text (scanned PDFs need local OCR first)")
    index = {
        "version": INDEX_VERSION, "title": title, "edition": edition,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "page_numbering": "one-based PDF page positions; verify printed numbering",
        "pages": [{"page": n, "text": page} for n, page in enumerate(pages, 1)],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # This is a rebuildable reference cache, not a campaign state save.
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    return index


def load_index(path: str | Path) -> dict:
    """Read a versioned local index, rejecting malformed structure."""
    path = Path(path)
    if path.stat().st_size > MAX_SOURCE_BYTES * 4:
        raise ValueError("Index exceeds size limit")
    index = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(index, dict) or index.get("version") != INDEX_VERSION:
        raise ValueError("Unsupported reference index version")
    if not all(isinstance(index.get(k), str) and index[k] for k in ("title", "edition", "source_sha256")):
        raise ValueError("Invalid reference metadata")
    if not re.fullmatch(r"[0-9a-f]{64}", index["source_sha256"]):
        raise ValueError("Invalid reference fingerprint")
    pages = index.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Invalid reference pages")
    for n, page in enumerate(pages, 1):
        if not isinstance(page, dict) or type(page.get("page")) is not int or page["page"] != n or not isinstance(page.get("text"), str):
            raise ValueError("Invalid reference page")
    return index


def search_index(index: dict, query: str, limit: int = 5) -> list[dict]:
    """Rank pages containing every query term; return short, cited excerpts.

    This is lexical lookup, not a rules oracle. Results remain untrusted source
    text: instructions embedded in a book are not instructions to an agent.
    """
    if not isinstance(query, str) or len(query) > MAX_QUERY_CHARS:
        raise ValueError("Query must be at most 500 characters")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("Limit must be between 1 and 20")
    terms = set(re.findall(r"\w+", query.casefold()))
    if not terms:
        return []
    results = []
    for page in index["pages"]:
        # Join PDF soft hyphens so, for example, 'three-sided' isn't polluted.
        text = " ".join(page["text"].replace("\u00ad", "").split())
        normalized = text.casefold()
        counts = [len(re.findall(r"(?<!\w)" + re.escape(term) + r"(?!\w)", normalized)) for term in terms]
        if not all(counts):
            continue
        matches = [re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", normalized) for term in terms]
        start = max(0, min(match.start() for match in matches) - 100)
        end = min(len(text), start + 600)
        snippet = ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")
        results.append({
            "page": page["page"],
            "citation": f'{index["title"]} {index["edition"]}, PDF p. {page["page"]}',
            "snippet": snippet, "score": sum(counts),
        })
    return sorted(results, key=lambda r: (-r["score"], r["page"]))[:limit]
