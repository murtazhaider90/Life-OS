from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..context_models import FocusDomainRule, InterventionEvent
from ..context_schemas import FocusDomainCreate, FocusModeRequest, FocusReleaseRequest
from ..db import get_db
from ..security import require_local_or_token
from ..services.adguard import AdGuardNotConfigured, AdGuardRequestError, adguard_configured
from ..services.focus import apply_focus_mode, focus_preview, focus_recommendation, release_focus_mode

router = APIRouter(prefix="/api/focus", tags=["focus"], dependencies=[Depends(require_local_or_token)])


@router.get("/domains")
def list_domains(db: Session = Depends(get_db)):
    return db.scalars(select(FocusDomainRule).order_by(FocusDomainRule.domain)).all()


@router.post("/domains")
def create_domain(payload: FocusDomainCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(FocusDomainRule).where(FocusDomainRule.domain == payload.domain))
    if existing:
        existing.enabled = True
        existing.reason = payload.reason
        db.commit(); db.refresh(existing)
        return existing
    row = FocusDomainRule(**payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.post("/domains/{rule_id}/disable")
def disable_domain(rule_id: int, db: Session = Depends(get_db)):
    row = db.get(FocusDomainRule, rule_id)
    if not row:
        raise HTTPException(404, "focus domain not found")
    row.enabled = False
    db.commit(); db.refresh(row)
    return row


@router.get("/status")
def status(db: Session = Depends(get_db)):
    active = db.scalars(select(InterventionEvent).where(
        InterventionEvent.kind == "focus_mode",
        InterventionEvent.status == "active",
    ).order_by(InterventionEvent.requested_at.desc())).all()
    return {
        "adguard_configured": adguard_configured(),
        "enabled_domains": [r.domain for r in db.scalars(select(FocusDomainRule).where(FocusDomainRule.enabled.is_(True))).all()],
        "active_interventions": [{
            "id": row.id,
            "target": row.target,
            "expires_at": row.expires_at,
            "status": row.status,
        } for row in active],
    }


@router.get("/recommendation")
def recommendation(as_of: datetime | None = None, db: Session = Depends(get_db)):
    return focus_recommendation(db, as_of=as_of)


@router.get("/preview")
def preview(db: Session = Depends(get_db)):
    return focus_preview(db)


@router.post("/apply")
def apply(payload: FocusModeRequest, db: Session = Depends(get_db)):
    if not payload.confirm:
        raise HTTPException(409, "explicit confirm=true is required before changing AdGuard Home rules")
    try:
        return apply_focus_mode(db, payload.duration_minutes)
    except AdGuardNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except AdGuardRequestError as exc:
        raise HTTPException(502, f"AdGuard Home request failed: {exc}") from exc


@router.post("/release")
def release(payload: FocusReleaseRequest, db: Session = Depends(get_db)):
    if not payload.confirm:
        raise HTTPException(409, "explicit confirm=true is required before changing AdGuard Home rules")
    try:
        return release_focus_mode(db)
    except AdGuardNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except AdGuardRequestError as exc:
        raise HTTPException(502, f"AdGuard Home request failed: {exc}") from exc
