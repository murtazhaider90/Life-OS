from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..context_models import SleepRecord
from ..models import CalendarEvent, Task, UserStateInput
from .briefing import morning_briefing
from .weekly_planner import build_weekly_plan, get_active_weekly_plan


_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def _local_now(now: datetime | None = None) -> datetime:
    tz = ZoneInfo(get_settings().timezone)
    if now is None:
        return datetime.now(tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=tz)
    return now.astimezone(tz)


def _number(token: str | None) -> int | None:
    if token is None:
        return None
    token = token.lower()
    return int(token) if token.isdigit() else _NUMBER_WORDS.get(token)


def assistant_prompts(db: Session, now: datetime | None = None) -> list[dict]:
    now = _local_now(now)
    prompts: list[dict] = []

    pending_count = len(db.scalars(select(Task).where(Task.completed.is_(False))).all())
    if pending_count == 0:
        prompts.append({
            "id": "missing_tasks",
            "priority": 100,
            "prompt": "What is one real task you need to get done?",
            "reason": "I cannot plan useful work until at least one pending task exists.",
            "example": "Add task finish lab report for 90 minutes priority 5",
        })

    upcoming = db.scalars(select(CalendarEvent).where(
        CalendarEvent.starts_at >= now,
        CalendarEvent.starts_at < now + timedelta(days=7),
    )).all()
    if not upcoming:
        prompts.append({
            "id": "missing_commitments",
            "priority": 80,
            "prompt": "Do you have any fixed lectures, appointments, work shifts, or other commitments in the next 7 days?",
            "reason": "The planner needs fixed commitments before it can safely use your free time.",
            "example": "Add event aerodynamics lecture on 2026-10-26 from 10 am to 11 am",
        })

    recent_state = db.scalar(select(UserStateInput).where(
        UserStateInput.observed_at >= now - timedelta(hours=12),
        UserStateInput.observed_at <= now,
    ).order_by(UserStateInput.observed_at.desc()))
    if recent_state is None:
        prompts.append({
            "id": "missing_state",
            "priority": 70,
            "prompt": "Quick check-in: what are your energy and focus from 1 to 5?",
            "reason": "A recent self-report lets me adjust the suggested first work block.",
            "example": "Energy 3, focus 2",
        })

    recent_sleep = db.scalar(select(SleepRecord).where(
        SleepRecord.sleep_end >= now - timedelta(hours=36),
        SleepRecord.sleep_end <= now,
    ).order_by(SleepRecord.sleep_end.desc()))
    if recent_sleep is None:
        prompts.append({
            "id": "missing_sleep",
            "priority": 60,
            "prompt": "If you want context-aware planning, when did you sleep and wake up?",
            "reason": "Without a recent sleep record, sleep remains unknown rather than being guessed.",
            "example": "I slept from 1 am to 7 am",
        })

    week_start = now.date() - timedelta(days=now.weekday())
    if pending_count > 0 and get_active_weekly_plan(db, week_start) is None:
        prompts.append({
            "id": "missing_week_plan",
            "priority": 50,
            "prompt": "You have pending work but no active weekly plan. Want me to generate it?",
            "reason": "A weekly plan gives the dashboard concrete next actions.",
            "example": "Generate my weekly plan",
        })

    prompts.sort(key=lambda x: -x["priority"])
    return prompts


def _parse_rating(text: str, label: str) -> int | None:
    match = re.search(rf"\b{label}\b(?:\s+(?:is|at))?\s*[:=-]?\s*(one|two|three|four|five|[1-5])\b", text, re.I)
    return _number(match.group(1)) if match else None


def _parse_clock(hour: str, minute: str | None, ampm: str | None) -> tuple[int, int]:
    h = int(hour)
    m = int(minute or 0)
    if not (0 <= m <= 59):
        raise ValueError("invalid minute")
    if ampm:
        if not (1 <= h <= 12):
            raise ValueError("invalid hour")
        h = (0 if h == 12 else h) if ampm.lower() == "am" else (12 if h == 12 else h + 12)
    elif not (0 <= h <= 23):
        raise ValueError("invalid hour")
    return h, m


