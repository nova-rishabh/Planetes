"""Planetes API. Only GET /api/health exists in D1.1; the rest arrives in D1.2 (docs/06)."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from planetes.contracts import Error, ErrorBody, Health

from .irsa_status import CachedProbe

log = logging.getLogger("planetes.api")

ErrorCode = Literal["BAD_INPUT", "NOT_FOUND", "NO_COVERAGE", "IRSA_TIMEOUT", "IRSA_ERROR", "TOO_LARGE", "INTERNAL"]


def code_version() -> str:
    """GIT_COMMIT, else Render's RENDER_GIT_COMMIT (first 7 chars), else "dev"."""
    explicit = os.environ.get("GIT_COMMIT", "").strip()
    if explicit:
        return explicit
    render = os.environ.get("RENDER_GIT_COMMIT", "").strip()
    if render:
        return render[:7]
    return "dev"


def allowed_origins() -> list[str]:
    """ALLOWED_ORIGINS, comma-separated. Unset/empty = no cross-origin access."""
    return [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]


def error_response(status: int, code: ErrorCode, message: str, hint: str | None = None) -> JSONResponse:
    body = Error(schema_version="1.0", error=ErrorBody(code=code, message=message, hint=hint))
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


def _code_for_status(status: int) -> ErrorCode:
    if status == 404:
        return "NOT_FOUND"
    if status == 413:
        return "TOO_LARGE"
    if 400 <= status < 500:
        return "BAD_INPUT"
    return "INTERNAL"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(headers={"User-Agent": "planetes-api"}) as client:
        app.state.http = client
        app.state.irsa_probe = CachedProbe()
        yield


app = FastAPI(
    title="Planetes API",
    version=code_version(),
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(StarletteHTTPException)
async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return error_response(exc.status_code, _code_for_status(exc.status_code), str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    where = ".".join(str(p) for p in first.get("loc", ()))
    return error_response(422, "BAD_INPUT", f"{where}: {first.get('msg', 'invalid input')}".strip(": "))


@app.exception_handler(Exception)
async def internal_error(_: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error", exc_info=exc)
    return error_response(500, "INTERNAL", "Internal server error")


router = APIRouter(prefix="/api")


@router.get("/health", response_model=Health)
async def health(request: Request) -> Health:
    irsa = await request.app.state.irsa_probe.get(request.app.state.http)
    return Health(
        schema_version="1.0",
        status="ok",
        code_version=code_version(),
        irsa_tap=irsa,
        default_release="QR3",
        cache_entries=0,
    )


app.include_router(router)
