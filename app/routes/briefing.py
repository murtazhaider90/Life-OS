from datetime import date, datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..security import require_local_or_token
from ..services.briefing import morning_briefing

router = APIRouter(prefix="/api/briefing", tags=["briefing"], dependencies=[Depends(require_local_or_token)])


@router.get("/morning")
def morning(brief_date: date, as_of: datetime | None = None, db: Session = Depends(get_db)):
    return morning_briefing(db, brief_date, as_of=as_of)
