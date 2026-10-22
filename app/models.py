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


class ActivityRule(Base):
    __tablename__ = "activity_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    target_type: Mapped[str] = mapped_column(String(32), index=True)  # application | domain
    pattern: Mapped[str] = mapped_column(String(255), index=True)
    label: Mapped[str] = mapped_column(String(32), index=True)  # study | distraction | neutral
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ActivityEvent(Base):
    __tablename__ = "activity_events"
    __table_args__ = (UniqueConstraint("source", "source_event_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    application: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    idle_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    study_session_id: Mapped[int | None] = mapped_column(ForeignKey("study_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(80), default="desktop_agent", index=True)
    source_event_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.OBSERVATION)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ActivityLabel(Base):
    __tablename__ = "activity_labels"
    id: Mapped[int] = mapped_column(primary_key=True)
    activity_event_id: Mapped[int] = mapped_column(ForeignKey("activity_events.id", ondelete="CASCADE"), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(32), index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("activity_rules.id", ondelete="SET NULL"), nullable=True)
    basis: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserStateInput(Base):
    __tablename__ = "user_state_inputs"
    id: Mapped[int] = mapped_column(primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    energy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    focus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confused: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    study_session_id: Mapped[int | None] = mapped_column(ForeignKey("study_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.USER_ESTIMATE)
    source: Mapped[str] = mapped_column(String(80), default="manual_input")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class StudyAttempt(Base):
    __tablename__ = "study_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    study_session_id: Mapped[int | None] = mapped_column(ForeignKey("study_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    module: Mapped[str] = mapped_column(String(120), index=True)
    topic: Mapped[str] = mapped_column(String(160), index=True)
    learning_objective: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_material: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_type: Mapped[ProvenanceType] = mapped_column(Enum(ProvenanceType), default=ProvenanceType.OBSERVATION)
    source: Mapped[str] = mapped_column(String(80), default="manual_input")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    reason: Mapped[str] = mapped_column(String(80), default="initial")
    window_start_hour: Mapped[int] = mapped_column(Integer, default=8)
    window_end_hour: Mapped[int] = mapped_column(Integer, default=22)
    max_block_minutes: Mapped[int] = mapped_column(Integer, default=60)
    required_minutes: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_minutes: Mapped[int] = mapped_column(Integer, default=0)
    capacity_shortfall_minutes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WeeklyPlanBlock(Base):
    __tablename__ = "weekly_plan_blocks"
    id: Mapped[int] = mapped_column(primary_key=True)
    weekly_plan_id: Mapped[int] = mapped_column(ForeignKey("weekly_plans.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    plan_date: Mapped[date] = mapped_column(Date, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    minimum_viable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    rationale: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class InferenceRecord(Base):
    __tablename__ = "inferences"
    id: Mapped[int] = mapped_column(primary_key=True)
    inference_key: Mapped[str] = mapped_column(String(120), index=True)
    domain: Mapped[str] = mapped_column(String(80), index=True)
    conclusion: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), index=True)
    evidence_json: Mapped[str] = mapped_column(Text, default="[]")
    contradictory_evidence_json: Mapped[str] = mapped_column(Text, default="[]")
    date_range_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_range_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
