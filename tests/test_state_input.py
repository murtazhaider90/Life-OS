from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas import ActivityEventCreate, UserStateInputCreate


def test_state_input_requires_a_signal():
    with pytest.raises(ValidationError):
        UserStateInputCreate(observed_at=datetime.now(timezone.utc))


def test_activity_domain_rejects_full_url():
    with pytest.raises(ValidationError):
        ActivityEventCreate(kind="domain_sample", occurred_at=datetime.now(timezone.utc), domain="https://example.com/path")
