from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..context_models import MealRecord, SleepRecord, TrainingRecord
from ..context_schemas import MealRecordCreate, SleepRecordCreate, TrainingRecordCreate
from ..db import get_db
from ..models import ProvenanceType
from ..security import require_local_or_token
from ..services.context import current_context, weekly_context_summary

router = APIRouter(prefix="/api/context", tags=["context"], dependencies=[Depends(require_local_or_token)])


def _provenance(source: str) -> ProvenanceType:
    return ProvenanceType.USER_ESTIMATE if source == "manual_input" else ProvenanceType.EXTERNAL_SOURCE


def _delete_or_404(db: Session, model, row_id: int):
    row = db.get(model, row_id)
    if not row:
        raise HTTPException(404, "context record not found")
    db.delete(row); db.commit()
    return {"deleted": True, "id": row_id}


@router.post("/sleep")
def create_sleep(payload: SleepRecordCreate, db: Session = Depends(get_db)):
    row = SleepRecord(**payload.model_dump(), provenance_type=_provenance(payload.source))
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/sleep")
def list_sleep(limit: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)):
    return db.scalars(select(SleepRecord).order_by(SleepRecord.sleep_end.desc()).limit(limit)).all()


@router.delete("/sleep/{row_id}")
def delete_sleep(row_id: int, db: Session = Depends(get_db)):
    return _delete_or_404(db, SleepRecord, row_id)


@router.post("/training")
def create_training(payload: TrainingRecordCreate, db: Session = Depends(get_db)):
    row = TrainingRecord(**payload.model_dump(), provenance_type=_provenance(payload.source))
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/training")
def list_training(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)):
    return db.scalars(select(TrainingRecord).order_by(TrainingRecord.starts_at.desc()).limit(limit)).all()


@router.delete("/training/{row_id}")
def delete_training(row_id: int, db: Session = Depends(get_db)):
    return _delete_or_404(db, TrainingRecord, row_id)


@router.post("/meals")
def create_meal(payload: MealRecordCreate, db: Session = Depends(get_db)):
    row = MealRecord(**payload.model_dump(), provenance_type=_provenance(payload.source))
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/meals")
def list_meals(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)):
    return db.scalars(select(MealRecord).order_by(MealRecord.consumed_at.desc()).limit(limit)).all()


@router.delete("/meals/{row_id}")
def delete_meal(row_id: int, db: Session = Depends(get_db)):
    return _delete_or_404(db, MealRecord, row_id)


@router.get("/summary")
def summary(as_of: datetime | None = None, db: Session = Depends(get_db)):
    return current_context(db, as_of=as_of)


@router.get("/weekly")
def weekly(week_start: date, db: Session = Depends(get_db)):
    return weekly_context_summary(db, week_start)
