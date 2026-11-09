"""D1.2 endpoint and job-queue tests. No outside requests; frame bytes are written straight to the cache."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import main
from api.jobs import JobError, JobManager, TooManyJobs
from api.tests.test_health import _validator

VALID = {"ra": 269.4521, "dec": 4.6934}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("GCP_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.setenv("MAX_FRAMES", "60")
    with TestClient(main.app) as c:
        yield c


def _wait(c: TestClient, job_id: str) -> dict:
    for _ in range(100):
        body = c.get(f"/api/jobs/{job_id}").json()
        if body["status"] in ("done", "error"):
            return body
        time.sleep(0.02)
    raise AssertionError("job did not finish")


def test_views_not_built_yet_say_so(client: TestClient) -> None:
    resp = client.post("/api/timelapse", json={**VALID, "mode": "stacks"})
    assert resp.status_code == 200
    _validator("job_created.schema.json").validate(resp.json())
    job = _wait(client, resp.json()["job_id"])
    _validator("job.schema.json").validate(job)
    assert job["status"] == "error" and job["result"] is None
    assert job["error"]["code"] == "BAD_INPUT"


@pytest.mark.network
def test_real_barnard_timelapse(client: TestClient) -> None:
    """Live IRSA: three D3 exposures of Barnard's Star, Gaia DR3 proper motion (source 4472832130942575872)."""
    body = {
        "ra": 269.44850252543836,
        "dec": 4.739420051112412,
        "fov_deg": 0.05,
        "mode": "exposures",
        "detectors": [3],
        "max_frames": 3,
        "pm": {"pm_ra_masyr": -801.5509783684709, "pm_dec_masyr": 10362.394206546573, "ref_epoch_jyear": 2016.0},
    }
    job_id = client.post("/api/timelapse", json=body).json()["job_id"]
    for _ in range(1800):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("done", "error"):
            break
        time.sleep(0.5)
    print("job:", job["status"], job["error"], job["progress"])
    _validator("job.schema.json").validate(job)
    assert job["status"] == "done"
    frames = job["result"]["frames"]
    assert 1 <= len(frames) <= 3
    first = frames[0]
    assert client.get(first["image_url"]).status_code == 200
    assert client.get(first["flags_url"]).status_code == 200
    # The star moves north (~10.4"/yr) through the time-lapse.
    ys = [f["target_xy"][1] for f in frames]
    assert ys == sorted(ys)


def test_timelapse_limits(client: TestClient) -> None:
    resp = client.post("/api/timelapse", json={**VALID, "max_frames": 61})
    assert resp.status_code == 413 and resp.json()["error"]["code"] == "TOO_LARGE"
    resp = client.post("/api/timelapse", json={**VALID, "fov_deg": 0.9})
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "BAD_INPUT"
    _validator("error.schema.json").validate(resp.json())


def test_unknown_job(client: TestClient) -> None:
    resp = client.get("/api/jobs/j_nope")
    assert resp.status_code == 404
    _validator("error.schema.json").validate(resp.json())


def test_frames_served_from_cache(client: TestClient) -> None:
    fid = "f_0123456789ab"
    main.app.state.cache.put(f"frames/{fid}.webp", b"RIFF-bytes", "image/webp")
    main.app.state.cache.put(f"frames/{fid}_flags.png", b"png-bytes", "image/png")
    img = client.get(f"/api/frames/{fid}.webp")
    assert img.status_code == 200 and img.content == b"RIFF-bytes"
    assert img.headers["content-type"] == "image/webp" and "immutable" in img.headers["cache-control"]
    flags = client.get(f"/api/frames/{fid}/flags.png")
    assert flags.status_code == 200 and flags.headers["content-type"] == "image/png"
    for url in ["/api/frames/f_ffffffffffff.webp", "/api/frames/..%2Fsecret.webp", "/api/frames/f_XYZ.webp"]:
        assert client.get(url).status_code == 404


def test_health_counts_cache(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def ok(_: object) -> str:
        return "ok"

    monkeypatch.setattr(main.app.state.irsa_probe, "get", ok)
    main.app.state.cache.put("frames/f_0123456789ab.webp", b"x")
    body = client.get("/api/health").json()
    _validator("health.schema.json").validate(body)
    assert body["cache_entries"] == 1


def test_manager_done_error_and_per_client_limit() -> None:
    m = JobManager(workers=2, per_client=1)
    gate = threading.Event()

    def slow(ctx):  # noqa: ANN001
        ctx.progress(1, 2, "half")
        gate.wait(5)
        raise JobError("NO_COVERAGE", "No SPHEREx frames cover this position")

    jid = m.submit("timelapse", "1.2.3.4", slow)
    with pytest.raises(TooManyJobs):
        m.submit("timelapse", "1.2.3.4", slow)
    m.submit("timelapse", "5.6.7.8", lambda ctx: (_ for _ in ()).throw(JobError("NO_COVERAGE", "No frames here")))
    gate.set()
    for _ in range(100):
        if m.get(jid).status == "error":
            break
        time.sleep(0.02)
    job = m.get(jid)
    assert job.status == "error" and job.error.code == "NO_COVERAGE" and job.progress.done == 1
    m.shutdown()
