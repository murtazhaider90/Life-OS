from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from statistics import mean
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import ActivityEvent, ActivityLabel, InferenceRecord, StudyAttempt, StudySession, Task, WeeklyPlanBlock
from .activity import session_metrics
from .learning import topic_evidence
from .weekly_planner import get_active_weekly_plan
from .planner import _ensure_tz


def _bounds(week_start: date) -> tuple[datetime, datetime, ZoneInfo]:
    tz = ZoneInfo(get_settings().timezone)
    start = datetime.combine(week_start, time(0), tzinfo=tz)
    end = start + timedelta(days=7)
    return start, end, tz


def _duration_minutes(session: StudySession, tz: ZoneInfo) -> int:
    if not session.actual_start or not session.ended_at:
        return 0
    start = _ensure_tz(session.actual_start, tz)
    end = _ensure_tz(session.ended_at, tz)
    return max(0, int((end - start).total_seconds() // 60))


def _music_inference(db: Session, sessions: list[StudySession], start: datetime, end: datetime) -> dict | None:
    on = [s for s in sessions if s.music_on is True and s.focus_rating is not None]
    off = [s for s in sessions if s.music_on is False and s.focus_rating is not None]
    if len(on) < 3 or len(off) < 3:
        return None
    on_focus = mean([s.focus_rating for s in on])
    off_focus = mean([s.focus_rating for s in off])
    diff = off_focus - on_focus
    if abs(diff) < 0.5:
        conclusion = f"Recorded focus ratings were similar with music on ({on_focus:.1f}/5) and off ({off_focus:.1f}/5) this week."
    elif diff > 0:
        conclusion = f"Recorded focus ratings were higher with music off ({off_focus:.1f}/5) than on ({on_focus:.1f}/5) this week."
    else:
        conclusion = f"Recorded focus ratings were higher with music on ({on_focus:.1f}/5) than off ({off_focus:.1f}/5) this week."
    total = len(on) + len(off)
    confidence = min(0.75, 0.45 + 0.025 * total)
    status = "developing" if total >= 10 else "provisional"
    key = f"music_focus:{start.date().isoformat()}"
    existing = db.scalar(select(InferenceRecord).where(
        InferenceRecord.inference_key == key,
        InferenceRecord.date_range_start == start,
        InferenceRecord.date_range_end == end,
    ))
    if existing is None:
        existing = InferenceRecord(
            inference_key=key,
            domain="study_context",
            conclusion=conclusion,
            confidence=confidence,
            evidence_count=total,
            status=status,
            evidence_json=json.dumps([
                {"music_on_sessions": len(on), "mean_focus": on_focus},
                {"music_off_sessions": len(off), "mean_focus": off_focus},
            ]),
            contradictory_evidence_json=json.dumps([
                {"note": "Individual sessions may contradict the aggregate; this comparison is observational and does not establish causation."}
            ]),
            date_range_start=start,
            date_range_end=end,
        )
        db.add(existing); db.flush()
    return {
        "conclusion": existing.conclusion,
        "confidence": existing.confidence,
        "evidence_count": existing.evidence_count,
        "status": existing.status,
        "note": "Confidence is an internal evidence heuristic, not a scientific probability; the comparison is observational, not causal.",
    }


def build_weekly_review(db: Session, week_start: date) -> dict:
    start, end, tz = _bounds(week_start)
    sessions = db.scalars(select(StudySession).where(
        StudySession.actual_start >= start,
        StudySession.actual_start < end,
    ).order_by(StudySession.actual_start)).all()
    attempts = db.scalars(select(StudyAttempt).where(
        StudyAttempt.attempted_at >= start,
        StudyAttempt.attempted_at < end,
    )).all()

    study_minutes = sum(_duration_minutes(s, tz) for s in sessions)
    modules = sorted({s.module for s in sessions if s.module})
    topics = sorted({s.topic for s in sessions if s.topic})
    completed_sessions = sum(1 for s in sessions if s.completed)
    completion_rate = (completed_sessions / len(sessions)) if sessions else None

    total_questions = sum(a.total_count or 0 for a in attempts if a.correct_count is not None and a.total_count is not None)
    correct_questions = sum(a.correct_count or 0 for a in attempts if a.correct_count is not None and a.total_count is not None)
    accuracy = (correct_questions / total_questions) if total_questions else None

    weak = [x for x in topic_evidence(db, as_of=end) if x["status"] in {"weak", "requires_retrieval", "developing"}]
    overdue = db.scalars(select(Task).where(Task.completed.is_(False), Task.deadline.is_not(None), Task.deadline < end)).all()
    upcoming_end = end + timedelta(days=7)
    upcoming = db.scalars(select(Task).where(Task.completed.is_(False), Task.deadline >= end, Task.deadline < upcoming_end)).all()

    latencies: list[int] = []
    distraction_seconds = 0
    labelled_seconds = 0
    for session in sessions:
        metrics = session_metrics(db, session.id)
        if metrics["start_latency_seconds"] is not None:
            latencies.append(metrics["start_latency_seconds"])
        distraction_seconds += metrics["distraction_seconds"]
        labelled_seconds += metrics["distraction_seconds"] + metrics["study_labelled_seconds"] + metrics["neutral_labelled_seconds"]
    average_start_latency_minutes = (mean(latencies) / 60) if latencies else None
    distraction_share = (distraction_seconds / labelled_seconds) if labelled_seconds else None

    time_buckets: dict[str, list[StudySession]] = defaultdict(list)
    for session in sessions:
        if not session.actual_start:
            continue
        hour = _ensure_tz(session.actual_start, tz).hour
        bucket = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
        time_buckets[bucket].append(session)
    time_patterns = []
    for bucket, rows in sorted(time_buckets.items()):
        if len(rows) < 3:
            continue
        rated = [r.focus_rating for r in rows if r.focus_rating is not None]
        time_patterns.append({
            "period": bucket,
            "sessions": len(rows),
            "completion_rate": sum(1 for r in rows if r.completed) / len(rows),
            "average_focus": mean(rated) if rated else None,
        })

    music = _music_inference(db, sessions, start, end)

    active_plan = get_active_weekly_plan(db, week_start)
    planned_task_ids: set[int] = set()
    minimum_viable_task_ids: set[int] = set()
    if active_plan:
        blocks = db.scalars(select(WeeklyPlanBlock).where(WeeklyPlanBlock.weekly_plan_id == active_plan.id)).all()
        planned_task_ids = {b.task_id for b in blocks}
        minimum_viable_task_ids = {b.task_id for b in blocks if b.minimum_viable}
    completed_planned = 0
    completed_minimum = 0
    for task_id in planned_task_ids:
        task = db.get(Task, task_id)
        if task and task.completed and task.completed_at and _ensure_tz(task.completed_at, tz) <= end:
            completed_planned += 1
            if task_id in minimum_viable_task_ids:
                completed_minimum += 1

    insights = []
    if music:
        insights.append({"type": "music_context", **music})
    if average_start_latency_minutes is not None and len(latencies) >= 3:
        insights.append({
            "type": "start_latency",
            "conclusion": f"Average recorded study start latency was {average_start_latency_minutes:.1f} minutes across {len(latencies)} sessions.",
            "evidence_count": len(latencies),
            "status": "descriptive",
        })
    if distraction_share is not None:
        insights.append({
            "type": "explicit_distraction",
            "conclusion": f"Explicitly labelled distraction accounted for {distraction_share:.0%} of labelled activity time during recorded study sessions.",
            "evidence_count": sum(1 for s in sessions if s.actual_start and s.ended_at),
            "status": "descriptive",
            "note": "Only activity covered by explicit user rules contributes to this percentage.",
        })

    db.commit()
    return {
        "week_start": week_start,
        "academic": {
            "study_minutes": study_minutes,
            "study_sessions": len(sessions),
            "modules_covered": modules,
            "topics_covered": topics,
            "scored_questions": total_questions,
            "correct_questions": correct_questions,
            "recorded_accuracy": accuracy,
            "weak_or_due_topics": weak[:10],
            "overdue_tasks": [{"id": t.id, "title": t.title, "deadline": t.deadline} for t in overdue],
            "upcoming_deadlines": [{"id": t.id, "title": t.title, "deadline": t.deadline} for t in upcoming],
        },
        "behavioral": {
            "average_start_latency_minutes": average_start_latency_minutes,
            "session_completion_rate": completion_rate,
            "explicit_label_distraction_share": distraction_share,
            "time_of_day_patterns": time_patterns,
            "music_observation": music or {"status": "insufficient_evidence", "reason": "need at least 3 rated sessions with music on and 3 with music off"},
            "phone_usage": {"status": "not_available", "reason": "phone telemetry is not integrated"},
        },
        "physical_context": {
            "status": "not_available",
            "reason": "sleep, training and meal integrations are Phase 5; no values are invented",
        },
        "planning": {
            "active_plan_version": active_plan.version if active_plan else None,
            "planned_tasks": len(planned_task_ids),
            "completed_planned_tasks_by_week_end": completed_planned,
            "minimum_viable_tasks": len(minimum_viable_task_ids),
            "completed_minimum_viable_tasks_by_week_end": completed_minimum,
            "capacity_shortfall_minutes": active_plan.capacity_shortfall_minutes if active_plan else None,
        },
        "insights": insights[:5],
    }
