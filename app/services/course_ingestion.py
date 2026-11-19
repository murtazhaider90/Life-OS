from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import CourseChunk, CourseDocument
from .documents import chunk_pages, extract_pages, infer_document_type, sha256_bytes
from .rag import index_chunk


class DuplicateDocumentError(ValueError):
    pass


def ingest_document_bytes(
    db: Session,
    *,
    filename: str,
    data: bytes,
    title: str | None = None,
    module: str | None = None,
    week: str | None = None,
    topic: str | None = None,
    document_type: str | None = None,
    academic_year: str | None = None,
    source: str = "user_upload",
    analyse: bool = True,
) -> dict:
    digest = sha256_bytes(data)
    existing = db.scalar(select(CourseDocument).where(CourseDocument.sha256 == digest))
    if existing:
        raise DuplicateDocumentError(f"document already ingested as id={existing.id}")

    pages = extract_pages(filename, data)
    doc = CourseDocument(
        title=title or filename,
        module=module,
        week=week,
        topic=topic,
        document_type=document_type or infer_document_type(filename),
        source=source,
        academic_year=academic_year,
        original_filename=filename,
        sha256=digest,
    )
    db.add(doc)
    db.flush()

    chunks: list[CourseChunk] = []
    for idx, (page, content) in enumerate(chunk_pages(pages)):
        chunk = CourseChunk(
            document_id=doc.id,
            chunk_index=idx,
            page=page,
            content=content,
        )
        db.add(chunk)
        db.flush()
        index_chunk(db, chunk, doc)
        chunks.append(chunk)

    db.commit()
    db.refresh(doc)

    analysis = None
    if analyse and chunks and module:
        from .academic import analyse_document_structure
        analysis = analyse_document_structure(db, doc.id, persist=True)

    return {
        "document_id": doc.id,
        "chunks": len(chunks),
        "sha256": digest,
        "document_type": doc.document_type,
        "analysis": analysis,
    }
