from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from ..models import ActivityEvent, ActivityLabel, ActivityRule, StudySession


def _domain_matches(domain: str, pattern: str) -> bool:
    domain = domain.lower().rstrip(".")
    pattern = pattern.lower().lstrip(".").rstrip(".")
    return domain == pattern or domain.endswith("." + pattern)


def find_matching_rule(db: Session, event: ActivityEvent) -> ActivityRule | None:
    rules = db.scalars(select(ActivityRule).where(ActivityRule.enabled.is_(True)).order_by(ActivityRule.id)).all()
    for rule in rules:
        if rule.target_type == "application" and event.application:
            if event.application.casefold() == rule.pattern.casefold():
                return rule
        elif rule.target_type == "domain" and event.domain:
            if _domain_matches(event.domain, rule.pattern):
                return rule
    return None


def label_event(db: Session, event: ActivityEvent) -> ActivityLabel | None:
    rule = find_matching_rule(db, event)
    if not rule:
        return None
    existing = db.scalar(select(ActivityLabel).where(ActivityLabel.activity_event_id == event.id))
    if existing:
        existing.label = rule.label
        existing.rule_id = rule.id
        existing.basis = f"explicit {rule.target_type} rule: {rule.pattern}"
        return existing
    label = ActivityLabel(
        activity_event_id=event.id,
        label=rule.label,
        rule_id=rule.id,
        basis=f"explicit {rule.target_type} rule: {rule.pattern}",
    )
    db.add(label)
    return label


def relabel_all(db: Session) -> int:
    db.execute(delete(ActivityLabel))
    events = db.scalars(select(ActivityEvent).order_by(ActivityEvent.id)).all()
    count = 0
    for event in events:
        if label_event(db, event):
            count += 1
    db.commit()
    return count


def session_metrics(db: Session, session_id: int) -> dict:
    session = db.get(StudySession, session_id)
    if not session:
        raise LookupError("study session not found")

    start_latency_seconds = None
    if session.planned_start and session.actual_start:
        start_latency_seconds = max(0, int((session.actual_start - session.planned_start).total_seconds()))

    window_start = session.actual_start or session.planned_start
    window_end = session.ended_at
    distraction_seconds = 0
    study_seconds = 0
    neutral_seconds = 0
    labelled_event_count = 0

    if window_start and window_end:
        rows = db.execute(
            select(ActivityEvent, ActivityLabel)
            .join(ActivityLabel, ActivityLabel.activity_event_id == ActivityEvent.id, isouter=True)
            .where(ActivityEvent.occurred_at >= window_start, ActivityEvent.occurred_at < window_end)
        ).all()
        for event, label in rows:
            if event.study_session_id not in (None, session.id):
                continue
            seconds = max(0, event.duration_seconds)
            if label:
                labelled_event_count += 1
                if label.label == "distraction":
                    distraction_seconds += seconds
                elif label.label == "study":
                    study_seconds += seconds
                elif label.label == "neutral":
                    neutral_seconds += seconds

    return {
        "study_session_id": session.id,
        "start_latency_seconds": start_latency_seconds,
        "distraction_seconds": distraction_seconds,
        "study_labelled_seconds": study_seconds,
        "neutral_labelled_seconds": neutral_seconds,
        "labelled_event_count": labelled_event_count,
        "classification_note": "Labels come only from enabled explicit activity rules; unlabelled activity is not assumed to be distraction.",
    }


def prune_raw_activity(db: Session, retention_days: int, now: datetime | None = None) -> int:
    if retention_days < 1:
        raise ValueError("retention_days must be positive")
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    result = db.execute(delete(ActivityEvent).where(ActivityEvent.occurred_at < cutoff))
    db.commit()
    return int(result.rowcount or 0)
