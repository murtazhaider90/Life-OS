from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import StudySession
from ..schemas import StudySessionCreate, StudySessionFinish
from ..security import require_local_or_token

router = APIRouter(prefix="/api/study-sessions", tags=["study"], dependencies=[Depends(require_local_or_token)])


@router.get("")
def list_sessions(db: Session = Depends(get_db)):
    return db.scalars(select(StudySession).order_by(StudySession.id.desc()).limit(100)).all()


@router.post("")
def create_session(payload: StudySessionCreate, db: Session = Depends(get_db)):
    row = StudySession(**payload.model_dump())
    if row.actual_start is None:
        row.actual_start = datetime.now(timezone.utc)
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.post("/{session_id}/finish")
def finish_session(session_id: int, payload: StudySessionFinish, db: Session = Depends(get_db)):
    row = db.get(StudySession, session_id)
    if not row:
        raise HTTPException(404, "study session not found")
    if row.actual_start and payload.ended_at <= row.actual_start:
        raise HTTPException(422, "ended_at must be after actual_start")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit(); db.refresh(row)
    return row
