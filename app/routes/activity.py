from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..db import get_db
from ..models import ActivityEvent, ActivityLabel, ActivityRule
from ..schemas import ActivityEventBatch, ActivityRuleCreate
from ..security import require_local_or_token
from ..services.activity import label_event, prune_raw_activity, relabel_all, session_metrics

router = APIRouter(prefix="/api/activity", tags=["activity"], dependencies=[Depends(require_local_or_token)])
settings = get_settings()


@router.post("/events/bulk")
def create_events(payload: ActivityEventBatch, db: Session = Depends(get_db)):
    created = 0
    duplicates = 0
    labelled = 0
    for item in payload.events:
        if item.source_event_id:
            existing = db.scalar(select(ActivityEvent).where(
                ActivityEvent.source == item.source,
                ActivityEvent.source_event_id == item.source_event_id,
            ))
            if existing:
                duplicates += 1
                continue
        row = ActivityEvent(**item.model_dump())
        db.add(row)
        db.flush()
        if label_event(db, row):
            labelled += 1
        created += 1
    db.commit()
    return {"created": created, "duplicates": duplicates, "labelled": labelled}


@router.get("/events")
def list_events(
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    query = select(ActivityEvent).order_by(ActivityEvent.occurred_at.desc()).limit(limit)
    if start is not None:
        query = query.where(ActivityEvent.occurred_at >= start)
    if end is not None:
        query = query.where(ActivityEvent.occurred_at < end)
    return db.scalars(query).all()


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    return db.scalars(select(ActivityRule).order_by(ActivityRule.id)).all()


@router.post("/rules")
def create_rule(payload: ActivityRuleCreate, db: Session = Depends(get_db)):
    rule = ActivityRule(**payload.model_dump())
    db.add(rule); db.commit(); db.refresh(rule)
    relabel_all(db)
    return rule


@router.post("/rules/{rule_id}/disable")
def disable_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(ActivityRule, rule_id)
    if not rule:
        raise HTTPException(404, "activity rule not found")
    rule.enabled = False
    db.commit()
    relabel_all(db)
    return rule


@router.get("/study-sessions/{session_id}/metrics")
def get_session_metrics(session_id: int, db: Session = Depends(get_db)):
    try:
        return session_metrics(db, session_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/retention/prune")
def prune(retention_days: int | None = None, db: Session = Depends(get_db)):
    days = retention_days or settings.raw_activity_retention_days
    try:
        deleted = prune_raw_activity(db, days)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"deleted": deleted, "retention_days": days}
