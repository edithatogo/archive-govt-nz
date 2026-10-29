# SPDX-License-Identifier: Apache-2.0
"""Durable local normalization attempts for non-interactive schedulers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sqlite3
import stat
import sys
import tempfile
from contextlib import closing
from dataclasses import replace
from itertools import islice
from pathlib import Path
from typing import Any, NoReturn

from jsonschema import Draft202012Validator, ValidationError

from archive_govt_nz.domains.health_appropriations.source_operations import (
    SOURCE_OPERATION_SCHEMA,
    SourceRequest,
    operate_source,
)

MAX_SOURCE_BYTES = 256 * 1024 * 1024
MAX_OUTPUT_BYTES = 512 * 1024 * 1024
MAX_RECEIPT_BYTES = 1024 * 1024
MAX_ATTEMPTS = 128


def _fail(code: str) -> NoReturn:
    raise ValueError(code)


def _sync_directory(path: Path) -> None:
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _write_receipt(attempt: Path, name: str, value: dict[str, Any]) -> None:
    temporary = attempt / f"{name}.pending"
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(attempt / name)
    _sync_directory(attempt)


def _digest(path: Path, *, max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        msg = "scheduled_input_invalid"
        raise ValueError(msg)
    if metadata.st_size > max_bytes:
        msg = "scheduled_input_size_invalid"
        raise ValueError(msg)
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            metadata.st_dev,
            metadata.st_ino,
        ):
            msg = "scheduled_input_invalid"
            raise ValueError(msg)
        digest = hashlib.sha256()
        total = 0
        while chunk := stream.read(1024 * 1024):
            total += len(chunk)
            if total > max_bytes:
                msg = "scheduled_input_size_invalid"
                raise ValueError(msg)
            digest.update(chunk)
        return digest.hexdigest()


def _identity(request: SourceRequest, runtime_fingerprint: str) -> str:
    payload = {
        "source": str(request.source.absolute()),
        "profile": request.profile,
        "sha256": request.expected_sha256,
        "vintage": request.source_vintage,
        "locator": request.source_locator,
        "observed_at": request.observed_at,
        "runtime_fingerprint": runtime_fingerprint,
    }
    if request.include_drift:
        payload["include_drift"] = True
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _runtime_fingerprint() -> str:
    """Bind replay to installed application source and dependency versions."""
    package_root = Path(__file__).resolve().parents[2]
    entries = [
        (path.relative_to(package_root).as_posix(), _digest(path))
        for path in sorted(package_root.rglob("*"))
        if path.is_file() and path.suffix in {".py", ".json"}
    ]
    dependencies = sorted(
        (distribution.metadata.get("Name", ""), distribution.version)
        for distribution in importlib.metadata.distributions()
    )
    descriptor = {
        "application_files": entries,
        "dependencies": dependencies,
        "python": sys.version,
        "system": platform.system(),
        "machine": platform.machine(),
    }
    return hashlib.sha256(
        json.dumps(descriptor, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _read_receipt(path: Path) -> bytes:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_RECEIPT_BYTES:
        _fail("scheduled_receipt_invalid")
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            metadata.st_dev,
            metadata.st_ino,
        ):
            _fail("scheduled_receipt_invalid")
        payload = stream.read(MAX_RECEIPT_BYTES + 1)
    if len(payload) > MAX_RECEIPT_BYTES:
        _fail("scheduled_receipt_invalid")
    return payload


def _verified_attempt(  # noqa: C901 - validate all replay boundaries
    attempt: Path, request: SourceRequest
) -> dict[str, Any] | None:
    receipt_path = attempt / "receipt.json"
    if not receipt_path.exists() and not receipt_path.is_symlink():
        return None
    if attempt.is_symlink() or receipt_path.is_symlink() or not receipt_path.is_file():
        msg = "scheduled_receipt_invalid"
        raise ValueError(msg)
    try:
        envelope = json.loads(_read_receipt(receipt_path))
        if not isinstance(envelope, dict) or set(envelope) != {
            "operation",
            "manifest_sha256",
        }:
            _fail("scheduled_receipt_invalid")
        receipt = envelope["operation"]
        Draft202012Validator(SOURCE_OPERATION_SCHEMA).validate(receipt)
        if (
            receipt["status"] != "written_local"
            or receipt["source_object_sha256"] != request.expected_sha256
            or receipt["profile"] != request.profile
        ):
            _fail("scheduled_receipt_invalid")
        output = attempt / "output"
        if output.is_symlink() or not output.is_dir():
            _fail("scheduled_output_invalid")
        pins = receipt["output_sha256"]
        if set(pins) | {"MANIFEST.json"} != {entry.name for entry in output.iterdir()}:
            _fail("scheduled_output_invalid")
        if _digest(output / "MANIFEST.json") != envelope["manifest_sha256"]:
            _fail("scheduled_output_invalid")
        for name, expected in pins.items():
            if Path(name).name != name or _digest(output / name) != expected:
                _fail("scheduled_output_invalid")
    except (OSError, KeyError, TypeError, ValueError, ValidationError) as error:
        msg = "scheduled_receipt_or_output_invalid"
        raise ValueError(msg) from error
    return receipt


def run_scheduled_normalization(  # noqa: C901, PLR0912, PLR0915 - explicit state and lock boundary
    request: SourceRequest, root: Path, *, dry_run: bool = True
) -> dict[str, Any]:
    """Run or replay one pinned normalization without overwriting attempts.

    Dry-run never creates state. Execution uses a kernel-released SQLite lock;
    incomplete attempts are preserved and a completed receipt is reused only
    after verifying its exact output inventory and source digest.
    """
    if (
        type(dry_run) is not bool
        or type(request.include_drift) is not bool
        or root.is_symlink()
    ):
        msg = "scheduled_arguments_invalid"
        raise ValueError(msg)
    if _digest(request.source, max_bytes=MAX_SOURCE_BYTES) != request.expected_sha256:
        msg = "scheduled_source_digest_mismatch"
        raise ValueError(msg)
    runtime_fingerprint = _runtime_fingerprint()
    job_id = _identity(request, runtime_fingerprint)
    job_dir = root / job_id
    if job_dir.is_symlink():
        msg = "scheduled_job_invalid"
        raise ValueError(msg)
    if dry_run:
        prospective = replace(request, output_dir=job_dir / "preflight-output")
        operation = operate_source(prospective)
        return {
            "job_id": job_id,
            "runtime_fingerprint": runtime_fingerprint,
            "status": "dry_run"
            if operation["status"] == "preflight_passed"
            else "failed",
            "operation": operation,
        }
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".scheduled-normalization.lock"
    if lock_path.is_symlink() or (lock_path.exists() and not lock_path.is_file()):
        msg = "scheduled_lock_invalid"
        raise ValueError(msg)
    try:
        connection = sqlite3.connect(lock_path, timeout=0)
    except sqlite3.Error as error:
        msg = "scheduled_lock_unavailable"
        raise ValueError(msg) from error
    with closing(connection) as lock:
        try:
            lock.execute("BEGIN EXCLUSIVE")
        except sqlite3.Error as error:
            msg = "scheduled_lock_unavailable"
            raise ValueError(msg) from error
        job_dir.mkdir(exist_ok=True)
        attempts = sorted(islice(job_dir.iterdir(), MAX_ATTEMPTS + 1))
        if len(attempts) > MAX_ATTEMPTS:
            msg = "scheduled_attempt_limit_exceeded"
            raise ValueError(msg)
        for attempt in attempts:
            if attempt.is_symlink() or not attempt.is_dir():
                msg = "scheduled_attempt_invalid"
                raise ValueError(msg)
            receipt = _verified_attempt(attempt, request)
            if receipt is not None:
                return {
                    "job_id": job_id,
                    "runtime_fingerprint": runtime_fingerprint,
                    "attempt": attempt.name,
                    "status": "reused",
                    "operation": receipt,
                }
        if len(attempts) == MAX_ATTEMPTS:
            msg = "scheduled_attempt_limit_exceeded"
            raise ValueError(msg)
        attempt = Path(tempfile.mkdtemp(prefix="attempt-", dir=job_dir))
        operation = operate_source(
            replace(request, output_dir=attempt / "output"), dry_run=False
        )
        if operation["status"] != "written_local":
            _write_receipt(attempt, "failure.json", operation)
            return {
                "job_id": job_id,
                "runtime_fingerprint": runtime_fingerprint,
                "attempt": attempt.name,
                "status": "failed",
                "operation": operation,
            }
        _write_receipt(
            attempt,
            "receipt.json",
            {
                "operation": operation,
                "manifest_sha256": _digest(attempt / "output" / "MANIFEST.json"),
            },
        )
        _verified_attempt(attempt, request)
        return {
            "job_id": job_id,
            "runtime_fingerprint": runtime_fingerprint,
            "attempt": attempt.name,
            "status": "written_local",
            "operation": operation,
        }
