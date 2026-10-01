from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LIFE_OS_", env_file=".env", extra="ignore")

    db_url: str = "sqlite:///./data/life_os.db"
    api_token: str | None = None
    bind_host: str = "127.0.0.1"
    bind_port: int = 8000
    timezone: str = "Europe/London"
    upload_dir: Path = Path("data/uploads")
    max_upload_bytes: int = 20 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
