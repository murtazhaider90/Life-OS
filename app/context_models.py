from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .models import ProvenanceType


class SleepRecord(Base):
    __tablename__ = "sleep_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    sleep_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sleep_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="manual_input")
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.USER_ESTIMATE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TrainingRecord(Base):
    __tablename__ = "training_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    intensity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    modality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="manual_input")
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.USER_ESTIMATE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MealRecord(Base):
    __tablename__ = "meal_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    consumed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    meal_type: Mapped[str] = mapped_column(String(40))
    size_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="manual_input")
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.USER_ESTIMATE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FocusDomainRule(Base):
    __tablename__ = "focus_domain_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    adguard_rule_owned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class InterventionEvent(Base):
    __tablename__ = "intervention_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(80), index=True)
    target: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(40), index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    source: Mapped[str] = mapped_column(String(80), default="life_os")
