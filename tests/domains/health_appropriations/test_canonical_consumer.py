"""Verified canonical packages are the direct analytical input boundary."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pytest
from tests.domains.health_appropriations.test_budget_classification import inputs
from tests.domains.health_appropriations.test_historical_snapshot import (
    _package as historical_raw_package,
)

from archive_govt_nz.domains.health_appropriations import canonical_consumer
from archive_govt_nz.domains.health_appropriations.budget_canonical_export import (
    export_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.canonical_consumer import (
    HISTORICAL_NOMINAL_SCHEMA,
    NOMINAL_BUDGET_SCHEMA,
    query_historical_nominal,
    query_nominal_budget,
)
from archive_govt_nz.domains.health_appropriations.historical_canonical_export import (
    export_historical_canonical,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)


def _package(tmp_path: Path) -> CanonicalPackageInput:
    source = inputs(tmp_path)
    output = tmp_path / "canonical"
    export_budget_appropriations(
        tmp_path / "package",
        source["manifest_sha256"],
        tmp_path / "source.xlsx",
        output,
        dry_run=False,
    )
    marker = output / "LOCAL_BUDGET.json"
    return CanonicalPackageInput(
        kind="budget",
        root=output,
        marker_sha256=hashlib.sha256(marker.read_bytes()).hexdigest(),
        original=tmp_path / "source.xlsx",
        raw_root=tmp_path / "package",
        raw_manifest_sha256=source["manifest_sha256"],
    )


def _historical_package(tmp_path: Path) -> CanonicalPackageInput:
    raw, original, pin = historical_raw_package(tmp_path)
    output = tmp_path / "historical-canonical"
    export_historical_canonical(raw, original, pin, output, write=True)
    marker = output / "LOCAL_CANONICAL.json"
    return CanonicalPackageInput(
        kind="historical",
        root=output,
        marker_sha256=hashlib.sha256(marker.read_bytes()).hexdigest(),
        original=original,
        raw_root=raw,
        raw_manifest_sha256=pin,
    )


def test_exact_nominal_query_retains_source_labels_and_lineage(tmp_path: Path) -> None:
    package = _package(tmp_path)
    before = {
        path: path.read_bytes()
        for path in (
            package.original,
            *package.root.iterdir(),
            *package.raw_root.iterdir(),
        )
    }
    table, receipt = query_nominal_budget((package,))
    assert table.schema.equals(NOMINAL_BUDGET_SCHEMA, check_metadata=True)
    assert table.num_rows == 1
    row = table.to_pylist()[0]
    assert row["total_amount"] == Decimal("246.000000000000000000")
    assert row["input_count"] == 2
    assert row["source_label"] == "Care"
    assert row["vote"] == row["department"] == row["portfolio"] == "Health"
    assert row["unit"] == "NZD_thousands"
    assert len(row["input_record_ids"]) == 2
    assert receipt == query_nominal_budget((package,))[1]
    assert receipt["currency_state"] == "unknown"
    assert receipt["price_basis_state"] == "unknown"
    assert receipt["classification_mapping"] == "not_performed"
    assert before == {path: path.read_bytes() for path in before}


def test_wrong_kind_and_repeated_identity_fail_closed(tmp_path: Path) -> None:
    package = _package(tmp_path)
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget((package, package))
    wrong = CanonicalPackageInput(
        kind="classification",
        root=package.root,
        marker_sha256=package.marker_sha256,
        original=package.original,
        raw_root=package.raw_root,
        raw_manifest_sha256=package.raw_manifest_sha256,
    )
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget((wrong,))


def test_alternative_packages_for_one_vintage_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = _package(tmp_path)
    canonical, receipt = canonical_consumer.read_verified_canonical_tables(package)
    table = canonical["appropriation_fact"]
    ids = [f"alternative-{index}" for index in range(table.num_rows)]
    alternative = table.set_column(
        table.schema.get_field_index("record_id"), "record_id", pa.array(ids)
    )
    responses = iter(
        ((canonical, receipt), ({"appropriation_fact": alternative}, receipt))
    )
    monkeypatch.setattr(
        canonical_consumer,
        "read_verified_canonical_tables",
        lambda _package: next(responses),
    )

    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget((package, package))


def test_historical_query_is_an_identity_projection(tmp_path: Path) -> None:
    package = _historical_package(tmp_path)
    table, receipt = query_historical_nominal((package,))
    assert table.schema.equals(HISTORICAL_NOMINAL_SCHEMA, check_metadata=True)
    assert table.num_rows == receipt["input_records"]
    assert receipt["aggregation"] == "none"
    assert receipt["currency_state"] == "source_assertion_preserved"
    assert receipt["price_basis_state"] == "unknown"
    assert all(
        row["formula_policy"] == "identity_projection_no_cross_source_aggregation/v1"
        for row in table.to_pylist()
    )


def test_historical_query_rejects_budget_package(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_historical_nominal((_package(tmp_path),))


@pytest.mark.parametrize("packages", [[], (), [object()]])
def test_exact_tuple_boundary(packages: object) -> None:
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget(packages)  # type: ignore[arg-type]
