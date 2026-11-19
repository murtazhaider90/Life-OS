from __future__ import annotations

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..academic_models import Assessment, LearningObjective, MistakeRecord
from ..academic_schemas import (
    AcademicQuestionRequest,
    AcademicQuizRequest,
    AssessmentBreakdownRequest,
    AssessmentCreate,
    MistakeCreate,
    RevisionPlanRequest,
)
from ..db import get_db
from ..models import ProvenanceType
from ..security import require_local_or_token
from ..services.academic import (
    analyse_document_structure,
    answer_academic_question,
    assessment_breakdown,
    generate_retrieval_quiz,
    module_overview,
    revision_plan,
)
from ..services.ai import ai_provider_status

router = APIRouter(
    prefix="/api/academic",
    tags=["academic"],
    dependencies=[Depends(require_local_or_token)],
)


@router.get("/status")
def status(db: Session = Depends(get_db)):
    return {
        "ai": ai_provider_status(),
        "modules": module_overview(db),
        "grounding": "uploaded course material is the default evidence boundary",
    }


@router.get("/modules")
def modules(db: Session = Depends(get_db)):
    return module_overview(db)


@router.post("/ask")
def ask(payload: AcademicQuestionRequest, db: Session = Depends(get_db)):
    return answer_academic_question(
        db,
        payload.question,
        module=payload.module,
        topic=payload.topic,
        limit=payload.limit,
        allow_general_knowledge=payload.allow_general_knowledge,
    )


@router.post("/documents/{document_id}/analyse")
def analyse(document_id: int, db: Session = Depends(get_db)):
    try:
        return analyse_document_structure(db, document_id, persist=True)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/objectives")
def objectives(
    module: str | None = None,
    topic: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(LearningObjective).order_by(LearningObjective.module, LearningObjective.id)
    rows = db.scalars(query).all()
    if module:
        rows = [r for r in rows if r.module.casefold() == module.casefold()]
    if topic:
        rows = [r for r in rows if topic.casefold() in ((r.topic or "") + " " + r.objective).casefold()]
    return rows


@router.get("/assessments")
def assessments(module: str | None = None, db: Session = Depends(get_db)):
    rows = db.scalars(select(Assessment).order_by(Assessment.deadline, Assessment.title)).all()
    if module:
        rows = [r for r in rows if r.module.casefold() == module.casefold()]
    return rows


@router.post("/assessments")
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    row = Assessment(
        module=payload.module,
        title=payload.title,
        assessment_type=payload.assessment_type,
        deadline=payload.deadline,
        weight_percent=payload.weight_percent,
        brief=payload.brief,
        criteria_json=json.dumps(payload.criteria),
        status="manual",
        provenance_type=ProvenanceType.USER_ESTIMATE,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/assessments/{assessment_id}/breakdown")
def breakdown(
    assessment_id: int,
    payload: AssessmentBreakdownRequest,
    db: Session = Depends(get_db),
):
    try:
        return assessment_breakdown(db, assessment_id, create_tasks=payload.create_tasks)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/revision-plan")
def build_revision_plan(payload: RevisionPlanRequest, db: Session = Depends(get_db)):
    return revision_plan(
        db,
        module=payload.module,
        create_tasks=payload.create_tasks,
        horizon_days=payload.horizon_days,
    )


@router.post("/quiz")
def quiz(payload: AcademicQuizRequest, db: Session = Depends(get_db)):
    return generate_retrieval_quiz(
        db,
        module=payload.module,
        topic=payload.topic,
        count=payload.count,
    )


@router.post("/mistakes")
def create_mistake(payload: MistakeCreate, db: Session = Depends(get_db)):
    row = MistakeRecord(**payload.model_dump(), source="manual_input")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/mistakes")
def mistakes(
    module: str | None = None,
    topic: str | None = None,
    unresolved_only: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(MistakeRecord)
        .order_by(MistakeRecord.occurred_at.desc())
        .limit(limit)
    ).all()
    if module:
        rows = [r for r in rows if r.module.casefold() == module.casefold()]
    if topic:
        rows = [r for r in rows if r.topic.casefold() == topic.casefold()]
    if unresolved_only:
        rows = [r for r in rows if not r.resolved]
    return rows


@router.post("/mistakes/{mistake_id}/resolve")
def resolve_mistake(mistake_id: int, db: Session = Depends(get_db)):
    row = db.get(MistakeRecord, mistake_id)
    if not row:
        raise HTTPException(404, "mistake not found")
    row.resolved = True
    db.commit()
    db.refresh(row)
    return row
