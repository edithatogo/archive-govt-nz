"""Replay retained donor parity read-only; print payload-free evidence JSON."""

# Standalone evidence recipe, deliberately linear for auditability.
# ruff: noqa: INP001, C901, PLR0915

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
LIMIT = 16 * 1024 * 1024


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
    for item in manifest["objects"]:
        digest = item["sha256"]
        path = root / "bronze-cas/sha256" / digest[:2] / digest
        payload = read(path, digest)
        if len(payload) != item["byte_count"]:
            message = "replay_donor_length"
            raise ValueError(message)
        if item["path"] == "data/processed/health_funding_nz.sqlite":
            donor_path, donor_hash = path, digest
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
        deviations.append(
            {
                key: row[key]
                for key in (
                    "status",
                    "reason",
                    "source_record_id",
                    "source_object_sha256",
                    "source_coordinate",
                    "resolution",
                )
            }
            | {
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
                "rationale": (
                    "Retain exact source and donor observations separately; "
                    "SQLite REAL equality does not prove exact decimal equality."
                ),
            }
        )
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
        "binary_representation_flags": sum(
            row["representation_changed"] for row in records
        ),
        "rights_state": "not_evaluated",
        "publication_state": "no_action",
        "repair_approval": "not_asserted",
    }


if __name__ == "__main__":
    print(json.dumps(replay(Path(sys.argv[1])), sort_keys=True, indent=2))  # noqa: T201