def _parse_sleep(text: str, now: datetime) -> tuple[datetime, datetime] | None:
    match = re.search(
        r"\b(?:i\s+)?slept\s+from\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+to\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",
        text,
        re.I,
    )
    if not match:
        return None
    sh, sm = _parse_clock(match.group(1), match.group(2), match.group(3))
    eh, em = _parse_clock(match.group(4), match.group(5), match.group(6))
    end = datetime.combine(now.date(), time(eh, em), tzinfo=now.tzinfo)
    if end > now + timedelta(hours=2):
        end -= timedelta(days=1)
    start = datetime.combine(end.date(), time(sh, sm), tzinfo=now.tzinfo)
    if start >= end:
        start -= timedelta(days=1)
    if end - start > timedelta(hours=18):
        raise ValueError("sleep interval looks too long; please give clearer times")
    return start, end


def _parse_deadline(text: str, now: datetime) -> datetime | None:
    iso = re.search(r"\bdue\s+(\d{4}-\d{2}-\d{2})(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?)?", text, re.I)
    if iso:
        day = date.fromisoformat(iso.group(1))
        h, m = _parse_clock(iso.group(2), iso.group(3), iso.group(4)) if iso.group(2) else (17, 0)
        return datetime.combine(day, time(h, m), tzinfo=now.tzinfo)

    weekday = re.search(r"\bdue\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text, re.I)
    if weekday:
        target = _WEEKDAYS[weekday.group(1).lower()]
        delta = (target - now.weekday()) % 7 or 7
        return datetime.combine(now.date() + timedelta(days=delta), time(17, 0), tzinfo=now.tzinfo)
    return None


def _task_from_text(text: str, now: datetime) -> tuple[str, int, int, datetime | None] | None:
    lowered = text.lower().strip()
    prefixes = ("add task ", "new task ", "i need to ", "i have to ", "remind me to ")
    prefix = next((p for p in prefixes if lowered.startswith(p)), None)
    if not prefix:
        return None

    raw = text[len(prefix):].strip()
    duration = 45
    priority = 3

    duration_match = re.search(r"\bfor\s+(\d+)\s*(minutes?|mins?|hours?|hrs?)\b", raw, re.I)
    if duration_match:
        amount = int(duration_match.group(1))
        unit = duration_match.group(2).lower()
        duration = amount * 60 if unit.startswith(("hour", "hr")) else amount

    priority_match = re.search(r"\bpriority\s*([1-5])\b", raw, re.I)
    if priority_match:
        priority = int(priority_match.group(1))

    deadline = _parse_deadline(raw, now)

    title = raw
    title = re.sub(r"\bfor\s+\d+\s*(?:minutes?|mins?|hours?|hrs?)\b", "", title, flags=re.I)
    title = re.sub(r"\bpriority\s*[1-5]\b", "", title, flags=re.I)
    title = re.sub(r"\bdue\s+\d{4}-\d{2}-\d{2}(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?", "", title, flags=re.I)
    title = re.sub(r"\bdue\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", "", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip(" ,.-")
    if not title:
        raise ValueError("I need a task title.")
    return title, max(5, min(duration, 480)), priority, deadline


def _event_from_text(text: str, now: datetime) -> tuple[str, datetime, datetime] | None:
    match = re.match(
        r"^(?:add event|add commitment)\s+(.+?)\s+on\s+(\d{4}-\d{2}-\d{2})\s+from\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+to\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$",
        text.strip(),
        re.I,
    )
    if not match:
        return None
    title = match.group(1).strip()
    day = date.fromisoformat(match.group(2))
    sh, sm = _parse_clock(match.group(3), match.group(4), match.group(5))
    eh, em = _parse_clock(match.group(6), match.group(7), match.group(8))
    start = datetime.combine(day, time(sh, sm), tzinfo=now.tzinfo)
    end = datetime.combine(day, time(eh, em), tzinfo=now.tzinfo)
    if end <= start:
        raise ValueError("the event end time must be after the start time")
    return title, start, end


def handle_assistant_message(db: Session, text: str, now: datetime | None = None) -> dict:
    now = _local_now(now)
    clean = text.strip()
    lowered = clean.lower()

    if lowered in {"help", "what can you do", "what can i say"}:
        return {
            "reply": "You can say: “Energy 3, focus 2”, “Add task finish lab report for 90 minutes priority 5”, “Add event lecture on 2026-10-26 from 10 am to 11 am”, “I slept from 1 am to 7 am”, “Generate my weekly plan”, or “What should I do now?”.",
            "action": "help",
            "stored_raw_transcript": False,
        }

    if any(phrase in lowered for phrase in ("what should i do", "what do i do now", "next action", "what's next", "whats next")):
        briefing = morning_briefing(db, now.date(), as_of=now)
        action = briefing.get("next_action")
        if action:
            return {
                "reply": f"Do {action['title']}. Start with {action.get('suggested_initial_minutes') or action['duration_minutes']} minutes. {action.get('instruction') or ''}".strip(),
                "action": "next_action",
                "data": action,
                "stored_raw_transcript": False,
            }
        return {
            "reply": "I do not have a pending academic action yet. Add a task and I can plan from there.",
            "action": "next_action",
            "stored_raw_transcript": False,
        }

    if "generate" in lowered and "week" in lowered and "plan" in lowered:
        monday = now.date() - timedelta(days=now.weekday())
        result = build_weekly_plan(db, monday)
        return {
            "reply": f"Done. Weekly plan version {result['version']} has {len(result['blocks'])} blocks and {result['capacity_shortfall_minutes']} minutes of capacity shortfall.",
            "action": "generate_weekly_plan",
            "data": {"version": result["version"], "blocks": len(result["blocks"]), "capacity_shortfall_minutes": result["capacity_shortfall_minutes"]},
            "stored_raw_transcript": False,
        }

    energy = _parse_rating(clean, "energy")
    focus = _parse_rating(clean, "focus")
    if energy is not None or focus is not None:
        row = UserStateInput(observed_at=now, energy=energy, focus=focus, source="voice_or_text_assistant")
        db.add(row); db.commit(); db.refresh(row)
        pieces = ([f"energy {energy}/5"] if energy is not None else []) + ([f"focus {focus}/5"] if focus is not None else [])
        return {
            "reply": f"Saved {' and '.join(pieces)}. I will use that only as a user estimate for planning.",
            "action": "state_input",
            "data": {"id": row.id, "energy": energy, "focus": focus},
            "stored_raw_transcript": False,
        }

    sleep = _parse_sleep(clean, now)
    if sleep:
        start, end = sleep
        row = SleepRecord(sleep_start=start, sleep_end=end, source="voice_or_text_assistant")
        db.add(row); db.commit(); db.refresh(row)
        minutes = int((end - start).total_seconds() // 60)
        return {
            "reply": f"Saved a {minutes // 60}h {minutes % 60}m sleep record ending at {end.strftime('%H:%M')}. I treated the times as the most recent overnight interval.",
            "action": "sleep_record",
            "data": {"id": row.id, "sleep_start": start, "sleep_end": end, "duration_minutes": minutes},
            "stored_raw_transcript": False,
        }

    event_data = _event_from_text(clean, now)
    if event_data:
        title, starts_at, ends_at = event_data
        duplicate = db.scalar(select(CalendarEvent).where(
            CalendarEvent.title == title,
            CalendarEvent.starts_at == starts_at,
            CalendarEvent.ends_at == ends_at,
        ))
        if duplicate:
            return {
                "reply": f"That event already exists: {title} at {starts_at.strftime('%a %d %b %H:%M')}.",
                "action": "duplicate_event",
                "stored_raw_transcript": False,
            }
        event = CalendarEvent(
            title=title,
            starts_at=starts_at,
            ends_at=ends_at,
            event_type="fixed",
            source="voice_or_text_assistant",
        )
        db.add(event); db.commit(); db.refresh(event)
        return {
            "reply": f"Added {title} on {starts_at.strftime('%a %d %b')} from {starts_at.strftime('%H:%M')} to {ends_at.strftime('%H:%M')}.",
            "action": "event_created",
            "data": {"id": event.id, "title": title, "starts_at": starts_at, "ends_at": ends_at},
            "stored_raw_transcript": False,
        }

    task_data = _task_from_text(clean, now)
    if task_data:
        title, duration, priority, deadline = task_data
        task = Task(
            title=title,
            duration_minutes=duration,
            priority=priority,
            difficulty=3,
            deadline=deadline,
            source="voice_or_text_assistant",
        )
        db.add(task); db.commit(); db.refresh(task)
        due_text = f", due {deadline.strftime('%a %d %b %H:%M')}" if deadline else ""
        return {
            "reply": f"Added “{title}” for {duration} minutes at priority {priority}{due_text}.",
            "action": "task_created",
            "data": {"id": task.id, "title": task.title, "duration_minutes": duration, "priority": priority, "deadline": deadline},
            "stored_raw_transcript": False,
        }

    prompts = assistant_prompts(db, now)
    suggestion = prompts[0]["prompt"] if prompts else "Ask “what should I do now?” or tell me a task, commitment, energy/focus rating, sleep interval, or to generate the weekly plan."
    return {
        "reply": f"I did not change anything because I could not map that safely to a structured action. {suggestion}",
        "action": "no_action",
        "stored_raw_transcript": False,
    }
