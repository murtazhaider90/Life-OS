from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import httpx


class LifeOSConnectionError(RuntimeError):
    pass


@dataclass
class LifeOSClient:
    base_url: str = "http://127.0.0.1:8000"
    timeout_seconds: float = 5.0
    transport: httpx.BaseTransport | None = None

    def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            with httpx.Client(
                base_url=self.base_url.rstrip("/"),
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.request(method, path, **kwargs)
                if response.is_error:
                    detail = None
                    try:
                        payload = response.json()
                        if isinstance(payload, dict):
                            detail = payload.get("detail")
                    except ValueError:
                        pass
                    if not detail:
                        detail = response.text.strip() or response.reason_phrase
                    raise LifeOSConnectionError(
                        f"{response.status_code} {response.reason_phrase}: {detail}"
                    )
                if not response.content:
                    return None
                return response.json()
        except LifeOSConnectionError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise LifeOSConnectionError(str(exc)) from exc

    def health(self) -> dict:
        return self._request("GET", "/health")

    def assistant_status(self) -> dict:
        return self._request("GET", "/api/assistant/status")

    def send_message(self, text: str) -> dict:
        text = text.strip()
        if not text:
            raise ValueError("message cannot be empty")
        return self._request("POST", "/api/assistant/message", json={"text": text})
