"""Replay retained donor parity read-only; print payload-free evidence JSON."""

# Standalone evidence recipe, deliberately linear for auditability.
# ruff: noqa: INP001, C901, PLR0912, PLR0915

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from decimal import Decimal
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.health_appropriations.donor_parity import (
    Repair,
    compare_databases,
    read_database,
)
from archive_govt_nz.domains.health_appropriations.historical_reconciliation import (
    compare_historical,
)

DONOR_MANIFEST = "893f387e1f361400285ccc84802b497e87802d1ad913826ff7d9055b07a03b74"
RAW_MANIFEST = "fb405a2fdbb2809093cb03d62ddbe1fcb1a1f6f91d304666e8ef0964813f73fb"
GOLD_SQLITE = "515f0eeb579a479f2e65dd112abf2e13879e6ee6d840c8b19d933eccf488c973"
DONOR_PROCESS_SCRIPT = (
    "0beb01bbf6956f6ed9f5925c73199dc0a67f6022673dba78fded819597d63ed3"
)
LIMIT = 16 * 1024 * 1024
SHA256_HEX_LENGTH = 64


def replay(root: Path) -> dict[str, Any]:
    """Verify pinned local inputs twice and return row digests and explanations."""
    observed: dict[Path, str] = {}

    def read(path: Path, pin: str) -> bytes:
        with path.open("rb") as stream:
            data = stream.read(LIMIT + 1)
        if len(data) > LIMIT or hashlib.sha256(data).hexdigest() != pin:
            message = "replay_input_fixity"
            raise ValueError(message)
        observed[path] = pin
        return data

    manifest = json.loads(read(root / "manifests/donor-4668e6c.json", DONOR_MANIFEST))
    if (
        manifest["commit"],
        manifest["tree"],
        manifest["file_count"],
        manifest["total_bytes"],
    ) != (
        "4668e6c3b1b492086941d4c1ef96e299250a8301",
        "c6d44ff79eda73cfc6ba7db5764e27ce01b890e1",
        23,
        6604301,
    ):
        message = "replay_donor_identity"
        raise ValueError(message)
    donor_path = None
    donor_hash = None
    process_script_verified = False
    for item in manifest["objects"]:
        digest = item["sha256"]
        path = root / "bronze-cas/sha256" / digest[:2] / digest
        payload = read(path, digest)
        if len(payload) != item["byte_count"]:
            message = "replay_donor_length"
            raise ValueError(message)
        if item["path"] == "data/processed/health_funding_nz.sqlite":
            donor_path, donor_hash = path, digest
        if item["path"] == "process_data.py":
            process_script_verified = digest == DONOR_PROCESS_SCRIPT
    if not process_script_verified:
        message = "replay_process_script_identity"
        raise ValueError(message)
    if donor_path is None or donor_hash is None:
        message = "replay_missing_donor_database"
        raise ValueError(message)
    donor = read_database(donor_path, donor_hash)
    gold_path = root / "gold/donor-4668e6c/health_funding_nz.sqlite"
    read(gold_path, GOLD_SQLITE)
    gold = compare_databases(donor, read_database(gold_path, GOLD_SQLITE))
    raw_root = root / "gold/raw-compatibility-20260831-v1"
    raw_manifest = json.loads(read(raw_root / "MANIFEST.json", RAW_MANIFEST))
    # Fixed member names: never follow paths supplied by a manifest.
    records = [
        json.loads(line)
        for line in read(
            raw_root / "records.jsonl", raw_manifest["output_sha256"]["records.jsonl"]
        ).splitlines()
    ]
    lineage = [
        json.loads(line)
        for line in read(
            raw_root / "field_lineage.jsonl",
            raw_manifest["output_sha256"]["field_lineage.jsonl"],
        ).splitlines()
    ]
    raw_hash = raw_manifest["output_sha256"]["compatibility.sqlite"]
    read(raw_root / "compatibility.sqlite", raw_hash)
    raw = read_database(raw_root / "compatibility.sqlite", raw_hash)
    initial = compare_databases(donor, raw)
    historical = [
        {**row["source_context"], "amount": Decimal(row["exact_amount"])}
        for row in records
        if row["table"] in ("historical_health_spending", "gdp_historical")
    ]
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.deserialize(read(donor_path, donor_hash))
        connection.execute("PRAGMA query_only=ON")
        oracle = {
            "health_spending": [
                (year, str(value))
                for year, value in connection.execute(
                    "SELECT Year, HealthSpendingMillions "
                    "FROM historical_health_spending ORDER BY rowid"
                )
            ],
            "nominal_gdp": [
                (year, str(value))
                for year, value in connection.execute(
                    "SELECT Year, NominalGDPMillions FROM gdp_historical ORDER BY rowid"
                )
            ],
        }
    historical_comparison = compare_historical(historical, lineage, oracle)
    source_only = {
        row["source_record_id"]: row
        for row in historical_comparison
        if row["status"] == "source_only"
    }
    by_row = {(row["table"], row["sqlite_row_number"]): row for row in records}
    repairs = []
    for row in initial["rows"]:
        if row["status"] == "match":
            continue
        if row["status"] != "candidate_only":
            message = "unexpected_donor_omission"
            raise ValueError(message)
        record = by_row[(row["table"], row["candidate_row"])]
        difference = source_only[record["record_id"]]
        if difference["reason"] != "annotated_year_absent_from_donor":
            message = "unexpected_addition_reason"
            raise ValueError(message)
        repairs.append(
            Repair(
                row["id"],
                difference["source_object_sha256"],
                difference["source_coordinate"],
                "Retain annotated source year omitted by donor; "
                "preserve both derivatives.",
                "test_historical_reconciliation.py::test_complete_union_and_explicit_differences",
            )
        )
    explained = compare_databases(donor, raw, repairs=tuple(repairs))
    deviations = []
    for row in historical_comparison:
        if row["status"] == "exact_match":
            continue
        deviations.append(disposition_historical_deviation(row))
    validate_historical_deviations(deviations)
    for path, pin in list(observed.items()):
        read(path, pin)
    return {
        "schema_version": "archive-govt-nz.health-donor-parity-replay/v1",
        "evidence_kind": "observed_retained_actual_bytes",
        "donor_manifest_sha256": DONOR_MANIFEST,
        "raw_manifest_sha256": RAW_MANIFEST,
        "donor_objects_verified": len(manifest["objects"]),
        "donor_bytes_verified": sum(item["byte_count"] for item in manifest["objects"]),
        "input_files_verified_before_and_after": len(observed),
        "gold": gold,
        "raw": explained,
        "historical_counts": dict(
            Counter(row["status"] for row in historical_comparison)
        ),
        "exact_decimal_deviations": deviations,
        "historical_deviation_dispositions": "accepted_retain_both_no_replacement",
        "donor_process_script_sha256": DONOR_PROCESS_SCRIPT,
        "binary_representation_flags": sum(
            row["representation_changed"] for row in records
        ),
        "rights_state": "not_evaluated",
        "publication_state": "no_action",
        "repair_approval": "not_asserted",
    }


