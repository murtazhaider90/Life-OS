from datetime import date, datetime
from zoneinfo import ZoneInfo
from app.models import CalendarEvent, Task
from app.services.planner import build_daily_plan


def test_planner_avoids_calendar_conflict(db):
    tz = ZoneInfo("Europe/London")
    db.add(CalendarEvent(title="Lecture", starts_at=datetime(2026,10,2,9,0,tzinfo=tz), ends_at=datetime(2026,10,2,10,0,tzinfo=tz)))
    db.add(Task(title="Problem set", duration_minutes=60, priority=5, difficulty=4))
    db.commit()
    blocks = build_daily_plan(db, date(2026,10,2), 8, 12, 10)
    assert len(blocks) == 1
    assert blocks[0].ends_at <= datetime(2026,10,2,9,0,tzinfo=tz) or blocks[0].starts_at >= datetime(2026,10,2,10,0,tzinfo=tz)


def test_planner_prioritizes_earlier_deadline(db):
    tz = ZoneInfo("Europe/London")
    later = Task(title="Later", duration_minutes=30, priority=5, deadline=datetime(2026,10,10,12,0,tzinfo=tz))
    sooner = Task(title="Sooner", duration_minutes=30, priority=1, deadline=datetime(2026,10,3,12,0,tzinfo=tz))
    db.add_all([later, sooner]); db.commit()
    blocks = build_daily_plan(db, date(2026,10,2), 8, 10, 0)
    assert blocks[0].task_id == sooner.id
