"""Offline scheduler plan and execution boundaries."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.capture import CaptureResult
from archive_govt_nz.warc import write_response_record

if TYPE_CHECKING:
    from archive_govt_nz.object_store import ContentAddressedStore

sys.path.insert(0, str(Path(__file__).parents[3] / "tools"))
import schedule_health_capture as scheduler  # pyright: ignore[reportMissingImports]


def pinned(path: Path, value: object) -> str:
    path.write_text(json.dumps(value), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_plan(tmp_path: Path) -> tuple[Path, str]:
    census = tmp_path / "census.json"
    census_hash = pinned(
        census,
        {
            "cutoff": "2026-01-01",
            "records": [
                {
                    "source_id": "one",
                    "url": "https://www.treasury.govt.nz/a.csv",
                    "media_type": "text/csv",
                    "disposition": "discovered",
                }
            ],
        },
    )
    plan = tmp_path / "plan.json"
    digest = pinned(
        plan,
        {
            "schema_version": "archive-govt-nz.health-capture-schedule/v1",
            "census": str(census),
            "census_sha256": census_hash,
            "max_resource_bytes": 1024,
        },
    )
    return plan, digest


@pytest.mark.anyio
async def test_preflight_is_read_only_and_rejects_changed_census(
    tmp_path: Path,
) -> None:
    plan, digest = make_plan(tmp_path)
    output = tmp_path / "output"
    result = await scheduler.run_plan(plan, digest, output)
    assert result["status"] == "planned"
    assert result["selected"] == 1
    assert not output.exists()
    (tmp_path / "census.json").write_text("{}")
    with pytest.raises(ValueError, match="input_digest_mismatch"):
        await scheduler.run_plan(plan, digest, output, execute=True)
    assert not output.exists()


@pytest.mark.anyio
async def test_plan_limit_matches_capture_warc_body_limit(tmp_path: Path) -> None:
    plan, _ = make_plan(tmp_path)
    config = json.loads(plan.read_text())
    config["max_resource_bytes"] = 64 * 1024 * 1024
    digest = pinned(plan, config)
    assert (await scheduler.run_plan(plan, digest, tmp_path / "out"))[
        "status"
    ] == "planned"
    config["max_resource_bytes"] += 1
    digest = pinned(plan, config)
    with pytest.raises(ValueError, match="capture_schedule_invalid"):
        await scheduler.run_plan(plan, digest, tmp_path / "out", execute=True)
    assert not (tmp_path / "out").exists()


@pytest.mark.anyio
async def test_execution_is_explicit_and_uses_pinned_preservation_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, digest = make_plan(tmp_path)
    seen = []

    async def fake_capture(args: argparse.Namespace) -> dict[str, int]:
        seen.append(args)
        return {"selected": 1, "captured": 1}

    monkeypatch.setattr(scheduler, "_capture", fake_capture)
    result = await scheduler.run_plan(plan, digest, tmp_path / "output", execute=True)
    assert result["status"] == "completed"
    assert seen[0].preservation_only is True
    assert seen[0].resume is True
    assert seen[0].census_sha256 == result["census_sha256"]


@pytest.mark.anyio
async def test_capture_and_replay_preserve_originals_without_second_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scheduler uses the actual capture checkpoint and verifies its replay."""
    plan, digest = make_plan(tmp_path)
    calls: list[str] = []

    async def local_capture(
        _client: object,
        url: str,
        store: ContentAddressedStore,
        _config: object,
        *,
        transaction_warc_path: Path,
    ) -> CaptureResult:
        calls.append(url)
        payload = b"synthetic"
        stored = store.put_bytes(payload)
        warc = write_response_record(
            transaction_warc_path,
            url=url,
            status_code=200,
            headers={"content-type": "text/csv"},
            body=payload,
        )
        return CaptureResult(url, 200, "text/csv", stored, warc)

    monkeypatch.setitem(scheduler._capture.__globals__, "capture_url", local_capture)  # noqa: SLF001
    output = tmp_path / "output"
    first = await scheduler.run_plan(plan, digest, output, execute=True)
    before = (output / "manifest.json").read_bytes()
    second = await scheduler.run_plan(plan, digest, output, execute=True)
    assert first == second
    assert (output / "manifest.json").read_bytes() == before
    assert len(calls) == 1
