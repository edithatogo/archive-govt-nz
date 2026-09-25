"""Offline fiscal-runner persistence and fail-closed resume contracts."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from typing import IO, Any

import pytest

from archive_govt_nz.capture import CaptureAttempt, CaptureError, CaptureResult
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError
from archive_govt_nz.warc import write_response_record


def test_process_kill_releases_runner_lock_and_preserves_lock_inode(
    tmp_path: Path,
) -> None:
    """A hard-killed owner cannot strand the runner's SQLite lock."""
    manifest = tmp_path / "checkpoint.json"
    lock = manifest.with_name(manifest.name + ".lock")
    code = """from pathlib import Path
import sys, time
from capture_health_resources import _exclusive_capture_lock
with _exclusive_capture_lock(Path(sys.argv[1])):
    print('locked', flush=True)
    time.sleep(60)
"""
    environment = os.environ.copy()
    paths = ["src", "tools"]
    if environment.get("PYTHONPATH"):
        paths.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    child = subprocess.Popen(
        [sys.executable, "-c", code, str(manifest)],
        cwd=Path(__file__).parents[3],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "locked"
        assert lock.is_file()
        runner = runpy.run_path(
            str(Path(__file__).parents[3] / "tools/capture_health_resources.py")
        )
        with (
            pytest.raises(FileExistsError, match="capture_lock_unavailable"),
            runner["_exclusive_capture_lock"](manifest),
        ):
            pytest.fail("competing runner entered the active lock")
        child.kill()
        child.wait(timeout=10)
        with runner["_exclusive_capture_lock"](manifest):
            assert lock.is_file()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


@pytest.mark.anyio
@pytest.mark.parametrize("fault", ["swap", "query", "url", "status", "body", "legacy"])
async def test_resume_requires_warc_source_response_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    """Mutable manifest hashes cannot reassign a retained response to a source."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    census = json.loads(args.census.read_text())
    first = census["records"][0]
    census["records"] = [
        dict(first, source_id=str(i), url=f"https://www.treasury.govt.nz/one.csv?q={i}")
        for i in range(2)
    ]
    args.census.write_text(json.dumps(census))
    if fault == "swap":
        census["records"][1]["url"] = "https://www.treasury.govt.nz/two.csv"
        args.census.write_text(json.dumps(census))
    result = await execute(args)
    row, other = result["results"]
    if fault in {"swap", "query"}:
        for key in (
            "object_id",
            "sha256",
            "blake3",
            "bytes",
            "warc_path",
            "warc_sha256",
            "url",
            "status_code",
        ):
            row[key] = other[key]
    elif fault == "url":
        row["url"] += "&different=1"
    elif fault == "status":
        row["status_code"] = 201
    elif fault == "body":
        receipt = ContentAddressedStore(args.store_root).put_bytes(b"different")
        row.update(
            object_id=receipt.object_id,
            sha256=receipt.sha256,
            blake3=receipt.blake3,
            bytes=receipt.byte_count,
        )
    else:
        path = args.warc_dir / row["warc_path"]
        payload = b"\r\n".join(
            line
            for line in path.read_bytes().split(b"\r\n")
            if not line.startswith(
                (b"WARC-Request-URL-SHA256:", b"WARC-Final-URL-SHA256:")
            )
        )
        path.write_bytes(payload)
        row["warc_sha256"] = hashlib.sha256(payload).hexdigest()
    args.manifest.write_text(json.dumps(result))
    before = args.manifest.read_bytes()
    args.resume = True
    with pytest.raises(ValueError, match="resume_warc"):
        await execute(args)
    assert len(calls) == 2
    assert args.manifest.read_bytes() == before


def setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Any, argparse.Namespace, list[str]]:
    """Load the actual runner with a local immutable-object capture boundary."""
    execute = runpy.run_path(
        str(Path(__file__).parents[3] / "tools/capture_health_resources.py")
    )["_capture"]
    census = tmp_path / "census.json"
    census.write_text(
        json.dumps(
            {
                "cutoff": "2026-09-07",
                "records": [
                    {
                        "source_id": "one",
                        "url": "https://www.treasury.govt.nz/one.csv",
                        "disposition": "discovered",
                        "media_type": "text/csv",
                    }
                ],
            }
        )
    )
    args = argparse.Namespace(
        census=census,
        store_root=tmp_path / "cas",
        warc_dir=tmp_path / "warcs",
        manifest=tmp_path / "manifest.json",
        max_resource_bytes=1024,
        resume=False,
    )
    calls: list[str] = []

    async def local(
        _client: object,
        url: str,
        store: ContentAddressedStore,
        _config: object,
        *,
        transaction_warc_path: Path,
    ) -> CaptureResult:
        calls.append(url)
        payload = b"synthetic"
        receipt = store.put_bytes(payload)
        warc = write_response_record(
            transaction_warc_path,
            url=url,
            status_code=200,
            headers={"content-type": "text/csv"},
            body=payload,
        )
        return CaptureResult(url, 200, "text/csv", receipt, warc)

    monkeypatch.setitem(execute.__globals__, "capture_url", local)
    return execute, args, calls


@pytest.mark.anyio
async def test_warc_sync_uses_writable_handle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Model Windows fsync while retaining the actual sync and WARC bytes."""
    execute, args, _ = setup(tmp_path, monkeypatch)
    original_open = Path.open
    original_sync = execute.__globals__["os"].fsync
    handles: list[IO[Any]] = []
    synced: list[bool] = []

    def tracked_open(  # noqa: PLR0913, PLR0917 -- mirrors Path.open
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        handle = original_open(path, mode, buffering, encoding, errors, newline)
        if path.name == "response.warc":
            handles.append(handle)
        return handle

    def checked_sync(descriptor: int) -> None:
        for handle in handles:
            if not handle.closed and handle.fileno() == descriptor:
                synced.append(handle.writable())
                assert handle.writable(), "Windows requires a writable sync handle"
        original_sync(descriptor)

    monkeypatch.setattr(Path, "open", tracked_open)
    monkeypatch.setattr(execute.__globals__["os"], "fsync", checked_sync)
    result = await execute(args)
    assert result["captured"] == 1
    assert synced == [True]
    row = result["results"][0]
    assert (
        hashlib.sha256((args.warc_dir / row["warc_path"]).read_bytes()).hexdigest()
        == row["warc_sha256"]
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "fault",
    [
        "context",
        "rights",
        "sha256",
        "blake3",
        "bytes",
        "request_url_sha256",
        "unknown",
        "duplicate",
        "warc",
        "missing_warc",
        "object",
        "escape",
        "absolute",
    ],
)
async def test_resume_rejects_drift_before_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    """Never use a drifted or corrupt retained receipt as a successful skip."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    result = await execute(args)
    row = result["results"][0]
    if fault == "context":
        args.max_resource_bytes += 1
    elif fault in {"rights", "sha256", "blake3", "request_url_sha256", "bytes"}:
        row[fault] = "wrong"
    elif fault == "unknown":
        row["source_id"] = "unknown"
    elif fault == "duplicate":
        result["results"].append(dict(row))
    elif fault in {"warc", "missing_warc"}:
        path = args.warc_dir / row["warc_path"]
        if fault == "warc":
            path.write_bytes(b"corrupt")
        else:
            path.unlink()
    elif fault == "object":
        ContentAddressedStore(args.store_root).verify(
            row["object_id"]
        ).path.write_bytes(b"corrupt")
    elif fault == "escape":
        row["warc_path"] = "../escape.warc"
    else:
        row["warc_path"] = str(tmp_path / "absolute.warc")
    args.manifest.write_text(json.dumps(result))
    before = args.manifest.read_bytes()
    args.resume = True
    with pytest.raises((ValueError, ObjectStoreError, FileNotFoundError)):
        await execute(args)
    assert len(calls) == 1
    assert args.manifest.read_bytes() == before
    assert args.manifest.with_name(args.manifest.name + ".lock").is_file()


@pytest.mark.anyio
async def test_duplicate_census_identity_is_rejected_before_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two inputs cannot share one resumability key."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    census = json.loads(args.census.read_text())
    census["records"] *= 2
    args.census.write_text(json.dumps(census))
    with pytest.raises(ValueError, match="duplicate_source_id"):
        await execute(args)
    assert not calls
    assert not args.manifest.exists()


def test_cli_empty_selection_writes_checkpoint_and_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the real parser and entrypoint without selecting a network URL."""
    _, args, _ = setup(tmp_path, monkeypatch)
    args.census.write_text('{"cutoff":"2026-09-07","records":[]}')
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "capture_health_resources.py",
            "--census",
            str(args.census),
            "--store-root",
            str(args.store_root),
            "--warc-dir",
            str(args.warc_dir),
            "--manifest",
            str(args.manifest),
        ],
    )
    with pytest.raises(SystemExit) as error:
        runpy.run_path(
            str(Path(__file__).parents[3] / "tools/capture_health_resources.py"),
            run_name="__main__",
        )
    assert error.value.code == 0
    assert json.loads(args.manifest.read_text())["results"] == []


