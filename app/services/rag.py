from sqlalchemy import text
from sqlalchemy.orm import Session
from ..models import CourseChunk, CourseDocument


def _fts_query(query: str) -> str:
    tokens = [t.replace('"', '') for t in query.split() if t.strip()]
    if not tokens:
        raise ValueError("query cannot be empty")
    return " OR ".join(f'"{t}"' for t in tokens[:20])


def index_chunk(db: Session, chunk: CourseChunk, doc: CourseDocument) -> None:
    db.execute(text("DELETE FROM course_chunks_fts WHERE chunk_id=:id"), {"id": str(chunk.id)})
    db.execute(
        text("INSERT INTO course_chunks_fts(chunk_id,module,topic,title,content) VALUES(:id,:module,:topic,:title,:content)"),
        {"id": str(chunk.id), "module": doc.module or "", "topic": doc.topic or "", "title": doc.title, "content": chunk.content},
    )


def search_course(db: Session, query: str, module: str | None = None, limit: int = 5) -> list[dict]:
    match = _fts_query(query)
    rows = db.execute(
        text("SELECT chunk_id, bm25(course_chunks_fts) AS score FROM course_chunks_fts WHERE course_chunks_fts MATCH :q ORDER BY score LIMIT :limit"),
        {"q": match, "limit": max(limit * 4, limit)},
    ).all()
    results: list[dict] = []
    for chunk_id, score in rows:
        chunk = db.get(CourseChunk, int(chunk_id))
        if not chunk:
            continue
        doc = db.get(CourseDocument, chunk.document_id)
        if module and (doc.module or "").lower() != module.lower():
            continue
        results.append({
            "chunk_id": chunk.id,
            "document_id": doc.id,
            "title": doc.title,
            "module": doc.module,
            "topic": doc.topic,
            "page": chunk.page,
            "content": chunk.content,
            "retrieval_score": float(score),
            "source": doc.source,
        })
        if len(results) >= limit:
            break
    return results
