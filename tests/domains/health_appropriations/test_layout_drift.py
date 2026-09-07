"""Profile-bound selection receipts reuse verified extraction, never rerun it."""

import hashlib
import json
from decimal import localcontext
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook
from tests.domains.health_appropriations.test_budget_reader import _rewrite

from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)
from archive_govt_nz.domains.health_appropriations.budget_reader import SCHEMAS
from archive_govt_nz.domains.health_appropriations.layout_drift import (
    compare_budget_layout,
)

HEADERS = (
    "Vote",
    "Year",
    "Department",
    "Appropriation Name",
    "Functional Classification",
    "Amount $000",
    "Amount Type",
    "Portfolio Name",
)


def build(
    root: Path,
    *,
    reverse: bool = False,
    rows: int = 1,
    vintage: str = "Budget-2026",
    extra: str = "Extra",
) -> tuple[Path, str]:
    """Produce synthetic input through the unchanged real adapter."""
    root.mkdir()
    book = Workbook()
    sheet = book.active
    assert sheet is not None
    sheet.title = "Raw Data"
    labels = [*HEADERS, extra]
    values = [
        "Health",
        2026,
        "Department",
        "Care",
        "Health",
        rows * 7,
        "Main Estimates",
        "Portfolio",
        None,
    ]
    sheet.append(labels[::-1] if reverse else labels)
    for _ in range(rows):
        sheet.append(values[::-1] if reverse else values)
    original = root / "original.xlsx"
    book.save(original)
    book.close()
    package = root / "package"
    normalize_budget_workbook(
        original,
        package,
        expected_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
        source_vintage=vintage,
        observed_at="2026-09-07T00:00:00Z",
        source_locator="synthetic.xlsx",
    )
    return package, hashlib.sha256((package / "MANIFEST.json").read_bytes()).hexdigest()


def compare(
    left: tuple[Path, str], right: tuple[Path, str], profile: str = "budget-2026/v1"
) -> dict:
    """Exercise the public boundary with explicit baseline and observation pins."""
    return compare_budget_layout(left[0], left[1], right[0], right[1], profile=profile)


def test_repeat_is_deterministic_nonmutating_and_not_source_verification(
    tmp_path: Path,
) -> None:
    package = build(tmp_path / "a")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = compare(package, package)
    assert result == compare(package, package)
    assert result["status"] == "matching_selection"
    assert result["changes"] == []
    assert result["reference_selection_matches"] is True
    assert result["reference"]["manifest_sha256"] == package[1]
    assert result["reference"] == result["observation"]
    assert result["original_reinspection"] == "not_performed"
    assert result["normalization_approval"] == "not_granted"
    assert result["rights_state"] == "not_evaluated"
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_receipt_binds_exact_column_coordinates_and_inputs(tmp_path: Path) -> None:
    package = build(tmp_path / "a")
    manifest = json.loads((package[0] / "MANIFEST.json").read_bytes())
    result = compare(package, package)
    observed = result["observation"]
    assert observed["source_object_sha256"] == manifest["source_object_sha256"]
    assert observed["output_sha256"] == manifest["output_sha256"]
    assert observed["counts"] == manifest["counts"]
    selection = observed["selection"]
    assert selection == {
        "sheet": "Raw Data",
        "header_row": 1,
        "first_data_row": 2,
        "predicate": "Vote equals Health",
        "columns": [
            {
                "column": index,
                "source_label_sha256": hashlib.sha256(label.encode()).hexdigest(),
                "target_field": field,
                "selection_role": "vote_filter" if index == 1 else "retained_field",
            }
            for index, (label, field) in enumerate(
                zip(
                    [*HEADERS, "Extra"],
                    [
                        "retained_only",
                        "year",
                        "department",
                        "appropriation_name",
                        "functional_classification",
                        "amount",
                        "amount_type",
                        "portfolio_name",
                        "retained_only",
                    ],
                    strict=True,
                ),
                1,
            )
        ],
    }
    assert (
        observed["selection_sha256"]
        == hashlib.sha256(
            json.dumps(
                selection, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
    )
    with localcontext() as context:
        context.prec = 2
        assert compare(package, package) == result
        assert context.prec == 2


def test_value_and_extent_change_are_not_column_drift(tmp_path: Path) -> None:
    result = compare(build(tmp_path / "a"), build(tmp_path / "b", rows=2))
    assert result["status"] == "matching_selection"
    assert (
        result["reference"]["manifest_sha256"]
        != result["observation"]["manifest_sha256"]
    )
    assert (
        result["reference"]["selection_sha256"]
        == result["observation"]["selection_sha256"]
    )
    assert result["reference"]["counts"] != result["observation"]["counts"]


@pytest.mark.parametrize("change", ["reverse", "extra"])
def test_column_drift_has_both_bound_signatures_without_raw_labels(
    tmp_path: Path, change: str
) -> None:
    observation = (
        build(tmp_path / "b", reverse=True)
        if change == "reverse"
        else build(tmp_path / "b", extra="PRIVATE SOURCE LABEL")
    )
    result = compare(build(tmp_path / "a"), observation)
    assert result["status"] == "selection_drift"
    assert result["changes"] == ["column_selection_changed"]
    assert result["reference_selection_matches"] is False
    assert (
        result["reference"]["selection_sha256"]
        != result["observation"]["selection_sha256"]
    )
    assert "PRIVATE SOURCE LABEL" not in json.dumps(result)


@pytest.mark.parametrize("profile", ["budget-2025/v1", "budget-2026/v1"])
def test_supported_profiles_reuse_adapter_and_schema_hashes(
    tmp_path: Path, profile: str
) -> None:
    package = build(tmp_path / "a", vintage="Budget-" + profile.split("-")[1][:4])
    result = compare(package, package, profile)
    assert result["profile"] == profile
    assert result["transformation_id"] == "budget-expenditure/v1"
    assert result["output_schema_sha256"] == {
        name: hashlib.sha256(schema.serialize().to_pybytes()).hexdigest()
        for name, schema in sorted(SCHEMAS.items())
    }


def test_unknown_profile_fails_before_io(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"^budget_layout_contract$"):
        compare((tmp_path / "missing", "a" * 64), (tmp_path, "b" * 64), "new/v1")


def test_cross_vintage_is_not_a_comparable_profile(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"^budget_layout_contract$"):
        compare(build(tmp_path / "a"), build(tmp_path / "b", vintage="Budget-2025"))


@pytest.mark.parametrize("fault", ["pin", "missing", "payload", "schema", "header"])
def test_reader_failures_cannot_receive_matching_selection(
    tmp_path: Path, fault: str
) -> None:
    package, pin = build(tmp_path / "a")
    if fault == "pin":
        pin = "0" * 64
    elif fault == "missing":
        (package / "MANIFEST.json").unlink()
    elif fault == "payload":
        (package / "field_lineage.parquet").write_bytes(b"corrupt")
    else:
        name = "field_lineage.parquet"
        links = pq.read_table(package / name).to_pylist()
        if fault == "schema":
            for row in links:
                row.pop("field")
        else:
            links[0]["source_coordinate"] = "'Raw Data'!Z2"
        pin = _rewrite(package, name, links)
    with pytest.raises(ValueError, match=r"^budget_layout_contract$"):
        compare((package, pin), (package, pin))
