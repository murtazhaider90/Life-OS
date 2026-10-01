from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import StudyAttempt


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def topic_evidence(db: Session, as_of: datetime | None = None) -> list[dict]:
    """Return descriptive topic status from recorded attempts.

    Thresholds are transparent planning heuristics, not scientific measurements:
    - insufficient evidence: fewer than 2 attempts and fewer than 5 scored questions
    - weak: scored accuracy <70% or mean confidence <=2/5
    - requires retrieval: enough evidence exists and last attempt was >=7 days ago
    - developing: scored accuracy <85% or mean confidence <=3/5
    - stable: none of the above
    """
    as_of = _aware(as_of or datetime.now(timezone.utc))
    attempts = db.scalars(select(StudyAttempt).where(StudyAttempt.attempted_at <= as_of).order_by(StudyAttempt.attempted_at)).all()
    groups: dict[tuple[str, str, str | None], list[StudyAttempt]] = defaultdict(list)
    for attempt in attempts:
        groups[(attempt.module, attempt.topic, attempt.learning_objective)].append(attempt)

    output: list[dict] = []
    for (module, topic, objective), rows in groups.items():
        scored = [r for r in rows if r.correct_count is not None and r.total_count is not None]
        total_questions = sum(r.total_count or 0 for r in scored)
        correct_questions = sum(r.correct_count or 0 for r in scored)
        accuracy = (correct_questions / total_questions) if total_questions else None
        confidences = [r.confidence for r in rows if r.confidence is not None]
        avg_confidence = mean(confidences) if confidences else None
        last_attempt = max(_aware(r.attempted_at) for r in rows)
        days_since = max(0, (as_of - last_attempt).days)
        evidence_count = len(rows)

        reasons: list[str] = []
        if evidence_count < 2 and total_questions < 5:
            status = "insufficient_evidence"
            reasons.append("fewer than 2 attempts and fewer than 5 scored questions")
        elif (accuracy is not None and accuracy < 0.70) or (avg_confidence is not None and avg_confidence <= 2.0):
            status = "weak"
            if accuracy is not None and accuracy < 0.70:
                reasons.append(f"recorded accuracy is {accuracy:.0%}, below the 70% weak-topic heuristic")
            if avg_confidence is not None and avg_confidence <= 2.0:
                reasons.append(f"mean self-reported confidence is {avg_confidence:.1f}/5")
        elif days_since >= 7:
            status = "requires_retrieval"
            reasons.append(f"last recorded attempt was {days_since} days ago")
        elif (accuracy is not None and accuracy < 0.85) or (avg_confidence is not None and avg_confidence <= 3.0):
            status = "developing"
            if accuracy is not None and accuracy < 0.85:
                reasons.append(f"recorded accuracy is {accuracy:.0%}, below the 85% developing heuristic")
            if avg_confidence is not None and avg_confidence <= 3.0:
                reasons.append(f"mean self-reported confidence is {avg_confidence:.1f}/5")
        else:
            status = "stable"
            reasons.append("recorded attempts do not currently trigger a weak/developing/retrieval heuristic")

        recommended_action = None
        if status == "weak":
            recommended_action = "Do 30 minutes of closed-notes practice, then review mistakes for 15 minutes."
        elif status == "requires_retrieval":
            recommended_action = "Do 20 minutes of retrieval practice from memory before consulting notes."
        elif status == "developing":
            recommended_action = "Attempt a short problem set without notes and record errors/confidence."

        output.append({
            "module": module,
            "topic": topic,
            "learning_objective": objective,
            "status": status,
            "evidence_count": evidence_count,
            "scored_questions": total_questions,
            "correct_questions": correct_questions,
            "accuracy": accuracy,
            "average_confidence": avg_confidence,
            "last_attempted_at": last_attempt,
            "days_since_attempt": days_since,
            "reasons": reasons,
            "recommended_action": recommended_action,
            "measurement_note": "Status is a transparent internal planning heuristic based only on recorded attempts; it is not a scientific mastery score.",
        })

    rank = {"weak": 0, "requires_retrieval": 1, "developing": 2, "insufficient_evidence": 3, "stable": 4}
    return sorted(output, key=lambda x: (rank[x["status"]], x["module"].casefold(), x["topic"].casefold()))
