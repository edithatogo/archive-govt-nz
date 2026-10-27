# SPDX-License-Identifier: Apache-2.0
"""Metadata preserves scoped rights, physical schemas and verified derivation."""

import hashlib
import json
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from rdflib import Graph, URIRef
from tests.domains.health_appropriations import test_overview_rights as shared

from archive_govt_nz.domains.health_appropriations import overview_rights
from archive_govt_nz.domains.health_appropriations import (
    qualified_overview_metadata as metadata,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations.source_operations import (
        SourceRequest,
    )


qualified_inputs = shared.qualified_inputs


@pytest.fixture
def metadata_input(
    tmp_path: Path,
    qualified_inputs: tuple[SourceRequest, dict[str, Any], Path, bytes, bytes],
) -> metadata.QualifiedOverviewInput:
    request, query, evidence, _, _ = qualified_inputs
    pq.write_table(
        pa.Table.from_pylist(query["records"]),
        request.output_dir / "vote_health_overview_facts.parquet",
    )
    facts = (request.output_dir / "vote_health_overview_facts.parquet").read_bytes()
    manifest = json.dumps(
        {
            "output_sha256": {
                "vote_health_overview_facts.parquet": hashlib.sha256(facts).hexdigest()
            }
        }
    ).encode()
    (request.output_dir / "MANIFEST.json").write_bytes(manifest)
    pin = hashlib.sha256(manifest).hexdigest()
    query["source_silver_manifest_sha256"] = pin
    package = tmp_path / "qualified"
    overview_rights.qualify_overview_package(request, pin, evidence, package)
    return metadata.QualifiedOverviewInput(
        request,
        pin,
        evidence,
        package,
        hashlib.sha256((package / "MANIFEST.json").read_bytes()).hexdigest(),
    )


def test_four_profiles_bind_only_qualified_data_and_preserve_inputs(
    metadata_input: metadata.QualifiedOverviewInput, tmp_path: Path
) -> None:
    value = metadata_input
    before = {p.name: p.read_bytes() for p in value.package.iterdir()}
    docs = metadata.project_qualified_overview_metadata((value,))
    assert docs == metadata.project_qualified_overview_metadata((value,))
    assert before == {p.name: p.read_bytes() for p in value.package.iterdir()}
    catalogue = json.loads(docs["catalogue.json"])
    package = catalogue["packages"][0]
    fields = package["tables"][0]["fields"]
    assert {f["name"] for f in fields} == {
        "value",
        "source_page",
        "summary_measure",
        "rights_state",
    }
    expected = {package["id"] + ":" + r["path"] for r in package["inventory"]}
    for filename in (
        "dcat.json",
        "prov.json",
        "croissant.json",
        "ro-crate-metadata.json",
    ):
        graph = Graph().parse(data=docs[filename].decode(), format="json-ld")
        predicate = URIRef(
            "http://purl.org/dc/terms/license"
            if filename in {"dcat.json", "prov.json"}
            else "http://schema.org/license"
        )
        triples = list(graph.triples((None, predicate, None)))
        assert len(triples) == 2
        assert all(
            o == URIRef("https://creativecommons.org/licenses/by/4.0/")
            for _, _, o in triples
        )
        if filename in {"dcat.json", "prov.json"}:
            assert all(
                isinstance(o, URIRef)
                for _, _, o in graph.triples(
                    (None, URIRef("http://purl.org/dc/terms/rights"), None)
                )
            )
        if filename == "prov.json":
            assert {str(s) for s, _, _ in triples} == expected
            assert not list(
                graph.triples(
                    (None, URIRef("http://www.w3.org/ns/prov#generatedAtTime"), None)
                )
            )
    croissant, crate = (
        json.loads(docs["croissant.json"]),
        json.loads(docs["ro-crate-metadata.json"]),
    )
    assert "license" not in croissant
    assert "license" not in next(n for n in crate["@graph"] if n["@id"] == "./")
    assert all(
        n["creditText"] == "Synthetic test attribution"
        for n in croissant["distribution"]
    )
    report = json.loads(docs["profile-validation.json"])
    assert report["qualified_data_resources"] == 2
    assert report["publication"] == "not_performed"
    assert report["full_conformance"] == "not_asserted"
    assert metadata.export_qualified_overview_metadata(
        (value,), tmp_path / "first"
    ) == metadata.export_qualified_overview_metadata((value,), tmp_path / "second")


def test_forged_rights_or_missing_evidence_cannot_create_metadata(
    metadata_input: metadata.QualifiedOverviewInput, tmp_path: Path
) -> None:
    value = metadata_input
    manifest_path = value.package / "MANIFEST.json"
    original = manifest_path.read_bytes()
    manifest = json.loads(original)
    manifest["license"] = "CC0-1.0"
    manifest_path.write_text(json.dumps(manifest))
    forged = replace(
        value, manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    )
    with pytest.raises(ValueError, match="overview_rights_contract"):
        metadata.export_qualified_overview_metadata((forged,), tmp_path / "forged")
    assert not (tmp_path / "forged").exists()
    manifest_path.write_bytes(original)
    (value.evidence_root / "observation.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        metadata.export_qualified_overview_metadata((value,), tmp_path / "missing")
    assert not (tmp_path / "missing").exists()
    with pytest.raises(ValueError, match="qualified_overview_metadata_contract"):
        metadata.project_qualified_overview_metadata((value, value))
