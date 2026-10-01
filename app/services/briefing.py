from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import CalendarEvent, Task, WeeklyPlanBlock
from .planner import _ensure_tz
from .weekly_planner import get_active_weekly_plan


def morning_briefing(db: Session, brief_date: date, as_of: datetime | None = None) -> dict:
    tz = ZoneInfo(get_settings().timezone)
    day_start = datetime.combine(brief_date, time(0), tzinfo=tz)
    day_end = day_start + timedelta(days=1)
    now = _ensure_tz(as_of, tz) if as_of else datetime.now(tz)

    events = db.scalars(select(CalendarEvent).where(
        CalendarEvent.starts_at >= day_start,
        CalendarEvent.starts_at < day_end,
    ).order_by(CalendarEvent.starts_at)).all()

    week_start = brief_date - timedelta(days=brief_date.weekday())
    plan = get_active_weekly_plan(db, week_start)
    candidate_blocks = []
    if plan:
        blocks = db.scalars(select(WeeklyPlanBlock).where(
            WeeklyPlanBlock.weekly_plan_id == plan.id,
            WeeklyPlanBlock.plan_date == brief_date,
        ).order_by(WeeklyPlanBlock.starts_at)).all()
        for block in blocks:
            task = db.get(Task, block.task_id)
            if task and not task.completed and _ensure_tz(block.ends_at, tz) > now:
                candidate_blocks.append((block, task))

    next_action = None
    if candidate_blocks:
        block, task = candidate_blocks[0]
        duration = int((_ensure_tz(block.ends_at, tz) - _ensure_tz(block.starts_at, tz)).total_seconds() // 60)
        next_action = {
            "task_id": task.id,
            "title": task.title,
            "module": task.module,
            "topic": task.topic,
            "objective": task.objective,
            "source_material": task.source_material,
            "planned_start": block.starts_at,
            "duration_minutes": duration,
            "minimum_viable": block.minimum_viable,
            "instruction": f"Open {task.source_material}." if task.source_material else f"Open the material for {task.title}.",
            "why": block.rationale,
        }
    else:
        pending = list(db.scalars(select(Task).where(Task.completed.is_(False))).all())
        pending.sort(key=lambda t: (t.deadline is None, _ensure_tz(t.deadline, tz) if t.deadline else datetime.max.replace(tzinfo=tz), -t.priority))
        if pending:
            task = pending[0]
            next_action = {
                "task_id": task.id,
                "title": task.title,
                "module": task.module,
                "topic": task.topic,
                "duration_minutes": min(task.duration_minutes, 45),
                "instruction": f"Open {task.source_material}." if task.source_material else f"Open the material for {task.title}.",
                "why": "No active weekly block remains today, so this is the highest-priority pending task by deadline/priority.",
            }

    return {
        "date": brief_date,
        "sleep": {"status": "not_available", "reason": "sleep integration is not enabled; no sleep duration is inferred"},
        "today": [{
            "title": e.title,
            "starts_at": e.starts_at,
            "ends_at": e.ends_at,
            "event_type": e.event_type,
        } for e in events[:6]],
        "next_action": next_action,
        "plan_version": plan.version if plan else None,
        "presentation_note": "The briefing intentionally returns a short schedule and one next academic action rather than a giant task list.",
    }
