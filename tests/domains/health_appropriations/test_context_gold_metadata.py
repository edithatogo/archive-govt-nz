"""Context discovery covers verified payloads without inferring qualifications."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from jsonschema import Draft202012Validator
from tests.domains.health_appropriations.test_context_gold_verification import (
    _package,
    _rewrite_manifest,
)
from tests.domains.health_appropriations.test_fiscal_analytical_reports import queries

from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_reports as reports,
)
from archive_govt_nz.domains.health_appropriations import gold_metadata as metadata


def context_package(root: Path) -> metadata.GoldInput:
    root, _ = _package(root)
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    for name, entry in manifest["products"].items():
        if name.endswith(".parquet"):
            pq.write_table(
                pa.table(
                    {"period_token": ["2024/25", None], "status": ["observed", None]}
                ),
                root / name,
            )
            payload = (root / name).read_bytes()
            entry.update(
                bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), rows=2
            )
    return metadata.GoldInput(
        "context_source_separated", root, _rewrite_manifest(root, manifest)
    )


def test_context_products_have_complete_repeatable_metadata(tmp_path: Path) -> None:
    value = context_package(tmp_path / "context")
    before = {p.name: p.read_bytes() for p in value.root.iterdir()}
    payloads = metadata.project_gold_metadata((value,))
    assert payloads == metadata.project_gold_metadata((value,))
    for filename, schema_name in (
        ("citations.json", "health-gold-citations-v7"),
        ("changelog.json", "health-gold-changelog-v7"),
        ("source_drillthrough.json", "health-gold-source-drillthrough-v5"),
    ):
        schema = json.loads(
            (
                Path(__file__).parents[3] / "schemas" / (schema_name + ".schema.json")
            ).read_bytes()
        )
        Draft202012Validator(schema).validate(json.loads(payloads[filename]))
    catalogue = json.loads(payloads["catalogue.json"])
    package = catalogue["packages"][0]
    assert package["profile"] == "context_source_separated"
    assert {p["path"] for p in package["inventory"]} == set(before)
    assert len(package["tables"]) == 3
    assert all(t["null_status_rows"] == 1 for t in package["tables"])
    assert package["rights"] == "not_evaluated"
    assert package["source_reverification"] == "not_performed"
    references = json.loads(payloads["source_drillthrough.json"])["packages"][0][
        "references"
    ]
    assert len(references) == 5
    assert all(r["kind"] == "sha256" for r in references)
    assert "distinct source tokens" in payloads["DATASET_CARD.md"].decode()
    assert package["tables"][0]["observed_period_tokens"] == ["2024/25"]
    assert {p.name: p.read_bytes() for p in value.root.iterdir()} == before
    output = tmp_path / "metadata"
    receipt = metadata.export_gold_metadata((value,), output, write=True)
    assert (
        metadata.verify_gold_metadata((value,), output, receipt["manifest_sha256"])[
            "status"
        ]
        == "verified"
    )


def test_context_metadata_rejects_changed_output(tmp_path: Path) -> None:
    value = context_package(tmp_path / "context")
    (value.root / "context-quality-report.md").write_text("changed")
    with pytest.raises(ValueError, match="gold_metadata_contract"):
        metadata.project_gold_metadata((value,))


def test_report_products_are_discoverable_without_invented_recordsets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    values = queries()
    monkeypatch.setattr(
        reports.ops,
        "query_fiscal_analytical_gold",
        lambda *_, table, **__: values[table],
    )
    output = tmp_path / "reports"
    receipt = reports.export_fiscal_analytical_reports(
        tmp_path / "source", "a" * 64, output, write=True
    )
    value = metadata.GoldInput(
        "fiscal_analytical_reports", output, receipt["manifest_sha256"]
    )
    payloads = metadata.project_gold_metadata((value,))
    package = json.loads(payloads["catalogue.json"])["packages"][0]
    assert package["tables"] == []
    assert len(package["inventory"]) == len(list(output.iterdir()))
    assert package["source_references"] == [
        {"field_path": "/gold_manifest_sha256", "kind": "sha256", "value": "a" * 64}
    ]
    assert package["id"] in payloads["DATASET_CARD.md"].decode()
