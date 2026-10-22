from datetime import date, datetime, timedelta, timezone

from app.context_models import MealRecord, SleepRecord, TrainingRecord
from app.models import UserStateInput
from app.services.context import current_context, weekly_context_summary


def test_missing_primary_context_stays_unknown(db):
    now = datetime(2026, 10, 22, 8, 0, tzinfo=timezone.utc)
    result = current_context(db, as_of=now)
    assert result["planning_load"] == "unknown_capacity"
    assert result["recommended_block_minutes"] == 45
    assert "sleep" in result["missing_signals"]
    assert "state_input" in result["missing_signals"]


def test_recorded_low_sleep_and_energy_reduce_planning_block(db):
    now = datetime(2026, 10, 22, 8, 0, tzinfo=timezone.utc)
    db.add(SleepRecord(
        sleep_start=now - timedelta(hours=6),
        sleep_end=now - timedelta(hours=1),
        quality=2,
    ))
    db.add(UserStateInput(
        observed_at=now - timedelta(minutes=10),
        energy=2,
        focus=3,
    ))
    db.add(TrainingRecord(
        starts_at=now - timedelta(hours=2),
        duration_minutes=60,
        intensity=4,
        modality="gym",
    ))
    db.commit()

    result = current_context(db, as_of=now)
    assert result["planning_load"] == "reduced_capacity"
    assert result["recommended_block_minutes"] == 25
    assert result["sleep"]["duration_minutes"] == 300
    assert len(result["reasons"]) >= 3
    assert "medical" in result["interpretation_note"]


def test_weekly_context_is_descriptive_only(db):
    start = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
    db.add(SleepRecord(
        sleep_start=start + timedelta(hours=23),
        sleep_end=start + timedelta(days=1, hours=7),
        quality=4,
    ))
    db.add(TrainingRecord(
        starts_at=start + timedelta(days=1, hours=17),
        duration_minutes=45,
        intensity=3,
        modality="run",
    ))
    db.add(MealRecord(
        consumed_at=start + timedelta(days=1, hours=19),
        meal_type="dinner",
        size_rating=3,
    ))
    db.commit()

    result = weekly_context_summary(db, date(2026, 10, 19))
    assert result["sleep"]["records"] == 1
    assert result["sleep"]["average_duration_minutes"] == 480
    assert result["training"]["total_minutes"] == 45
    assert result["meals"]["records"] == 1
    assert "does not infer dietary quality" in result["meals"]["note"]
