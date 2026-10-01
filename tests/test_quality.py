import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from app.schemas import CalendarEventCreate
from app.models import ProvenanceType
from app.provenance import record_evidence


def test_calendar_rejects_non_positive_duration():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        CalendarEventCreate(title="Impossible", starts_at=now, ends_at=now)


def test_ai_inference_requires_confidence(db):
    with pytest.raises(ValueError):
        record_evidence(db, provenance_type=ProvenanceType.AI_INFERENCE, source="model", value={"claim":"x"})


def test_calendar_requires_explicit_timezone():
    naive = datetime(2026, 10, 2, 9, 0)
    with pytest.raises(ValidationError):
        CalendarEventCreate(title="Naive", starts_at=naive, ends_at=naive.replace(hour=10))
