"""Named canonical Gold queries preserve typed facts and source boundaries."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_canonical_gold_verification import (
    _package,
    _ready_server,
)

from archive_govt_nz import cli, mcp_server
from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_queries as query,
)

AMOUNT = Decimal("12.345678901234567890")


def source_value(field: pa.Field, year: int) -> object:
    kind = field.type
    values = (
        (pa.types.is_string(kind), f"{field.name}-{year}"),
        (pa.types.is_decimal(kind), AMOUNT),
        (pa.types.is_integer(kind), 1),
        (pa.types.is_boolean(kind), False),
        (pa.types.is_date(kind), date(year, 6, 30)),
        (pa.types.is_timestamp(kind), datetime(year, 7, 1, tzinfo=UTC)),
        (pa.types.is_list(kind), [f"id-{year}"]),
    )
    for matches, value in values:
        if matches:
            return value
    pytest.fail(f"fixture requires an explicit value for {field.name}: {kind}")


def source_row(schema: pa.Schema, year: int) -> dict[str, Any]:
    row = {field.name: source_value(field, year) for field in schema}
    row["source_vintage"] = "pinned-source-vintage"
    row["period_token"] = f"FY{year}/{str(year + 1)[-2:]}"
    for name in ("record_id", "input_record_id"):
        if name in row:
            row[name] = f"id-{year}"
    if "currency" in row and schema.field("currency").nullable:
        row["currency"] = None
    return row


def repin(root: Path) -> str:
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_bytes())
    for name, metadata in manifest["outputs"].items():
        payload = (root / name).read_bytes()
        metadata.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    marker.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    return hashlib.sha256(marker.read_bytes()).hexdigest()


@pytest.fixture
def package(tmp_path: Path) -> tuple[Path, str]:
    root, _ = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_bytes())
    del manifest["outputs"]["observations.parquet"]
    (root / "observations.parquet").unlink()
    for product, (name, schema) in query.PRODUCTS.items():
        table = pa.Table.from_pylist(
            [source_row(schema, year) for year in (2025, 2024)], schema=schema
        )
        pq.write_table(table, root / name, compression="zstd", use_dictionary=False)
        manifest["products"][product] = {"input_records": 2}
        manifest["outputs"][name] = {"rows": 2}
    marker.write_text(json.dumps(manifest))
    return root, repin(root)


def test_all_existing_fact_products_have_named_queries() -> None:
    assert set(query.PRODUCTS) == {
        "historical",
        "budget",
        "revenue",
        "pharmac",
        "moh",
        "crown_befu",
        "crown_hyefu",
        "fiscal_crown",
    }


@pytest.mark.parametrize("product", list(query.PRODUCTS))
def test_exact_named_query_retains_source_context_without_writes(
    package: tuple[Path, str], product: str
) -> None:
    root, pin = package
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    result = query.query_canonical_gold(root, pin, product=product, limit=1)
    assert result["status"] == "verified", result
    assert result["row_count"] == 1
    assert result["total_rows"] == 2
    assert result["truncated"] is True
    row = result["rows"][0]
    financial_period = "FY2024/25"
    assert row["period_token"] == financial_period
    assert set(row) == set(query.PRODUCTS[product][1].names)
    assert row["source_vintage"] == "pinned-source-vintage"
    amount = "total_amount" if product == "budget" else "amount"
    assert row[amount] == str(AMOUNT)
    if "currency" in row:
        assert row["currency"] is None
    if product == "budget":
        assert row["input_record_ids"] == ["id-2024"]
        assert row["department"] == "department-2024"
        assert row["portfolio"] == "portfolio-2024"
    if "observed_at" in row:
        assert row["observed_at"] == "2024-07-01T00:00:00+00:00"
    if product == "pharmac":
        assert row["funding_regime"] == "funding_regime-2024"
        assert row["budget_scope"] == "budget_scope-2024"
    assert result["package_report_caveats"] == {
        "classification_mapping": "not_inferred",
        "revision_interpretation": "not_assessed",
        "cross_source_comparison": "not_performed",
    }
    assert result["source_reverification"] == "not_performed"
    assert result["publication"] == "not_performed"
    assert before == {path.name: path.read_bytes() for path in root.iterdir()}


@pytest.mark.parametrize("case", ["pin", "payload", "schema", "row_count", "expanded"])
def test_invalid_packages_and_expansion_fail_closed(
    package: tuple[Path, str], monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    root, pin = package
    name = query.PRODUCTS["historical"][0]
    if case == "pin":
        pin = "0" * 64
    elif case == "payload":
        (root / name).write_bytes(b"changed")
    elif case == "schema":
        pq.write_table(pa.table({"wrong": [1]}), root / name)
        pin = repin(root)
    elif case == "row_count":
        marker = root / "MANIFEST.json"
        data = json.loads(marker.read_bytes())
        data["outputs"][name]["rows"] = 1
        marker.write_text(json.dumps(data))
        pin = repin(root)
    else:
        monkeypatch.setattr(query, "MAX_EXPANDED_BYTES", 1)
    result = query.query_canonical_gold(root, pin)
    assert result["status"] == "failed"
    assert str(root) not in json.dumps(result)


def test_missing_product_and_invalid_arguments_remain_explicit(
    package: tuple[Path, str],
) -> None:
    root, pin = package
    marker = root / "MANIFEST.json"
    data = json.loads(marker.read_bytes())
    del data["products"]["budget"]
    marker.write_text(json.dumps(data))
    pin = repin(root)
    result = query.query_canonical_gold(root, pin, product="budget")
    assert result["error"] == "canonical_gold_query_product_unavailable"
    invalid_cases: list[dict[str, Any]] = [
        {"product": "SELECT * FROM read_csv('/etc/passwd')"},
        {"limit": True},
    ]
    for changes in invalid_cases:
        assert (
            query.query_canonical_gold(root, pin, **changes)["error"]
            == "canonical_gold_query_invalid"
        )
        with pytest.raises(ValueError, match="arguments_invalid"):
            query.mcp_call(
                {
                    "package_dir": str(root),
                    "manifest_sha256": pin,
                    "product": "historical",
                    **changes,
                }
            )


def test_real_cli_parser_and_initialized_mcp_share_exact_readback(
    package: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, pin = package
    expected = query.query_canonical_gold(root, pin, product="budget")
    result = cli.app(
        [
            "health-appropriations-query-canonical-gold",
            str(root),
            pin,
            "--product",
            "budget",
        ],
        exit_on_error=False,
        result_action="return_value",
    )
    actual = json.loads(capsys.readouterr().out)
    assert result == 0
    actual.pop("command")
    assert actual == expected
    server = _ready_server()
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": query.TOOL_NAME,
                "arguments": {
                    "package_dir": str(root),
                    "manifest_sha256": pin,
                    "product": "budget",
                },
            },
        }
    )
    assert response is not None
    assert response["result"]["structuredContent"] == expected
    assert response["result"]["isError"] is False
    tool = next(
        tool for tool in mcp_server.list_tools() if tool["name"] == query.TOOL_NAME
    )
    assert tool["annotations"]["readOnlyHint"] is True
    failed = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": query.TOOL_NAME,
                "arguments": {
                    "package_dir": str(root),
                    "manifest_sha256": "0" * 64,
                    "product": "budget",
                },
            },
        }
    )
    assert failed is not None
    assert failed["result"]["isError"] is True
    assert failed["result"]["structuredContent"]["status"] == "failed"


@pytest.mark.parametrize("case", ["dictionary", "external_chunk"])
def test_unsafe_parquet_is_rejected_before_materialization(
    package: tuple[Path, str], monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    root, _ = package
    name, schema = query.PRODUCTS["historical"]
    if case == "dictionary":
        row = source_row(schema, 2024)
        row["source_label"] = "x" * 4096
        pq.write_table(pa.Table.from_pylist([row] * 100, schema=schema), root / name)
    else:
        metadata = pq.read_metadata(root / name)
        metadata.set_file_path("../outside.parquet")
        metadata.write_metadata_file(root / name)
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_bytes())
    manifest["outputs"][name]["rows"] = 100 if case == "dictionary" else 2
    marker.write_text(json.dumps(manifest))
    pin = repin(root)
    monkeypatch.setattr(query, "MAX_EXPANDED_BYTES", 64 * 1024)

    def unexpected_read(*_args: object, **_kwargs: object) -> None:
        pytest.fail("unsafe dictionary payload must be rejected before Arrow decoding")

    monkeypatch.setattr(pq.ParquetFile, "read", unexpected_read)
    result = query.query_canonical_gold(root, pin)
    expected = "resource_limit" if case == "dictionary" else "payload_invalid"
    assert result["error"] == f"canonical_gold_query_{expected}"
