"""FastAPI entry point. Creates FastAPI app and setup/teardown logic."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.main import api_router
from src.core.config import settings
from src.core.exception_handlers import setup_exception_handlers

app = FastAPI(title=settings.PROJECT_NAME)

setup_exception_handlers(app)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router=api_router, prefix=settings.API_V1_STR)
