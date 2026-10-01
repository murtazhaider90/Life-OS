from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..config import get_settings
from ..db import get_db
from ..models import CourseChunk, CourseDocument
from ..security import require_local_or_token
from ..services.documents import chunk_pages, extract_pages, sha256_bytes
from ..services.rag import index_chunk, search_course

router = APIRouter(prefix="/api/course", tags=["course"], dependencies=[Depends(require_local_or_token)])
settings = get_settings()


@router.post("/documents")
async def ingest_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    module: str | None = Form(default=None),
    week: str | None = Form(default=None),
    topic: str | None = Form(default=None),
    document_type: str = Form(default="other"),
    academic_year: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "document too large")
    digest = sha256_bytes(data)
    existing = db.scalar(select(CourseDocument).where(CourseDocument.sha256 == digest))
    if existing:
        raise HTTPException(409, f"document already ingested as id={existing.id}")
    try:
        pages = extract_pages(file.filename or "upload.txt", data)
    except ValueError as exc:
        raise HTTPException(415, str(exc)) from exc
    doc = CourseDocument(
        title=title, module=module, week=week, topic=topic, document_type=document_type,
        source="user_upload", academic_year=academic_year,
        original_filename=file.filename or "upload", sha256=digest,
    )
    db.add(doc); db.flush()
    chunks = []
    for idx, (page, content) in enumerate(chunk_pages(pages)):
        chunk = CourseChunk(document_id=doc.id, chunk_index=idx, page=page, content=content)
        db.add(chunk); db.flush(); index_chunk(db, chunk, doc); chunks.append(chunk)
    db.commit(); db.refresh(doc)
    return {"document_id": doc.id, "chunks": len(chunks), "sha256": digest}


@router.get("/search")
def search(q: str, module: str | None = None, limit: int = 5, db: Session = Depends(get_db)):
    if limit < 1 or limit > 20:
        raise HTTPException(422, "limit must be 1..20")
    try:
        return search_course(db, q, module=module, limit=limit)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
