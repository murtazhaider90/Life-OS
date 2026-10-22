import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

_HOST_RE = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.I)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must include an explicit timezone offset")
    return value


class SleepRecordCreate(BaseModel):
    sleep_start: datetime
    sleep_end: datetime
    quality: int | None = Field(default=None, ge=1, le=5)
    source: str = Field(default="manual_input", max_length=80)
    source_ref: str | None = Field(default=None, max_length=255)

    _start_tz = field_validator("sleep_start")(_aware)
    _end_tz = field_validator("sleep_end")(_aware)

    @model_validator(mode="after")
    def valid_range(self):
        if self.sleep_end <= self.sleep_start:
            raise ValueError("sleep_end must be after sleep_start")
        if (self.sleep_end - self.sleep_start).total_seconds() > 24 * 3600:
            raise ValueError("sleep record cannot exceed 24 hours")
        return self


class TrainingRecordCreate(BaseModel):
    starts_at: datetime
    duration_minutes: int = Field(ge=1, le=1440)
    intensity: int | None = Field(default=None, ge=1, le=5)
    modality: str | None = Field(default=None, max_length=120)
    source: str = Field(default="manual_input", max_length=80)
    source_ref: str | None = Field(default=None, max_length=255)

    _starts_tz = field_validator("starts_at")(_aware)


class MealRecordCreate(BaseModel):
    consumed_at: datetime
    meal_type: str = Field(min_length=1, max_length=40)
    size_rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=1000)
    source: str = Field(default="manual_input", max_length=80)
    source_ref: str | None = Field(default=None, max_length=255)

    _consumed_tz = field_validator("consumed_at")(_aware)


class FocusDomainCreate(BaseModel):
    domain: str
    reason: str | None = Field(default=None, max_length=255)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str):
        value = value.strip().lower().rstrip(".")
        if "://" in value or "/" in value or not _HOST_RE.fullmatch(value):
            raise ValueError("enter a hostname only, for example reddit.com")
        return value


class FocusModeRequest(BaseModel):
    duration_minutes: int = Field(default=45, ge=5, le=480)
    confirm: bool = False


class FocusReleaseRequest(BaseModel):
    confirm: bool = False
