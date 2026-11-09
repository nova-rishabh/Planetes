"""Two-layer byte cache: local disk first, then an optional Google Cloud Storage bucket.

Render's disk is wiped on every deploy, so rendered frames and job results are also written to the
GCS bucket (docs/02 "Persistent cache", setup in docs/RUNBOOK.md). Without GCS settings the cache is
local only. A cache miss is always `None`; nothing is ever made up to fill it.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Protocol

log = logging.getLogger("planetes.cache")

# Keys are relative paths like "frames/f_3a9c1e0b7d22.webp": safe characters only, no "..".
_KEY_RE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*(/[A-Za-z0-9_-][A-Za-z0-9_.-]*)*$")


def check_key(key: str) -> str:
    """Return the key if it is a safe relative path, else raise ValueError."""
    if not _KEY_RE.match(key) or ".." in key.split("/"):
        raise ValueError(f"Unsafe cache key: {key!r}")
    return key


class RemoteStore(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def put(self, key: str, data: bytes, content_type: str) -> None: ...


class GcsStore:
    """One GCS bucket. Uses google-cloud-storage (Client.from_service_account_info, Blob.upload_from_string,
    Blob.download_as_bytes), checked against version 3.17.1."""

    def __init__(self, bucket: str, service_account_info: dict[str, Any]) -> None:
        from google.cloud import storage  # imported lazily: only the API needs GCS

        client = storage.Client.from_service_account_info(service_account_info)
        self._bucket = client.bucket(bucket)
        self.bucket_name = bucket

    def get(self, key: str) -> bytes | None:
        from google.api_core.exceptions import NotFound

        try:
            return self._bucket.blob(key).download_as_bytes(timeout=30)
        except NotFound:
            return None

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._bucket.blob(key).upload_from_string(data, content_type=content_type, timeout=60)


class Cache:
    def __init__(self, local_dir: Path, remote: RemoteStore | None = None) -> None:
        self.local_dir = Path(local_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self.remote = remote

    def _path(self, key: str) -> Path:
        return self.local_dir / check_key(key)

    def get(self, key: str) -> bytes | None:
        """Local copy if present, else the remote copy (then saved locally), else None."""
        path = self._path(key)
        if path.is_file():
            return path.read_bytes()
        if self.remote is None:
            return None
        try:
            data = self.remote.get(key)
        except Exception:  # remote trouble is a miss, never a crash
            log.warning("Remote cache read failed for %s", key, exc_info=True)
            return None
        if data is not None:
            self._write_local(path, data)
        return data

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Write locally, then to the remote store if there is one (remote failures are logged only)."""
        path = self._path(key)
        self._write_local(path, data)
        if self.remote is not None:
            try:
                self.remote.put(key, data, content_type)
            except Exception:
                log.warning("Remote cache write failed for %s", key, exc_info=True)

    def local_count(self) -> int:
        """Number of files in the local layer (reported as cache_entries by /api/health)."""
        return sum(1 for p in self.local_dir.rglob("*") if p.is_file() and not p.name.startswith(".tmp"))

    @staticmethod
    def _write_local(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.replace(tmp, path)  # atomic: readers never see half a file
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise


def from_env() -> Cache:
    """CACHE_DIR (default ./.planetes-cache), plus GCS when GCS_BUCKET and GCP_SERVICE_ACCOUNT_JSON are set."""
    local_dir = Path(os.environ.get("CACHE_DIR", "").strip() or ".planetes-cache")
    bucket = os.environ.get("GCS_BUCKET", "").strip()
    key_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "").strip()
    remote: RemoteStore | None = None
    if bucket and key_json:
        try:
            remote = GcsStore(bucket, json.loads(key_json))
            log.info("Cache: local %s + GCS bucket %s", local_dir, bucket)
        except Exception:
            log.error("GCS cache disabled: could not use GCP_SERVICE_ACCOUNT_JSON", exc_info=True)
    else:
        log.info("Cache: local %s only (GCS_BUCKET or GCP_SERVICE_ACCOUNT_JSON not set)", local_dir)
    return Cache(local_dir, remote)
