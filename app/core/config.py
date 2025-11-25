from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Async AI Task Runner"
    app_version: str = "0.1.0"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://taskuser:taskpass@localhost:5433/task_runner"

    # API
    api_v1_str: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()