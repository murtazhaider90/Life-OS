from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas import WeeklyPlanRequest, WeeklyReplanRequest
from ..security import require_local_or_token
from ..services.weekly_planner import build_weekly_plan, get_active_weekly_plan, replan_week, _serialize_plan

router = APIRouter(prefix="/api/plans/weekly", tags=["weekly-planning"], dependencies=[Depends(require_local_or_token)])


@router.post("")
def create_weekly_plan(payload: WeeklyPlanRequest, db: Session = Depends(get_db)):
    try:
        return build_weekly_plan(
            db,
            payload.week_start,
            payload.day_start_hour,
            payload.day_end_hour,
            payload.max_block_minutes,
            payload.minimum_gap_minutes,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/active")
def active_weekly_plan(week_start: date, db: Session = Depends(get_db)):
    plan = get_active_weekly_plan(db, week_start)
    if not plan:
        raise HTTPException(404, "active weekly plan not found")
    return _serialize_plan(db, plan)


@router.post("/replan")
def replan(payload: WeeklyReplanRequest, db: Session = Depends(get_db)):
    try:
        return replan_week(
            db,
            payload.week_start,
            payload.as_of,
            payload.day_start_hour,
            payload.day_end_hour,
            payload.max_block_minutes,
            payload.minimum_gap_minutes,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
