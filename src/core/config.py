from typing import List, Annotated
from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


# def parse_cors(url: str) -> List[str]:
#     return url


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file="../.env"
    )

    PROJECT_NAME: str

    FRONTEND_HOST: str = "http://localhost:5173"

    BACKEND_CORS_ORIGINS: str

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
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
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
    TO_NUMBER: str
    VONAGE_BRAND_NAME: str


settings = Settings()
