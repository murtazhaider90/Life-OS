import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas import PlanRequest
from ..security import require_local_or_token
from ..services.planner import build_daily_plan

router = APIRouter(prefix="/api/plans", tags=["planning"], dependencies=[Depends(require_local_or_token)])


@router.post("/daily")
def daily_plan(payload: PlanRequest, db: Session = Depends(get_db)):
    blocks = build_daily_plan(db, payload.plan_date, payload.day_start_hour, payload.day_end_hour, payload.minimum_gap_minutes)
    return [{
        "id": b.id,
        "plan_date": b.plan_date,
        "task_id": b.task_id,
        "starts_at": b.starts_at,
        "ends_at": b.ends_at,
        "rationale": b.rationale,
        "evidence": json.loads(b.evidence_json),
    } for b in blocks]
