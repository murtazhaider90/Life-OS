import hmac
from fastapi import Header, HTTPException, Request
from .config import get_settings


settings = get_settings()


def require_local_or_token(request: Request, authorization: str | None = Header(default=None)) -> None:
    host = request.client.host if request.client else None
    is_local = host in {"127.0.0.1", "::1", "localhost", "testclient"}
    if is_local:
        return
    if not settings.api_token:
        raise HTTPException(503, "API token is required when not running localhost-only")
    expected = f"Bearer {settings.api_token}"
    if authorization is None or not hmac.compare_digest(authorization, expected):
        raise HTTPException(401, "Valid bearer token required")
