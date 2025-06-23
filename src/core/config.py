"""Project Settings and Configurations using Pydantic Settings.

Env Variables are automatically imported and validated.
"""

import logging

from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler

uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_error_logger = logging.getLogger("uvicorn.error")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
starlette_logger = logging.getLogger("starlette")


uvicorn_logger.propagate = False
uvicorn_error_logger.propagate = False
uvicorn_access_logger.propagate = False
starlette_logger.propagate = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s | %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(markup=True, show_path=True, rich_tracebacks=True)],
    )

    PROJECT_NAME: str
    SUPABASE_URL: str
    SUPABASE_KEY: str

    BACKEND_CORS_ORIGINS: str
    FRONTEND_SCHEME: str
    NETLOC: str

    API_V1_STR: str = "/api/v1"

    POSTGRES_SCHEME: str = "postgresql+psycopg"
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # makes the function a real field on the model {a: 5, b: 6, c: all_cors_origins}
    @computed_field
    @property  # makes functin avaliable as dot notation foo.bar() -> foo.bar
    def sqlalchemy_database_uri(self) -> PostgresDsn:
        """Compose db connection string."""
        return MultiHostUrl.build(
            scheme=self.POSTGRES_SCHEME,
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    VONAGE_API_KEY: str
    VONAGE_API_SECRET: str
    VONAGE_NUMBER: str


settings = Settings()