def test_atomic_checkpoint_failure_keeps_previous_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed rename leaves the preceding checkpoint and removes only temp bytes."""
    execute, args, _ = setup(tmp_path, monkeypatch)
    args.manifest.write_bytes(b"prior")

    def fail(_self: Path, _target: Path) -> None:
        message = "synthetic_replace_failure"
        raise OSError(message)

    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(OSError, match="synthetic_replace_failure"):
        execute.__globals__["_write"](args.manifest, {})
    assert args.manifest.read_bytes() == b"prior"
    assert not list(tmp_path.glob("capture-*"))


@pytest.mark.anyio
async def test_repeated_interruption_keeps_unvisited_retained_captures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Checkpointing a retry cannot drop later resources already captured."""
    execute, args, _ = setup(tmp_path, monkeypatch)
    census = json.loads(args.census.read_text())
    first = census["records"][0]
    census["records"] = [
        dict(first, source_id=name, url=f"https://www.treasury.govt.nz/{name}.csv")
        for name in ("one", "two", "three")
    ]
    args.census.write_text(json.dumps(census))
    local = execute.__globals__["capture_url"]
    phase = 0

    async def interrupted(
        client: object,
        url: str,
        store: ContentAddressedStore,
        config: object,
        *,
        transaction_warc_path: Path,
    ) -> CaptureResult:
        if url.endswith("three.csv") and phase < 2:
            raise asyncio.CancelledError
        if url.endswith("one.csv") and phase == 0:
            message = "retryable_status"
            raise CaptureError(message)
        return await local(
            client, url, store, config, transaction_warc_path=transaction_warc_path
        )

    monkeypatch.setitem(execute.__globals__, "capture_url", interrupted)
    with pytest.raises(asyncio.CancelledError):
        await execute(args)
    first_checkpoint = json.loads(args.manifest.read_text())
    two = first_checkpoint["results"][1]
    args.resume = True
    phase = 1
    with pytest.raises(asyncio.CancelledError):
        await execute(args)
    checkpoint = json.loads(args.manifest.read_text())
    assert checkpoint["captured"] == 2
    assert checkpoint["results"][1] == two
    phase = 2
    complete = await execute(args)
    assert complete["captured"] == 3
    assert complete["results"][1] == two
    assert args.manifest.with_name(args.manifest.name + ".lock").is_file()


