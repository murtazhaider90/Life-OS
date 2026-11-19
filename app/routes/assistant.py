from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..assistant_schemas import AssistantMessageRequest
from ..db import get_db
from ..security import require_local_or_token
from ..services.assistant import assistant_prompts, handle_assistant_message

router = APIRouter(prefix="/api/assistant", tags=["assistant"], dependencies=[Depends(require_local_or_token)])


@router.get("/status")
def status(as_of: datetime | None = None, db: Session = Depends(get_db)):
    prompts = assistant_prompts(db, now=as_of)
    return {
        "needs_input": bool(prompts),
        "questions": prompts,
        "raw_transcripts_persisted": False,
        "note": "The assistant processes text to create structured records but does not persist the raw conversation transcript.",
    }


@router.post("/message")
def message(payload: AssistantMessageRequest, db: Session = Depends(get_db)):
    try:
        return handle_assistant_message(db, payload.text)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
