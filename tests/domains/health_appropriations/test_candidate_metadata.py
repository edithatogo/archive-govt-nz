# SPDX-License-Identifier: Apache-2.0
"""Candidate metadata follows physical schemas and retains release qualification gaps."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from rdflib import Graph
from tests.domains.health_appropriations.test_candidate_paths import (
    build_health_candidate,
)

from archive_govt_nz.domains.health_appropriations.candidate_metadata import (
    project_candidate_inventory,
)
from archive_govt_nz.domains.health_appropriations.candidate_readiness import (
    verify_candidate,
)


def test_inventory_uses_actual_fields_and_rejects_ambiguous_arrow_columns(
    tmp_path: Path,
) -> None:
    path = tmp_path / "actual.parquet"
    pq.write_table(pa.table({"amount (source)": [1], "year": [2026]}), path)
    before = path.read_bytes()
    products = project_candidate_inventory(tmp_path)
    croissant = json.loads(products["metadata/croissant.json"])
    fields = croissant["cr:recordSet"][0]["cr:field"]
    assert [field["name"] for field in fields] == ["amount (source)", "year"]
    assert fields[0]["cr:source"]["cr:extract"]["cr:column"] == "amount (source)"
    assert fields[0]["@id"].endswith("amount%20%28source%29")
    assert "license" not in croissant
    assert "datePublished" not in croissant
    for name in (
        "metadata/croissant.json",
        "ro-crate-metadata.json",
        "metadata/dcat.json",
        "metadata/prov.json",
    ):
        assert len(Graph().parse(data=products[name].decode(), format="json-ld")) > 0
    report = json.loads(products["metadata/profile-validation.json"])
    assert report["release_readiness"] == "blocked"
    assert report["full_conformance"] == "not_asserted"
    assert report["payload_staging"] == "outside_projection_scope"
    assert {p.name for p in tmp_path.iterdir()} == {"actual.parquet"}
    assert products == project_candidate_inventory(tmp_path)
    assert path.read_bytes() == before
    pq.write_table(
        pa.Table.from_arrays([pa.array([1]), pa.array([2])], names=["same", "same"]),
        path,
    )
    with pytest.raises(ValueError, match="candidate_metadata_contract"):
        project_candidate_inventory(tmp_path)
    path.write_bytes(before)
    (tmp_path / "original").mkdir()
    (tmp_path / "original/source.csv").write_bytes(b"source bytes")
    (tmp_path / "metadata").mkdir()
    (tmp_path / "metadata/rights.json").write_text(
        json.dumps(
            {"resources": [{"path": "original/source.csv", "source_sha256": "0" * 64}]}
        )
    )
    with pytest.raises(ValueError, match="candidate_metadata_contract"):
        project_candidate_inventory(tmp_path)


@pytest.mark.parametrize("suffix", ["csv", "1234567890"])
def test_builder_preserves_originals_and_emits_an_unqualified_local_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    suffix: str,
) -> None:
    original = tmp_path / "source.csv"
    original.write_bytes(b"year,value\n2026,1\n")
    source_hash = hashlib.sha256(original.read_bytes()).hexdigest()

    class Store:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def verify(self, object_id: str) -> SimpleNamespace:
            assert object_id == "sha256:" + source_hash
            return SimpleNamespace(path=original)

    monkeypatch.setattr(build_health_candidate, "ContentAddressedStore", Store)
    capture = tmp_path / "capture.json"
    capture.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "state": "captured",
                        "source_id": "f" * 128,
                        "object_id": "sha256:" + source_hash,
                        "sha256": source_hash,
                        "url": f"https://example.test/source.{suffix}",
                        "rights": {
                            "state": "eligible",
                            "license": "CC-BY-4.0",
                            "evidence": "https://example.test/terms",
                            "attribution": "Fixture",
                        },
                    }
                ]
            }
        )
    )
    census = tmp_path / "census.json"
    census.write_text(json.dumps({"records": [{"disposition": "captured"}]}))
    silver, gold = tmp_path / "silver", tmp_path / "gold"
    silver.mkdir()
    (gold / "analytics").mkdir(parents=True)
    (gold / "plots").mkdir()
    pq.write_table(pa.table({"actual_value": [1]}), silver / "donor_facts.parquet")
    pq.write_table(
        pa.table({"actual_year": [2026]}), gold / "analytics" / "actual.parquet"
    )
    (gold / "health_funding_nz.sqlite").write_bytes(b"opaque compatibility fixture")
    inventories = []
    for label in ("first", "second"):
        output = tmp_path / label
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "build_health_candidate",
                "--capture-manifest",
                str(capture),
                "--store-root",
                str(tmp_path / "store"),
                "--silver-dir",
                str(silver),
                "--gold-dir",
                str(gold),
                "--source-census",
                str(census),
                "--output-dir",
                str(output),
            ],
        )
        assert build_health_candidate.main() == 0
        manifest = json.loads((output / "MANIFEST.json").read_text())
        assert manifest["candidate_state"] == "partial_not_release_ready"
        assert (
            manifest["rights_gate"]
            == "original_assertions_only_derivatives_unqualified"
        )
        assert (
            output / "original" / ("f" * 128 + "." + suffix)
        ).read_bytes() == original.read_bytes()
        assert "license:" not in (output / "README.md").read_text()
        rights = json.loads((output / "metadata/rights.json").read_text())
        assert {row["eligibility"] for row in rights["resources"]} == {
            "capture_asserted_eligible"
        }
        croissant = json.loads((output / "metadata/croissant.json").read_text())
        assert "datePublished" not in croissant
        assert {
            f["name"] for rs in croissant["cr:recordSet"] for f in rs["cr:field"]
        } == {"actual_value", "actual_year"}
        inventories.append(
            {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
        )
    assert inventories[0] == inventories[1]
    final_root = tmp_path / "second"
    manifest_pin = hashlib.sha256(
        (final_root / "MANIFEST.json").read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError, match="candidate_release_gate_failed"):
        verify_candidate(final_root, expected_manifest_sha256=manifest_pin)