def disposition_historical_deviation(row: dict[str, Any]) -> dict[str, Any]:
    """Explain source-only and decimal-representation differences without repair."""
    if (
        row["status"] not in {"source_only", "value_difference"}
        or not isinstance(row["source_object_sha256"], str)
        or len(row["source_object_sha256"]) != SHA256_HEX_LENGTH
        or not isinstance(row["source_coordinate"], str)
        or not row["source_coordinate"]
        or not row["reason"]
    ):
        message = "unqualified_historical_deviation"
        raise ValueError(message)
    if row["status"] == "source_only":
        label = row.get("source_year_label")
        if (
            not isinstance(label, str)
            or label[-1:] not in {"†", "*", "^", "#"}
            or row["reason"] != "annotated_year_absent_from_donor"
            or row["donor_value"] is not None
        ):
            message = "unexplained_annotated_source_only_year"
            raise ValueError(message)
        basis = "donor_numeric_year_coercion_drops_footnote_marker"
        rationale = (
            "The pinned donor transform coerces year labels with errors=coerce; "
            "the footnote-marked source year is retained separately."
        )
    else:
        try:
            binary_equal = float(row["source_value"]) == float(row["donor_value"])
        except TypeError, ValueError, OverflowError:
            binary_equal = False
        if not binary_equal:
            message = "unexplained_historical_numeric_difference"
            raise ValueError(message)
        basis = "sqlite_real_retains_binary_value_not_decimal_token"
        rationale = (
            "The source decimal token and donor SQLite REAL parse to the same "
            "binary float; retain the source token and donor scalar separately."
        )
    return {
        "disposition": "accepted",
        "replacement_value": None,
        "publication_approved": False,
        "disposition_basis": basis,
        **{
            key: row[key]
            for key in (
                "status",
                "reason",
                "source_record_id",
                "source_object_sha256",
                "source_coordinate",
                "resolution",
                "source_year_label",
            )
        },
        "source_value_sha256": hashlib.sha256(
            str(row["source_value"]).encode()
        ).hexdigest(),
        "donor_value_sha256": hashlib.sha256(
            str(row["donor_value"]).encode()
        ).hexdigest(),
        "test_reference": (
            "test_historical_reconciliation.py::"
            "test_complete_union_and_explicit_differences"
        ),
        "rationale": rationale,
    }


def validate_historical_deviations(rows: list[dict[str, Any]]) -> None:
    """Require the evidenced population and non-mutating dispositions."""
    if Counter(row["status"] for row in rows) != Counter(
        {"source_only": 29, "value_difference": 1}
    ):
        message = "historical_deviation_count_mismatch"
        raise ValueError(message)
    if any(
        row["disposition"] != "accepted"
        or row["replacement_value"] is not None
        or row["publication_approved"] is not False
        for row in rows
    ):
        message = "historical_deviation_disposition_mismatch"
        raise ValueError(message)


if __name__ == "__main__":
    print(json.dumps(replay(Path(sys.argv[1])), sort_keys=True, indent=2))  # noqa: T201
