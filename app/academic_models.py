from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .models import ProvenanceType


class LearningObjective(Base):
    __tablename__ = "learning_objectives"
    __table_args__ = (
        UniqueConstraint("source_chunk_id", "objective", name="uq_learning_objective_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(120), index=True)
    topic: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    subtopic: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    objective: Mapped[str] = mapped_column(Text)
    assessment_relevance: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    status: Mapped[str] = mapped_column(String(32), default="extracted", index=True)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("course_documents.id", ondelete="CASCADE"), index=True)
    source_chunk_id: Mapped[int] = mapped_column(ForeignKey("course_chunks.id", ondelete="CASCADE"), index=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(
        Enum(ProvenanceType), default=ProvenanceType.EXTERNAL_SOURCE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        UniqueConstraint("source_document_id", "title", name="uq_assessment_source_title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    assessment_type: Mapped[str] = mapped_column(String(80), default="assessment", index=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    weight_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    criteria_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(32), default="extracted", index=True)
    source_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("course_documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("course_chunks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(
        Enum(ProvenanceType), default=ProvenanceType.EXTERNAL_SOURCE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class MistakeRecord(Base):
    __tablename__ = "mistake_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(120), index=True)
    topic: Mapped[str] = mapped_column(String(160), index=True)
    learning_objective: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    mistake_type: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    correction: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_material: Mapped[str | None] = mapped_column(String(255), nullable=True)
    study_attempt_id: Mapped[int | None] = mapped_column(
        ForeignKey("study_attempts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(
        Enum(ProvenanceType), default=ProvenanceType.OBSERVATION
    )
    source: Mapped[str] = mapped_column(String(80), default="manual_input")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
