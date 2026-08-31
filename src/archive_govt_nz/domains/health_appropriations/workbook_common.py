"""Shared integrity, numeric and derivative-writing contracts for workbooks."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq

if TYPE_CHECKING:
    from pathlib import Path

    import pyarrow as pa

_MAX_YEAR = 9999


def identity(*parts: object) -> str:
    """Identify a deterministic ordered tuple of source/transformation keys."""
    return "sha256:" + hashlib.sha256("\x1f".join(map(str, parts)).encode()).hexdigest()


def encode_json(value: object) -> str:
    """Retain Unicode source values in stable key order."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def exact_number(value: object, *, year: bool = False) -> Decimal | None:
    """Accept integral years or exact decimal128(20,3), never silent rounding."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    if year:
        return number if 1 <= number <= _MAX_YEAR and number == int(number) else None
    if abs(number) >= Decimal("1e17"):
        return None
    scaled = number.quantize(Decimal("0.001"))
    return scaled if scaled == number else None


def source_context(
    sha256: str, source_locator: str, source_vintage: str, observed_at: str
) -> dict[str, Any]:
    """Validate caller-supplied observation context without attesting capture."""
    if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise ValueError("invalid_source_sha256")
    observed = datetime.fromisoformat(observed_at)
    if (
        observed.tzinfo is None
        or not source_vintage.strip()
        or not source_locator.strip()
    ):
        raise ValueError("invalid_source_context")
    return {
        "source_object_sha256": sha256,
        "source_observation_id": identity(sha256, source_locator, observed_at),
        "source_locator": source_locator,
        "source_vintage": source_vintage,
        "observed_at": observed.astimezone(UTC),
    }


def verified_snapshot(source: Path, expected_sha256: str, *, max_bytes: int) -> bytes:
    """Read one capped snapshot and verify the exact bytes used for parsing."""
    if max_bytes <= 0:
        raise ValueError("invalid_source_limit")
    with source.open("rb") as handle:
        payload = handle.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError("source_byte_limit")
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("source_hash_mismatch")
    return payload


def write_workbook_outputs(
    output_dir: Path, outputs: dict[str, pa.Table], receipt: dict[str, object]
) -> dict[str, object]:
    """Reserve a new directory, hash written derivatives, then write a manifest.

    Partial directories are not resumable or valid without a complete manifest
    and matching hashes. No original, existing output or publication is changed.
    """
    if not outputs:
        raise ValueError("empty_outputs")
    if any(
        re.fullmatch(r"[a-z][a-z0-9_]*\.parquet", name) is None
        or re.fullmatch(r"con|prn|aux|nul|com[1-9]|lpt[1-9]", name.split(".")[0])
        is not None
        for name in outputs
    ):
        raise ValueError("invalid_output_name")
    output_dir.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name, table in outputs.items():
        path = output_dir / name
        with path.open("xb") as handle:
            pq.write_table(table, handle)
        with path.open("rb") as handle:
            hashes[name] = hashlib.file_digest(handle, "sha256").hexdigest()
    result = json.loads(encode_json({**receipt, "output_sha256": hashes}))
    with (output_dir / "MANIFEST.json").open(
        "x", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(encode_json(result) + "\n")
    return result
