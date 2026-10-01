import hashlib
import io
import re
from pathlib import Path
from pypdf import PdfReader


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_pages(filename: str, data: bytes) -> list[tuple[int | None, str]]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    if suffix in {".txt", ".md", ".markdown"}:
        return [(None, data.decode("utf-8"))]
    raise ValueError("Supported document formats: PDF, TXT, MD")


def chunk_pages(pages: list[tuple[int | None, str]], target_chars: int = 1800, overlap_chars: int = 250) -> list[tuple[int | None, str]]:
    chunks: list[tuple[int | None, str]] = []
    for page, text in pages:
        clean = re.sub(r"\s+", " ", text).strip()
        if not clean:
            continue
        start = 0
        while start < len(clean):
            end = min(len(clean), start + target_chars)
            if end < len(clean):
                split = clean.rfind(". ", start, end)
                if split > start + target_chars // 2:
                    end = split + 1
            chunks.append((page, clean[start:end].strip()))
            if end >= len(clean):
                break
            start = max(start + 1, end - overlap_chars)
    return chunks
