from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logger import init_logger
from src.api.main import api_router
from src.core.config import settings

init_logger()


app = FastAPI(title=settings.PROJECT_NAME)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router=api_router, prefix=settings.API_V1_STR)
