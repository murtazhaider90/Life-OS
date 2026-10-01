from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Task
from ..schemas import TaskCreate
from ..security import require_local_or_token

router = APIRouter(prefix="/api/tasks", tags=["tasks"], dependencies=[Depends(require_local_or_token)])


@router.get("")
def list_tasks(db: Session = Depends(get_db)):
    return db.scalars(select(Task).order_by(Task.completed, Task.deadline, Task.priority.desc())).all()


@router.post("")
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump(), source="manual_input")
    db.add(task)
    db.commit(); db.refresh(task)
    return task


@router.post("/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "task not found")
    task.completed = True
    task.completed_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(task)
    return task
