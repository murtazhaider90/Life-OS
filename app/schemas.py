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
