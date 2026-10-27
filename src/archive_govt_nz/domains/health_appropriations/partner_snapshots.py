# SPDX-License-Identifier: Apache-2.0
"""Offline partner snapshots and explicitly scoped negative mapping evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

_LEDGER_SHA256 = "7d8038095f29b739eb1028e72f8f67d1b9d4192fc86c1c28f61b2f152254720b"
_MAX_BYTES = 4 * 1024 * 1024
_MAX_NODES = 256
_MAX_FILES = 32
_MAX_SNAPSHOTS = 4


@dataclass(frozen=True)
class PartnerSnapshot:
    """One explicitly pinned retained Hub or GitHub evidence slice."""

    key: str
    root: Path
    snapshot_sha256: str


def _require(condition: object) -> None:
    if not condition:
        message = "partner_snapshot_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def _ledger() -> dict[str, Any]:
    return json.loads(
        verified_snapshot(
            Path(__file__).with_name("partner_review_20261028.json"),
            _LEDGER_SHA256,
            max_bytes=_MAX_BYTES,
        )
    )


def _safe(path: Path) -> None:
    _require(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))


def _snapshot(value: PartnerSnapshot, expected: dict[str, Any]) -> dict[str, bytes]:
    _safe(value.root)
    _require(
        value.root.is_dir() and value.snapshot_sha256 == expected["snapshot_sha256"]
    )
    _safe(value.root / "SNAPSHOT.json")
    marker = verified_snapshot(
        value.root / "SNAPSHOT.json", value.snapshot_sha256, max_bytes=_MAX_BYTES
    )
    _require(json.loads(marker)["inventory"] == expected["inventory"])
    entries = expected["inventory"]
    names = {r["path"] for r in entries}
    _require(0 < len(names) == len(entries) <= _MAX_FILES)
    _require(sum(r["bytes"] for r in entries) <= 16 * _MAX_BYTES)
    observed = set()
    nodes = list(islice(value.root.rglob("*"), _MAX_NODES + 1))
    _require(len(nodes) <= _MAX_NODES)
    for path in nodes:
        _safe(path)
        if path.is_file():
            observed.add(path.relative_to(value.root).as_posix())
    _require(observed == names | {"SNAPSHOT.json"})
    payloads = {}
    for row in entries:
        path = Path(row["path"])
        _require(
            not path.is_absolute()
            and ".." not in path.parts
            and path.as_posix() == row["path"]
        )
        payload = verified_snapshot(
            value.root / path, row["sha256"], max_bytes=_MAX_BYTES
        )
        _require(len(payload) == row["bytes"])
        payloads[row["path"]] = payload
    return payloads


def _partner_descriptors(
    ledger: dict[str, Any], payloads: dict[str, dict[str, bytes]]
) -> dict[str, Any]:
    descriptors = {}
    for partner, review in sorted(ledger["partners"].items()):
        _require(
            review["disposition"] == "excluded"
            and review["method"] == "reviewed_record_grain_exclusion"
        )
        _require(review["reason"] == "record_grain_incompatible_with_annual_vote_total")
        key = review["snapshot_key"]
        snapshot = ledger["snapshots"][key]
        table = review["target_table"]
        raw = payloads[key][table]
        rows = (
            [json.loads(line) for line in raw.splitlines()]
            if table.endswith(".jsonl")
            else json.loads(raw)["sources"]
        )
        identifiers = sorted(r[review["target_record_field"]] for r in rows)
        _require(
            identifiers == review["target_record_ids"]
            and len(set(identifiers)) == len(rows)
        )
        descriptors[partner] = {
            "partner": partner,
            "repository": snapshot["repository"],
            "revision": snapshot["revision"],
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "target_table": table,
            "target_record_ids": identifiers,
            "target_record_count": len(rows),
            "record_grain": review["record_grain"],
            "exclusion_scope": review["exclusion_scope"],
            "publisher_control_observations": review["publisher_control_observations"],
            "publisher_control_scope": "selected_retained_members_only",
            "evidence_snapshots": [
                dict(key=k, **v)
                for k, v in sorted(ledger["snapshots"].items())
                if v["partner"] == partner
            ],
        }
    return descriptors


def project_partner_federation(
    readiness: bytes, snapshots: tuple[PartnerSnapshot, ...]
) -> dict[str, bytes]:
    """Resolve pinned headline pairs without accepting a positive join or rights grant.

    The committed review binds an exact source-readiness digest and both partner
    snapshots plus their retained review evidence. Exclusion applies only to this
    annual-total grain, not all partner records, future vintages or other joins.
    """
    ledger = _ledger()
    _require(ledger["scope"] == "qualified_annual_vote_total_only")
    _require(hashlib.sha256(readiness).hexdigest() == ledger["source_readiness_sha256"])
    _require(type(snapshots) is tuple and 0 < len(snapshots) <= _MAX_SNAPSHOTS)
    _require(len({s.key for s in snapshots}) == len(snapshots))
    _require({s.key for s in snapshots} == set(ledger["snapshots"]))
    payloads = {s.key: _snapshot(s, ledger["snapshots"][s.key]) for s in snapshots}
    descriptors = _partner_descriptors(ledger, payloads)
    baseline = json.loads(readiness)
    _require(
        baseline["approved_links"] == []
        and len(baseline["records"]) == ledger["pair_count"]
    )
    review_pin = hashlib.sha256(_json(ledger)).hexdigest()
    records = []
    for row in baseline["records"]:
        _require(row["disposition"] == "pending")
        partner = row["target_repository"]
        evidence = descriptors[partner]
        records.append(
            {
                **row,
                "disposition": "excluded",
                "reason": ledger["partners"][partner]["reason"],
                "mapping_method": "reviewed_record_grain_exclusion",
                "target_manifest_sha256": evidence["snapshot_sha256"],
                "target_snapshot_revision": evidence["revision"],
                "target_record_grain": evidence["record_grain"],
                "target_record_count": evidence["target_record_count"],
                "mapping_review_sha256": review_pin,
                "target_key": None,
                "target_scheme_version": None,
                "confidence": None,
            }
        )
    baseline.pop("required_evidence", None)
    report = {
        **baseline,
        "schema_version": "archive-govt-nz.health-federation-readiness/v2",
        "records": records,
        "excluded_pairs": len(records),
        "pending_pairs": 0,
        "review_scope": ledger["scope"],
        "review_status": "complete_for_pinned_scope",
        "positive_link_admission": "not_qualified",
        "positive_link_requirements": [
            "compatible_record_grain_and_versioned_keys",
            "source_specific_rights_and_period_qualification",
            "reviewed_relationship_method_confidence_and_lineage",
        ],
    }
    return {
        "federation_readiness.json": _json(report),
        "partner_snapshots.json": _json(
            {
                "schema_version": "archive-govt-nz.health-partner-snapshots/v1",
                "mapping_review_sha256": review_pin,
                "partners": list(descriptors.values()),
                "rights_policy": "source_specific_not_inherited",
                "publication": "not_performed",
            }
        ),
    }
