from datetime import datetime, timedelta, timezone

from app.models import ActivityEvent, ActivityLabel, ActivityRule, StudySession, UserStateInput
from app.services.activity import label_event, prune_raw_activity, session_metrics


def test_domain_rule_is_explicit_and_suffix_matches(db):
    rule = ActivityRule(target_type="domain", pattern="example.com", label="distraction")
    db.add(rule); db.flush()
    event = ActivityEvent(
        kind="domain_sample",
        occurred_at=datetime.now(timezone.utc),
        duration_seconds=60,
        domain="social.example.com",
        source="test",
    )
    db.add(event); db.flush()
    label = label_event(db, event)
    db.commit()
    assert label is not None
    assert label.label == "distraction"
    assert "explicit domain rule" in label.basis


def test_unlabelled_activity_is_not_assumed_distraction(db):
    event = ActivityEvent(
        kind="app_sample",
        occurred_at=datetime.now(timezone.utc),
        duration_seconds=15,
        application="UnknownApp",
        source="test",
    )
    db.add(event); db.flush()
    assert label_event(db, event) is None


def test_session_metrics_start_latency_and_distraction(db):
    start = datetime(2026, 10, 2, 10, 5, tzinfo=timezone.utc)
    session = StudySession(
        planned_start=start - timedelta(minutes=5),
        actual_start=start,
        ended_at=start + timedelta(minutes=30),
        planned_minutes=30,
    )
    db.add(session); db.flush()
    rule = ActivityRule(target_type="application", pattern="SocialApp", label="distraction")
    db.add(rule); db.flush()
    distraction = ActivityEvent(
        kind="app_sample",
        occurred_at=start + timedelta(minutes=3),
        duration_seconds=45,
        application="SocialApp",
        study_session_id=session.id,
        source="test",
    )
    study = ActivityEvent(
        kind="app_sample",
        occurred_at=start + timedelta(minutes=4),
        duration_seconds=60,
        application="MATLAB",
        study_session_id=session.id,
        source="test",
    )
    db.add_all([distraction, study]); db.flush()
    label_event(db, distraction)
    db.add(ActivityRule(target_type="application", pattern="MATLAB", label="study")); db.flush()
    label_event(db, study)
    db.commit()

    metrics = session_metrics(db, session.id)
    assert metrics["start_latency_seconds"] == 300
    assert metrics["distraction_seconds"] == 45
    assert metrics["study_labelled_seconds"] == 60


def test_raw_activity_retention_does_not_delete_state_inputs(db):
    now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
    db.add(ActivityEvent(kind="app_sample", occurred_at=now - timedelta(days=60), duration_seconds=15, source="test"))
    db.add(ActivityEvent(kind="app_sample", occurred_at=now - timedelta(days=2), duration_seconds=15, source="test"))
    db.add(UserStateInput(observed_at=now - timedelta(days=60), energy=3))
    db.commit()

    deleted = prune_raw_activity(db, 45, now=now)
    assert deleted == 1
    assert db.query(ActivityEvent).count() == 1
    assert db.query(UserStateInput).count() == 1
