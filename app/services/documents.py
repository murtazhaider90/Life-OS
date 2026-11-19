from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from pypdf import PdfReader


SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".markdown", ".docx", ".pptx"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_pages(filename: str, data: bytes) -> list[tuple[int | None, str]]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    if suffix in {".txt", ".md", ".markdown"}:
        return [(None, data.decode("utf-8"))]
    if suffix == ".docx":
        from docx import Document
        doc = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [(None, text)]
    if suffix == ".pptx":
        from pptx import Presentation
        presentation = Presentation(io.BytesIO(data))
        slides: list[tuple[int | None, str]] = []
        for idx, slide in enumerate(presentation.slides, start=1):
            parts: list[str] = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    parts.append(shape.text)
            slides.append((idx, "\n".join(parts)))
        return slides
    raise ValueError("Supported document formats: PDF, TXT, MD, DOCX, PPTX")


def chunk_pages(
    pages: list[tuple[int | None, str]],
    target_chars: int = 1800,
    overlap_chars: int = 250,
) -> list[tuple[int | None, str]]:
    chunks: list[tuple[int | None, str]] = []
    for page, raw_text in pages:
        clean = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        clean = re.sub(r"[ \t]+", " ", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
        if not clean:
            continue
        start = 0
        while start < len(clean):
            end = min(len(clean), start + target_chars)
            if end < len(clean):
                candidates = [
                    clean.rfind("\n", start + target_chars // 2, end),
                    clean.rfind(". ", start + target_chars // 2, end),
                ]
                split = max(candidates)
                if split > start:
                    end = split + 1
            content = clean[start:end].strip()
            if content:
                chunks.append((page, content))
            if end >= len(clean):
                break
            start = max(start + 1, end - overlap_chars)
    return chunks


def infer_document_type(filename: str) -> str:
    name = Path(filename).stem.casefold()
    rules = [
        (("marking", "rubric", "mark scheme"), "marking_criteria"),
        (("coursework", "assignment", "assessment brief"), "coursework_spec"),
        (("handbook", "module guide"), "handbook"),
        (("syllabus", "module specification"), "syllabus"),
        (("lecture", "slides"), "lecture"),
        (("tutorial", "problem sheet", "problem set"), "tutorial"),
        (("worked example", "solutions"), "worked_examples"),
        (("lab", "laboratory"), "lab"),
        (("revision",), "revision"),
        (("notes",), "notes"),
    ]
    for needles, value in rules:
        if any(n in name for n in needles):
            return value
    return "other"
