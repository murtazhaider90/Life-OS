from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models import StudySession, Task
from app.services.briefing import morning_briefing
from app.services.review import build_weekly_review
from app.services.weekly_planner import build_weekly_plan


def test_morning_briefing_returns_one_next_action(db):
    tz = ZoneInfo("Europe/London")
    monday = date(2026, 10, 5)
    task = Task(title="Do tutorial questions", module="Aerodynamics", topic="Boundary layer", source_material="Tutorial 4", duration_minutes=45, priority=5)
    db.add(task); db.commit()
    build_weekly_plan(db, monday, day_start_hour=8, day_end_hour=12, max_block_minutes=60, minimum_gap_minutes=0)

    result = morning_briefing(db, monday, as_of=datetime(2026, 10, 5, 7, 30, tzinfo=tz))
    assert result["next_action"]["task_id"] == task.id
    assert result["next_action"]["instruction"] == "Open Tutorial 4."
    assert result["sleep"]["status"] == "not_available"
    assert "giant task list" in result["presentation_note"]


def test_weekly_review_music_observation_stays_observational(db):
    tz = ZoneInfo("Europe/London")
    monday = date(2026, 10, 5)
    for i in range(6):
        start = datetime(2026, 10, 5 + i, 10, 5, tzinfo=tz)
        db.add(StudySession(
            planned_start=start - timedelta(minutes=5),
            actual_start=start,
            ended_at=start + timedelta(minutes=30),
            planned_minutes=30,
            completed=True,
            music_on=i < 3,
            focus_rating=2 if i < 3 else 4,
            module="Aerodynamics",
            topic="Boundary layer",
        ))
    db.commit()

    review = build_weekly_review(db, monday)
    music = review["behavioral"]["music_observation"]
    assert music["status"] == "provisional"
    assert "higher with music off" in music["conclusion"]
    assert "observational" in music["note"]
    assert review["behavioral"]["average_start_latency_minutes"] == 5
    assert review["physical_context"]["status"] == "not_available"


def test_weekly_review_does_not_infer_music_effect_from_tiny_sample(db):
    tz = ZoneInfo("Europe/London")
    monday = date(2026, 10, 5)
    for i, music in enumerate([True, False]):
        start = datetime(2026, 10, 5 + i, 9, 0, tzinfo=tz)
        db.add(StudySession(actual_start=start, ended_at=start + timedelta(minutes=20), completed=True, music_on=music, focus_rating=3))
    db.commit()
    review = build_weekly_review(db, monday)
    assert review["behavioral"]["music_observation"]["status"] == "insufficient_evidence"
