from datetime import datetime
from zoneinfo import ZoneInfo

from app.context_models import SleepRecord
from app.models import CalendarEvent, Task, UserStateInput
from app.services.assistant import assistant_prompts, handle_assistant_message


def test_assistant_asks_for_missing_information_without_inventing_it(db):
    now = datetime(2026, 10, 22, 9, 0, tzinfo=ZoneInfo("Europe/London"))
    prompts = assistant_prompts(db, now)
    ids = [p["id"] for p in prompts]
    assert ids[0] == "missing_tasks"
    assert "missing_commitments" in ids
    assert "missing_state" in ids
    assert "missing_sleep" in ids


def test_assistant_saves_energy_and_focus_as_structured_estimate(db):
    now = datetime(2026, 10, 22, 9, 0, tzinfo=ZoneInfo("Europe/London"))
    result = handle_assistant_message(db, "Energy 2, focus 4", now)
    row = db.query(UserStateInput).one()
    assert result["action"] == "state_input"
    assert row.energy == 2
    assert row.focus == 4
    assert result["stored_raw_transcript"] is False


def test_assistant_creates_task_from_spoken_style_command(db):
    now = datetime(2026, 10, 22, 9, 0, tzinfo=ZoneInfo("Europe/London"))
    result = handle_assistant_message(
        db,
        "Add task finish lab report for 90 minutes priority 5 due friday",
        now,
    )
    task = db.query(Task).one()
    assert result["action"] == "task_created"
    assert task.title == "finish lab report"
    assert task.duration_minutes == 90
    assert task.priority == 5
    assert task.deadline is not None
    assert task.deadline.date().isoformat() == "2026-10-23"


def test_assistant_creates_explicit_calendar_event(db):
    now = datetime(2026, 10, 22, 9, 0, tzinfo=ZoneInfo("Europe/London"))
    result = handle_assistant_message(
        db,
        "Add event aerodynamics lecture on 2026-10-26 from 10 am to 11 am",
        now,
    )
    event = db.query(CalendarEvent).one()
    assert result["action"] == "event_created"
    assert event.title == "aerodynamics lecture"
    assert event.starts_at.hour == 10
    assert event.ends_at.hour == 11


def test_assistant_parses_recent_overnight_sleep(db):
    now = datetime(2026, 10, 22, 9, 0, tzinfo=ZoneInfo("Europe/London"))
    result = handle_assistant_message(db, "I slept from 1 am to 7 am", now)
    row = db.query(SleepRecord).one()
    assert result["action"] == "sleep_record"
    assert int((row.sleep_end - row.sleep_start).total_seconds() // 60) == 360


def test_assistant_refuses_ambiguous_text_instead_of_mutating(db):
    now = datetime(2026, 10, 22, 9, 0, tzinfo=ZoneInfo("Europe/London"))
    result = handle_assistant_message(db, "I feel kind of weird today", now)
    assert result["action"] == "no_action"
    assert db.query(Task).count() == 0
    assert db.query(UserStateInput).count() == 0
