"""Reports keep exclusions, source drill-through and accounting breaks explicit."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from rdflib import XSD, Graph, Literal, URIRef

from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_reports as reports,
)


def queries() -> dict[str, dict[str, Any]]:
    nominal = [
        {
            "period_start": f"{year - 1}-07-01",
            "period_end": f"{year}-06-30",
            "numerator_id": f"health-{year}",
            "numerator_amount": "10.000000000000000000",
            "accounting_basis": "PBE Standards",
            "source_object_sha256": "a" * 64,
            "source_vintage": "fixture-vintage",
        }
        for year in (2024, 2025)
    ]
    shares: list[dict[str, Any]] = [
        {**row, "measure": measure, "percent": "5.000000000000", "status": "calculated"}
        for row in nominal
        for measure in (
            "health_share_gdp",
            "health_share_core_crown",
            "health_share_total_crown",
        )
    ]
    shares[1].update({"percent": None, "status": "missing_denominator"})
    rates: list[dict[str, Any]] = [
        {
            **row,
            "source_dollars_per_mean_resident": "100.000000000000",
            "status": "calculated",
        }
        for row in nominal
    ]
    rates[0].update(
        {"source_dollars_per_mean_resident": None, "status": "missing_population"}
    )
    cpi = [
        {
            **row,
            "nominal_amount_millions": row["numerator_amount"],
            "cpi_benchmark_millions": "11.000000000000",
            "status": "calculated",
            "numerator_gst_basis": "exclusive",
            "health_source_sha256": row["source_object_sha256"],
            "health_vintage": row["source_vintage"],
        }
        for row in nominal
    ]
    return {
        name: {
            "status": "verified",
            "rows": rows,
            "row_count": len(rows),
            "total_rows": len(rows),
            "truncated": False,
        }
        for name, rows in {
            "nominal": nominal,
            "shares": shares,
            "per_capita": rates,
            "cpi_benchmark": cpi,
        }.items()
    }


def test_repeat_outputs_dry_run_fixity_and_exclusions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = queries()
    monkeypatch.setattr(
        reports.ops, "query_fiscal_analytical_gold", lambda *_, table, **__: data[table]
    )
    source = tmp_path / "source"
    source.mkdir()
    (source / "preserved").write_bytes(b"original")
    first, second = tmp_path / "first", tmp_path / "second"
    dry = reports.export_fiscal_analytical_reports(source, "a" * 64, first)
    assert not first.exists()
    result = reports.export_fiscal_analytical_reports(
        source, "a" * 64, first, write=True
    )
    repeated = reports.export_fiscal_analytical_reports(
        source, "a" * 64, second, write=True
    )
    assert result == repeated
    assert dry["manifest_sha256"] == result["manifest_sha256"]
    verified = reports.verify_fiscal_analytical_reports(
        first, result["manifest_sha256"]
    )
    assert verified["status"] == "verified"
    assert verified["metadata_projections"] == "byte_equal"
    for path in first.iterdir():
        assert path.read_bytes() == (second / path.name).read_bytes()
    manifest = json.loads((first / "manifest.json").read_bytes())
    for filename, record in manifest["files"].items():
        assert (
            hashlib.sha256((first / filename).read_bytes()).hexdigest()
            == record["sha256"]
        )
    summary = json.loads((first / "summary.json").read_bytes())
    assert summary["rows"] == 12
    assert summary["plotted_points"] == 10
    assert summary["excluded_points"] == 2
    assert (
        summary["series"]["health_share_core_crown"]["exclusions"][0]["status"]
        == "missing_denominator"
    )
    assert summary["series"]["per_capita"]["points"][0]["numerator_id"] == "health-2025"
    assert (source / "preserved").read_bytes() == b"original"
    catalogue = Graph().parse(
        data=(first / "catalogue.json").read_bytes(), format="json-ld"
    )
    provenance = Graph().parse(
        data=(first / "provenance.json").read_bytes(), format="json-ld"
    )
    parent = URIRef(f"urn:sha256:{'a' * 64}")
    for filename, record in manifest["files"].items():
        if filename in ("catalogue.json", "provenance.json"):
            continue
        entity = URIRef(f"urn:sha256:{record['sha256']}")
        assert (
            entity,
            URIRef("http://www.w3.org/ns/prov#wasDerivedFrom"),
            parent,
        ) in provenance
        assert (
            entity,
            URIRef("http://purl.org/dc/terms/title"),
            Literal(filename),
        ) in catalogue
        checksum = URIRef(f"urn:sha256:{record['sha256']}:checksum")
        assert (
            checksum,
            URIRef("http://spdx.org/rdf/terms#checksumValue"),
            Literal(record["sha256"], datatype=XSD.hexBinary),
        ) in catalogue
    with pytest.raises(FileExistsError):
        reports.export_fiscal_analytical_reports(source, "a" * 64, first, write=True)
    (first / "catalogue.json").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="fiscal_report"):
        reports.verify_fiscal_analytical_reports(first, result["manifest_sha256"])


@pytest.mark.parametrize("case", ["failed", "truncated", "amount", "identity"])
def test_invalid_query_or_cross_table_identity_prevents_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    data = queries()
    if case == "failed":
        data["shares"]["status"] = "failed"
    elif case == "truncated":
        data["shares"]["truncated"] = True
    elif case == "amount":
        data["nominal"]["rows"][0]["numerator_amount"] = "NaN"
    else:
        data["cpi_benchmark"]["rows"][0]["numerator_id"] = "different-source"
    monkeypatch.setattr(
        reports.ops, "query_fiscal_analytical_gold", lambda *_, table, **__: data[table]
    )
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="fiscal_report"):
        reports.export_fiscal_analytical_reports(
            tmp_path / "source", "a" * 64, output, write=True
        )
    assert not output.exists()


def test_output_overlap_rejected_before_query(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected(*_: object, **__: object) -> object:
        pytest.fail("overlapping output must fail before query")

    monkeypatch.setattr(reports.ops, "query_fiscal_analytical_gold", unexpected)
    for target in (tmp_path, tmp_path / "source" / "report"):
        with pytest.raises(ValueError, match="fiscal_report_output_overlap"):
            reports.export_fiscal_analytical_reports(
                tmp_path / "source", "a" * 64, target, write=True
            )
