"""Secure error handling — never leak secrets or stack traces to clients."""

from __future__ import annotations

import logging
import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings

logger = logging.getLogger("occ.security")

_SECRET_PATTERNS = re.compile(
    r"(password|secret|api[_-]?key|token|authorization|bearer)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def sanitize_message(message: str) -> str:
    cleaned = _SECRET_PATTERNS.sub(r"\1=[REDACTED]", message or "")
    # Drop obvious connection strings
    cleaned = re.sub(r"postgres(?:ql)?://\S+", "postgres://[REDACTED]", cleaned, flags=re.I)
    cleaned = re.sub(r"mysql://\S+", "mysql://[REDACTED]", cleaned, flags=re.I)
    return cleaned[:800]


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(_request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, str):
            detail = sanitize_message(detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        # Pydantic errors are safe (field paths) — still sanitize messages
        errors = []
        for err in exc.errors():
            item = dict(err)
            if "msg" in item:
                item["msg"] = sanitize_message(str(item["msg"]))
            # ctx may contain input values — drop to avoid leaking
            item.pop("ctx", None)
            item.pop("input", None)
            errors.append(item)
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception):
        settings = get_settings()
        logger.exception("Unhandled server error: %s", type(exc).__name__)
        detail = "Internal server error"
        if settings.expose_error_details:
            detail = sanitize_message(f"{type(exc).__name__}: {exc}")
        return JSONResponse(status_code=500, content={"detail": detail})
