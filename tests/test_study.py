from datetime import datetime, timedelta, timezone
from app.models import StudySession


def test_study_session_can_preserve_music_hypothesis_data(db):
    start = datetime.now(timezone.utc)
    row = StudySession(module="Aerodynamics", topic="Boundary layers", actual_start=start, planned_minutes=45, music_on=True, focus_rating=2)
    db.add(row); db.commit(); db.refresh(row)
    assert row.music_on is True
    assert row.focus_rating == 2
