import json
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import EvidenceRecord
from ..security import require_local_or_token

router = APIRouter(prefix="/api/evidence", tags=["evidence"], dependencies=[Depends(require_local_or_token)])


@router.get("")
def list_evidence(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.scalars(select(EvidenceRecord).order_by(EvidenceRecord.observed_at.desc()).limit(min(max(limit, 1), 500))).all()
    return [{
        "id": r.id, "type": r.provenance_type, "source": r.source,
        "source_ref": r.source_ref, "value": json.loads(r.value_json),
        "confidence": r.confidence, "observed_at": r.observed_at,
    } for r in rows]
