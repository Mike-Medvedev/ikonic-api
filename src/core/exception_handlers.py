"""Global exception handlers for FastAPI endpoints.

Defines and registers centralized handlers for common exceptions.
Returns opaque error responses to avoid exposing internal implementation details.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from core.exceptions import InvalidTokenError, ResourceNotFoundError

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register Global Exception Handlers for FastAPI endpoints."""

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.error("Database error on %s: %s", str(request.url), exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error occured"},
        )

    @app.exception_handler(ResourceNotFoundError)
    async def missing_resource_exception_handler(
        request: Request, exc: ResourceNotFoundError
    ) -> JSONResponse:
        logger.error(
            "Resource not found error on %s: %s", str(request.url), exc, exc_info=True
        )
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_handler(request: Request, exc: InvalidTokenError) -> None:
        logger.error("%s on %s", str(exc), str(request.url))
        return JSONResponse(status_code=403, content={"detail": str(exc)})
