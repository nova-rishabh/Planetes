"""Planetes API (docs/03 §3). D1.2 so far: /health, POST /timelapse, /jobs/{id}, /frames/{id}.webp and flags.png."""

from __future__ import annotations

import logging
import math
import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import APIRouter, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from planetes import cache as cache_mod
from planetes.contracts import (
    Error,
    ErrorBody,
    Health,
    Job,
    JobCreated,
    Opinions,
    OpinionsRequest,
    Overlays,
    Resolved,
    TimelapseRequest,
)
from planetes.overlays import build_overlays, query_allwise_sources, query_gaia_sources
from planetes.resolve import resolve_response

from .irsa_status import CachedProbe
from .jobs import JobManager, TooManyJobs
from .opinions import opinions_for
from .timelapse import run_timelapse

log = logging.getLogger("planetes.api")

FRAME_ID_RE = re.compile(r"^f_[0-9a-f]{12}$")
# Frame ids are hashes of obs_id + cutout params, so a frame's bytes never change: cache for a year.
IMMUTABLE = "public, max-age=31536000, immutable"

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


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


def client_ip(request: Request) -> str:
    """Rightmost X-Forwarded-For entry (added by Render's proxy), else the socket peer."""
    fwd = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    if fwd:
        return fwd[-1]
    return request.client.host if request.client else "unknown"


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
        app.state.cache = cache_mod.from_env()
        app.state.jobs = JobManager(workers=env_int("JOB_WORKERS", 2), per_client=3)
        try:
            yield
        finally:
            app.state.jobs.shutdown()


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
        cache_entries=request.app.state.cache.local_count(),
    )


@router.post("/timelapse", response_model=JobCreated)
async def start_timelapse(body: TimelapseRequest, request: Request) -> JobCreated | JSONResponse:
    max_frames = env_int("MAX_FRAMES", 60)
    if body.max_frames > max_frames:
        return error_response(413, "TOO_LARGE", f"max_frames is limited to {max_frames}", "Ask for fewer frames.")
    try:
        cache = request.app.state.cache
        version = code_version()
        workers = env_int("IRSA_CONCURRENCY", 8)
        job_id = request.app.state.jobs.submit(
            "timelapse", client_ip(request), lambda ctx: run_timelapse(body, ctx, cache, version, workers)
        )
    except TooManyJobs:
        return error_response(429, "TOO_LARGE", "Too many jobs running for you at once", "Wait for one to finish.")
    return JobCreated(schema_version="1.0", job_id=job_id)


@router.post("/opinions", response_model=Opinions, response_model_by_alias=True)
async def opinions(body: OpinionsRequest) -> Opinions:
    return await run_in_threadpool(opinions_for, body)


@router.get("/resolve", response_model=Resolved)
async def get_resolve(q: str) -> Resolved | JSONResponse:
    try:
        return await run_in_threadpool(resolve_response, q)
    except LookupError as exc:
        return error_response(404, "NOT_FOUND", str(exc))
    except ValueError as exc:
        return error_response(400, "BAD_INPUT", str(exc))
    except Exception as exc:
        log.exception("Resolver error", exc_info=exc)
        return error_response(500, "INTERNAL", f"Resolver error: {exc}")


@router.get("/overlays", response_model=Overlays)
async def get_overlays(
    ra: float,
    dec: float,
    fov_deg: float = 0.1,
    mjd: str | None = None,
    catalogs: str = "gaia,allwise",
) -> Overlays | JSONResponse:
    if not (0.0 <= ra < 360.0):
        return error_response(400, "BAD_INPUT", "ra must be in [0, 360) degrees")
    if not (-90.0 <= dec <= 90.0):
        return error_response(400, "BAD_INPUT", "dec must be in [-90, 90] degrees")
    if fov_deg <= 0 or fov_deg > 0.5:
        return error_response(400, "BAD_INPUT", "fov_deg must be in (0, 0.5] degrees")

    mjds: list[float] = []
    if mjd:
        for part in mjd.split(","):
            part = part.strip()
            if part:
                try:
                    mjds.append(float(part))
                except ValueError:
                    return error_response(400, "BAD_INPUT", f"Invalid MJD value: {part}")

    cat_list = [c.strip().lower() for c in catalogs.split(",") if c.strip()]
    radius_deg = fov_deg / math.sqrt(2)

    gaia_records = []
    wise_records = []

    try:
        if "gaia" in cat_list:
            gaia_records = await run_in_threadpool(query_gaia_sources, ra, dec, radius_deg)
        if "allwise" in cat_list:
            wise_records = await run_in_threadpool(query_allwise_sources, ra, dec, radius_deg)
        return await run_in_threadpool(build_overlays, gaia_records, wise_records, mjds)
    except Exception as exc:
        log.exception("Overlay query error", exc_info=exc)
        return error_response(500, "IRSA_ERROR", f"Catalog query failed: {exc}")


@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, request: Request) -> Job | JSONResponse:
    job = request.app.state.jobs.get(job_id)
    if job is None:
        return error_response(404, "NOT_FOUND", "No such job", "Jobs are kept for an hour; start a new one.")
    return job


async def _frame_file(request: Request, frame_id: str, suffix: str, media_type: str) -> Response:
    if not FRAME_ID_RE.match(frame_id):
        return error_response(404, "NOT_FOUND", "No such frame")
    data = await run_in_threadpool(request.app.state.cache.get, f"frames/{frame_id}{suffix}")
    if data is None:
        return error_response(404, "NOT_FOUND", "Frame not rendered or no longer cached", "Run the time-lapse again.")
    return Response(content=data, media_type=media_type, headers={"Cache-Control": IMMUTABLE})


@router.get("/frames/{frame_id}.webp", response_class=Response)
async def frame_image(frame_id: str, request: Request) -> Response:
    return await _frame_file(request, frame_id, ".webp", "image/webp")


@router.get("/frames/{frame_id}/flags.png", response_class=Response)
async def frame_flags(frame_id: str, request: Request) -> Response:
    return await _frame_file(request, frame_id, "_flags.png", "image/png")


app.include_router(router)
