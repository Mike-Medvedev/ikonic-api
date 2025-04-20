"""Global exception handlers for FastAPI endpoints.

Defines and registers centralized handlers for common exceptions.
Returns opaque error responses to avoid exposing internal implementation details.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register Global Exception Handlers for FastAPI endpoints."""

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> None:
        logger.error("Database error on %s: %s", str(request.url), exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error occured"},
        )
