"""Produce audited Arrow IPC and Parquet from existing source-verified SOC JSON.

The conversion never captures sources, changes original tokens, or deploys a Space.
Run against a pinned normalisation receipt, not unverified user-supplied rows.
PyArrow is the repository's existing declared dependency, imported only at export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SUPPORTED = frozenset({"census-long", "census-extended", "turnout-age"})
VALID_STATUSES = frozenset({"observed", "estimated", "provisional", "suppressed", "missing", "unavailable"})
NUMERIC = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def require(condition: bool, reason: str) -> None:
    """Fail closed on unsafe or unsupported source data."""
    if not condition:
        raise ValueError(reason)


def sha256(data: bytes) -> str:
    """Hash source bytes without depending on local path names."""
    return hashlib.sha256(data).hexdigest()


def verify_receipt(input_file: Path, receipt: dict[str, Any]) -> str:
    """Require the independent normalisation receipt to pin the input bytes."""
    name = input_file.name
    outputs = receipt.get("outputs")
    require(isinstance(outputs, dict) and name in outputs, "missing input receipt manifest")
    value = outputs[name]
    if isinstance(value, dict):
        expected = value.get("json_sha256")
    else:
        expected = value
    require(isinstance(expected, str) and bool(re.fullmatch(r"[a-f0-9]{64}", expected)),
            "invalid receipt hash")
    actual = sha256(input_file.read_bytes())
    require(actual == expected, "input hash differs from source normalisation receipt")
    return actual


def _decimal(value: object) -> Decimal:
    require(isinstance(value, str) and 0 < len(value) < 100 and bool(NUMERIC.fullmatch(value)),
            "invalid numeric token")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid numeric token") from exc
    require(number.is_finite(), "invalid numeric token")
    digits = len(number.as_tuple().digits)
    fractional = max(0, -number.as_tuple().exponent)
    integer_digits = max(0, digits - fractional)
    require(fractional <= 14 and integer_digits <= 24, "decimal exceeds documented Arrow precision")
    return number


def prepare_records(rows: list[dict[str, Any]], dataset: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Validate source grain, missingness and exact values before columnar export."""
    require(dataset in SUPPORTED, "unsupported dataset")
    require(isinstance(rows, list) and bool(rows), "empty or invalid input rows")
    columns = set(rows[0])
    require(all(isinstance(r, dict) and set(r) == columns for r in rows), "inconsistent source columns")
    require("synthetic" in columns and all(r["synthetic"] is False for r in rows),
            "synthetic observations are not eligible for empirical columnar output")
    prepared: list[dict[str, Any]] = []
    seen: set[tuple[object, ...]] = set()
    suppressed = 0
    for row in rows:
        prepared_row = dict(row)
        require(isinstance(row.get("source_sha256"), str)
                and bool(re.fullmatch("[a-f0-9]{64}", row["source_sha256"])),
                "missing original source digest")
        if dataset.startswith("census-"):
            key = (row.get("source_id"), row.get("sheet"), row.get("cell"))
            require(all(isinstance(v, str) and bool(v) for v in key), "invalid source cell identity")
            require(row.get("measurement_kind") in {"mean", "median", "count"}, "unknown measurement kind")
            status = row.get("status")
            require(status in VALID_STATUSES, "invalid source status")
            if status in {"suppressed", "missing", "unavailable"}:
                require(row.get("value") is None, "suppressed or missing value must be null")
                prepared_row["value_decimal"] = None
                suppressed += status == "suppressed"
            else:
                n = _decimal(row.get("value"))
                if row.get("measurement_kind") == "count":
                    require(n >= 0 and n == n.to_integral_value(), "invalid source count")
                prepared_row["value_decimal"] = n
            require(isinstance(row.get("raw_token"), (str, type(None))), "invalid raw token")
        else:
            key = (row.get("electorate_number"), row.get("age_band"))
            require(all(v is not None for v in key), "invalid turnout identity")
            require(row.get("election_year") == 2023, "incorrect election year")
            for field in ("voters", "nonvoters", "enrolled"):
                require(type(row.get(field)) is int and row[field] >= 0, "invalid turnout count")
            require(row["voters"] + row["nonvoters"] == row["enrolled"]
                    and row["enrolled"] > 0, "turnout counts do not reconcile")
            require(isinstance(row.get("turnout_percent"), (float, int)),
                    "invalid turnout rate")
        require(key not in seen, "duplicate source grain")
        seen.add(key)
        prepared.append(prepared_row)
    return prepared, {"observations": len(prepared), "suppressed": suppressed}


