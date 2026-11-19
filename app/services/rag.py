from __future__ import annotations

import re
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from ..models import CourseChunk, CourseDocument


_STOPWORDS = {
    "a","an","and","are","as","at","be","by","for","from","how","i","in","is",
    "it","me","my","of","on","or","that","the","this","to","what","when","where",
    "which","who","why","with",
}

_SOURCE_PRIORITY = {
    "handbook": 100,
    "syllabus": 95,
    "coursework_spec": 95,
    "marking_criteria": 95,
    "lecture": 80,
    "tutorial": 75,
    "worked_examples": 75,
    "lab": 70,
    "revision": 65,
    "notes": 55,
    "other": 50,
}

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions?", re.I),
    re.compile(r"system\s+prompt", re.I),
    re.compile(r"you\s+are\s+(?:chatgpt|an?\s+assistant)", re.I),
    re.compile(r"follow\s+these\s+instructions", re.I),
    re.compile(r"developer\s+message", re.I),
]


def _query_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-%.]*", query.casefold())
    useful = [t for t in tokens if t not in _STOPWORDS and len(t) > 1]
    return useful[:20] or tokens[:12]


def _fts_query(query: str) -> str:
    tokens = [t.replace('"', "") for t in _query_tokens(query) if t.strip()]
    if not tokens:
        raise ValueError("query cannot be empty")
    return " OR ".join(f'"{t}"' for t in tokens)


def source_priority(document_type: str) -> int:
    return _SOURCE_PRIORITY.get((document_type or "other").casefold(), 50)


def detect_untrusted_instructions(content: str) -> list[str]:
    flags: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(content):
            flags.append(pattern.pattern)
    return flags


def index_chunk(db: Session, chunk: CourseChunk, doc: CourseDocument) -> None:
    db.execute(text("DELETE FROM course_chunks_fts WHERE chunk_id=:id"), {"id": str(chunk.id)})
    db.execute(
        text(
            "INSERT INTO course_chunks_fts(chunk_id,module,topic,title,content) "
            "VALUES(:id,:module,:topic,:title,:content)"
        ),
        {
            "id": str(chunk.id),
            "module": doc.module or "",
            "topic": doc.topic or "",
            "title": doc.title,
            "content": chunk.content,
        },
    )


def remove_document_from_index(db: Session, document_id: int) -> None:
    ids = db.scalars(
        select(CourseChunk.id).where(CourseChunk.document_id == document_id)
    ).all()
    for chunk_id in ids:
        db.execute(text("DELETE FROM course_chunks_fts WHERE chunk_id=:id"), {"id": str(chunk_id)})


def search_course(
    db: Session,
    query: str,
    module: str | None = None,
    topic: str | None = None,
    limit: int = 5,
) -> list[dict]:
    match = _fts_query(query)
    candidate_limit = min(max(limit * 12, 60), 400)
    rows = db.execute(
        text(
            "SELECT chunk_id, bm25(course_chunks_fts) AS score "
            "FROM course_chunks_fts "
            "WHERE course_chunks_fts MATCH :q "
            "ORDER BY score LIMIT :limit"
        ),
        {"q": match, "limit": candidate_limit},
    ).all()

    results: list[dict] = []
    for chunk_id, score in rows:
        chunk = db.get(CourseChunk, int(chunk_id))
        if not chunk:
            continue
        doc = db.get(CourseDocument, chunk.document_id)
        if not doc:
            continue
        if module and (doc.module or "").casefold() != module.casefold():
            continue
        if topic and topic.casefold() not in ((doc.topic or "") + " " + chunk.content).casefold():
            continue
        results.append({
            "chunk_id": chunk.id,
            "document_id": doc.id,
            "title": doc.title,
            "module": doc.module,
            "topic": doc.topic,
            "week": doc.week,
            "document_type": doc.document_type,
            "academic_year": doc.academic_year,
            "page": chunk.page,
            "content": chunk.content,
            "retrieval_score": float(score),
            "source_priority": source_priority(doc.document_type),
            "source": doc.source,
            "security_flags": detect_untrusted_instructions(chunk.content),
        })

    results.sort(key=lambda r: (-r["source_priority"], r["retrieval_score"]))
    return results[:limit]
