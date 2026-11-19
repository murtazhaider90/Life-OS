from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..context_models import FocusDomainRule, InterventionEvent
from ..models import ActivityEvent, ActivityLabel
from .adguard import AdGuardHomeClient, adguard_configured


def _aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def managed_rule(domain: str) -> str:
    return f"||{domain}^"


def managed_domains(db: Session, *, enabled_only: bool = True) -> list[str]:
    query = select(FocusDomainRule).order_by(FocusDomainRule.domain)
    if enabled_only:
        query = query.where(FocusDomainRule.enabled.is_(True))
    return [r.domain for r in db.scalars(query).all()]


def focus_preview(db: Session) -> dict:
    domains = managed_domains(db)
    return {
        "configured": adguard_configured(),
        "domains": domains,
        "rules": [managed_rule(d) for d in domains],
        "note": "Applying focus mode preserves existing AdGuard Home user rules. Release removes only rules that Life OS itself added.",
    }


def focus_recommendation(
    db: Session,
    as_of: datetime | None = None,
    window_minutes: int = 30,
    threshold_seconds: int = 300,
) -> dict:
    now = as_of or datetime.now(timezone.utc)
    start = now - timedelta(minutes=window_minutes)
    rows = db.execute(
        select(ActivityEvent, ActivityLabel)
        .join(ActivityLabel, ActivityLabel.activity_event_id == ActivityEvent.id)
        .where(
            ActivityEvent.occurred_at >= start,
            ActivityEvent.occurred_at <= now,
            ActivityLabel.label == "distraction",
        )
    ).all()
    seconds = sum(max(0, event.duration_seconds) for event, _ in rows)
    triggered = seconds >= threshold_seconds
    return {
        "window_minutes": window_minutes,
        "explicit_distraction_seconds": seconds,
        "threshold_seconds": threshold_seconds,
        "recommend_focus_mode": triggered,
        "message": (
            "Explicitly-labelled distraction crossed the configured soft threshold; focus mode is available but is not applied automatically."
            if triggered
            else "No focus-mode trigger from explicitly-labelled activity in this window."
        ),
        "evidence_note": "Only events labelled by explicit user activity rules count as distraction.",
    }


def _status_rules(client: AdGuardHomeClient) -> list[str]:
    return list(client.filtering_status().get("user_rules") or [])


def apply_focus_mode(
    db: Session,
    duration_minutes: int,
    *,
    client: AdGuardHomeClient | None = None,
    now: datetime | None = None,
) -> dict:
    client = client or AdGuardHomeClient.from_settings()
    now = _aware_utc(now or datetime.now(timezone.utc))
    rows = db.scalars(
        select(FocusDomainRule)
        .where(FocusDomainRule.enabled.is_(True))
        .order_by(FocusDomainRule.domain)
    ).all()
    if not rows:
        return {"applied": False, "reason": "no enabled focus domains"}

    current = _status_rules(client)
    additions: list[str] = []
    for row in rows:
        rule = managed_rule(row.domain)
        if rule not in current:
            current.append(rule)
            additions.append(rule)
            row.adguard_rule_owned = True

    if additions:
        client.set_user_rules(current)

    event = InterventionEvent(
        kind="focus_mode",
        target=",".join(r.domain for r in rows),
        status="active",
        requested_at=now,
        applied_at=now,
        expires_at=now + timedelta(minutes=duration_minutes),
        details_json=json.dumps({"domains": [r.domain for r in rows], "added_rules": additions, "duration_minutes": duration_minutes}),
    )
    db.add(event); db.commit(); db.refresh(event)
    return {
        "applied": True,
        "intervention_event_id": event.id,
        "domains": [r.domain for r in rows],
        "added_rules": additions,
        "expires_at": event.expires_at,
    }


def release_focus_mode(
    db: Session,
    *,
    client: AdGuardHomeClient | None = None,
    now: datetime | None = None,
    status: str = "released",
) -> dict:
    client = client or AdGuardHomeClient.from_settings()
    now = _aware_utc(now or datetime.now(timezone.utc))
    owned_rows = db.scalars(
        select(FocusDomainRule).where(FocusDomainRule.adguard_rule_owned.is_(True))
    ).all()
    owned_rules = {managed_rule(row.domain) for row in owned_rows}
    current = _status_rules(client)
    kept = [rule for rule in current if rule not in owned_rules]
    removed = [rule for rule in current if rule in owned_rules]
    if removed:
        client.set_user_rules(kept)
    for row in owned_rows:
        row.adguard_rule_owned = False

    active = db.scalars(
        select(InterventionEvent).where(
            InterventionEvent.kind == "focus_mode",
            InterventionEvent.status == "active",
        )
    ).all()
    for event in active:
        event.status = status
    db.commit()
    return {"released": True, "removed_rules": removed, "at": now}


def reconcile_expired_focus_mode(db: Session, *, client: AdGuardHomeClient | None = None, now: datetime | None = None) -> dict:
    now = _aware_utc(now or datetime.now(timezone.utc))
    active = db.scalars(
        select(InterventionEvent).where(
            InterventionEvent.kind == "focus_mode",
            InterventionEvent.status == "active",
        )
    ).all()
    expired = [e for e in active if e.expires_at is not None and _aware_utc(e.expires_at) <= now]
    remaining = [e for e in active if e.expires_at is None or _aware_utc(e.expires_at) > now]

    if expired and not remaining:
        return release_focus_mode(db, client=client, now=now, status="expired")

    for event in expired:
        event.status = "expired"
    db.commit()
    return {"expired_events": len(expired), "active_events": len(remaining), "released": False}
