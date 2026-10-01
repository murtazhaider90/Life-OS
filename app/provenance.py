import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import EvidenceRecord, ProvenanceType


def record_evidence(
    db: Session,
    *,
    provenance_type: ProvenanceType,
    source: str,
    value: dict,
    source_ref: str | None = None,
    confidence: float | None = None,
    observed_at: datetime | None = None,
) -> EvidenceRecord:
    if provenance_type in {ProvenanceType.AI_INFERENCE, ProvenanceType.AI_RECOMMENDATION} and confidence is None:
        raise ValueError("AI-derived evidence must include confidence")
    row = EvidenceRecord(
        provenance_type=provenance_type,
        source=source,
        source_ref=source_ref,
        value_json=json.dumps(value, sort_keys=True),
        confidence=confidence,
        observed_at=observed_at or datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    return row
