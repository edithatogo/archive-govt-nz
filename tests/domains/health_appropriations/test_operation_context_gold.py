"""Gold consumes verified canonical context and reconciles saved products."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_context_operation_canonical import (
    CASES,
    _fixture,
)

from archive_govt_nz.domains.health_appropriations import (
    context_gold,
)
from archive_govt_nz.domains.health_appropriations import (
    operation_context_gold as gold,
)
from archive_govt_nz.domains.health_appropriations.context_gold_verification import (
    verify_context_gold_package,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import encode_json
from archive_govt_nz.schemas.health_recordset_normalization import validate_table


def _inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[tuple[gold.OperationContextInput, ...], Path]:
    source_root = tmp_path / "sources"
    source_root.mkdir()
    inputs = []
    identities = {}
    for index, case in enumerate(CASES):
        root = tmp_path / f"profile-{index}"
        root.mkdir()
        request, _, _, _ = _fixture(root, monkeypatch, case)
        original = source_root / request.expected_sha256[:2] / request.expected_sha256
        original.parent.mkdir(exist_ok=True)
        original.write_bytes(request.source.read_bytes())
        family, series = {
            "cpiq-se9a/v1": ("cpi", "CPIQ.SE9A"),
            "population-annual-mean-context/v1": (
                "population",
                "DPE056AA:Mean year ended:Total:Total All Ages:Annual-Jun",
            ),
            "qes-june2026-table8/v1": ("wage", "QEMQ.SASZ9A"),
            "gdp-expenditure-actual-2026q1/v1": ("gdp", "SNEQ/SG03AB01GE00S900"),
            "gdp-expenditure-actual-2026q2/v1": ("gdp", "SNEQ/SG03AB01GE00S900"),
        }[case.profile]
        identities[(family, request.expected_sha256)] = (series, case.vintage)
        inputs.append(
            gold.OperationContextInput(
                case.profile,
                request.output_dir,
                hashlib.sha256(
                    (request.output_dir / "MANIFEST.json").read_bytes()
                ).hexdigest(),
            )
        )
    monkeypatch.setattr(context_gold, "_EXPECTED_SOURCE_IDENTITIES", identities)
    return tuple(inputs), source_root


def _tree(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.iterdir()
    }


def test_gold_reconciles_canonical_products_status_and_repeat_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, sources = _inputs(tmp_path, monkeypatch)
    output = tmp_path / "gold"
    before = [_tree(item.package_dir) for item in inputs]
    planned = gold.export_operation_context_gold(inputs, sources, output)
    assert planned["status"] == "planned"
    assert not output.exists()
    written = gold.export_operation_context_gold(inputs, sources, output, write=True)
    assert written["status"] == "complete"
    pin = written["manifest_sha256"]
    verified = gold.verify_operation_context_gold(
        inputs, sources, output, manifest_sha256=pin
    )
    assert verified["status"] == "verified"
    assert verified["verification_scope"] == "source_regenerated_canonical_products"
    assert verify_context_gold_package(output, pin)["status"] == "failed"
    rows = gold.query_operation_context_observations(
        inputs, sources, output, manifest_sha256=pin
    ).to_pylist()
    assert len(rows) == 168
    assert len({row["input_record_id"] for row in rows}) == len(rows)
    provisional = [
        row for row in rows if row["family"] == "population" and row["status"] == "P"
    ]
    assert len(provisional) == 2
    assert {row["admission_reason"] for row in provisional} == {"provisional"}
    assert all(
        row["admission"] == "excluded_from_numeric_series" for row in provisional
    )
    manifest = json.loads((output / "MANIFEST.json").read_text())
    assert len(manifest["input_operations"]) == 5
    assert (
        manifest["source_family_policy"]
        == "separate_series_vintages_no_joins_or_pooling"
    )
    assert manifest["rights_state"] == "not_evaluated"
    assert manifest["denominator_selection"] == "not_performed"
    assert manifest["currency_admission"] == "not_performed"
    for item in manifest["input_operations"]:
        facts = pq.read_table(output / item["canonical_facts_file"])
        lineage = pq.read_table(output / item["canonical_lineage_file"])
        validate_table(
            item["projection"]["recordset"],
            facts,
            version=item["projection"]["recordset_version"],
        )
        validate_table(
            "field_lineage", lineage, version=item["projection"]["recordset_version"]
        )
        assert set(lineage.column("target_record_id").to_pylist()) <= set(
            facts.column("record_id").to_pylist()
        )
    repeated = tmp_path / "repeat"
    gold.export_operation_context_gold(
        tuple(reversed(inputs)), sources, repeated, write=True
    )
    assert _tree(repeated) == _tree(output)
    assert [_tree(item.package_dir) for item in inputs] == before
    with pytest.raises(ValueError, match="operation_context_gold_invalid"):
        gold.export_operation_context_gold(inputs, sources, output, write=True)


@pytest.mark.parametrize(
    "mutation", ["fact", "report", "metadata", "pin", "extra", "input_pin"]
)
def test_readback_rejects_tampering_even_with_rehashed_candidate_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    inputs, sources = _inputs(tmp_path, monkeypatch)
    output = tmp_path / "gold"
    result = gold.export_operation_context_gold(inputs, sources, output, write=True)
    pin = result["manifest_sha256"]
    path = output / "MANIFEST.json"
    manifest = json.loads(path.read_text())
    if mutation in {"fact", "report"}:
        name = (
            "context_observations.parquet"
            if mutation == "fact"
            else "context-quality-report.md"
        )
        (output / name).write_bytes(b"forged")
        manifest["products"][name]["sha256"] = hashlib.sha256(b"forged").hexdigest()
        manifest["products"][name]["bytes"] = 6
    elif mutation == "metadata":
        manifest["denominator_selection"] = "approved"
    elif mutation == "pin":
        pin = "a" * 64
    elif mutation == "extra":
        (output / "extra").write_bytes(b"extra")
    else:
        inputs = (replace(inputs[0], manifest_sha256="a" * 64), *inputs[1:])
    if mutation in {"fact", "report", "metadata"}:
        path.write_text(encode_json(manifest) + "\n")
        pin = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="operation_context_gold_invalid"):
        gold.verify_operation_context_gold(inputs, sources, output, manifest_sha256=pin)


def test_refuses_missing_duplicate_profiles_overlaps_and_partial_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, sources = _inputs(tmp_path, monkeypatch)
    for bad in (inputs[:-1], (inputs[0], *inputs[:-1])):
        with pytest.raises(ValueError, match="operation_context_gold_invalid"):
            gold.export_operation_context_gold(bad, sources, tmp_path / "out")
    for bad_output in (sources / "out", inputs[0].package_dir / "out"):
        with pytest.raises(ValueError, match="operation_context_gold_invalid"):
            gold.export_operation_context_gold(inputs, sources, bad_output, write=True)
    partial = tmp_path / "partial"
    partial.mkdir()
    (partial / "context_observations.parquet").write_bytes(b"partial")
    with pytest.raises(ValueError, match="operation_context_gold_invalid"):
        gold.export_operation_context_gold(inputs, sources, partial, write=True)
    assert not (partial / "MANIFEST.json").exists()


def test_readback_bounds_directory_membership_before_scanning_extra_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs, sources = _inputs(tmp_path, monkeypatch)
    output = tmp_path / "gold"
    result = gold.export_operation_context_gold(inputs, sources, output, write=True)
    original = Path.iterdir

    def entries(path: Path) -> Iterator[Path]:
        yield from original(path)
        if path == output:
            yield output / "unexpected"
            pytest.fail("readback scanned past the first unexpected entry")

    monkeypatch.setattr(Path, "iterdir", entries)
    with pytest.raises(ValueError, match="operation_context_gold_invalid"):
        gold.verify_operation_context_gold(
            inputs, sources, output, manifest_sha256=result["manifest_sha256"]
        )
