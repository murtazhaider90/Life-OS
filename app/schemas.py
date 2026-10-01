from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator, model_validator


def _must_be_timezone_aware(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("datetime must include an explicit timezone offset")
    return value


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    module: str | None = None
    topic: str | None = None
    objective: str | None = None
    expected_output: str | None = None
    source_material: str | None = None
    duration_minutes: int = Field(default=30, ge=5, le=480)
    difficulty: int = Field(default=3, ge=1, le=5)
    priority: int = Field(default=3, ge=1, le=5)
    deadline: datetime | None = None

    _deadline_tz = field_validator("deadline")(_must_be_timezone_aware)


class CalendarEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    starts_at: datetime
    ends_at: datetime
    event_type: str = "fixed"
    source: str = "manual_input"
    source_ref: str | None = None

    _starts_tz = field_validator("starts_at")(_must_be_timezone_aware)
    _ends_tz = field_validator("ends_at")(_must_be_timezone_aware)

    @model_validator(mode="after")
    def valid_range(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class StudySessionCreate(BaseModel):
    task_id: int | None = None
    module: str | None = None
    topic: str | None = None
    planned_start: datetime | None = None
    actual_start: datetime | None = None
    planned_minutes: int = Field(default=30, ge=5, le=480)
    music_on: bool | None = None

    _planned_tz = field_validator("planned_start")(_must_be_timezone_aware)
    _actual_tz = field_validator("actual_start")(_must_be_timezone_aware)


class StudySessionFinish(BaseModel):
    ended_at: datetime
    focus_rating: int | None = Field(default=None, ge=1, le=5)
    energy_rating: int | None = Field(default=None, ge=1, le=5)
    difficulty_rating: int | None = Field(default=None, ge=1, le=5)
    confused: bool | None = None
    completed: bool = True
    notes: str | None = None

    _ended_tz = field_validator("ended_at")(_must_be_timezone_aware)


class PlanRequest(BaseModel):
    plan_date: date
    day_start_hour: int = Field(default=8, ge=0, le=23)
    day_end_hour: int = Field(default=22, ge=1, le=24)
    minimum_gap_minutes: int = Field(default=10, ge=0, le=60)

    @model_validator(mode="after")
    def valid_day(self):
        if self.day_end_hour <= self.day_start_hour:
            raise ValueError("day_end_hour must be after day_start_hour")
        return self


class ActivityEventCreate(BaseModel):
    device_id: str | None = Field(default=None, max_length=80)
    kind: str = Field(min_length=1, max_length=40)
    occurred_at: datetime
    duration_seconds: int = Field(default=0, ge=0, le=3600)
    application: str | None = Field(default=None, max_length=160)
    domain: str | None = Field(default=None, max_length=255)
    idle_seconds: int | None = Field(default=None, ge=0, le=86400)
    study_session_id: int | None = None
    source: str = Field(default="desktop_agent", min_length=1, max_length=80)
    source_event_id: str | None = Field(default=None, max_length=120)

    _occurred_tz = field_validator("occurred_at")(_must_be_timezone_aware)

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str | None):
        if value is None:
            return None
        value = value.strip().lower().rstrip(".")
        if "/" in value or "://" in value:
            raise ValueError("domain must be hostname only; paths and URLs are not stored")
        return value or None


class ActivityEventBatch(BaseModel):
    events: list[ActivityEventCreate] = Field(min_length=1, max_length=500)


class ActivityRuleCreate(BaseModel):
    target_type: str
    pattern: str = Field(min_length=1, max_length=255)
    label: str

    @field_validator("target_type")
    @classmethod
    def valid_target(cls, value: str):
        value = value.lower()
        if value not in {"application", "domain"}:
            raise ValueError("target_type must be application or domain")
        return value

    @field_validator("label")
    @classmethod
    def valid_label(cls, value: str):
        value = value.lower()
        if value not in {"study", "distraction", "neutral"}:
            raise ValueError("label must be study, distraction, or neutral")
        return value


class UserStateInputCreate(BaseModel):
    observed_at: datetime
    energy: int | None = Field(default=None, ge=1, le=5)
    focus: int | None = Field(default=None, ge=1, le=5)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    confused: bool | None = None
    study_session_id: int | None = None

    _observed_tz = field_validator("observed_at")(_must_be_timezone_aware)

    @model_validator(mode="after")
    def at_least_one_signal(self):
        if all(v is None for v in (self.energy, self.focus, self.difficulty, self.confused)):
            raise ValueError("provide at least one state signal")
        return self