@pytest.mark.anyio
async def test_observation_history_retains_retry_and_immutable_source_versions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resume appends attempt history and never replaces captured versions."""
    execute, args, _ = setup(tmp_path, monkeypatch)
    census = json.loads(args.census.read_text())
    first = census["records"][0]
    census["records"] = [
        dict(first, source_id="one", url="https://www.treasury.govt.nz/one.csv"),
        dict(first, source_id="two", url="https://www.treasury.govt.nz/two.csv"),
    ]
    args.census.write_text(json.dumps(census))
    phase = 0

    async def observed(
        _client: object,
        url: str,
        store: ContentAddressedStore,
        _config: object,
        *,
        transaction_warc_path: Path,
    ) -> CaptureResult:
        nonlocal phase
        payload = b"v1" if phase == 0 else b"v2"
        receipt = store.put_bytes(payload)
        warc_receipt = write_response_record(
            transaction_warc_path,
            url=url,
            status_code=200,
            headers={"content-type": "text/csv", "etag": f'"{payload.decode()}"'},
            body=payload,
        )
        return CaptureResult(
            url,
            200,
            "text/csv",
            receipt,
            warc_receipt,
            attempt_receipts=(CaptureAttempt(url, 200, "captured", 0.0),),
        )

    def event(outcome: str) -> dict[str, object]:
        value: dict[str, object] = {
            "source_id": "one",
            "observed_at": "2026-09-26T00:00:00Z",
            "outcome": outcome,
            "attempts": [{"status_code": None, "outcome": outcome}],
        }
        value["observation_id"] = execute.__globals__["_observation_id"]("one", value)
        return value

    args.manifest.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-capture-manifest/v1",
                "capture_context": {
                    "census_sha256": hashlib.sha256(
                        args.census.read_bytes()
                    ).hexdigest(),
                    "max_resource_bytes": args.max_resource_bytes,
                    "contract": "health-capture-resume/v1",
                },
                "results": [{"source_id": "one", "state": "retryable"}],
                "observations": [event("transport_retryable")],
            }
        )
    )
    args.resume = True
    phase = 0
    monkeypatch.setitem(execute.__globals__, "capture_url", observed)
    first = await execute(args)
    checkpoint = json.loads(args.manifest.read_text())
    assert [row["outcome"] for row in checkpoint["observations"]] == [
        "transport_retryable",
        "captured",
        "captured",
    ]
    old_version = checkpoint["observations"][1]
    monkeypatch.setitem(execute.__globals__, "capture_url", observed)
    phase = 1
    args.manifest = tmp_path / "next-observation.json"
    args.resume = False
    complete = await execute(args)
    assert complete["observations"][0]["sha256"] != old_version["sha256"]
    assert len({event["observation_id"] for event in complete["observations"]}) == 2
    assert complete["observations"][0]["source_id"] == "one"
    assert complete["observations"][1]["source_id"] == "two"
    assert old_version["etag"] == '"v1"'
    assert old_version["validator_state"] == "present"
    assert (args.warc_dir / old_version["warc_path"]).is_file()


@pytest.mark.anyio
async def test_refuse_implicit_overwrite_and_competing_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Existing checkpoints and active/stale locks fail closed."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    await execute(args)
    before = args.manifest.read_bytes()
    with pytest.raises(ValueError, match="manifest_exists"):
        await execute(args)
    # A legacy directory has no trustworthy ownership record; do not reclaim.
    args.manifest = tmp_path / "legacy.json"
    lock = args.manifest.with_name(args.manifest.name + ".lock")
    lock.mkdir()
    args.resume = True
    with pytest.raises(FileExistsError):
        await execute(args)
    assert len(calls) == 1
    assert lock.is_dir()
    assert (tmp_path / "manifest.json").read_bytes() == before


@pytest.mark.anyio
async def test_checkpoint_write_failure_retains_orphan_warc_for_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure before manifest promotion never replaces the retained attempt."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    original = execute.__globals__["_write"]

    def fail(_path: Path, _value: object) -> None:
        msg = "synthetic_checkpoint_failure"
        raise OSError(msg)

    monkeypatch.setitem(execute.__globals__, "_write", fail)
    with pytest.raises(OSError, match="synthetic_checkpoint_failure"):
        await execute(args)
    old = next(args.warc_dir.rglob("*.warc"))
    digest = hashlib.sha256(old.read_bytes()).hexdigest()
    assert not args.manifest.exists()
    monkeypatch.setitem(execute.__globals__, "_write", original)
    args.resume = True
    result = await execute(args)
    assert len(calls) == 1
    assert hashlib.sha256(old.read_bytes()).hexdigest() == digest
    assert (
        result["results"][0]["warc_path"] == old.relative_to(args.warc_dir).as_posix()
    )
    assert result["results"][0]["observation_time_state"] == (
        "recovered_at_not_source_observed_at"
    )
    assert result["observations"][0]["outcome"] == "recovered_orphan_warc"


@pytest.mark.anyio
async def test_ambiguous_orphan_warcs_are_not_adopted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two equally matching unlinked WARCs remain untouched and trigger capture."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    original = execute.__globals__["_write"]

    def fail(_path: Path, _value: object) -> None:
        msg = "synthetic_checkpoint_failure"
        raise OSError(msg)

    monkeypatch.setitem(execute.__globals__, "_write", fail)
    with pytest.raises(OSError, match="synthetic_checkpoint_failure"):
        await execute(args)
    first = next(args.warc_dir.rglob("*.warc"))
    duplicate = args.warc_dir / "attempt-ambiguous" / "response.warc"
    duplicate.parent.mkdir()
    duplicate.write_bytes(first.read_bytes())
    first_digest = hashlib.sha256(first.read_bytes()).hexdigest()
    monkeypatch.setitem(execute.__globals__, "_write", original)
    args.resume = True
    result = await execute(args)
    assert len(calls) == 2
    assert result["observations"][0]["outcome"] == "captured"
    assert hashlib.sha256(first.read_bytes()).hexdigest() == first_digest
    assert duplicate.read_bytes() == first.read_bytes()


@pytest.mark.anyio
async def test_invalid_orphan_body_is_rejected_before_cas_promotion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A WARC digest failure cannot leave its untrusted body in the CAS."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    original = execute.__globals__["_write"]

    def fail(_path: Path, _value: object) -> None:
        msg = "synthetic_checkpoint_failure"
        raise OSError(msg)

    monkeypatch.setitem(execute.__globals__, "_write", fail)
    with pytest.raises(OSError, match="synthetic_checkpoint_failure"):
        await execute(args)
    orphan = next(args.warc_dir.rglob("*.warc"))
    orphan.write_bytes(orphan.read_bytes().replace(b"synthetic", b"tampered!"))
    monkeypatch.setitem(execute.__globals__, "_write", original)
    args.resume = True
    result = await execute(args)
    assert len(calls) == 2
    assert result["observations"][0]["outcome"] == "captured"
    with pytest.raises(ObjectStoreError, match="object_missing"):
        ContentAddressedStore(args.store_root).verify(
            "sha256:" + hashlib.sha256(b"tampered!").hexdigest()
        )


@pytest.mark.anyio
async def test_retryable_checkpoint_is_retried_not_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only verified captured rows qualify for resume skipping."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    local = execute.__globals__["capture_url"]

    async def fail(*_args: object, **_kwargs: object) -> CaptureResult:
        msg = "retryable_status"
        raise CaptureError(msg)

    monkeypatch.setitem(execute.__globals__, "capture_url", fail)
    failed = await execute(args)
    assert failed["results"][0]["state"] == "retryable"
    monkeypatch.setitem(execute.__globals__, "capture_url", local)
    args.resume = True
    result = await execute(args)
    assert result["captured"] == 1
    assert len(calls) == 1
