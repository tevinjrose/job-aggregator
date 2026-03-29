from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_ignore_empty=True,
    )

    anthropic_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./jobradar.db"


settings = Settings()
