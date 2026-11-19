from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
import httpx
from ..config import get_settings


class AdGuardNotConfigured(RuntimeError):
    pass


class AdGuardRequestError(RuntimeError):
    pass


@dataclass
class AdGuardHomeClient:
    base_url: str
    username: str
    password: str
    timeout_seconds: float = 5.0

    @classmethod
    def from_settings(cls) -> "AdGuardHomeClient":
        settings = get_settings()
        if not settings.adguard_base_url or not settings.adguard_username or not settings.adguard_password:
            raise AdGuardNotConfigured("AdGuard Home is not configured in .env")
        parsed = urlparse(settings.adguard_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise AdGuardNotConfigured("LIFE_OS_ADGUARD_BASE_URL must be a valid http(s) URL")
        return cls(
            base_url=settings.adguard_base_url.rstrip("/"),
            username=settings.adguard_username,
            password=settings.adguard_password,
        )

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = httpx.request(
                method,
                f"{self.base_url}/control{path}",
                auth=(self.username, self.password),
                timeout=self.timeout_seconds,
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            raise AdGuardRequestError(str(exc)) from exc

    def filtering_status(self) -> dict:
        return self._request("GET", "/filtering/status").json()

    def set_user_rules(self, rules: list[str]) -> None:
        self._request("POST", "/filtering/set_rules", json={"rules": rules})


def adguard_configured() -> bool:
    settings = get_settings()
    return bool(settings.adguard_base_url and settings.adguard_username and settings.adguard_password)
