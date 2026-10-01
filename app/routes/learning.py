from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import StudyAttempt
from ..schemas import StudyAttemptCreate
from ..security import require_local_or_token
from ..services.learning import topic_evidence

router = APIRouter(prefix="/api/learning", tags=["learning"], dependencies=[Depends(require_local_or_token)])


@router.post("/attempts")
def create_attempt(payload: StudyAttemptCreate, db: Session = Depends(get_db)):
    row = StudyAttempt(**payload.model_dump(), source="manual_input")
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/attempts")
def list_attempts(limit: int = 100, db: Session = Depends(get_db)):
    return db.scalars(select(StudyAttempt).order_by(StudyAttempt.attempted_at.desc()).limit(min(max(limit, 1), 500))).all()


@router.get("/topics")
def topics(as_of: datetime | None = None, db: Session = Depends(get_db)):
    return topic_evidence(db, as_of=as_of or datetime.now(timezone.utc))
