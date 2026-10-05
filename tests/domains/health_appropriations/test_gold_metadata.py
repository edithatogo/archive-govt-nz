"""Metadata describes verified Gold bytes without promoting release eligibility."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from rdflib import Graph, Literal, Namespace, URIRef
from tests.domains.health_appropriations.test_budget_comparison_gold import fixture
from tests.domains.health_appropriations.test_fiscal_analytical_gold import (
    fixture_inputs,
    fixture_tables,
)

from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_gold as fiscal,
)
from archive_govt_nz.domains.health_appropriations import gold_metadata as metadata

pytest_plugins = ["tests.domains.health_appropriations.test_local_rdf"]


def packages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[metadata.GoldInput, ...]:
    budget_root = tmp_path / "budget"
    budget_root.mkdir()
    budget, pin = fixture(budget_root, monkeypatch)
    monkeypatch.setattr(fiscal, "build_tables", lambda _: (fixture_tables(), {}))
    target = tmp_path / "fiscal"
    receipt = fiscal.export_fiscal_analytical_gold(
        fixture_inputs(tmp_path / "inputs"), target, write=True
    )
    return (
        metadata.GoldInput("budget_comparison", budget, pin),
        metadata.GoldInput("fiscal_analytical", target, receipt["manifest_sha256"]),
    )


def assert_snapshot_projections(
    first: Path,
    catalogue: dict[str, Any],
    values: tuple[metadata.GoldInput, ...],
) -> None:
    citations = json.loads((first / "citations.json").read_text())
    changelog = json.loads((first / "changelog.json").read_text())
    drillthrough = json.loads((first / "source_drillthrough.json").read_text())
    packages = catalogue["packages"]
    assert citations["schema_version"] == metadata.VERSION
    assert changelog["schema_version"] == metadata.VERSION
    assert citations["scope"] == "local_content_addressed_gold_packages"
    assert changelog["comparison"] == "snapshot_only_no_prior_version_comparison"
    assert changelog["federation"] == "no_approved_links_emitted"
    schemas = Path(__file__).parents[3] / "schemas"
    for filename, schema_name in (
        ("citations.json", "health-gold-citations-v3.schema.json"),
        ("changelog.json", "health-gold-changelog-v3.schema.json"),
        (
            "source_drillthrough.json",
            "health-gold-source-drillthrough-v1.schema.json",
        ),
    ):
        schema = json.loads((schemas / schema_name).read_text())
        Draft202012Validator(schema).validate(
            json.loads((first / filename).read_text())
        )
    assert len(citations["records"]) == len(packages) == 2
    assert len(changelog["packages"]) == 2
    assert drillthrough["schema_version"] == metadata.SOURCE_DRILLTHROUGH_VERSION
    assert drillthrough["rights"] == "not_evaluated"
    assert drillthrough["publication"] == "not_performed"
    assert len(drillthrough["packages"]) == 2
    for package in packages:
        citation = next(
            item for item in citations["records"] if item["package_id"] == package["id"]
        )
        change = next(
            item
            for item in changelog["packages"]
            if item["package_id"] == package["id"]
        )
        assert citation["manifest_sha256"] == package["manifest_sha256"]
        assert citation["rights"] == package["rights"]
        assert citation["publication"] == package["publication"]
        assert change["manifest_sha256"] == package["manifest_sha256"]
        assert change["rights"] == package["rights"]
        assert change["publication"] == package["publication"]
        assert change["tables"] == [
            {"path": table["path"], "rows": table["rows"]}
            for table in package["tables"]
        ]
        source_record = next(
            item
            for item in drillthrough["packages"]
            if item["package_id"] == package["id"]
        )
        assert source_record["manifest_sha256"] == package["manifest_sha256"]
        input_value = next(
            item
            for item in values
            if item.manifest_sha256 == package["manifest_sha256"]
        )
        marker_name = (
            "MANIFEST.json"
            if input_value.profile == "budget_comparison"
            else "manifest.json"
        )
        source_manifest = json.loads((input_value.root / marker_name).read_text())
        if source_record["references"]:
            assert source_record["no_reference_reason"] is None
        else:
            assert (
                source_record["no_reference_reason"]
                == "source_reference_fields_absent_from_package_manifest"
            )
        for reference in source_record["references"]:
            selected: Any = source_manifest
            for token in reference["field_path"].split("/")[1:]:
                selected = selected[token.replace("~1", "/").replace("~0", "~")]
            assert selected == reference["value"]


@pytest.mark.parametrize(
    "manifest_field",
    [
        {"source_object_sha256": "z" * 64},
        {"cpi_definition_url": "http://example.govt.nz/series"},
        {"cpi_definition_url": "https://example.govt.nz/bad locator"},
    ],
)
def test_source_drillthrough_rejects_malformed_recorded_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    manifest_field: dict[str, str],
) -> None:
    fiscal_input = packages(tmp_path, monkeypatch)[1]
    marker = fiscal_input.root / "manifest.json"
    manifest = json.loads(marker.read_text())
    manifest["input_receipts"] = {"malformed_fixture": manifest_field}
    marker.write_text(json.dumps(manifest))
    altered = metadata.GoldInput(
        fiscal_input.profile,
        fiscal_input.root,
        hashlib.sha256(marker.read_bytes()).hexdigest(),
    )
    with pytest.raises(ValueError, match="gold_metadata_contract"):
        metadata.project_gold_metadata((altered,))


def test_exact_catalogue_repeat_build_and_reconstruction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = packages(tmp_path, monkeypatch)
    first, second = tmp_path / "first", tmp_path / "second"
    before = {p: p.read_bytes() for v in values for p in v.root.iterdir()}
    dry = metadata.export_gold_metadata(values, first)
    assert dry["status"] == "dry_run"
    assert not first.exists()
    result = metadata.export_gold_metadata(values, first, write=True)
    repeat = metadata.export_gold_metadata(tuple(reversed(values)), second, write=True)
    assert repeat == result
    console = Path(sys.executable).parent / (
        "archive-govt-nz.exe" if sys.platform == "win32" else "archive-govt-nz"
    )
    by_profile = {v.profile: v for v in values}
    args = [
        str(console),
        "health-appropriations-build-gold-metadata",
        "--fiscal-package",
        str(by_profile["fiscal_analytical"].root),
        "--fiscal-manifest-sha256",
        by_profile["fiscal_analytical"].manifest_sha256,
        "--budget-package",
        str(by_profile["budget_comparison"].root),
        "--budget-manifest-sha256",
        by_profile["budget_comparison"].manifest_sha256,
        "--output-dir",
        str(tmp_path / "console"),
    ]
    dry_cli = subprocess.run(
        args, capture_output=True, text=True, check=True, timeout=30
    )
    assert json.loads(dry_cli.stdout)["status"] == "dry_run"
    assert not (tmp_path / "console").exists()
    actual_cli = subprocess.run(
        [*args, "--write"], capture_output=True, text=True, check=True, timeout=30
    )
    envelope = json.loads(actual_cli.stdout)
    assert envelope["manifest_sha256"] == result["manifest_sha256"]
    assert envelope["verification"]["status"] == "verified"
    failed_cli = subprocess.run(
        [*args, "--write"], capture_output=True, text=True, check=False, timeout=30
    )
    assert failed_cli.returncode == 2
    assert json.loads(failed_cli.stdout)["error"] == "gold_metadata_build_failed"
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    verified = metadata.verify_gold_metadata(values, first, result["manifest_sha256"])
    assert verified["status"] == "verified"
    catalogue = json.loads((first / "catalogue.json").read_text())
    assert catalogue["release_readiness"] == "blocked_unassessed_rights_and_publication"
    assert len(catalogue["packages"]) == 2
    assert sum(len(p["tables"]) for p in catalogue["packages"]) == 5
    assert_snapshot_projections(first, catalogue, values)
    for package in catalogue["packages"]:
        value = next(
            v for v in values if v.manifest_sha256 == package["manifest_sha256"]
        )
        for item in package["inventory"]:
            content = before[value.root / item["path"]]
            assert item["sha256"] == hashlib.sha256(content).hexdigest()
            assert item["bytes"] == len(content)
        assert package["rights"] == "not_evaluated"
    assert before == {p: p.read_bytes() for v in values for p in v.root.iterdir()}
    text = b"\n".join(p.read_bytes() for p in first.iterdir()).decode()
    assert str(tmp_path) not in text
    assert '"license"' not in text
    assert '"downloadURL"' not in text
    with pytest.raises(FileExistsError):
        metadata.export_gold_metadata(values, first, write=True)
    with pytest.raises(
        ValueError, match=r"gold_metadata_contract|source_hash_mismatch"
    ):
        metadata.export_gold_metadata(values, values[0].root, write=True)
    with pytest.raises(
        ValueError, match=r"gold_metadata_contract|source_hash_mismatch"
    ):
        metadata.project_gold_metadata(values + values)
    with pytest.raises(
        ValueError, match=r"gold_metadata_contract|source_hash_mismatch"
    ):
        metadata.project_gold_metadata(
            (metadata.GoldInput("unknown", values[0].root, values[0].manifest_sha256),)
        )
    with pytest.raises(
        ValueError, match=r"gold_metadata_contract|source_hash_mismatch"
    ):
        metadata.project_gold_metadata(())


def test_tampered_inputs_outputs_and_pins_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = packages(tmp_path, monkeypatch)
    target = tmp_path / "metadata"
    receipt = metadata.export_gold_metadata(values, target, write=True)
    with pytest.raises(
        ValueError, match=r"gold_metadata_contract|source_hash_mismatch"
    ):
        metadata.verify_gold_metadata(values, target, "0" * 64)
    (target / "catalogue.json").write_bytes(b"changed")
    with pytest.raises(
        ValueError, match=r"gold_metadata_contract|source_hash_mismatch"
    ):
        metadata.verify_gold_metadata(values, target, receipt["manifest_sha256"])
    fiscal_input = values[1]
    marker = fiscal_input.root / "manifest.json"
    original_marker = marker.read_bytes()
    manifest = json.loads(original_marker)
    for state in ("eligible_asserted", "restricted", None):
        altered = {**manifest, "rights": state}
        marker.write_text(json.dumps(altered))
        changed_pin = hashlib.sha256(marker.read_bytes()).hexdigest()
        changed = metadata.GoldInput(
            fiscal_input.profile, fiscal_input.root, changed_pin
        )
        with pytest.raises(ValueError, match="gold_metadata_contract"):
            metadata.project_gold_metadata((changed,))
    marker.write_bytes(original_marker)
    (values[0].root / "summary.json").write_bytes(b"changed")
    with pytest.raises(
        ValueError, match=r"gold_metadata_contract|source_hash_mismatch"
    ):
        metadata.export_gold_metadata(values, tmp_path / "not-created", write=True)
    assert not (tmp_path / "not-created").exists()


def test_offline_rdf_graphs_have_exact_inventory_and_derivation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parse_offline: Callable[[object], Graph],
) -> None:
    values = packages(tmp_path, monkeypatch)
    payloads = metadata.project_gold_metadata(values)
    dcat = parse_offline(json.loads(payloads["dcat.jsonld"]))
    prov = parse_offline(json.loads(payloads["prov.jsonld"]))
    assert isinstance(dcat, Graph)
    dcat_ns = Namespace("http://www.w3.org/ns/dcat#")
    prov_ns = Namespace("http://www.w3.org/ns/prov#")
    rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    spdx = Namespace("http://spdx.org/rdf/terms#")
    xsd = Namespace("http://www.w3.org/2001/XMLSchema#")
    assert len(list(dcat.subjects(rdf.type, dcat_ns.Dataset))) == 5
    assert len(list(dcat.subjects(rdf.type, dcat_ns.Distribution))) == 5
    catalogue = json.loads(payloads["catalogue.json"])
    for package in catalogue["packages"]:
        collection = URIRef(package["id"])
        assert (collection, rdf.type, prov_ns.Collection) in prov
        assert len(list(prov.objects(collection, prov_ns.hadMember))) == 5
        for table in package["tables"]:
            distribution = URIRef(table["id"] + ":distribution")
            checksum = next(dcat.objects(distribution, spdx.checksum))
            item = next(i for i in package["inventory"] if i["path"] == table["path"])
            assert (
                checksum,
                spdx.checksumValue,
                Literal(item["sha256"], datatype=xsd.hexBinary),
            ) in dcat
    assert {str(o) for o in prov.objects(None, prov_ns.wasDerivedFrom)} == {
        p["id"] for p in catalogue["packages"]
    }
