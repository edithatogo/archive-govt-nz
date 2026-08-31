"""Read-only partial-stage fixity planning; never repair or execute an attempt.

Inputs are caller-reviewed roots, not an adversarial filesystem sandbox. All four
selected originals are verified, not the other preserved donor objects. Reuse
means transport structure and pinned bytes, not semantic approval or rights.
"""

from __future__ import annotations

import json
import math
import re
from io import BytesIO
from itertools import islice
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.budget_reader import (
    DISPOSITION_SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.historical_snapshot import (
    SCHEMAS as HISTORICAL_SCHEMAS,
)
from archive_govt_nz.domains.health_appropriations.rebuild import PROFILES
from archive_govt_nz.domains.health_appropriations.silver import (
    LINEAGE_SCHEMA,
    SILVER_SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_snapshot,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

MAX_METADATA_BYTES = 4 * 1024 * 1024
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_ROWS = 100_000
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_THRIFT_STRING_BYTES = 4 * 1024 * 1024
MAX_THRIFT_CONTAINERS = 100_000
_FACTS = SILVER_SCHEMA.set(
    SILVER_SCHEMA.get_field_index("quality_flags"),
    pa.field("quality_flags", pa.list_(pa.field("element", pa.string()))),
)
_CELLS = pa.schema(
    [
        (name, pa.string())
        for name in (
            "source_object_sha256",
            "source_locator",
            "source_coordinate",
            "data_type",
            "raw_value_json",
            "disposition",
            "reason",
            "record_id",
        )
    ]
)


def _require(condition: object, reason: str = "resume_input_contract") -> None:
    if not condition:
        raise ValueError(reason)


def _pin(value: object) -> None:
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value))


def _safe(path: Path) -> None:
    _require(
        not any(part.is_symlink() for part in (path, *path.parents)),
        "unsafe_resume_path",
    )


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(result) == len(pairs))
    return result


def _float(token: str) -> float:
    number = float(token)
    _require(math.isfinite(number))
    return number


def _json(payload: bytes) -> dict[str, Any]:
    value = json.loads(
        payload, object_pairs_hook=_object, parse_float=_float, parse_constant=_float
    )
    _require(isinstance(value, dict))
    return value


def _snapshot(path: Path, pin: str, limit: int) -> bytes:
    _safe(path)
    _require(path.is_file())
    _pin(pin)
    return verified_snapshot(path, pin, max_bytes=limit)


