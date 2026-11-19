from datetime import datetime, timedelta, timezone

from app.context_models import FocusDomainRule
from app.models import ActivityEvent, ActivityLabel
from app.services.focus import apply_focus_mode, focus_recommendation, reconcile_expired_focus_mode, release_focus_mode


class FakeAdGuard:
    def __init__(self, rules=None):
        self.rules = list(rules or [])
        self.updates = []

    def filtering_status(self):
        return {"user_rules": list(self.rules)}

    def set_user_rules(self, rules):
        self.rules = list(rules)
        self.updates.append(list(rules))


def test_focus_mode_preserves_existing_rules_and_releases_only_life_os_rules(db):
    db.add(FocusDomainRule(domain="reddit.com", reason="focus"))
    db.commit()
    client = FakeAdGuard(["||existing.example^", "@@||allowed.example^"])
    now = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)

    applied = apply_focus_mode(db, 45, client=client, now=now)
    assert applied["applied"] is True
    assert "||reddit.com^" in client.rules
    assert "||existing.example^" in client.rules
    assert "@@||allowed.example^" in client.rules

    released = release_focus_mode(db, client=client, now=now + timedelta(minutes=10))
    assert "||reddit.com^" in released["removed_rules"]
    assert "||reddit.com^" not in client.rules
    assert "||existing.example^" in client.rules
    assert "@@||allowed.example^" in client.rules


def test_preexisting_matching_rule_is_not_owned_or_removed(db):
    db.add(FocusDomainRule(domain="reddit.com"))
    db.commit()
    client = FakeAdGuard(["||reddit.com^", "||existing.example^"])
    now = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)

    applied = apply_focus_mode(db, 45, client=client, now=now)
    assert applied["added_rules"] == []
    released = release_focus_mode(db, client=client, now=now + timedelta(minutes=1))
    assert released["removed_rules"] == []
    assert "||reddit.com^" in client.rules


def test_expiry_releases_owned_rule_even_if_domain_was_disabled_after_apply(db):
    rule = FocusDomainRule(domain="youtube.com")
    db.add(rule); db.commit()
    client = FakeAdGuard([])
    now = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
    apply_focus_mode(db, 5, client=client, now=now)
    rule.enabled = False
    db.commit()

    result = reconcile_expired_focus_mode(db, client=client, now=now + timedelta(minutes=6))
    assert result["released"] is True
    assert "||youtube.com^" not in client.rules


def test_focus_recommendation_counts_only_explicit_distraction_labels(db):
    now = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
    labelled = ActivityEvent(
        kind="domain_sample",
        occurred_at=now - timedelta(minutes=5),
        duration_seconds=360,
        domain="reddit.com",
        source="test",
    )
    unlabelled = ActivityEvent(
        kind="domain_sample",
        occurred_at=now - timedelta(minutes=4),
        duration_seconds=1200,
        domain="unknown.example",
        source="test",
    )
    db.add_all([labelled, unlabelled]); db.flush()
    db.add(ActivityLabel(
        activity_event_id=labelled.id,
        label="distraction",
        basis="explicit domain rule: reddit.com",
    ))
    db.commit()

    result = focus_recommendation(db, as_of=now)
    assert result["explicit_distraction_seconds"] == 360
    assert result["recommend_focus_mode"] is True
    assert "explicit user activity rules" in result["evidence_note"]
