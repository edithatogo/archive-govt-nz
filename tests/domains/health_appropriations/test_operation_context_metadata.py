"""Operation Gold metadata retains schemas, null statuses and source verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from jsonschema import Draft202012Validator
from tests.domains.health_appropriations.test_operation_context_gold import _inputs

from archive_govt_nz.domains.health_appropriations import (
    gold_discovery_profiles as discovery,
)
from archive_govt_nz.domains.health_appropriations import gold_metadata as metadata
from archive_govt_nz.domains.health_appropriations import operation_context_gold as gold


def test_operation_gold_metadata_describes_all_tables_and_nullable_source_statuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs, source_root = _inputs(tmp_path, monkeypatch)
    package = tmp_path / "gold"
    receipt = gold.export_operation_context_gold(
        inputs, source_root, package, write=True
    )
    value = metadata.OperationContextGoldInput(
        package, receipt["manifest_sha256"], inputs, source_root
    )
    payloads = metadata.project_gold_metadata((value,))
    profiles = tmp_path / "discovery"
    profile_receipt = discovery.export_profiles((value,), profiles, write=True)
    assert (
        discovery.verify_profiles(
            (value,), profiles, profile_receipt["manifest_sha256"]
        )["status"]
        == "verified_local_candidates"
    )
    croissant = json.loads((profiles / "croissant.json").read_bytes())
    assert len(croissant["cr:recordSet"]) == 13

    catalogue = json.loads(payloads["catalogue.json"])
    assert catalogue["schema_version"] == "archive-govt-nz.health-gold-metadata/v5"
    described = catalogue["packages"][0]
    assert described["profile"] == "operation_context"
    assert described["source_reverification"] == "performed_from_pinned_Bronze"
    assert described["rights"] == "not_evaluated"
    assert described["publication"] == "not_performed"
    tables = {table["path"]: table for table in described["tables"]}
    expected = {name for name in receipt["products"] if name.endswith(".parquet")}
    assert set(tables) == expected
    assert len(tables) == 13
    for name, table in tables.items():
        original = pq.read_table(package / name)
        assert table["rows"] == original.num_rows
        assert table["schema_ipc_hex"] == original.schema.serialize().to_pybytes().hex()
    observations = pq.read_table(package / "context_observations.parquet")
    status = observations["status"].to_pylist()
    descriptor = tables["context_observations.parquet"]
    assert descriptor["null_status_rows"] == status.count(None) > 0
    assert descriptor["states"] == {
        token: status.count(token) for token in set(status) if token is not None
    }
    assert tables["canonical_wage_lineage.parquet"]["record_kind"] == "field_lineage"
    inventory = {item["path"]: item for item in described["inventory"]}
    assert set(inventory) == {*receipt["products"], "MANIFEST.json"}
    assert inventory["MANIFEST.json"]["sha256"] == receipt["manifest_sha256"]
    assert str(tmp_path).encode() not in b"".join(payloads.values())
    for filename, schema_name in (
        ("citations.json", "health-gold-citations-v5.schema.json"),
        ("changelog.json", "health-gold-changelog-v5.schema.json"),
        ("source_drillthrough.json", "health-gold-source-drillthrough-v3.schema.json"),
    ):
        schema = json.loads(
            (Path(__file__).parents[3] / "schemas" / schema_name).read_text()
        )
        Draft202012Validator(schema).validate(json.loads(payloads[filename]))
    references = described["source_references"]
    assert any(item["kind"] == "recorded_https_locator" for item in references)
    manifest = json.loads((package / "MANIFEST.json").read_text())
    for reference in references:
        selected = manifest
        for raw_token in reference["field_path"].split("/")[1:]:
            token = raw_token.replace("~1", "/").replace("~0", "~")
            selected = (
                selected[int(token)] if isinstance(selected, list) else selected[token]
            )
        assert selected == reference["value"]


def test_metadata_package_repeat_readback_and_forged_rights_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs, source_root = _inputs(tmp_path, monkeypatch)
    package = tmp_path / "gold"
    gold_receipt = gold.export_operation_context_gold(
        inputs, source_root, package, write=True
    )
    value = metadata.OperationContextGoldInput(
        package, gold_receipt["manifest_sha256"], inputs, source_root
    )
    values = (value,)
    output = tmp_path / "metadata"
    assert metadata.export_gold_metadata(values, output)["status"] == "dry_run"
    assert not output.exists()
    written = metadata.export_gold_metadata(values, output, write=True)
    assert (
        metadata.verify_gold_metadata(values, output, written["manifest_sha256"])[
            "status"
        ]
        == "verified"
    )
    repeated = tmp_path / "repeat"
    metadata.export_gold_metadata(values, repeated, write=True)
    assert {p.name: p.read_bytes() for p in output.iterdir()} == {
        p.name: p.read_bytes() for p in repeated.iterdir()
    }
    for protected in (
        output,
        source_root / "metadata",
        inputs[0].package_dir / "metadata",
        package / "metadata",
    ):
        with pytest.raises(ValueError, match="gold_metadata_contract"):
            metadata.export_gold_metadata(values, protected, write=True)
    citation = output / "citations.json"
    forged = json.loads(citation.read_text())
    forged["records"][0]["rights"] = "eligible"
    citation.write_text(json.dumps(forged))
    marker = output / "MANIFEST.json"
    changed = json.loads(marker.read_text())
    changed["payloads"]["citations.json"] = {
        "sha256": hashlib.sha256(citation.read_bytes()).hexdigest(),
        "bytes": len(citation.read_bytes()),
    }
    marker.write_text(json.dumps(changed))
    forged_pin = hashlib.sha256(marker.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="gold_metadata_contract"):
        metadata.verify_gold_metadata(values, output, forged_pin)


def test_metadata_rejects_a_wrong_independent_operation_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs, source_root = _inputs(tmp_path, monkeypatch)
    package = tmp_path / "gold"
    receipt = gold.export_operation_context_gold(
        inputs, source_root, package, write=True
    )
    bad_inputs = (replace(inputs[0], manifest_sha256="0" * 64), *inputs[1:])
    value = metadata.OperationContextGoldInput(
        package, receipt["manifest_sha256"], bad_inputs, source_root
    )
    before = hashlib.sha256((package / "MANIFEST.json").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="gold_metadata_contract"):
        metadata.project_gold_metadata((value,))
    assert (
        hashlib.sha256((package / "MANIFEST.json").read_bytes()).hexdigest() == before
    )
