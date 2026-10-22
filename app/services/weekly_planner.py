from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import CalendarEvent, StudySession, Task, WeeklyPlan, WeeklyPlanBlock
from .planner import Interval, _free_windows, _task_sort_key, _ensure_tz
from .learning import topic_evidence


@dataclass
class Slot:
    cursor: datetime
    end: datetime


def _week_end(week_start: date) -> date:
    return week_start + timedelta(days=7)


def _week_bounds(week_start: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    return (
        datetime.combine(week_start, time(0), tzinfo=tz),
        datetime.combine(_week_end(week_start), time(0), tzinfo=tz),
    )


def _completed_work_minutes(db: Session, task_id: int, start: datetime, end: datetime) -> int:
    sessions = db.scalars(select(StudySession).where(
        StudySession.task_id == task_id,
        StudySession.completed.is_(True),
        StudySession.actual_start.is_not(None),
        StudySession.ended_at.is_not(None),
        StudySession.actual_start >= start,
        StudySession.actual_start < end,
    )).all()
    total = 0
    for session in sessions:
        s = _ensure_tz(session.actual_start, start.tzinfo)  # type: ignore[arg-type]
        e = _ensure_tz(session.ended_at, start.tzinfo)  # type: ignore[arg-type]
        total += max(0, int((e - s).total_seconds() // 60))
    return total


def _minimum_viable_task_ids(tasks: list[Task], week_start_dt: datetime, week_end_dt: datetime, learning_status: dict[tuple[str, str], str] | None = None) -> set[int]:
    essential: set[int] = set()
    best_by_module: dict[str, Task] = {}
    learning_status = learning_status or {}
    for task in tasks:
        deadline = _ensure_tz(task.deadline, week_start_dt.tzinfo) if task.deadline else None  # type: ignore[arg-type]
        if deadline is not None and deadline < week_end_dt:
            essential.add(task.id)
        if task.module and task.topic and learning_status.get((task.module, task.topic)) == "weak" and task.priority >= 3:
            essential.add(task.id)
        if task.priority >= 4:
            key = task.module or "__general__"
            current = best_by_module.get(key)
            if current is None or _task_sort_key(task, week_start_dt) < _task_sort_key(current, week_start_dt):
                best_by_module[key] = task
    essential.update(task.id for task in best_by_module.values())
    if not essential and tasks:
        essential.add(tasks[0].id)
    return essential


def _build_slots(
    db: Session,
    week_start: date,
    day_start_hour: int,
    day_end_hour: int,
    gap_minutes: int,
    as_of: datetime | None,
) -> tuple[list[Slot], int]:
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    week_start_dt, week_end_dt = _week_bounds(week_start, tz)
    events = db.scalars(select(CalendarEvent).where(CalendarEvent.starts_at < week_end_dt, CalendarEvent.ends_at > week_start_dt)).all()
    event_intervals = [Interval(_ensure_tz(e.starts_at, tz), _ensure_tz(e.ends_at, tz)) for e in events]
    slots: list[Slot] = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        day_start = datetime.combine(day, time(day_start_hour), tzinfo=tz)
        end_time = time(0) if day_end_hour == 24 else time(day_end_hour)
        end_date = day + timedelta(days=1) if day_end_hour == 24 else day
        day_end = datetime.combine(end_date, end_time, tzinfo=tz)
        if as_of is not None:
            local_as_of = _ensure_tz(as_of, tz)
            if day_end <= local_as_of:
                continue
            day_start = max(day_start, local_as_of)
        busy = [b for b in event_intervals if b.end > day_start and b.start < day_end]
        for window in _free_windows(day_start, day_end, busy):
            if window.end > window.start:
                slots.append(Slot(window.start, window.end))
    return slots, len(events)


def _next_version(db: Session, week_start: date) -> int:
    plans = db.scalars(select(WeeklyPlan).where(WeeklyPlan.week_start == week_start)).all()
    return max((p.version for p in plans), default=0) + 1


def _serialize_plan(db: Session, plan: WeeklyPlan, missed_block_ids: list[int] | None = None) -> dict:
    tz = ZoneInfo(get_settings().timezone)
    blocks = db.scalars(select(WeeklyPlanBlock).where(WeeklyPlanBlock.weekly_plan_id == plan.id).order_by(WeeklyPlanBlock.starts_at)).all()
    serialized_blocks = []
    for b in blocks:
        starts_at = _ensure_tz(b.starts_at, tz)
        ends_at = _ensure_tz(b.ends_at, tz)
        serialized_blocks.append({
            "id": b.id,
            "task_id": b.task_id,
            "plan_date": b.plan_date,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "minutes": int((ends_at - starts_at).total_seconds() // 60),
            "minimum_viable": b.minimum_viable,
            "rationale": b.rationale,
            "evidence": json.loads(b.evidence_json),
        })
    return {
        "id": plan.id,
        "week_start": plan.week_start,
        "version": plan.version,
        "status": plan.status,
        "reason": plan.reason,
        "required_minutes": plan.required_minutes,
        "scheduled_minutes": plan.scheduled_minutes,
        "capacity_shortfall_minutes": plan.capacity_shortfall_minutes,
        "missed_block_ids": missed_block_ids or [],
        "blocks": serialized_blocks,
    }


def get_active_weekly_plan(db: Session, week_start: date) -> WeeklyPlan | None:
    return db.scalar(select(WeeklyPlan).where(
        WeeklyPlan.week_start == week_start,
        WeeklyPlan.status == "active",
    ).order_by(WeeklyPlan.version.desc()))


def build_weekly_plan(
    db: Session,
    week_start: date,
    day_start_hour: int = 8,
    day_end_hour: int = 22,
    max_block_minutes: int = 60,
    minimum_gap_minutes: int = 10,
    *,
    as_of: datetime | None = None,
    reason: str = "initial",
) -> dict:
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    week_start_dt, week_end_dt = _week_bounds(week_start, tz)
    effective_as_of = _ensure_tz(as_of, tz) if as_of else week_start_dt
    if effective_as_of >= week_end_dt:
        raise ValueError("as_of is outside the requested week")

    tasks = list(db.scalars(select(Task).where(Task.completed.is_(False))).all())
    learning_rows = topic_evidence(db, as_of=effective_as_of)
    learning_status = {(row["module"], row["topic"]): row["status"] for row in learning_rows}
    learning_rank = {"weak": 0, "requires_retrieval": 1, "developing": 2}
    def weekly_sort_key(task: Task):
        base = _task_sort_key(task, effective_as_of)
        status = learning_status.get((task.module, task.topic)) if task.module and task.topic else None
        return (base[0], learning_rank.get(status, 3), base[1], base[2], base[3])
    tasks.sort(key=weekly_sort_key)
    minimum_viable_ids = _minimum_viable_task_ids(tasks, week_start_dt, week_end_dt, learning_status)

    old_active = db.scalars(select(WeeklyPlan).where(WeeklyPlan.week_start == week_start, WeeklyPlan.status == "active")).all()
    for old in old_active:
        old.status = "superseded"

    plan = WeeklyPlan(
        week_start=week_start,
        version=_next_version(db, week_start),
        status="active",
        reason=reason,
        window_start_hour=day_start_hour,
        window_end_hour=day_end_hour,
        max_block_minutes=max_block_minutes,
    )
    db.add(plan); db.flush()

    slots, calendar_count = _build_slots(db, week_start, day_start_hour, day_end_hour, minimum_gap_minutes, effective_as_of)
    gap = timedelta(minutes=minimum_gap_minutes)
    required_minutes = 0
    scheduled_minutes = 0
    sequence = 0

    for task in tasks:
        worked = _completed_work_minutes(db, task.id, week_start_dt, effective_as_of)
        remaining = max(0, task.duration_minutes - worked)
        required_minutes += remaining
        deadline = _ensure_tz(task.deadline, tz) if task.deadline else None
        placement_deadline = deadline if deadline is not None and deadline > effective_as_of else None

        while remaining > 0:
            placed = False
            for slot in slots:
                latest_end = min(slot.end, placement_deadline) if placement_deadline is not None else slot.end
                available = int((latest_end - slot.cursor).total_seconds() // 60)
                if available <= 0:
                    continue
                target = min(remaining, max_block_minutes, available)
                minimum_useful = min(20, remaining)
                if target < minimum_useful:
                    continue
                block_start = slot.cursor
                block_end = block_start + timedelta(minutes=target)
                topic_status = learning_status.get((task.module, task.topic)) if task.module and task.topic else None
                evidence = [
                    {"type": "FACT", "source": "task", "task_id": task.id, "priority": task.priority, "deadline": deadline.isoformat() if deadline else None, "remaining_minutes_before_block": remaining},
                    {"type": "FACT", "source": "calendar", "conflicts_checked": calendar_count},
                    {"type": "OBSERVATION", "source": "study_sessions", "completed_task_minutes_this_week": worked},
                ]
                if topic_status is not None:
                    evidence.append({"type": "OBSERVATION", "source": "learning_engine", "module": task.module, "topic": task.topic, "status": topic_status})
                is_minimum = task.id in minimum_viable_ids
                rationale = "Minimum-viable-week task; " if is_minimum else "Weekly required-work task; "
                rationale += f"placed in verified free capacity before its deadline where applicable; chunk={target}m."
                block = WeeklyPlanBlock(
                    weekly_plan_id=plan.id,
                    task_id=task.id,
                    plan_date=block_start.date(),
                    starts_at=block_start,
                    ends_at=block_end,
                    sequence=sequence,
                    minimum_viable=is_minimum,
                    rationale=rationale,
                    evidence_json=json.dumps(evidence),
                )
                db.add(block); db.flush()
                sequence += 1
                scheduled_minutes += target
                remaining -= target
                slot.cursor = block_end + gap
                placed = True
                break
            if not placed:
                break

    plan.required_minutes = required_minutes
    plan.scheduled_minutes = scheduled_minutes
    plan.capacity_shortfall_minutes = max(0, required_minutes - scheduled_minutes)
    db.commit(); db.refresh(plan)
    return _serialize_plan(db, plan)


def replan_week(
    db: Session,
    week_start: date,
    as_of: datetime,
    day_start_hour: int = 8,
    day_end_hour: int = 22,
    max_block_minutes: int = 60,
    minimum_gap_minutes: int = 10,
) -> dict:
    tz = ZoneInfo(get_settings().timezone)
    local_as_of = _ensure_tz(as_of, tz)
    current = get_active_weekly_plan(db, week_start)
    missed: list[int] = []
    if current:
        rows = db.scalars(select(WeeklyPlanBlock).where(WeeklyPlanBlock.weekly_plan_id == current.id)).all()
        for block in rows:
            end = _ensure_tz(block.ends_at, tz)
            task = db.get(Task, block.task_id)
            completed_by_then = bool(task and task.completed and task.completed_at and _ensure_tz(task.completed_at, tz) <= end)
            if end < local_as_of and not completed_by_then:
                missed.append(block.id)

    result = build_weekly_plan(
        db,
        week_start,
        day_start_hour,
        day_end_hour,
        max_block_minutes,
        minimum_gap_minutes,
        as_of=local_as_of,
        reason="replan",
    )
    result["missed_block_ids"] = missed
    return result
