"""Deterministic local reports from the same pinned fiscal analytical queries."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

import matplotlib as mpl

mpl.use("Agg")
from matplotlib import pyplot as plt

from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_gold as gold,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_operations as ops,
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.fiscal-analytical-reports/v2"
_MAX_BYTES = 8 * 1024 * 1024
_MAX_TOTAL = 64 * 1024 * 1024
_MAX_NUMBER_TEXT = 80
_MAX_ID = 200
_FIRST_YEAR = 1972
_LAST_YEAR = 2025
_BASES = {"Cash", "old-GAAP", "IFRS", "PBE Standards"}
_SHARES = ("health_share_gdp", "health_share_core_crown", "health_share_total_crown")
_VIEWS = {
    "nominal": (
        "nominal",
        "numerator_amount",
        "Nominal Core Crown Health",
        "source millions",
    ),
    "health_share_gdp": ("shares", "percent", "Core Crown Health / GDP", "percent"),
    "health_share_core_crown": (
        "shares",
        "percent",
        "Core Crown Health / Core Crown expenses",
        "percent",
    ),
    "health_share_total_crown": (
        "shares",
        "percent",
        "Core Crown Health / Total Crown expenses",
        "percent",
    ),
    "per_capita": (
        "per_capita",
        "source_dollars_per_mean_resident",
        "Core Crown Health per mean resident",
        "source dollars per mean resident",
    ),
    "cpi_benchmark": (
        "cpi_benchmark",
        "cpi_benchmark_millions",
        "Household-CPI FY2025 benchmark",
        "source millions at FY2025 household CPI",
    ),
}


def _require(condition: object) -> None:
    if not condition:
        msg = "fiscal_report_invalid"
        raise ValueError(msg)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def _number(value: object) -> Decimal:
    _require(type(value) is str and len(str(value)) <= _MAX_NUMBER_TEXT)
    try:
        result = Decimal(str(value))
    except ArithmeticError:
        msg = "fiscal_report_amount_invalid"
        raise ValueError(msg) from None
    _require(result.is_finite() and result.copy_abs() < Decimal("1e30"))
    return result


def _key(row: dict[str, Any]) -> tuple[str, str]:
    end = date.fromisoformat(row["period_end"])
    _require(
        _FIRST_YEAR <= end.year <= _LAST_YEAR
        and (end.month, end.day) in ((3, 31), (6, 30))
    )
    _require(
        type(row["numerator_id"]) is str and 0 < len(row["numerator_id"]) <= _MAX_ID
    )
    _require(row["accounting_basis"] in _BASES)
    return row["period_end"], row["numerator_id"]


def _qualifications(queries: dict[str, dict[str, Any]]) -> dict[tuple[str, str], str]:
    """Join GST labels only after exact parent identity, amount and context checks."""
    nominal = {_key(row): row for row in queries["nominal"]["rows"]}
    cpi = {_key(row): row for row in queries["cpi_benchmark"]["rows"]}
    _require(len(nominal) == len(queries["nominal"]["rows"]))
    _require(
        len(cpi) == len(queries["cpi_benchmark"]["rows"]) and set(cpi) == set(nominal)
    )
    parent_fields = {
        "shares": ("numerator_amount", "source_object_sha256", "source_vintage"),
        "per_capita": (
            "health_amount_millions",
            "health_source_sha256",
            "health_vintage",
        ),
        "cpi_benchmark": (
            "nominal_amount_millions",
            "health_source_sha256",
            "health_vintage",
        ),
    }
    for table, (amount, source, vintage) in parent_fields.items():
        for row in queries[table]["rows"]:
            key = _key(row)
            _require(key in nominal)
            parent = nominal[key]
            _require(
                _number(row[amount]) == _number(parent["numerator_amount"])
                and row[source] == parent["source_object_sha256"]
                and row[vintage] == parent["source_vintage"]
                and all(
                    row[field] == parent[field]
                    for field in (
                        "period_start",
                        "accounting_basis",
                        "numerator_source_time_status",
                        "numerator_coverage",
                    )
                )
            )
    result = {}
    for key, row in cpi.items():
        _require(row["numerator_gst_basis"] in ("inclusive", "exclusive"))
        result[key] = row["numerator_gst_basis"]
    return result


def _reconciliation(
    queries: dict[str, dict[str, Any]], manifest_sha256: str
) -> dict[str, Any]:
    """Tie each admitted source observation to every derived output row."""
    nominal_rows = queries["nominal"]["rows"]
    nominal = {_key(row): row for row in nominal_rows}
    _require(len(nominal) == len(nominal_rows))
    expected = set(nominal)

    shares: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in queries["shares"]["rows"]:
        key = _key(row)
        measure = row["measure"]
        _require(key in expected and measure in _SHARES)
        share_key = (key[0], key[1], measure)
        _require(share_key not in shares)
        _require(
            _number(row["numerator_amount"])
            == _number(nominal[key]["numerator_amount"])
        )
        shares[share_key] = row
    _require(
        set(shares)
        == {
            (end, numerator, measure)
            for end, numerator in expected
            for measure in _SHARES
        }
    )

    derived: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    for table in ("per_capita", "cpi_benchmark"):
        indexed = {_key(row): row for row in queries[table]["rows"]}
        _require(
            len(indexed) == len(queries[table]["rows"]) and set(indexed) == expected
        )
        derived[table] = indexed

    rows = []
    for key, source in sorted(nominal.items()):
        share_rows = {
            measure: shares[(key[0], key[1], measure)] for measure in sorted(_SHARES)
        }
        rate = derived["per_capita"][key]
        cpi = derived["cpi_benchmark"][key]
        rows.append(
            {
                "source": {
                    "period_start": source["period_start"],
                    "period_end": key[0],
                    "numerator_id": key[1],
                    "amount": source["numerator_amount"],
                    "accounting_basis": source["accounting_basis"],
                    "source_object_sha256": source["source_object_sha256"],
                    "source_vintage": source["source_vintage"],
                    "source_time_status": source["numerator_source_time_status"],
                    "coverage": source["numerator_coverage"],
                },
                "source_amount_control": "exact_parent_amount_equality",
                "shares": {
                    measure: {
                        "denominator_id": row["denominator_id"],
                        "denominator_amount": row["denominator_amount"],
                        "denominator_source_time_status": row[
                            "denominator_source_time_status"
                        ],
                        "denominator_coverage": row["denominator_coverage"],
                        "denominator_accounting_basis": row[
                            "denominator_accounting_basis"
                        ],
                        "period_definition_evidence_sha256": row[
                            "period_definition_evidence_sha256"
                        ],
                        "percent": row["percent"],
                        "status": row["status"],
                        "formula_policy": row["formula_policy"],
                    }
                    for measure, row in share_rows.items()
                },
                "per_capita": {
                    "population_id": rate["population_id"],
                    "population_source_sha256": rate["population_source_sha256"],
                    "population_vintage": rate["population_vintage"],
                    "population_source_time_status": rate[
                        "population_source_time_status"
                    ],
                    "mean_population": rate["mean_population"],
                    "unit": rate["unit"],
                    "population_period_evidence_sha256": rate[
                        "population_period_evidence_sha256"
                    ],
                    "amount": rate["source_dollars_per_mean_resident"],
                    "status": rate["status"],
                    "formula_policy": rate["formula_policy"],
                },
                "cpi_benchmark": {
                    "cpi_source_sha256": cpi["cpi_source_sha256"],
                    "cpi_vintage": cpi["cpi_vintage"],
                    "cpi_definition_evidence_sha256": cpi[
                        "cpi_definition_evidence_sha256"
                    ],
                    "period_cpi_ids": cpi["period_cpi_ids"],
                    "period_cpi_source_time_statuses": cpi[
                        "period_cpi_source_time_statuses"
                    ],
                    "benchmark_cpi_ids": cpi["benchmark_cpi_ids"],
                    "benchmark_cpi_source_time_statuses": cpi[
                        "benchmark_cpi_source_time_statuses"
                    ],
                    "period_cpi_mean": cpi["period_cpi_mean"],
                    "benchmark_cpi_mean": cpi["benchmark_cpi_mean"],
                    "benchmark_period_start": cpi["benchmark_period_start"],
                    "benchmark_period_end": cpi["benchmark_period_end"],
                    "numerator_gst_basis": cpi["numerator_gst_basis"],
                    "unit": cpi["unit"],
                    "amount": cpi["cpi_benchmark_millions"],
                    "status": cpi["status"],
                    "formula_policy": cpi["formula_policy"],
                },
            }
        )
    return {
        "schema_version": "archive-govt-nz.fiscal-gold-source-reconciliation/v1",
        "gold_manifest_sha256": manifest_sha256,
        "status": "all_derived_rows_tied_to_source",
        "source_observations": len(rows),
        "aggregate_source_totals": "not_computed_overlapping_periods_and_bases",
        "rows": rows,
    }


def _series(
    queries: dict[str, dict[str, Any]], gst: dict[tuple[str, str], str]
) -> dict[str, dict[str, Any]]:
    _require(all(row["measure"] in _SHARES for row in queries["shares"]["rows"]))
    result = {}
    for name, (table, column, title, unit) in _VIEWS.items():
        rows = [
            row
            for row in queries[table]["rows"]
            if table != "shares" or row["measure"] == name
        ]
        points, exclusions = [], []
        for row in rows:
            key = _key(row)
            _require(key in gst)
            status = row.get("status", "source_observation")
            if status not in ("calculated", "source_observation"):
                exclusions.append(
                    {"period_end": key[0], "numerator_id": key[1], "status": status}
                )
                continue
            _number(row[column])
            points.append(
                {
                    "period_end": key[0],
                    "numerator_id": key[1],
                    "amount": row[column],
                    "accounting_basis": row["accounting_basis"],
                    "gst_basis": gst[key],
                }
            )
        result[name] = {
            "title": title,
            "unit": unit,
            "points": points,
            "exclusions": exclusions,
        }
    return result


def _plot(series: dict[str, Any]) -> bytes:
    """Convert exact values only for display; never interpolate or connect points."""
    points = series["points"]
    with mpl.rc_context({"font.family": "DejaVu Sans", "text.usetex": False}):
        figure, axis = plt.subplots(figsize=(14, 8), dpi=100)
        try:
            contexts = sorted(
                {
                    (p["accounting_basis"], p["gst_basis"], p["period_end"][5:7])
                    for p in points
                }
            )
            for basis, gst, month in contexts:
                selected = [
                    (i, p)
                    for i, p in enumerate(points)
                    if (p["accounting_basis"], p["gst_basis"], p["period_end"][5:7])
                    == (basis, gst, month)
                ]
                axis.scatter(
                    [i for i, _ in selected],
                    [float(_number(p["amount"])) for _, p in selected],
                    label=f"{basis}; GST {gst}; year ends month {month}",
                )
            positions = list(range(0, len(points), 5))
            axis.set_xticks(
                positions, [points[i]["period_end"] for i in positions], rotation=45
            )
            axis.set_title(series["title"])
            axis.set_ylabel(series["unit"])
            axis.set_xlabel(
                "Discrete source fiscal periods; missing observations omitted"
            )
            if contexts:
                axis.legend(fontsize=8)
            figure.text(
                0.02,
                0.02,
                (
                    "Reporting/GST bases are distinguished. "
                    "No interpolation, health-input-cost or ISO-currency claim."
                ),
                fontsize=8,
            )
            figure.tight_layout(rect=(0, 0.05, 1, 1))
            output = BytesIO()
            figure.savefig(output, format="png", metadata={"Software": VERSION})
            return output.getvalue()
        finally:
            plt.close(figure)


def _provenance(pin: str, payloads: dict[str, bytes]) -> dict[str, Any]:
    """Describe actual local derivation edges without dates, actors or rights."""
    parent = f"urn:sha256:{pin}"
    return {
        "@context": {
            "prov": "http://www.w3.org/ns/prov#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        },
        "@graph": [
            {"@id": parent, "@type": "prov:Entity"},
            *[
                {
                    "@id": f"urn:sha256:{hashlib.sha256(value).hexdigest()}",
                    "@type": "prov:Entity",
                    "prov:wasDerivedFrom": {"@id": parent},
                    "rdfs:label": name,
                }
                for name, value in sorted(payloads.items())
            ],
        ],
    }


def _catalogue(pin: str, payloads: dict[str, bytes]) -> dict[str, Any]:
    """Generate a bounded DCAT distribution inventory with exact byte checksums."""
    distributions = []
    for name, value in sorted(payloads.items()):
        digest = hashlib.sha256(value).hexdigest()
        media = (
            "image/png"
            if name.endswith(".png")
            else ("text/markdown" if name.endswith(".md") else "application/json")
        )
        distributions.append(
            {
                "@id": f"urn:sha256:{digest}",
                "@type": "dcat:Distribution",
                "dct:title": name,
                "dcat:byteSize": {
                    "@value": len(value),
                    "@type": "xsd:nonNegativeInteger",
                },
                "dcat:mediaType": {
                    "@id": f"https://www.iana.org/assignments/media-types/{media}"
                },
                "spdx:checksum": {
                    "@id": f"urn:sha256:{digest}:checksum",
                    "@type": "spdx:Checksum",
                    "spdx:algorithm": {"@id": "spdx:checksumAlgorithm_sha256"},
                    "spdx:checksumValue": {"@value": digest, "@type": "xsd:hexBinary"},
                },
            }
        )
    catalogue_digest = hashlib.sha256(_json(distributions)).hexdigest()
    return {
        "@context": {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
            "prov": "http://www.w3.org/ns/prov#",
            "spdx": "http://spdx.org/rdf/terms#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
        },
        "@id": f"urn:archive-govt-nz:fiscal-reports:{catalogue_digest}",
        "dct:hasVersion": VERSION,
        "@type": "dcat:Dataset",
        "dct:title": "Local Fiscal analytical reports",
        "prov:wasDerivedFrom": {"@id": f"urn:sha256:{pin}"},
        "dcat:distribution": distributions,
    }


def export_fiscal_analytical_reports(
    package_dir: Path, manifest_sha256: str, output_dir: Path, *, write: bool = False
) -> dict[str, Any]:
    """Build bounded companion reports, retaining the source package unchanged."""
    if write and (
        output_dir.resolve().is_relative_to(package_dir.resolve())
        or package_dir.resolve().is_relative_to(output_dir.resolve())
    ):
        msg = "fiscal_report_output_overlap"
        raise ValueError(msg)
    queries = {
        name: ops.query_fiscal_analytical_gold(
            package_dir, manifest_sha256, table=name, limit=200
        )
        for name in gold.TABLE_SCHEMAS
    }
    _require(
        all(q["status"] == "verified" and not q["truncated"] for q in queries.values())
    )
    series = _series(queries, _qualifications(queries))
    reconciliation = _reconciliation(queries, manifest_sha256)
    summary = {
        "schema_version": VERSION,
        "gold_manifest_sha256": manifest_sha256,
        "rows": sum(q["row_count"] for q in queries.values()),
        "plotted_points": sum(len(s["points"]) for s in series.values()),
        "excluded_points": sum(len(s["exclusions"]) for s in series.values()),
        "series": series,
        "queries": queries,
        "verification_scope": "pinned_gold_fixity_not_original_reverification",
        "rights": "not_evaluated",
        "publication": "not_performed",
        "health_input_cost_deflator": "not_asserted",
        "currency_iso": "not_asserted",
        "rendering": "discrete_points_grouped_accounting_GST_fiscal_month",
    }
    payloads = {f"{name}.png": _plot(value) for name, value in series.items()}
    payloads["summary.json"] = _json(summary)
    payloads["reconciliation.json"] = _json(reconciliation)
    payloads["schemas.json"] = _json(
        {
            name: [
                {"name": f.name, "type": str(f.type), "nullable": f.nullable}
                for f in schema
            ]
            for name, schema in gold.TABLE_SCHEMAS.items()
        }
    )
    card = [
        "# Fiscal analytical reports",
        "",
        "Local companion products from pinned Gold.",
        "Rights are not evaluated; publication is not performed.",
        "Household CPI is not a health input cost deflator.",
        "Source currency has no asserted ISO code.",
        "Original-source verification is separate.",
        "Exact values and source IDs remain in summary.json and reconciliation.json.",
        (
            "Source observations tied row by row: "
            f"{reconciliation['source_observations']}."
        ),
        "Aggregate source totals are not computed across overlapping periods or bases.",
        "",
        "| Series | Plotted | Excluded |",
        "| --- | ---: | ---: |",
    ]
    card.extend(
        f"| {name} | {len(s['points'])} | {len(s['exclusions'])} |"
        for name, s in series.items()
    )
    payloads["DATASET_CARD.md"] = ("\n".join(card) + "\n").encode()
    provenance = _provenance(manifest_sha256, payloads)
    catalogue = _catalogue(manifest_sha256, payloads)
    payloads["provenance.json"] = _json(provenance)
    payloads["catalogue.json"] = _json(catalogue)
    inventory = {
        name: {"sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}
        for name, value in sorted(payloads.items())
    }
    _require(all(record["bytes"] <= _MAX_BYTES for record in inventory.values()))
    _require(sum(record["bytes"] for record in inventory.values()) <= _MAX_TOTAL)
    manifest = {
        "schema_version": VERSION,
        "renderer_version": mpl.__version__,
        "gold_manifest_sha256": manifest_sha256,
        "files": inventory,
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
    payloads["manifest.json"] = _json(manifest)
    expected_pin = hashlib.sha256(payloads["manifest.json"]).hexdigest()
    if write:
        output_dir.mkdir(parents=True, exist_ok=False)
        for filename, value in payloads.items():
            with (output_dir / filename).open("xb") as stream:
                stream.write(value)
        verify_fiscal_analytical_reports(output_dir, expected_pin)
    return {
        "schema_version": VERSION,
        "status": "written" if write else "dry_run",
        "manifest_sha256": expected_pin,
        "readback": "verified" if write else "not_performed",
        "files": inventory,
        "plotted_points": summary["plotted_points"],
        "excluded_points": summary["excluded_points"],
    }


def verify_fiscal_analytical_reports(
    root: Path, manifest_sha256: str
) -> dict[str, Any]:
    """Check exact report fixity and metadata projections, without reading Gold."""
    names = {
        *(f"{name}.png" for name in _VIEWS),
        "summary.json",
        "reconciliation.json",
        "schemas.json",
        "DATASET_CARD.md",
        "provenance.json",
        "catalogue.json",
    }
    _require(not root.is_symlink() and root.is_dir())
    _require({p.name for p in root.iterdir()} == names | {"manifest.json"})
    marker = root / "manifest.json"
    _require(
        not marker.is_symlink()
        and marker.is_file()
        and marker.stat().st_size <= _MAX_BYTES
    )
    content = marker.read_bytes()
    _require(hashlib.sha256(content).hexdigest() == manifest_sha256)
    manifest = json.loads(content)
    _require(manifest["schema_version"] == VERSION and set(manifest["files"]) == names)
    payloads = {}
    total = 0
    for name in sorted(names):
        path = root / name
        _require(
            not path.is_symlink()
            and path.is_file()
            and path.stat().st_size <= _MAX_BYTES
        )
        value = path.read_bytes()
        record = manifest["files"][name]
        _require(
            len(value) == record["bytes"]
            and hashlib.sha256(value).hexdigest() == record["sha256"]
        )
        total += len(value)
        _require(total <= _MAX_TOTAL)
        payloads[name] = value
    base = {
        name: value
        for name, value in payloads.items()
        if name not in ("catalogue.json", "provenance.json")
    }
    pin = manifest["gold_manifest_sha256"]
    _require(payloads["catalogue.json"] == _json(_catalogue(pin, base)))
    _require(payloads["provenance.json"] == _json(_provenance(pin, base)))
    return {
        "schema_version": VERSION,
        "status": "verified",
        "manifest_sha256": manifest_sha256,
        "files_verified": len(names),
        "metadata_projections": "byte_equal",
        "source_reverification": "not_performed",
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
