"""Pinned Budget comparison Gold, reports and bounded read-only operations."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from itertools import islice
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from jsonschema import Draft202012Validator
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from archive_govt_nz.domains.health_appropriations import (
    budget_vintage_comparison as comparison,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

VERSION = "archive-govt-nz.budget-comparison-gold/v1"
QUERY_VERSION = "archive-govt-nz.budget-comparison-query/v1"
TOOL_NAME = "health_appropriations_query_budget_comparison"
MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 200
SCHEMA = pa.schema(
    [
        pa.field(
            field.name,
            pa.list_(pa.field("element", field.type.value_type))
            if pa.types.is_list(field.type)
            else field.type,
        )
        for field in comparison.SCHEMA
    ]
)
PAYLOADS = {"comparison.parquet", "summary.json", "README.md", "differences.png"}
INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["package_dir", "manifest_sha256"],
    "properties": {
        "package_dir": {"type": "string", "minLength": 1, "maxLength": 4096},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "limit": {"type": "integer", "minimum": 1, "maximum": MAX_ROWS},
    },
}
OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "status"],
    "properties": {
        "schema_version": {"const": QUERY_VERSION},
        "status": {"enum": ["verified", "failed"]},
        "error": {"type": "string"},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "rows": {
            "type": "array",
            "maxItems": MAX_ROWS,
            "items": {
                "type": "object",
                "required": SCHEMA.names,
                "additionalProperties": False,
                "properties": {
                    name: {
                        "type": ["string", "integer", "null", "array"],
                        "items": {"type": ["string", "integer", "null"]},
                    }
                    for name in SCHEMA.names
                },
            },
        },
        "row_count": {"type": "integer", "minimum": 0, "maximum": MAX_ROWS},
        "total_rows": {"type": "integer", "minimum": 0, "maximum": MAX_ROWS},
        "truncated": {"type": "boolean"},
        "decimal_encoding": {"const": "exact_string"},
        "date_encoding": {"const": "iso8601"},
        "verification_scope": {
            "const": "pinned_gold_payloads_schema_and_report_projection"
        },
        "source_reverification": {"const": "not_performed"},
        "source_bindings": {"type": "object"},
        "caveats": {"type": "array", "items": {"type": "string"}},
        "semantic_comparability": {"const": "not_established"},
        "rights": {"const": "not_evaluated"},
        "publication": {"const": "not_performed"},
    },
    "allOf": [
        {
            "if": {"properties": {"status": {"const": "verified"}}},
            "then": {
                "required": [
                    "manifest_sha256",
                    "rows",
                    "row_count",
                    "total_rows",
                    "truncated",
                    "decimal_encoding",
                    "date_encoding",
                    "verification_scope",
                    "source_reverification",
                    "source_bindings",
                    "caveats",
                    "semantic_comparability",
                    "rights",
                    "publication",
                ]
            },
            "else": {"required": ["error"]},
        }
    ],
}
MCP_TOOL = {
    "name": TOOL_NAME,
    "description": (
        "Verify a pinned local Budget comparison Gold package and return "
        "bounded exact rows. Arithmetic diagnostics only; no source "
        "re-verification, mapping, rights assessment or publication."
    ),
    "inputSchema": INPUT_SCHEMA,
    "outputSchema": OUTPUT_SCHEMA,
    "annotations": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


def _require(condition: object) -> None:
    if not condition:
        message = "budget_comparison_gold_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, default=str, sort_keys=True, indent=2, ensure_ascii=False)
        + "\n"
    ).encode()


def _rows(table: pa.Table) -> list[dict[str, Any]]:
    return json.loads(_json(table.to_pylist()))


def _summary(table: pa.Table, receipt: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(table)
    points = sum(r["state"] == "unique_literal_pair" for r in rows)
    return {
        "schema_version": VERSION,
        "rows": rows,
        "comparison_receipt": receipt,
        "plot_points": points,
        "plot_excluded_groups": len(rows) - points,
        "plot_display": "float_only_exact_values_retained_in_table_and_summary",
        "semantic_comparability": "not_established",
        "rights": "not_evaluated",
        "publication": "not_performed",
    }


def _report(summary: dict[str, Any]) -> bytes:
    lines = [
        "# Budget estimate-transition diagnostics",
        "",
        (
            "Exact source values and coordinates are in comparison.parquet "
            "and summary.json."
        ),
        "",
        (
            "Differences are later minus earlier in NZD thousands. Literal "
            "pairs do not establish restated comparability or budget "
            "performance. Unmatched and ambiguous groups are retained without "
            "a difference. June flow dates do not establish appropriation "
            "authority duration."
        ),
        "",
        "Source caveats: " + ", ".join(summary["comparison_receipt"]["caveats"]) + ".",
        "",
        "| Plot group | Fiscal year end | State | Difference (NZD thousands) |",
        "| --- | --- | --- | --- |",
    ]
    for number, row in enumerate(summary["rows"], 1):
        value = row["difference_later_minus_earlier"]
        lines.append(
            f"| G{number:03d} | {row['period_end']} | {row['state']} | "
            f"{value if value is not None else 'not computed'} |"
        )
    lines.extend(
        [
            "",
            (
                "Group numbers follow deterministic table order. Summary rows "
                "retain all dimensions, both input IDs and source row coordinates."
            ),
            "Rights are not evaluated; publication is not performed.",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def _plot(summary: dict[str, Any]) -> bytes:
    figure = Figure(figsize=(12, 5), dpi=120)
    canvas = FigureCanvasAgg(figure)
    axis = figure.subplots()
    for year, color in [(2025, "#2166ac"), (2026, "#b35806")]:
        selected = [
            (i + 1, r)
            for i, r in enumerate(summary["rows"])
            if r["year"] == year and r["state"] == "unique_literal_pair"
        ]
        axis.scatter(
            [i for i, _ in selected],
            [float(r["difference_later_minus_earlier"]) for _, r in selected],
            label=f"Year ended June {year}",
            color=color,
            s=25,
        )
    axis.axhline(0, color="#555555", linewidth=0.7)
    axis.set(
        xlabel="Deterministic group number (G001 etc.; see summary)",
        ylabel="Later minus earlier (NZD thousands)",
        title="Budget literal-pair arithmetic diagnostics",
    )
    axis.legend()
    figure.text(
        0.5,
        0.015,
        (
            "Unmatched/ambiguous groups excluded; comparability not "
            "established; exact values retained."
        ),
        ha="center",
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.045, 1, 1))
    output = BytesIO()
    canvas.print_png(output, metadata={"Software": VERSION})
    return output.getvalue()


def export_budget_comparison(
    earlier: comparison.BudgetComparisonInput,
    later: comparison.BudgetComparisonInput,
    output_dir: Path,
    *,
    write: bool = False,
) -> dict[str, Any]:
    """Reverify comparison inputs; dry run by default, exclusive output on write."""
    output = output_dir.resolve()
    for source in (earlier, later):
        for path in (source.original, source.package):
            resolved = path.resolve()
            _require(
                not output.is_relative_to(resolved)
                and not resolved.is_relative_to(output)
            )
    result = comparison.compare_budget_vintages(earlier, later)
    _require(result.table.num_rows <= MAX_ROWS)
    summary = _summary(result.table, result.receipt)
    base = {
        "schema_version": VERSION,
        "row_count": result.table.num_rows,
        "plot_points": summary["plot_points"],
        "plot_excluded_groups": summary["plot_excluded_groups"],
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
    if not write:
        return {**base, "status": "dry_run"}
    output_dir.mkdir(parents=True, exist_ok=False)
    stream = BytesIO()
    pq.write_table(result.table.cast(SCHEMA), stream)
    payloads = {
        "comparison.parquet": stream.getvalue(),
        "summary.json": _json(summary),
        "README.md": _report(summary),
        "differences.png": _plot(summary),
    }
    _require(all(len(payload) <= MAX_BYTES for payload in payloads.values()))
    for name, payload in payloads.items():
        with (output_dir / name).open("xb") as handle:
            handle.write(payload)
    manifest = {
        "schema_version": VERSION,
        "status": "complete",
        "payloads": {
            name: {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
            for name, payload in payloads.items()
        },
        "row_count": result.table.num_rows,
        "verification_scope": "pinned_gold_payloads_schema_and_report_projection",
        "source_reverification": "not_performed_by_reader",
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
    marker = _json(manifest)
    with (output_dir / "MANIFEST.json").open("xb") as handle:
        handle.write(marker)
    pin = hashlib.sha256(marker).hexdigest()
    read_budget_comparison(output_dir, pin)
    return {**base, "status": "written", "manifest_sha256": pin}


def read_budget_comparison(
    package_dir: Path, manifest_sha256: str
) -> tuple[pa.Table, dict[str, Any]]:
    """Check closed inventory, capped snapshots, schema and report projection."""
    _require(package_dir.is_dir() and not package_dir.is_symlink())
    _require(
        {p.name for p in islice(package_dir.iterdir(), 6)}
        == PAYLOADS | {"MANIFEST.json"}
    )
    _require(
        all(not (package_dir / n).is_symlink() for n in PAYLOADS | {"MANIFEST.json"})
    )
    manifest = json.loads(
        verified_snapshot(
            package_dir / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES
        )
    )
    _require(
        set(manifest)
        == {
            "schema_version",
            "status",
            "payloads",
            "row_count",
            "verification_scope",
            "source_reverification",
            "rights",
            "publication",
        }
    )
    _require(
        manifest["schema_version"] == VERSION
        and manifest["status"] == "complete"
        and set(manifest["payloads"]) == PAYLOADS
    )
    _require(
        manifest["verification_scope"]
        == "pinned_gold_payloads_schema_and_report_projection"
        and manifest["source_reverification"] == "not_performed_by_reader"
        and manifest["rights"] == "not_evaluated"
        and manifest["publication"] == "not_performed"
    )
    payloads = {}
    for name, binding in manifest["payloads"].items():
        _require(
            set(binding) == {"sha256", "bytes"}
            and type(binding["bytes"]) is int
            and 0 <= binding["bytes"] <= MAX_BYTES
        )
        data = verified_snapshot(
            package_dir / name, binding["sha256"], max_bytes=MAX_BYTES
        )
        _require(len(data) == binding["bytes"])
        payloads[name] = data
    with pq.ParquetFile(
        BytesIO(payloads["comparison.parquet"]),
        thrift_string_size_limit=MAX_BYTES,
        thrift_container_size_limit=100_000,
    ) as file:
        _require(file.schema_arrow.equals(SCHEMA, check_metadata=True))
        _require(
            file.metadata.num_rows <= MAX_ROWS
            and sum(
                file.metadata.row_group(i).total_byte_size
                for i in range(file.metadata.num_row_groups)
            )
            <= MAX_BYTES
        )
        # Small capped tables: synchronous decode releases Python buffers before exit.
        table = file.read(use_threads=False)
    _require(
        type(manifest["row_count"]) is int and manifest["row_count"] == table.num_rows
    )
    summary = json.loads(payloads["summary.json"])
    _require(summary == _summary(table, summary["comparison_receipt"]))
    _require(payloads["README.md"] == _report(summary))
    verified_snapshot(
        package_dir / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES
    )
    return table, summary


def query_budget_comparison(
    package_dir: Path, manifest_sha256: str, *, limit: int = 50
) -> dict[str, Any]:
    """Return bounded exact JSON values after scoped package verification."""
    base = {"schema_version": QUERY_VERSION}
    if type(limit) is not int or not 1 <= limit <= MAX_ROWS:
        return {**base, "status": "failed", "error": "budget_comparison_query_invalid"}
    try:
        table, summary = read_budget_comparison(package_dir, manifest_sha256)
        rows = _rows(table.slice(0, limit))
    except ValueError, OSError, KeyError, TypeError, AttributeError, pa.ArrowException:
        return {**base, "status": "failed", "error": "budget_comparison_query_failed"}
    return {
        **base,
        "status": "verified",
        "manifest_sha256": manifest_sha256,
        "rows": rows,
        "row_count": len(rows),
        "total_rows": table.num_rows,
        "truncated": len(rows) < table.num_rows,
        "decimal_encoding": "exact_string",
        "date_encoding": "iso8601",
        "verification_scope": "pinned_gold_payloads_schema_and_report_projection",
        "source_reverification": "not_performed",
        "source_bindings": summary["comparison_receipt"]["source_bindings"],
        "caveats": summary["comparison_receipt"]["caveats"],
        "semantic_comparability": "not_established",
        "rights": "not_evaluated",
        "publication": "not_performed",
    }


def mcp_call(arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate the closed MCP input contract before local reads."""
    _require(not any(Draft202012Validator(INPUT_SCHEMA).iter_errors(arguments)))
    return query_budget_comparison(
        Path(arguments["package_dir"]),
        arguments["manifest_sha256"],
        limit=arguments.get("limit", 50),
    )
