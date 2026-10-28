# SPDX-License-Identifier: Apache-2.0
"""Resource-bound publication profiles distinguish local qualification from approval."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from rdflib import Graph, Literal, URIRef

from archive_govt_nz.domains.health_appropriations import release_metadata as metadata
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def _case(
    tmp_path: Path, state: str = "eligible_asserted"
) -> tuple[Path, str, metadata.MetadataReleaseInput]:
    root = tmp_path / "candidate"
    root.mkdir()
    (root / "data").mkdir()
    (root / "metadata").mkdir()
    pq.write_table(
        pa.table({"source_amount": [123], "source_label": ["retained"]}),
        root / "data/facts.parquet",
    )
    (root / "metadata/rights.json").write_bytes(_json({"resources": []}))
    (root / "metadata/source-census.json").write_bytes(
        _json({"records": [{"disposition": "captured"}]})
    )
    store = ContentAddressedStore(tmp_path / "evidence")
    evidence = store.put_bytes(
        b"Fictional reviewed grant; not an actual publication approval."
    )
    facts_evidence = store.put_bytes(
        b"Fictional published fixture identity, creator and date."
    )
    facts = {
        "identifier": "urn:example:health:fixture",
        "name": "Fictional Health metadata fixture",
        "description": "Synthetic source assertions; no real publication is performed.",
        "version": "fixture-v1",
        "url": "https://example.test/dataset",
        "date_published": "2026-01-01",
        "creators": [
            {
                "id": "urn:example:publisher",
                "type": "Organization",
                "name": "Fictional publisher",
            }
        ],
    }
    names = {
        "data/facts.parquet",
        "README.md",
        "metadata/rights.json",
        "metadata/source-census.json",
        "MANIFEST.json",
    } | metadata.GENERATED_MEMBERS
    rows = [
        {
            "path": name,
            "payload_sha256": "0" * 64,
            "state": state if name == "data/facts.parquet" else "eligible_asserted",
            "license_uri": (
                "https://creativecommons.org/licenses/by/4.0/"
                if name == "data/facts.parquet"
                else "https://www.apache.org/licenses/LICENSE-2.0"
            )
            if state == "eligible_asserted" or name != "data/facts.parquet"
            else None,
            "attribution": "Fictional reviewed holder"
            if state == "eligible_asserted" or name != "data/facts.parquet"
            else None,
            "evidence_sha256": evidence.sha256,
        }
        for name in sorted(names)
    ]
    (root / "README.md").write_bytes(metadata.render_card(facts, rows))
    for row in rows:
        path = root / row["path"]
        if path.is_file():
            row["payload_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name, body in metadata.project_release_metadata(root, facts, rows).items():
        (root / name).write_bytes(body)
    files = [
        {
            "path": p.relative_to(root).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in sorted(root.rglob("*"))
        if p.is_file()
    ]
    manifest = {
        "schema_version": "archive-govt-nz.health-hf-candidate/v2",
        "dataset": "edithatogo/nz-health-appropriations",
        "version": facts["version"],
        "metadata_identifier": facts["identifier"],
        "metadata_profile": metadata.VERSION,
        "rights_gate": "requires_pinned_resource_contract",
        "source_disposition_gate": "passed",
        "candidate_state": "release_candidate_pending_contract_verification",
        "files": files,
    }
    body = _json(manifest)
    (root / "MANIFEST.json").write_bytes(body)
    pin = hashlib.sha256(body).hexdigest()
    for row in rows:
        row["payload_sha256"] = hashlib.sha256(
            (root / row["path"]).read_bytes()
        ).hexdigest()
    contract = {
        "schema_version": metadata.VERSION,
        "intended_use": "candidate_redistribution_review",
        "candidate_manifest_sha256": pin,
        "facts": facts,
        "facts_evidence_sha256": facts_evidence.sha256,
        "resources": rows,
    }
    contract_path = tmp_path / "reviewed-contract.json"
    body = _json(contract)
    contract_path.write_bytes(body)
    return (
        root,
        pin,
        metadata.MetadataReleaseInput(
            contract_path, hashlib.sha256(body).hexdigest(), store.root
        ),
    )


def test_mixed_licensing_profiles_are_bound_without_blanket_grants(
    tmp_path: Path,
) -> None:
    root, pin, inputs = _case(tmp_path)
    before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    receipt = metadata.verify_release_metadata(root, pin, inputs)
    assert receipt["status"] == "qualified_for_explicit_gate"
    assert receipt["publication_approval"] == "not_granted"
    assert receipt["rights_scope"] == "all_candidate_members_including_manifest"
    assert receipt["licenses"] == [
        "https://creativecommons.org/licenses/by/4.0/",
        "https://www.apache.org/licenses/LICENSE-2.0",
    ]
    assert before == {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    croissant = json.loads((root / "metadata/croissant.json").read_bytes())
    assert isinstance(croissant["license"], dict)
    assert "no dataset-wide grant" in croissant["license"]["description"]
    for name in (
        "metadata/dcat.json",
        "metadata/prov.json",
        "metadata/croissant.json",
        "ro-crate-metadata.json",
    ):
        graph = Graph().parse(data=(root / name).read_text(), format="json-ld")
        assert len(graph) > 0
    graph = Graph().parse(
        data=(root / "metadata/prov.json").read_text(), format="json-ld"
    )
    assert any(
        graph.triples(
            (
                None,
                URIRef("http://schema.org/creditText"),
                Literal("Fictional reviewed holder"),
            )
        )
    )


@pytest.mark.parametrize("state", ["unresolved", "restricted", "incompatible"])
def test_noneligible_resource_states_block_release(tmp_path: Path, state: str) -> None:
    root, pin, inputs = _case(tmp_path, state)
    result = metadata.verify_release_metadata(root, pin, inputs)
    assert result["status"] == "blocked"
    assert f"rights:{state}:data/facts.parquet" in result["blockers"]
    assert result["publication_approval"] == "not_granted"


def test_untrusted_record_pin_or_missing_evidence_cannot_qualify(
    tmp_path: Path,
) -> None:
    root, pin, inputs = _case(tmp_path)
    with pytest.raises(ValueError, match="metadata_release_contract"):
        metadata.verify_release_metadata(
            root, pin, replace(inputs, contract_sha256="0" * 64)
        )
    for path in inputs.evidence_root.rglob("*"):
        if path.is_file():
            path.unlink()
    with pytest.raises(ValueError, match="metadata_release_contract"):
        metadata.verify_release_metadata(root, pin, inputs)


def test_positive_qualified_readiness_requires_explicit_record_input(
    tmp_path: Path,
) -> None:
    from datetime import UTC, datetime, timedelta

    from archive_govt_nz.domains.health_appropriations.candidate_readiness import (
        ReleaseExpectation,
        verify_release_readiness,
    )

    root, pin, inputs = _case(tmp_path)
    body = _json(
        {
            "code_revision": "a" * 40,
            "candidate_manifest_sha256": pin,
            "parity": "passed",
            "recovery": "passed",
            "metadata_contract_sha256": inputs.contract_sha256,
            "validated_at": "2026-10-28T00:00:00+00:00",
        }
    )
    assurance = tmp_path / "assurance.json"
    assurance.write_bytes(body)
    expectation = ReleaseExpectation(
        pin,
        assurance,
        hashlib.sha256(body).hexdigest(),
        "a" * 40,
        datetime(2026, 10, 28, tzinfo=UTC),
        timedelta(days=1),
        inputs,
    )
    result = verify_release_readiness(root, expectation)
    assert result["release_readiness"] == "ready_for_explicit_gate"
    assert (
        result["metadata_validation"]["resources_verified"]
        == len(json.loads((root / "MANIFEST.json").read_bytes())["files"]) + 1
    )
    assert result["publication_approval"] == "not_granted"
    with pytest.raises(ValueError, match="candidate_metadata_release_unqualified"):
        verify_release_readiness(root, replace(expectation, metadata=None))
