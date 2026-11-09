"""In-memory background jobs (docs/02: asyncio + thread pool). One API instance, so memory is enough.

A job function gets a JobContext to report progress and partial results, and returns the final result
model. Raising JobError ends the job with that contract error code; any other exception becomes INTERNAL.
"""

from __future__ import annotations

import logging
import secrets
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Literal

from planetes.contracts import ErrorBody, Job, JobProgress, SpectrumResult, TimelapseResult

log = logging.getLogger("planetes.api.jobs")

ErrorCode = Literal["BAD_INPUT", "NOT_FOUND", "NO_COVERAGE", "IRSA_TIMEOUT", "IRSA_ERROR", "TOO_LARGE", "INTERNAL"]
JobKind = Literal["timelapse", "spectrum"]
Result = TimelapseResult | SpectrumResult
Status = Literal["queued", "running", "done", "error"]


class JobError(Exception):
    def __init__(self, code: ErrorCode, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.body = ErrorBody(code=code, message=message, hint=hint)


class TooManyJobs(Exception):
    pass


@dataclass
class _Record:
    job_id: str
    kind: JobKind
    client: str
    status: Status = "queued"
    done: int = 0
    total: int | None = None
    stage: str | None = "queued"
    result: Result | None = None
    error: ErrorBody | None = None
    finished_at: float | None = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class JobContext:
    """Handed to a job function so it can report how far it got."""

    def __init__(self, rec: _Record) -> None:
        self._rec = rec

    def progress(self, done: int, total: int | None, stage: str | None) -> None:
        with self._rec.lock:
            self._rec.done, self._rec.total, self._rec.stage = done, total, stage

    def partial(self, result: Result) -> None:
        with self._rec.lock:
            self._rec.result = result


JobFn = Callable[[JobContext], Result]


class JobManager:
    def __init__(self, workers: int = 2, per_client: int = 3, keep_s: float = 3600.0) -> None:
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="job")
        self._jobs: dict[str, _Record] = {}
        self._lock = threading.Lock()
        self.per_client = per_client
        self.keep_s = keep_s

    def submit(self, kind: JobKind, client: str, fn: JobFn) -> str:
        """Queue fn; raise TooManyJobs if this client already has per_client unfinished jobs."""
        with self._lock:
            self._purge()
            active = sum(1 for r in self._jobs.values() if r.client == client and r.status in ("queued", "running"))
            if active >= self.per_client:
                raise TooManyJobs
            rec = _Record(job_id="j_" + secrets.token_urlsafe(12), kind=kind, client=client)
            self._jobs[rec.job_id] = rec
        self._pool.submit(self._run, rec, fn)
        return rec.job_id

    def get(self, job_id: str) -> Job | None:
        rec = self._jobs.get(job_id)
        if rec is None:
            return None
        with rec.lock:
            return Job(
                schema_version="1.0",
                job_id=rec.job_id,
                kind=rec.kind,
                status=rec.status,
                progress=JobProgress(done=rec.done, total=rec.total, stage=rec.stage),
                result=rec.result,
                error=rec.error,
            )

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _run(self, rec: _Record, fn: JobFn) -> None:
        with rec.lock:
            rec.status, rec.stage = "running", "starting"
        try:
            result = fn(JobContext(rec))
        except JobError as exc:
            self._finish(rec, "error", error=exc.body)
        except Exception:
            log.exception("Job %s failed", rec.job_id)
            self._finish(rec, "error", error=ErrorBody(code="INTERNAL", message="Internal error while running the job"))
        else:
            self._finish(rec, "done", result=result)

    @staticmethod
    def _finish(rec: _Record, status: Status, result: Result | None = None, error: ErrorBody | None = None) -> None:
        with rec.lock:
            rec.status, rec.stage, rec.finished_at = status, status, time.monotonic()
            if result is not None:
                rec.result = result
            rec.error = error

    def _purge(self) -> None:
        now = time.monotonic()
        for jid in [j for j, r in self._jobs.items() if r.finished_at and now - r.finished_at > self.keep_s]:
            del self._jobs[jid]
