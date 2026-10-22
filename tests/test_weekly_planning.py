from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models import CalendarEvent, Task, WeeklyPlan, WeeklyPlanBlock
from app.services.weekly_planner import build_weekly_plan, replan_week


def test_weekly_plan_splits_around_hard_commitment_and_marks_minimum_viable(db):
    tz = ZoneInfo("Europe/London")
    monday = date(2026, 10, 5)
    urgent = Task(
        title="Aerodynamics problem set",
        module="Aerodynamics",
        duration_minutes=90,
        priority=2,
        deadline=datetime(2026, 10, 7, 17, 0, tzinfo=tz),
    )
    optional = Task(title="Read notes", module="Structures", duration_minutes=30, priority=2)
    lecture = CalendarEvent(
        title="Lecture",
        starts_at=datetime(2026, 10, 5, 9, 0, tzinfo=tz),
        ends_at=datetime(2026, 10, 5, 10, 0, tzinfo=tz),
    )
    db.add_all([urgent, optional, lecture]); db.commit()

    plan = build_weekly_plan(db, monday, day_start_hour=8, day_end_hour=12, max_block_minutes=60, minimum_gap_minutes=0)
    urgent_blocks = [b for b in plan["blocks"] if b["task_id"] == urgent.id]
    assert len(urgent_blocks) == 2
    assert sum(b["minutes"] for b in urgent_blocks) == 90
    assert all(b["minimum_viable"] is True for b in urgent_blocks)
    for block in urgent_blocks:
        assert block["ends_at"] <= lecture.starts_at or block["starts_at"] >= lecture.ends_at


def test_replan_creates_new_version_and_reports_missed_block(db):
    tz = ZoneInfo("Europe/London")
    monday = date(2026, 10, 5)
    task = Task(title="Tutorial", duration_minutes=60, priority=5)
    db.add(task); db.commit()
    first = build_weekly_plan(db, monday, day_start_hour=8, day_end_hour=10, max_block_minutes=60, minimum_gap_minutes=0)
    first_block_id = first["blocks"][0]["id"]

    replanned = replan_week(
        db,
        monday,
        as_of=datetime(2026, 10, 6, 8, 0, tzinfo=tz),
        day_start_hour=8,
        day_end_hour=10,
        max_block_minutes=60,
        minimum_gap_minutes=0,
    )
    assert replanned["version"] == 2
    assert first_block_id in replanned["missed_block_ids"]
    assert replanned["blocks"][0]["starts_at"].date() >= date(2026, 10, 6)
    plans = db.query(WeeklyPlan).order_by(WeeklyPlan.version).all()
    assert [p.status for p in plans] == ["superseded", "active"]


def test_overdue_task_remains_schedulable_and_capacity_shortfall_is_explicit(db):
    tz = ZoneInfo("Europe/London")
    monday = date(2026, 10, 5)
    overdue = Task(
        title="Overdue coursework",
        duration_minutes=300,
        priority=5,
        deadline=datetime(2026, 10, 4, 17, 0, tzinfo=tz),
    )
    db.add(overdue); db.commit()
    plan = build_weekly_plan(db, monday, day_start_hour=8, day_end_hour=9, max_block_minutes=60, minimum_gap_minutes=0)
    assert plan["scheduled_minutes"] > 0
    assert plan["capacity_shortfall_minutes"] == 0  # 7 one-hour windows provide enough weekly capacity

    impossible = Task(title="Huge task", duration_minutes=480, priority=1)
    db.add(impossible); db.commit()
    plan2 = build_weekly_plan(db, monday, day_start_hour=8, day_end_hour=9, max_block_minutes=60, minimum_gap_minutes=0)
    assert plan2["capacity_shortfall_minutes"] > 0


def test_weak_topic_breaks_tie_between_similarly_urgent_tasks(db):
    from app.models import StudyAttempt
    tz = ZoneInfo("Europe/London")
    monday = date(2026, 10, 5)
    now = datetime(2026, 10, 5, 7, 0, tzinfo=tz)
    weak_task = Task(title="Weak topic practice", module="Aero", topic="Layers", duration_minutes=30, priority=3)
    other_task = Task(title="Other practice", module="Aero", topic="Lift", duration_minutes=30, priority=3)
    db.add_all([weak_task, other_task]); db.flush()
    db.add_all([
        StudyAttempt(module="Aero", topic="Layers", attempted_at=now - timedelta(days=2), correct_count=2, total_count=5, confidence=2),
        StudyAttempt(module="Aero", topic="Layers", attempted_at=now - timedelta(days=1), correct_count=3, total_count=5, confidence=2),
    ])
    db.commit()
    plan = build_weekly_plan(db, monday, day_start_hour=8, day_end_hour=10, max_block_minutes=60, minimum_gap_minutes=0)
    assert plan["blocks"][0]["task_id"] == weak_task.id
    assert plan["blocks"][0]["minimum_viable"] is True
    assert any(e.get("source") == "learning_engine" and e.get("status") == "weak" for e in plan["blocks"][0]["evidence"])
