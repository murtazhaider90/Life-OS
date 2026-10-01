from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import UserStateInput
from ..schemas import UserStateInputCreate
from ..security import require_local_or_token

router = APIRouter(prefix="/api/state-inputs", tags=["state"], dependencies=[Depends(require_local_or_token)])


@router.post("")
def create_state_input(payload: UserStateInputCreate, db: Session = Depends(get_db)):
    row = UserStateInput(**payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("")
def list_state_inputs(limit: int = 100, db: Session = Depends(get_db)):
    return db.scalars(select(UserStateInput).order_by(UserStateInput.observed_at.desc()).limit(min(max(limit, 1), 500))).all()
