from typing import Literal, Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CalorieTracker"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # AI Processing Settings
    OPENAI_API_KEY: Optional[str] = None  # Optional: for GPT-4o fallback
    WHISPER_MODEL_SIZE: str = "medium"  # tiny, base, small, medium, large
    NER_CONFIDENCE_THRESHOLD: float = 0.65  # Threshold for LLM fallback

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
