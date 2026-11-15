"""Cache tests. The remote store is an in-memory test double; no network is used."""

from __future__ import annotations

from pathlib import Path

import pytest

from planetes import cache as cache_mod
from planetes.cache import Cache, check_key


class MemoryStore:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def get(self, key: str) -> bytes | None:
        hit = self.objects.get(key)
        return hit[0] if hit else None

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)


class BrokenStore:
    def get(self, key: str) -> bytes | None:
        raise OSError("network down")

    def put(self, key: str, data: bytes, content_type: str) -> None:
        raise OSError("network down")


def test_keys() -> None:
    assert check_key("frames/f_0123456789ab.webp") == "frames/f_0123456789ab.webp"
    for bad in ["../x", "a/../b", "/abs", "a//b", "", "a\\b", ".hidden", "frames/.."]:
        with pytest.raises(ValueError):
            check_key(bad)


def test_local_roundtrip(tmp_path: Path) -> None:
    c = Cache(tmp_path)
    assert c.get("frames/a.webp") is None
    c.put("frames/a.webp", b"abc", "image/webp")
    assert c.get("frames/a.webp") == b"abc"
    assert c.local_count() == 1


def test_remote_write_through_and_read_back(tmp_path: Path) -> None:
    store = MemoryStore()
    Cache(tmp_path / "one", store).put("jobs/x.json", b"{}", "application/json")
    assert store.objects["jobs/x.json"] == (b"{}", "application/json")
    # A fresh local disk (as after a Render deploy) reads it back from the remote and keeps a local copy.
    fresh = Cache(tmp_path / "two", store)
    assert fresh.get("jobs/x.json") == b"{}"
    assert (tmp_path / "two" / "jobs" / "x.json").read_bytes() == b"{}"


def test_remote_failure_is_a_miss(tmp_path: Path) -> None:
    c = Cache(tmp_path, BrokenStore())
    assert c.get("frames/a.webp") is None
    c.put("frames/a.webp", b"abc")  # remote failure is logged, local write still works
    assert c.get("frames/a.webp") == b"abc"


def test_from_env_local_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("GCS_BUCKET", "planetes-cache")
    monkeypatch.delenv("GCP_SERVICE_ACCOUNT_JSON", raising=False)
    c = cache_mod.from_env()
    assert c.remote is None and c.local_dir == tmp_path


def test_from_env_bad_key_falls_back_to_local(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("GCS_BUCKET", "planetes-cache")
    monkeypatch.setenv("GCP_SERVICE_ACCOUNT_JSON", "not json")
    assert cache_mod.from_env().remote is None
