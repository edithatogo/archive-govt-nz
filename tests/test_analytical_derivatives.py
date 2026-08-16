"""Tests for analytical columnar derivative generation."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

from __future__ import annotations

from typing import TYPE_CHECKING

import pyarrow.parquet as pq
from hypothesis import given, settings
from hypothesis import strategies as st

from archive_govt_nz.analytical_derivatives import (
    build_analytical_derivatives_suite,
    convert_tabular_bytes_to_parquet,
    materialize_tabular_derivative,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_convert_tabular_bytes_to_parquet(tmp_path: Path) -> None:
    """CSV bytes convert to valid readable Parquet table."""
    csv_data = b"id,name,value\n1,alpha,10.5\n2,beta,20.0\n3,gamma,30.25\n"
    output_path = tmp_path / "test.parquet"

    rows, cols, sha256_hash = convert_tabular_bytes_to_parquet(csv_data, output_path)

    assert rows == 3
    assert cols == 3
    assert len(sha256_hash) == 64
    assert output_path.is_file()

    table = pq.read_table(output_path)
    assert table.num_rows == 3
    assert table.column_names == ["id", "name", "value"]


@settings(deadline=None)
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=10000),
            st.text(
                alphabet=st.characters(categories=["L", "N"]), min_size=1, max_size=20
            ),
        ),
        min_size=1,
        max_size=50,
    )
)
def test_hypothesis_fuzz_csv_to_parquet(
    tmp_path_factory: pytest.TempPathFactory, data: list[tuple[int, str]]
) -> None:
    """Hypothesis fuzzing verifies arbitrary row structures roundtrip to Parquet."""
    tmp_path = tmp_path_factory.mktemp("fuzz_pq")
    header = "index,label\n"
    lines = [f"{idx},{lbl}\n" for idx, lbl in data]
    csv_bytes = (header + "".join(lines)).encode("utf-8")
    out_pq = tmp_path / "fuzz.parquet"

    rows, cols, _ = convert_tabular_bytes_to_parquet(csv_bytes, out_pq)
    assert rows == len(data)
    assert cols == 2

    table = pq.read_table(out_pq)
    assert table.num_rows == len(data)


def test_materialize_tabular_derivative(tmp_path: Path) -> None:
    """Derivative engine ingests CAS object and emits Parquet."""
    store = ContentAddressedStore(tmp_path / "objects")
    csv_bytes = b"year,metric,count\n2024,safety,100\n2025,safety,120\n"
    receipt = store.put_bytes(csv_bytes)

    item = {
        "resource_id": "res-1",
        "dataset_id": "ds-1",
        "format": "CSV",
        "sha256": receipt.sha256,
    }

    deriv_dir = tmp_path / "derivatives"
    result = materialize_tabular_derivative(item, store, deriv_dir)

    assert result.status == "materialized"
    assert result.row_count == 2
    assert result.column_count == 3
    assert result.derivative_path.is_file()


def test_build_analytical_derivatives_suite(tmp_path: Path) -> None:
    """Batch suite processes tabular files and ignores non-tabular resources."""
    store = ContentAddressedStore(tmp_path / "objects")
    csv_bytes = b"col1,col2\nval1,val2\n"
    receipt = store.put_bytes(csv_bytes)

    captures = [
        {
            "resource_id": "res-1",
            "dataset_id": "ds-1",
            "format": "CSV",
            "sha256": receipt.sha256,
        },
        {
            "resource_id": "res-2",
            "dataset_id": "ds-2",
            "format": "PDF",
            "sha256": "fake-pdf-hash",
        },
    ]

    deriv_dir = tmp_path / "derivatives"
    manifest = build_analytical_derivatives_suite(captures, store, deriv_dir)

    assert manifest["total_tabular_evaluated"] == 1
    assert manifest["materialized_count"] == 1
    assert len(manifest["derivatives"]) == 1
    assert manifest["derivatives"][0]["resource_id"] == "res-1"


def test_materialize_tabular_derivative_errors(tmp_path: Path) -> None:
    """Error paths handle missing CAS object and malformed content cleanly."""
    store = ContentAddressedStore(tmp_path / "objects")
    deriv_dir = tmp_path / "derivatives"

    # 1. Missing CAS Object
    missing_item = {
        "resource_id": "res-missing",
        "dataset_id": "ds-1",
        "format": "CSV",
        "sha256": "0" * 64,
    }
    res_missing = materialize_tabular_derivative(missing_item, store, deriv_dir)
    assert res_missing.status == "source_object_missing"

    # 2. Conversion Failure
    bad_bytes = b"\x00\xff\xfe\xfa\xfb\xfc"
    receipt = store.put_bytes(bad_bytes)
    bad_item = {
        "resource_id": "res-bad",
        "dataset_id": "ds-1",
        "format": "CSV",
        "sha256": receipt.sha256,
    }
    res_bad = materialize_tabular_derivative(bad_item, store, deriv_dir)
    assert res_bad.status == "conversion_failed"