def _arrow_table(prepared: list[dict[str, Any]], *, dataset: str, input_hash: str) -> Any:
    """Bind explicit decimals/booleans/integers and original textual tokens."""
    import pyarrow as pa

    booleans = {"synthetic", "electoral_roll_population", "categories_additive", "additive_across_tables"}
    integers = {"electorate_number", "election_year", "source_row", "voters", "nonvoters", "enrolled"}
    floats = {"turnout_percent"}
    names = list(prepared[0].keys())
    fields = []
    for name in names:
        if name == "value_decimal":
            field_type = pa.decimal128(38, 14)
        elif name in booleans:
            field_type = pa.bool_()
        elif name in integers:
            field_type = pa.int64()
        elif name in floats:
            field_type = pa.float64()
        else:
            field_type = pa.string()
        fields.append(pa.field(name, field_type, nullable=True))
    metadata = {b"source_dataset": dataset.encode(),
                b"source_normalised_json_sha256": input_hash.encode(),
                b"publication_status": b"candidate_not_dashboard_published"}
    schema = pa.schema(fields, metadata=metadata)
    table = pa.Table.from_pylist(prepared, schema=schema)
    require(table.to_pylist() == prepared, "Arrow in-memory type or value parity failure")
    return table


def export_dataset(input_file: Path, receipt: dict[str, Any], output: Path,
                   dataset: str) -> dict[str, Any]:
    """Atomically create Parquet, Arrow and an independently checkable receipt."""
    require(dataset in SUPPORTED and input_file.name == dataset + ".json",
            "dataset/file identity mismatch")
    source_hash = verify_receipt(input_file, receipt)
    raw = input_file.read_bytes()

    def no_invalid_constant(v: str) -> Any:
        raise ValueError("non-finite JSON token")

    rows = json.loads(raw, parse_constant=no_invalid_constant)
    prepared, counts = prepare_records(rows, dataset)
    table = _arrow_table(prepared, dataset=dataset, input_hash=source_hash)
    import pyarrow as pa
    import pyarrow.parquet as pq

    require(not output.exists(), "output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".soc-columnar-", dir=output.parent))
    try:
        parquet_path = temp / (dataset + ".parquet")
        ipc_path = temp / (dataset + ".arrow")
        pq.write_table(table, parquet_path, compression="zstd", version="2.6",
                       use_dictionary=True, write_statistics=True)
        with pa.OSFile(str(ipc_path), "wb") as sink:
            with pa.ipc.new_file(sink, table.schema) as writer:
                writer.write_table(table)
        reread_parquet = pq.read_table(parquet_path)
        with pa.memory_map(str(ipc_path), "r") as source:
            reread_ipc = pa.ipc.open_file(source).read_all()
        require(reread_parquet.equals(table) and reread_ipc.equals(table),
                "Parquet/Arrow round-trip parity failure")
        result = {
            "schema_version": "soc-columnar-export-v1",
            "dataset": dataset,
            "rows": counts["observations"],
            "suppressed": counts["suppressed"],
            "input_json_sha256": source_hash,
            "source_status": "source_normalised_not_dashboard_published",
            "round_trip_verified": True,
            "arrow_version": pa.__version__,
            "columns": [{"name": f.name, "type": str(f.type)} for f in table.schema],
            "outputs": {
                path.name: {"sha256": sha256(path.read_bytes()), "bytes": path.stat().st_size}
                for path in (parquet_path, ipc_path)
            },
            "deployed_to_hugging_face": False,
        }
        (temp / "columnar-receipt.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        os.replace(temp, output)
        return result
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def main() -> int:
    """Export only a receipt-backed candidate set, with no HF write or overwrite."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalised", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--datasets", nargs="+", default=["census-long", "turnout-age"])
    args = parser.parse_args()
    receipt_path = args.normalised / "normalisation-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    require(set(args.datasets) <= SUPPORTED, "unsupported dataset requested")
    require(not args.output.exists(), "output already exists")
    args.output.mkdir(parents=True)
    report = {}
    try:
        for dataset in args.datasets:
            report[dataset] = export_dataset(
                args.normalised / (dataset + ".json"),
                receipt, args.output / dataset, dataset
            )
        (args.output / "export-inventory.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    except Exception:
        shutil.rmtree(args.output)
        raise
    print(json.dumps({"datasets": sorted(report), "rows": {k: v["rows"] for k, v in report.items()},
                      "publication": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
