# SPDX-License-Identifier: Apache-2.0
"""Pinned partner evidence resolves only the reviewed negative mapping scope."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from tests.domains.health_appropriations import (
    test_qualified_overview_metadata as shared,
)

from archive_govt_nz.domains.health_appropriations import partner_snapshots as partners
from archive_govt_nz.domains.health_appropriations import (
    qualified_overview_metadata as metadata,
)

qualified_inputs = shared.qualified_inputs
metadata_input = shared.metadata_input


def _encode(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    ).encode()


@pytest.fixture
def reviewed_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[bytes, tuple[partners.PartnerSnapshot, ...], dict[str, Any]]:
    baseline = _encode(
        {
            "approved_links": [],
            "records": [
                {
                    "target_repository": p,
                    "package_id": "source:annual-total",
                    "disposition": "pending",
                    "target_key": None,
                    "confidence": None,
                }
                for p in ("reimbursement-atlas", "global-medicines-atlas")
            ],
        }
    )
    ledger: dict[str, Any] = {
        "scope": "qualified_annual_vote_total_only",
        "source_readiness_sha256": hashlib.sha256(baseline).hexdigest(),
        "pair_count": 2,
        "snapshots": {},
        "partners": {},
    }
    inputs = []
    for partner in ("reimbursement-atlas", "global-medicines-atlas"):
        root = tmp_path / partner
        root.mkdir()
        table = b'{"artifact_id":"artifact:one"}\n'
        (root / "gold.jsonl").write_bytes(table)
        inventory = [
            {
                "path": "gold.jsonl",
                "sha256": hashlib.sha256(table).hexdigest(),
                "bytes": len(table),
            }
        ]
        snapshot = _encode({"inventory": inventory})
        (root / "SNAPSHOT.json").write_bytes(snapshot)
        pin = hashlib.sha256(snapshot).hexdigest()
        inputs.append(partners.PartnerSnapshot(partner, root, pin))
        ledger["snapshots"][partner] = {
            "partner": partner,
            "kind": "hugging_face",
            "repository": "synthetic/" + partner,
            "revision": "a" * 40,
            "snapshot_sha256": pin,
            "inventory": inventory,
        }
        ledger["partners"][partner] = {
            "snapshot_key": partner,
            "target_table": "gold.jsonl",
            "target_record_field": "artifact_id",
            "target_record_ids": ["artifact:one"],
            "record_grain": "medallion_artifact_metadata",
            "disposition": "excluded",
            "reason": "record_grain_incompatible_with_annual_vote_total",
            "method": "reviewed_record_grain_exclusion",
            "rights_policy": "source_specific_not_inherited",
            "publisher_control_observations": [],
            "exclusion_scope": "reviewed synthetic scope",
        }
    monkeypatch.setattr(partners, "_ledger", lambda: ledger)
    return baseline, tuple(inputs), ledger


def test_pinned_review_resolves_pending_without_granting_links(
    reviewed_inputs: tuple[bytes, tuple[partners.PartnerSnapshot, ...], dict[str, Any]],
) -> None:
    baseline, snapshots, _ = reviewed_inputs
    first = partners.project_partner_federation(baseline, snapshots)
    assert first == partners.project_partner_federation(
        baseline, tuple(reversed(snapshots))
    )
    report = json.loads(first["federation_readiness.json"])
    assert report["approved_links"] == []
    assert report["pending_pairs"] == 0
    assert report["excluded_pairs"] == 2
    assert all(
        r["disposition"] == "excluded"
        and r["target_key"] is None
        and r["confidence"] is None
        for r in report["records"]
    )
    assert all(
        r["target_manifest_sha256"] == snapshots[i].snapshot_sha256
        for i, r in enumerate(report["records"])
    )
    assert (
        json.loads(first["partner_snapshots.json"])["rights_policy"]
        == "source_specific_not_inherited"
    )


def test_tampering_and_rehashed_forgery_do_not_become_review_evidence(
    reviewed_inputs: tuple[bytes, tuple[partners.PartnerSnapshot, ...], dict[str, Any]],
) -> None:
    baseline, snapshots, _ = reviewed_inputs
    with pytest.raises(ValueError, match="partner_snapshot_contract"):
        partners.project_partner_federation(baseline + b" ", snapshots)
    with pytest.raises(ValueError, match="partner_snapshot_contract"):
        partners.project_partner_federation(baseline, (snapshots[0], snapshots[0]))
    source = snapshots[0].root / "SNAPSHOT.json"
    source.write_bytes(source.read_bytes() + b" ")
    forged = replace(
        snapshots[0], snapshot_sha256=hashlib.sha256(source.read_bytes()).hexdigest()
    )
    with pytest.raises(ValueError, match="partner_snapshot_contract"):
        partners.project_partner_federation(baseline, (forged, snapshots[1]))


def test_export_wires_pinned_assessments_and_preserves_default_metadata(
    reviewed_inputs: tuple[bytes, tuple[partners.PartnerSnapshot, ...], dict[str, Any]],
    metadata_input: metadata.QualifiedOverviewInput,
    tmp_path: Path,
) -> None:
    _, snapshots, ledger = reviewed_inputs
    baseline = metadata.project_qualified_overview_discovery((metadata_input,))
    ledger["source_readiness_sha256"] = hashlib.sha256(
        baseline["federation_readiness.json"]
    ).hexdigest()
    output = tmp_path / "qualified-federation"
    pins = metadata.export_qualified_overview_metadata(
        (metadata_input,), output, include_discovery=True, partner_snapshots=snapshots
    )
    marker = json.loads((output / "MANIFEST.json").read_bytes())
    assert marker["schema_version"].endswith("/v3")
    assert len(pins) == 12
    assert metadata.project_qualified_overview_discovery((metadata_input,)) == baseline
    report = json.loads((output / "federation_readiness.json").read_bytes())
    schema = json.loads(
        (
            Path(__file__).parents[3]
            / "schemas/health-federation-readiness-v2.schema.json"
        ).read_bytes()
    )
    Draft202012Validator(schema).validate(report)
    with pytest.raises(ValueError, match="qualified_overview_metadata_contract"):
        metadata.export_qualified_overview_metadata(
            (metadata_input,),
            snapshots[0].root / "overlap",
            include_discovery=True,
            partner_snapshots=snapshots,
        )
    (snapshots[0].root / "gold.jsonl").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        metadata.export_qualified_overview_metadata(
            (metadata_input,),
            tmp_path / "rejected",
            include_discovery=True,
            partner_snapshots=snapshots,
        )
    assert not (tmp_path / "rejected").exists()
