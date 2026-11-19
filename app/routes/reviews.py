from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..security import require_local_or_token
from ..services.context import weekly_context_summary
from ..services.review import build_weekly_review

router = APIRouter(prefix="/api/reviews", tags=["reviews"], dependencies=[Depends(require_local_or_token)])


@router.get("/weekly")
def weekly_review(week_start: date, db: Session = Depends(get_db)):
    result = build_weekly_review(db, week_start)
    result["physical_context"] = weekly_context_summary(db, week_start)
    return result
