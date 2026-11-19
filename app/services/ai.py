from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import httpx
from ..config import get_settings


@dataclass
class AIMessage:
    role: str
    content: str


class AIProvider(ABC):
    """Provider boundary. The application never depends on a vendor SDK."""

    @abstractmethod
    def complete(self, messages: list[AIMessage]) -> str:
        raise NotImplementedError


class UnconfiguredAIProvider(AIProvider):
    def complete(self, messages: list[AIMessage]) -> str:
        raise RuntimeError(
            "No AI provider configured. Deterministic planning, retrieval, "
            "extractive academic answers and revision logic remain available."
        )


class ChatCompletionsProvider(AIProvider):
    """Small provider-neutral adapter for chat-completions-compatible HTTP APIs."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def complete(self, messages: list[AIMessage]) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": 0.1,
        }
        with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("AI provider returned an unexpected response shape") from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("AI provider returned an empty response")
        return content.strip()


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_base_url and settings.ai_model:
        return ChatCompletionsProvider(
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            api_key=settings.ai_api_key,
            timeout_seconds=settings.ai_timeout_seconds,
        )
    return UnconfiguredAIProvider()


def ai_provider_status() -> dict:
    settings = get_settings()
    return {
        "configured": bool(settings.ai_base_url and settings.ai_model),
        "model": settings.ai_model if settings.ai_base_url and settings.ai_model else None,
        "mode": "provider" if settings.ai_base_url and settings.ai_model else "extractive",
    }
