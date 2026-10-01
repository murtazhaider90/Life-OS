from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import CalendarEvent
from ..schemas import CalendarEventCreate
from ..security import require_local_or_token

router = APIRouter(prefix="/api/calendar", tags=["calendar"], dependencies=[Depends(require_local_or_token)])


@router.get("")
def list_events(db: Session = Depends(get_db)):
    return db.scalars(select(CalendarEvent).order_by(CalendarEvent.starts_at)).all()


@router.post("")
def create_event(payload: CalendarEventCreate, db: Session = Depends(get_db)):
    duplicate = db.scalar(select(CalendarEvent).where(
        CalendarEvent.title == payload.title,
        CalendarEvent.starts_at == payload.starts_at,
        CalendarEvent.ends_at == payload.ends_at,
        CalendarEvent.source == payload.source,
    ))
    if duplicate:
        raise HTTPException(409, "duplicate calendar event")
    event = CalendarEvent(**payload.model_dump())
    db.add(event); db.commit(); db.refresh(event)
    return event
