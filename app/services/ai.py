from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIMessage:
    role: str
    content: str


class AIProvider(ABC):
    """Provider boundary. The rest of the application must not depend on a vendor SDK."""

    @abstractmethod
    def complete(self, messages: list[AIMessage]) -> str:
        raise NotImplementedError


class UnconfiguredAIProvider(AIProvider):
    def complete(self, messages: list[AIMessage]) -> str:
        raise RuntimeError("No AI provider configured. Deterministic planning and retrieval remain available.")
