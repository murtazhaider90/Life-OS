from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import CourseDocument
from ..security import require_local_or_token
from ..services.course_ingestion import DuplicateDocumentError, ingest_document_bytes
from ..services.documents import infer_document_type
from ..services.rag import remove_document_from_index, search_course

router = APIRouter(
    prefix="/api/course",
    tags=["course"],
    dependencies=[Depends(require_local_or_token)],
)
settings = get_settings()


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, f"{file.filename or 'document'} is too large")
    return data


@router.get("/documents")
def list_documents(module: str | None = None, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(CourseDocument).order_by(CourseDocument.module, CourseDocument.title)
    ).all()
    if module:
        rows = [r for r in rows if (r.module or "").casefold() == module.casefold()]
    return rows


@router.post("/documents")
async def ingest_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    module: str | None = Form(default=None),
    week: str | None = Form(default=None),
    topic: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
    academic_year: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    data = await _read_upload(file)
    try:
        return ingest_document_bytes(
            db,
            filename=file.filename or "upload.txt",
            data=data,
            title=title or file.filename or "upload",
            module=module,
            week=week,
            topic=topic,
            document_type=document_type,
            academic_year=academic_year,
            source="user_upload",
            analyse=True,
        )
    except DuplicateDocumentError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(415, str(exc)) from exc


@router.post("/documents/bulk")
async def ingest_documents_bulk(
    files: list[UploadFile] = File(...),
    module: str = Form(...),
    academic_year: str | None = Form(default=None),
    topic: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if len(files) > 100:
        raise HTTPException(422, "bulk upload is limited to 100 files per request")

    results = []
    for file in files:
        data = await _read_upload(file)
        filename = file.filename or "upload.txt"
        try:
            result = ingest_document_bytes(
                db,
                filename=filename,
                data=data,
                title=filename,
                module=module,
                topic=topic,
                document_type=infer_document_type(filename),
                academic_year=academic_year,
                source="user_bulk_upload",
                analyse=True,
            )
            results.append({"filename": filename, "status": "ingested", **result})
        except DuplicateDocumentError as exc:
            results.append({"filename": filename, "status": "duplicate", "detail": str(exc)})
        except ValueError as exc:
            results.append({"filename": filename, "status": "unsupported_or_invalid", "detail": str(exc)})
    return {"module": module, "files": results}


@router.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(CourseDocument, document_id)
    if not doc:
        raise HTTPException(404, "course document not found")
    remove_document_from_index(db, document_id)
    title = doc.title
    db.delete(doc)
    db.commit()
    return {"deleted": True, "document_id": document_id, "title": title}


@router.get("/search")
def search(
    q: str,
    module: str | None = None,
    topic: str | None = None,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    if limit < 1 or limit > 20:
        raise HTTPException(422, "limit must be 1..20")
    try:
        return search_course(db, q, module=module, topic=topic, limit=limit)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
