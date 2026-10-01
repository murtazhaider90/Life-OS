import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import CalendarEvent, PlanBlock, Task


@dataclass(frozen=True)
class Interval:
    start: datetime
    end: datetime


def _merge(intervals: list[Interval]) -> list[Interval]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda i: i.start)
    out = [intervals[0]]
    for cur in intervals[1:]:
        prev = out[-1]
        if cur.start <= prev.end:
            out[-1] = Interval(prev.start, max(prev.end, cur.end))
        else:
            out.append(cur)
    return out


def _free_windows(day_start: datetime, day_end: datetime, busy: list[Interval]) -> list[Interval]:
    clipped = [Interval(max(day_start, b.start), min(day_end, b.end)) for b in busy if b.end > day_start and b.start < day_end]
    merged = _merge([b for b in clipped if b.end > b.start])
    cursor = day_start
    free: list[Interval] = []
    for b in merged:
        if b.start > cursor:
            free.append(Interval(cursor, b.start))
        cursor = max(cursor, b.end)
    if cursor < day_end:
        free.append(Interval(cursor, day_end))
    return free


def _task_sort_key(task: Task, now: datetime):
    deadline = task.deadline
    if deadline is None:
        deadline_pressure = 10**9
    else:
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=now.tzinfo)
        deadline_pressure = max(0, int((deadline - now).total_seconds() // 60))
    return (deadline_pressure, -task.priority, -task.difficulty, task.created_at)


def build_daily_plan(db: Session, plan_date: date, day_start_hour: int, day_end_hour: int, minimum_gap_minutes: int = 10) -> list[PlanBlock]:
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    start = datetime.combine(plan_date, time(day_start_hour), tzinfo=tz)
    end_time = time(0) if day_end_hour == 24 else time(day_end_hour)
    end_date = plan_date + timedelta(days=1) if day_end_hour == 24 else plan_date
    end = datetime.combine(end_date, end_time, tzinfo=tz)

    events = db.scalars(select(CalendarEvent).where(CalendarEvent.starts_at < end, CalendarEvent.ends_at > start)).all()
    busy = [Interval(_ensure_tz(e.starts_at, tz), _ensure_tz(e.ends_at, tz)) for e in events]
    free = _free_windows(start, end, busy)

    tasks = list(db.scalars(select(Task).where(Task.completed.is_(False))).all())
    tasks.sort(key=lambda t: _task_sort_key(t, start))

    db.execute(delete(PlanBlock).where(PlanBlock.plan_date == plan_date))
    blocks: list[PlanBlock] = []
    gap = timedelta(minutes=minimum_gap_minutes)
    window_index = 0
    cursor = free[0].start if free else end

    for task in tasks:
        duration = timedelta(minutes=task.duration_minutes)
        while window_index < len(free):
            window = free[window_index]
            cursor = max(cursor, window.start)
            if cursor + duration <= window.end:
                deadline_text = _ensure_tz(task.deadline, tz).isoformat() if task.deadline else "none"
                rationale = f"Scheduled deterministically from open capacity; priority={task.priority}, deadline={deadline_text}, duration={task.duration_minutes}m."
                evidence = [
                    {"type": "FACT", "source": "task", "task_id": task.id, "priority": task.priority, "deadline": deadline_text},
                    {"type": "FACT", "source": "calendar", "conflicts_checked": len(events)},
                ]
                block = PlanBlock(
                    plan_date=plan_date,
                    task_id=task.id,
                    starts_at=cursor,
                    ends_at=cursor + duration,
                    rationale=rationale,
                    evidence_json=json.dumps(evidence),
                )
                db.add(block)
                db.flush()
                blocks.append(block)
                cursor = block.ends_at + gap
                break
            window_index += 1
            if window_index < len(free):
                cursor = free[window_index].start
    db.commit()
    return blocks


def _ensure_tz(value: datetime, tz: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)
