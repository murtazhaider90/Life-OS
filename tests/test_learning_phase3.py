from datetime import datetime, timedelta, timezone

from app.models import StudyAttempt
from app.services.learning import topic_evidence


def test_weak_topic_requires_recorded_evidence(db):
    now = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    db.add_all([
        StudyAttempt(module="Aerodynamics", topic="Boundary layer", attempted_at=now - timedelta(days=2), correct_count=3, total_count=5, confidence=2),
        StudyAttempt(module="Aerodynamics", topic="Boundary layer", attempted_at=now - timedelta(days=1), correct_count=3, total_count=5, confidence=2),
        StudyAttempt(module="Structures", topic="Buckling", attempted_at=now - timedelta(days=1), correct_count=1, total_count=1, confidence=5),
    ])
    db.commit()

    rows = topic_evidence(db, as_of=now)
    aero = next(r for r in rows if r["topic"] == "Boundary layer")
    buckling = next(r for r in rows if r["topic"] == "Buckling")
    assert aero["status"] == "weak"
    assert aero["accuracy"] == 0.6
    assert aero["evidence_count"] == 2
    assert buckling["status"] == "insufficient_evidence"
