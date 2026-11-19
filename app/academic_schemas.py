from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("datetime must include an explicit timezone offset")
    return value


class AcademicQuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    module: str | None = Field(default=None, max_length=120)
    topic: str | None = Field(default=None, max_length=160)
    limit: int = Field(default=8, ge=1, le=20)
    allow_general_knowledge: bool = False


class AssessmentCreate(BaseModel):
    module: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=255)
    assessment_type: str = Field(default="assessment", max_length=80)
    deadline: datetime | None = None
    weight_percent: float | None = Field(default=None, ge=0, le=100)
    brief: str | None = Field(default=None, max_length=12000)
    criteria: list[str] = Field(default_factory=list, max_length=100)

    _deadline_tz = field_validator("deadline")(_aware)


class AssessmentBreakdownRequest(BaseModel):
    create_tasks: bool = False


class RevisionPlanRequest(BaseModel):
    module: str | None = Field(default=None, max_length=120)
    create_tasks: bool = False
    horizon_days: int = Field(default=14, ge=1, le=90)


class AcademicQuizRequest(BaseModel):
    module: str | None = Field(default=None, max_length=120)
    topic: str = Field(min_length=1, max_length=160)
    count: int = Field(default=5, ge=1, le=20)


class MistakeCreate(BaseModel):
    module: str = Field(min_length=1, max_length=120)
    topic: str = Field(min_length=1, max_length=160)
    learning_objective: str | None = Field(default=None, max_length=255)
    occurred_at: datetime
    mistake_type: str | None = Field(default=None, max_length=80)
    description: str = Field(min_length=1, max_length=4000)
    correction: str | None = Field(default=None, max_length=4000)
    source_material: str | None = Field(default=None, max_length=255)
    study_attempt_id: int | None = None

    _occurred_tz = field_validator("occurred_at")(_aware)