def _expected(
    donor: dict[str, Any], store_root: Path, pin: str, observed_at: str
) -> tuple[dict[str, Any], int]:
    _require(donor.get("schema_version") == "archive-govt-nz.health-donor-manifest/v1")
    rows = donor["objects"]
    _require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows))
    context = source_context(pin, "donor-manifest", "v1", observed_at)
    store = ContentAddressedStore(store_root, create=False)
    sources = {}
    byte_count = 0
    for name, profile in PROFILES.items():
        locator = "data/raw/" + profile.filename
        matches = [row for row in rows if row.get("path") == locator]
        _require(len(matches) == 1)
        row = matches[0]
        object_id = row["object_id"]
        _require(
            isinstance(object_id, str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", object_id)
        )
        path = store.get_path(object_id)
        digest = object_id.removeprefix("sha256:")
        payload = _snapshot(path, digest, MAX_FILE_BYTES)
        _require(row.get("sha256", digest) == digest)
        _require(row.get("byte_count", len(payload)) == len(payload))
        byte_count += len(payload)
        sources[name] = {
            "object_id": object_id,
            "sha256": digest,
            "locator": locator,
            "vintage": profile.vintage,
        }
    return {
        "schema_version": "archive-govt-nz.health-raw-rebuild/v1",
        "donor_manifest_sha256": pin,
        "observed_at": context["observed_at"].isoformat(),
        "sources": sources,
    }, byte_count


def _tables(root: Path, name: str, manifest: dict[str, Any]) -> dict[str, int]:
    profile = PROFILES[name]
    declared = manifest["counts"]
    count_keys = (
        {"facts", "lineage", "dispositions", "rejected"}
        if name == "historical"
        else {"normalized", "rejected", "input", "out_of_scope", "blank"}
        if name == "budget"
        else {
            "normalized",
            "rejected",
            "inventoried_cells",
            "context",
            "preserved_only",
        }
    )
    _require(isinstance(declared, dict) and set(declared) == count_keys)
    _require(all(type(value) is int and value >= 0 for value in declared.values()))
    _require(declared["rejected"] == 0)
    if name != "historical":
        total_key = "input" if name == "budget" else "inventoried_cells"
        _require(
            sum(value for key, value in declared.items() if key != total_key)
            == declared[total_key]
        )
    schemas = (
        HISTORICAL_SCHEMAS
        if name == "historical"
        else dict(
            zip(
                profile.outputs,
                (
                    _FACTS,
                    LINEAGE_SCHEMA,
                    DISPOSITION_SCHEMA if name == "budget" else _CELLS,
                ),
                strict=True,
            )
        )
    )
    _require(set(manifest["output_sha256"]) == set(schemas))
    counts = {}
    expanded = 0
    for filename, schema in schemas.items():
        payload = _snapshot(
            root / filename, manifest["output_sha256"][filename], MAX_FILE_BYTES
        )
        parquet = pq.ParquetFile(
            BytesIO(payload),
            thrift_string_size_limit=MAX_THRIFT_STRING_BYTES,
            thrift_container_size_limit=MAX_THRIFT_CONTAINERS,
        )
        _require(parquet.schema_arrow.equals(schema, check_metadata=True))
        _require(0 < parquet.metadata.num_rows <= MAX_ROWS)
        expanded += sum(
            parquet.metadata.row_group(index).total_byte_size
            for index in range(parquet.metadata.num_row_groups)
        )
        _require(expanded <= MAX_EXPANDED_BYTES)
        table = parquet.read()
        _require(table.schema.equals(schema, check_metadata=True))
        counts[filename] = table.num_rows
        for field in (
            "source_object_sha256",
            "source_locator",
            "source_vintage",
            "observed_at",
        ):
            if field in table.column_names:
                expected = manifest[field]
                values = table[field].to_pylist()
                if field == "observed_at":
                    values = [
                        value.isoformat() if value is not None else None
                        for value in values
                    ]
                _require(
                    all(value == expected for value in values), "stage_context_mismatch"
                )
    keys = (
        ("facts", "lineage", "dispositions")
        if name == "historical"
        else ("normalized", None, "input" if name == "budget" else "inventoried_cells")
    )
    for key, filename in zip(keys, profile.outputs, strict=True):
        if key is not None:
            count = manifest["counts"][key]
            _require(type(count) is int and count == counts[filename])
    return counts


def _reuse(root: Path, name: str, pin: str, manifest: dict[str, Any]) -> dict[str, Any]:
    try:
        counts = _tables(root, name, manifest)
        _snapshot(root / "MANIFEST.json", pin, MAX_METADATA_BYTES)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        if str(exc) in {"stage_context_mismatch", "unsafe_resume_path"}:
            raise
        return {"action": "reextract", "reason": "invalid_stage_payload"}
    return {
        "action": "reuse_verified",
        "reason": "pinned_structure_verified",
        "manifest_sha256": pin,
        "rows": counts,
    }


def _stage(
    root: Path, name: str, pin: str | None, plan: dict[str, Any]
) -> dict[str, Any]:
    _safe(root)
    if not root.exists():
        return {"action": "reextract", "reason": "missing_stage"}
    _require(root.is_dir())
    entries = list(islice(root.iterdir(), 5))
    for path in entries:
        _safe(path)
    if pin is None:
        return {"action": "reextract", "reason": "unpinned_stage"}
    if {path.name for path in entries} != {*PROFILES[name].outputs, "MANIFEST.json"}:
        return {"action": "reextract", "reason": "incomplete_stage"}
    try:
        manifest = _json(_snapshot(root / "MANIFEST.json", pin, MAX_METADATA_BYTES))
    except OSError, ValueError, TypeError:
        return {"action": "reextract", "reason": "invalid_stage_manifest"}
    source = plan["sources"][name]
    transformation = (
        "budget-expenditure/v1"
        if name == "budget"
        else "treasury-historical-health-gdp/v1"
        if name == "historical"
        else "treasury-health-expense-summary/v1"
    )
    _require(
        manifest.get("transformation_id") == transformation, "stage_context_mismatch"
    )
    if name in {"befu", "hyefu"}:
        _require(manifest.get("profile") == name, "stage_context_mismatch")
    _require(
        all(
            manifest.get(key) == value
            for key, value in {
                "schema_version": PROFILES[name].schema,
                "source_object_sha256": source["sha256"],
                "source_locator": source["locator"],
                "source_vintage": source["vintage"],
                "observed_at": plan["observed_at"],
            }.items()
        ),
        "stage_context_mismatch",
    )
    if manifest.get("status") != "passed":
        return {"action": "reextract", "reason": "stage_not_passed"}
    return _reuse(root, name, pin, manifest)


def plan_resume(  # noqa: PLR0913 - independently pinned, explicit read-only inputs.
    *,
    donor_manifest: Path,
    donor_manifest_sha256: str,
    previous_run: Path,
    previous_plan_sha256: str,
    store_root: Path,
    observed_at: str,
    stage_manifest_sha256: Mapping[str, str],
) -> dict[str, Any]:
    """Plan only: verify reviewed inputs without creating or modifying any file.

    Missing/unpinned/corrupt stages request re-extraction. Unsafe paths or a
    contradictory source context fail closed. All future execution must reverify
    these pins; this receipt does not authorize copying, normalization or release.
    """
    _safe(previous_run)
    _safe(store_root)
    _require(previous_run.is_dir() and store_root.is_dir())
    _require(set(stage_manifest_sha256) <= set(PROFILES))
    for pin in stage_manifest_sha256.values():
        _pin(pin)
    entries = list(islice(previous_run.iterdir(), 7))
    _require(
        {path.name for path in entries} <= {*PROFILES, "PLAN.json", "FAILURE.json"}
    )
    for path in entries:
        _safe(path)
    donor = _json(_snapshot(donor_manifest, donor_manifest_sha256, MAX_METADATA_BYTES))
    old = _json(
        _snapshot(previous_run / "PLAN.json", previous_plan_sha256, MAX_METADATA_BYTES)
    )
    expected, byte_count = _expected(
        donor, store_root, donor_manifest_sha256, observed_at
    )
    _require(old == expected, "resume_plan_context_mismatch")
    stages = {
        name: _stage(
            previous_run / name, name, stage_manifest_sha256.get(name), expected
        )
        for name in PROFILES
    }
    _snapshot(donor_manifest, donor_manifest_sha256, MAX_METADATA_BYTES)
    _snapshot(previous_run / "PLAN.json", previous_plan_sha256, MAX_METADATA_BYTES)
    return {
        "schema_version": "archive-govt-nz.health-readonly-resume-plan/v1",
        "donor_manifest_sha256": donor_manifest_sha256,
        "previous_plan_sha256": previous_plan_sha256,
        "stage_manifest_sha256": dict(sorted(stage_manifest_sha256.items())),
        "source_verification_scope": "selected_four_originals_only",
        "selected_source_bytes": byte_count,
        "source_plan": expected,
        "stages": stages,
        "execution": "not_performed",
        "verification_scope": "stage_fixity_and_structure_only",
        "semantic_validation": "not_performed",
        "rights_state": "not_evaluated",
    }
