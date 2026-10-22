from __future__ import annotations

from datetime import date, datetime, time, timedelta
from statistics import mean
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..context_models import MealRecord, SleepRecord, TrainingRecord
from ..models import UserStateInput
from .planner import _ensure_tz


def _latest_before(db: Session, model, column, as_of: datetime, lookback: timedelta):
    return db.scalar(
        select(model)
        .where(column <= as_of, column >= as_of - lookback)
        .order_by(column.desc())
    )


def current_context(db: Session, as_of: datetime | None = None) -> dict:
    tz = ZoneInfo(get_settings().timezone)
    local_now = _ensure_tz(as_of, tz) if as_of else datetime.now(tz)

    sleep = db.scalar(
        select(SleepRecord)
        .where(
            SleepRecord.sleep_end <= local_now,
            SleepRecord.sleep_end >= local_now - timedelta(hours=36),
        )
        .order_by(SleepRecord.sleep_end.desc())
    )
    state = _latest_before(db, UserStateInput, UserStateInput.observed_at, local_now, timedelta(hours=24))
    training = db.scalars(
        select(TrainingRecord)
        .where(
            TrainingRecord.starts_at <= local_now,
            TrainingRecord.starts_at >= local_now - timedelta(hours=24),
        )
        .order_by(TrainingRecord.starts_at.desc())
    ).all()
    meal = _latest_before(db, MealRecord, MealRecord.consumed_at, local_now, timedelta(hours=18))

    reasons: list[str] = []
    missing: list[str] = []
    load_points = 0
    sleep_minutes = None

    if sleep:
        start = _ensure_tz(sleep.sleep_start, tz)
        end = _ensure_tz(sleep.sleep_end, tz)
        sleep_minutes = max(0, int((end - start).total_seconds() // 60))
        if sleep_minutes < 360:
            load_points += 2
            reasons.append(f"last recorded sleep duration was {sleep_minutes / 60:.1f}h")
        elif sleep_minutes < 420:
            load_points += 1
            reasons.append(f"last recorded sleep duration was {sleep_minutes / 60:.1f}h")
        if sleep.quality is not None and sleep.quality <= 2:
            load_points += 1
            reasons.append(f"last recorded sleep quality was {sleep.quality}/5")
    else:
        missing.append("sleep")

    if state:
        if state.energy is not None and state.energy <= 2:
            load_points += 2
            reasons.append(f"latest self-reported energy was {state.energy}/5")
        if state.focus is not None and state.focus <= 2:
            load_points += 1
            reasons.append(f"latest self-reported focus was {state.focus}/5")
    else:
        missing.append("state_input")

    recent_hard_training = [
        t for t in training
        if t.intensity is not None
        and t.intensity >= 4
        and local_now - _ensure_tz(t.starts_at, tz) <= timedelta(hours=12)
    ]
    if recent_hard_training:
        load_points += 1
        reasons.append("a high-intensity training session was recorded within the last 12 hours")

    if meal is None:
        missing.append("meal")

    if sleep is None and state is None:
        planning_load = "unknown_capacity"
        recommended_block_minutes = 45
        recommended_gap_minutes = 10
        reasons.append("not enough primary context is recorded to classify planning capacity")
    elif load_points >= 3:
        planning_load = "reduced_capacity"
        recommended_block_minutes = 25
        recommended_gap_minutes = 15
    elif load_points >= 1:
        planning_load = "moderate_capacity"
        recommended_block_minutes = 40
        recommended_gap_minutes = 10
    else:
        planning_load = "normal_capacity"
        recommended_block_minutes = 60
        recommended_gap_minutes = 10

    return {
        "as_of": local_now,
        "planning_load": planning_load,
        "recommended_block_minutes": recommended_block_minutes,
        "recommended_gap_minutes": recommended_gap_minutes,
        "reasons": reasons,
        "missing_signals": missing,
        "sleep": None if not sleep else {
            "id": sleep.id,
            "sleep_start": sleep.sleep_start,
            "sleep_end": sleep.sleep_end,
            "duration_minutes": sleep_minutes,
            "quality": sleep.quality,
            "source": sleep.source,
            "provenance_type": sleep.provenance_type,
        },
        "state": None if not state else {
            "id": state.id,
            "energy": state.energy,
            "focus": state.focus,
            "difficulty": state.difficulty,
            "confused": state.confused,
            "observed_at": state.observed_at,
            "source": state.source,
            "provenance_type": state.provenance_type,
        },
        "training_last_24h": [{
            "id": t.id,
            "starts_at": t.starts_at,
            "duration_minutes": t.duration_minutes,
            "intensity": t.intensity,
            "modality": t.modality,
            "source": t.source,
        } for t in training],
        "latest_meal": None if not meal else {
            "id": meal.id,
            "consumed_at": meal.consumed_at,
            "meal_type": meal.meal_type,
            "size_rating": meal.size_rating,
            "source": meal.source,
        },
        "interpretation_note": "This is a deterministic planning-load heuristic, not a medical, sleep, nutrition, or recovery assessment. Missing signals remain missing.",
    }


def weekly_context_summary(db: Session, week_start: date) -> dict:
    tz = ZoneInfo(get_settings().timezone)
    start = datetime.combine(week_start, time(0), tzinfo=tz)
    end = start + timedelta(days=7)

    sleeps = db.scalars(
        select(SleepRecord).where(SleepRecord.sleep_end >= start, SleepRecord.sleep_end < end)
    ).all()
    training = db.scalars(
        select(TrainingRecord).where(TrainingRecord.starts_at >= start, TrainingRecord.starts_at < end)
    ).all()
    meals = db.scalars(
        select(MealRecord).where(MealRecord.consumed_at >= start, MealRecord.consumed_at < end)
    ).all()

    sleep_durations = [
        max(0, int((_ensure_tz(s.sleep_end, tz) - _ensure_tz(s.sleep_start, tz)).total_seconds() // 60))
        for s in sleeps
    ]
    sleep_qualities = [s.quality for s in sleeps if s.quality is not None]

    return {
        "week_start": week_start,
        "sleep": {
            "records": len(sleeps),
            "average_duration_minutes": mean(sleep_durations) if sleep_durations else None,
            "average_quality": mean(sleep_qualities) if sleep_qualities else None,
        },
        "training": {
            "sessions": len(training),
            "total_minutes": sum(t.duration_minutes for t in training),
            "high_intensity_sessions": sum(1 for t in training if t.intensity is not None and t.intensity >= 4),
        },
        "meals": {
            "records": len(meals),
            "note": "Meal logging is counted for context only; Life OS does not infer dietary quality from these records.",
        },
        "coverage": {
            "sleep_available": bool(sleeps),
            "training_available": bool(training),
            "meal_available": bool(meals),
        },
    }
