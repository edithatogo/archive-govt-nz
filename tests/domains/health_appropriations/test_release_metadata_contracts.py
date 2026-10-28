# SPDX-License-Identifier: Apache-2.0
"""Resource-bound publication profiles distinguish local qualification from approval."""

from __future__ import annotations

import hashlib
import json
import socket
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from rdflib import Dataset, Graph, Literal, URIRef

from archive_govt_nz.domains.health_appropriations import release_metadata as metadata
from archive_govt_nz.domains.health_appropriations.candidate_readiness import (
    ReleaseExpectation,
    verify_release_readiness,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def _case(
    tmp_path: Path,
    state: str = "eligible_asserted",
    *,
    facts_overrides: dict[str, object] | None = None,
    amount: object = 123,
) -> tuple[Path, str, metadata.MetadataReleaseInput]:
    root = tmp_path / "candidate"
    root.mkdir()
    (root / "data").mkdir()
    (root / "metadata").mkdir()
    pq.write_table(
        pa.table({"source_amount": [amount], "source_label": ["retained"]}),
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
        "name": "fictional-health-metadata-fixture",
        "description": "Synthetic source assertions; no real publication is performed.",
        "version": "1.0.0",
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
    facts.update(facts_overrides or {})
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


@pytest.mark.parametrize("missing", ["url", "date_published", "creators"])
def test_missing_facts_are_not_invented(tmp_path: Path, missing: str) -> None:
    """Missing publication facts remain blocked despite valid resource grants."""
    root, pin, inputs = _case(tmp_path, facts_overrides={missing: None})
    result = metadata.verify_release_metadata(root, pin, inputs)
    assert "metadata_fact_missing:" + missing in result["blockers"]
    croissant = json.loads((root / "metadata/croissant.json").read_bytes())
    assert "dct:conformsTo" not in croissant


@pytest.mark.parametrize(
    "fault", ["missing_member", "duplicate", "conflicting_grant", "forged_graph"]
)
def test_repinned_contract_does_not_admit_conflicts(tmp_path: Path, fault: str) -> None:
    """A new trusted pin cannot excuse incomplete or inconsistent resource claims."""
    root, pin, inputs = _case(tmp_path)
    contract = json.loads(inputs.contract_path.read_bytes())
    if fault == "missing_member":
        contract["resources"].pop()
    elif fault == "duplicate":
        contract["resources"].append(contract["resources"][0])
    elif fault == "conflicting_grant":
        contract["resources"][0]["state"] = "restricted"
    else:
        (root / "metadata/dcat.json").write_bytes(b"{}")
        manifest = json.loads((root / "MANIFEST.json").read_bytes())
        for row in manifest["files"]:
            if row["path"] == "metadata/dcat.json":
                row.update(bytes=2, sha256=hashlib.sha256(b"{}").hexdigest())
        (root / "MANIFEST.json").write_bytes(_json(manifest))
        pin = hashlib.sha256((root / "MANIFEST.json").read_bytes()).hexdigest()
        contract["candidate_manifest_sha256"] = pin
        for row in contract["resources"]:
            row["payload_sha256"] = hashlib.sha256(
                (root / row["path"]).read_bytes()
            ).hexdigest()
    body = _json(contract)
    inputs.contract_path.write_bytes(body)
    inputs = replace(inputs, contract_sha256=hashlib.sha256(body).hexdigest())
    with pytest.raises(ValueError, match="metadata_release_contract"):
        metadata.verify_release_metadata(root, pin, inputs)


def test_decimal_is_preserved_and_not_mapped_to_lossy_float(tmp_path: Path) -> None:
    """Unsupported physical types keep exact bytes and block profile readiness."""
    root, pin, inputs = _case(tmp_path, amount=Decimal("123.000000000000000001"))
    before = (root / "data/facts.parquet").read_bytes()
    result = metadata.verify_release_metadata(root, pin, inputs)
    assert result["status"] == "blocked"
    assert any(
        b.startswith("croissant_type_unsupported:decimal128")
        for b in result["blockers"]
    )
    assert (root / "data/facts.parquet").read_bytes() == before


@pytest.mark.parametrize(
    "member",
    [
        "metadata/dcat.json",
        "metadata/prov.json",
        "metadata/croissant.json",
        "ro-crate-metadata.json",
    ],
)
def test_expanded_grants_match_resource_record(
    tmp_path: Path,
    member: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An independent RDF dataset checks resource grants and the mixed-rights notice."""
    root, _, inputs = _case(tmp_path)
    record = json.loads(inputs.contract_path.read_bytes())
    grants = {r["path"]: r["license_uri"] for r in record["resources"]}
    document = json.loads((root / member).read_bytes())
    assert isinstance(document["@context"], dict)

    def denied(*_args: object, **_kwargs: object) -> None:
        reason = "external_access_denied"
        raise AssertionError(reason)

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    graph = Dataset().parse(
        data=json.dumps(document),
        format="json-ld",
        publicID="https://example.test/candidate/",
    )
    seen = set()
    notice = record["facts"]["identifier"] + ":resource-rights-notice"
    for subject, predicate, value, _context in graph.quads():
        if str(predicate) not in {
            "http://purl.org/dc/terms/license",
            "http://schema.org/license",
            "https://schema.org/license",
        }:
            continue
        assert isinstance(value, URIRef)
        if str(value) == notice:
            assert member in {"metadata/croissant.json", "ro-crate-metadata.json"}
            continue
        identity = str(subject).removesuffix(":distribution")
        paths = [
            p
            for p in grants
            if identity.endswith(":" + p)
            or identity == "https://example.test/candidate/" + p
        ]
        assert len(paths) == 1
        path = paths[0]
        assert str(value) == grants[path]
        seen.add(path)
    assert "data/facts.parquet" in seen
    if member == "metadata/croissant.json":
        assert any(graph.objects(None, URIRef("http://purl.org/dc/terms/conformsTo")))
        assert all(
            isinstance(value, Literal)
            for value in graph.objects(None, URIRef("https://schema.org/contentUrl"))
        )
        table = pq.read_table(root / "data/facts.parquet")
        objects = {node["name"]: node for node in document["distribution"]}
        fields = document["cr:recordSet"][0]["cr:field"]
        assert {f["name"]: f["cr:dataType"]["@id"] for f in fields} == {
            "source_amount": "cr:Int64",
            "source_label": "sc:Text",
        }
        assert {f["cr:source"]["cr:extract"]["cr:column"] for f in fields} == set(
            table.column_names
        )
        assert all(
            f["cr:source"]["cr:fileObject"]["@id"]
            == objects["data/facts.parquet"]["@id"]
            for f in fields
        )
        assert objects["data/facts.parquet"]["contentUrl"] == "../data/facts.parquet"
        assert {f["name"]: f["hag:arrowType"] for f in fields} == {
            "source_amount": "int64",
            "source_label": "string",
        }


def test_contextual_notice_cannot_alias_a_payload(tmp_path: Path) -> None:
    """A valid snapshot identifier cannot merge a FileObject with its rights notice."""
    root, _, inputs = _case(tmp_path)
    notice = root / "resource-rights-notice"
    notice.write_bytes(b"Retained source notice, not generated metadata.")
    contract = json.loads(inputs.contract_path.read_bytes())
    resources = contract["resources"]
    resources.append(
        {
            **resources[0],
            "path": notice.name,
            "payload_sha256": hashlib.sha256(notice.read_bytes()).hexdigest(),
        }
    )
    base = metadata.project_candidate_inventory(root, reconstruct=True)
    facts = contract["facts"]
    facts["identifier"] = (
        "urn:archive-govt-nz:health:candidate-payload-inventory:"
        + hashlib.sha256(base["metadata/payload-inventory.json"]).hexdigest()
    )
    with pytest.raises(ValueError, match="metadata_release_contract"):
        metadata.project_release_metadata(root, facts, resources)
