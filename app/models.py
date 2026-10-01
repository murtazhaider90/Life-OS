import enum
from datetime import datetime, date, timezone
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class ProvenanceType(str, enum.Enum):
    FACT = "FACT"
    OBSERVATION = "OBSERVATION"
    USER_ESTIMATE = "USER_ESTIMATE"
    AI_INFERENCE = "AI_INFERENCE"
    AI_RECOMMENDATION = "AI_RECOMMENDATION"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), index=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value_json: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    module: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    topic: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_material: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.FACT)
    source: Mapped[str] = mapped_column(String(80), default="manual_input")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_type: Mapped[str] = mapped_column(String(80), default="fixed")
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.FACT)
    source: Mapped[str] = mapped_column(String(80), default="manual_input")
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)


class StudySession(Base):
    __tablename__ = "study_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    module: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    topic: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    planned_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_minutes: Mapped[int] = mapped_column(Integer, default=30)
    focus_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confused: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    music_on: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.OBSERVATION)
    source: Mapped[str] = mapped_column(String(80), default="manual_input")


class CourseDocument(Base):
    __tablename__ = "course_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    module: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    week: Mapped[str | None] = mapped_column(String(40), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(String(80), default="other")
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.EXTERNAL_SOURCE)
    source: Mapped[str] = mapped_column(String(80), default="user_upload")
    academic_year: Mapped[str | None] = mapped_column(String(30), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    chunks: Mapped[list["CourseChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class CourseChunk(Base):
    __tablename__ = "course_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("course_documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    document: Mapped[CourseDocument] = relationship(back_populates="chunks")


class PlanBlock(Base):
    __tablename__ = "plan_blocks"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_date: Mapped[date] = mapped_column(Date, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rationale: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
