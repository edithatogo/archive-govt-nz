"""Operation manifests feed canonical tables without changing historical readers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_context_operations import (
    _context,
    _pin,
    _request,
)

from archive_govt_nz.domains.health_appropriations import (
    context_operation_canonical as projection,
)
from archive_govt_nz.domains.health_appropriations import (
    context_operations,
    cpi,
    cpi_canonical_projection,
    gdp,
    gdp_canonical_projection,
    population_annual_canonical_projection,
    population_annual_silver,
    qes,
    qes_canonical_projection,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import encode_json
from archive_govt_nz.schemas.health_recordset_normalization import validate_table


class Case(NamedTuple):
    """One exact family/profile, native API and existing canonical API."""

    profile: str
    vintage: str
    native: ModuleType
    normalizer: str
    canonical: ModuleType
    projector: str
    prefix: str = ""


CASES = (
    Case(
        "cpiq-se9a/v1",
        "Stats-NZ-CPI-2026-Q2",
        cpi,
        "normalize_cpi",
        cpi_canonical_projection,
        "project_cpi",
    ),
    Case(
        "population-annual-mean-context/v1",
        "2026-08-18",
        population_annual_silver,
        "normalize_population_annual",
        population_annual_canonical_projection,
        "project_population_annual",
    ),
    Case(
        "qes-june2026-table8/v1",
        "QES-2026-Q2",
        qes,
        "normalize_qes",
        qes_canonical_projection,
        "project_qes_earnings",
    ),
    Case(
        "gdp-expenditure-actual-2026q1/v1",
        gdp.VINTAGE,
        gdp,
        "normalize_gdp",
        gdp_canonical_projection,
        "project_gdp",
    ),
    Case(
        "gdp-expenditure-actual-2026q2/v1",
        gdp.JUNE_VINTAGE,
        gdp,
        "normalize_gdp",
        gdp_canonical_projection,
        "project_gdp_june",
        "JUNE_",
    ),
)


def _bytes(table: pa.Table) -> bytes:
    with pa.BufferOutputStream() as stream:
        pq.write_table(table, stream)
        return stream.getvalue().to_pybytes()


def _legacy_bytes(table: pa.Table) -> bytes:
    return encode_json(
        {
            "arrow_schema": table.schema.serialize().to_pybytes().hex(),
            "rows": table.to_pylist(),
        }
    ).encode()


def _fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: Case
) -> tuple[Any, Path, Path, str]:
    request = _request(tmp_path, case.profile, case.vintage)
    native = tmp_path / "native"
    getattr(case.native, case.normalizer)(
        request.source, native, **_context(request), dry_run=False
    )
    native_pin = _pin(native)
    # Fixture-only binding substitution; production keeps the fixed official
    # source/vintage/locator/observation cohort and original native manifest pin.
    for name, value in {
        "SOURCE_SHA256": request.expected_sha256,
        "SOURCE_LOCATOR": request.source_locator,
        "SOURCE_VINTAGE": request.source_vintage,
        "OBSERVED_AT": request.observed_at,
        "SOURCE_MANIFEST_SHA256": native_pin,
    }.items():
        monkeypatch.setattr(case.canonical, case.prefix + name, value)
    cas = tmp_path / "cas"
    original = cas / request.expected_sha256[:2] / request.expected_sha256
    original.parent.mkdir(parents=True)
    original.write_bytes(request.source.read_bytes())
    context_operations.normalize_context(
        request.source,
        request.output_dir,
        profile=case.profile,
        **_context(request),
        dry_run=False,
    )
    return request, native, cas, native_pin


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.profile)
def test_consumes_verified_operation_and_matches_existing_canonical_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: Case,
) -> None:
    request, native, cas, native_pin = _fixture(tmp_path, monkeypatch, case)
    old_project = getattr(case.canonical, case.projector)
    expected_facts, expected_lineage, _ = old_project(native, native_pin, cas)
    pin = _pin(request.output_dir)
    with pytest.raises(ValueError, match="canonical_projection_invalid"):
        old_project(request.output_dir, pin, cas)
    seen: list[context_operations.VerifiedContextOperation] = []
    read = context_operations.read_context

    def observe(  # noqa: PLR0913 - trace exact verified source context
        source: Path,
        output: Path,
        *,
        manifest_sha256: str,
        profile: str,
        expected_sha256: str,
        source_vintage: str,
        source_locator: str,
        observed_at: str,
    ) -> context_operations.VerifiedContextOperation:
        value = read(
            source,
            output,
            manifest_sha256=manifest_sha256,
            profile=profile,
            expected_sha256=expected_sha256,
            source_vintage=source_vintage,
            source_locator=source_locator,
            observed_at=observed_at,
        )
        seen.append(value)
        return value

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("new canonical route used historical filesystem reader")

    monkeypatch.setattr(context_operations, "read_context", observe)
    monkeypatch.setattr(case.canonical, case.projector, forbidden)
    before = {p.name: p.read_bytes() for p in request.output_dir.iterdir()}
    facts, lineage, receipt = projection.project_context_operation(
        request.source,
        request.output_dir,
        manifest_sha256=pin,
        profile=case.profile,
        **_context(request),
    )
    assert _bytes(facts) == _bytes(expected_facts)
    if case.profile == "qes-june2026-table8/v1":
        with pytest.raises(ValueError, match="health_recordset_normalization"):
            validate_table("field_lineage", expected_lineage, version="v2")
        validate_table("field_lineage", lineage, version="v2")
        with pytest.raises(pa.ArrowInvalid, match="non-nullable"):
            _bytes(expected_lineage)
        completed = lineage.to_pylist()
        assert len(completed) == len({row["record_id"] for row in completed}) == 90
        assert {row["target_record_id"] for row in completed} == {
            row["record_id"] for row in facts.to_pylist()
        }
        preserved = (
            "target_record_id",
            "field",
            "source_coordinate",
            "raw_value",
            "normalized_value",
            "rule",
        )
        assert (
            lineage.select(preserved).to_pylist()
            == expected_lineage.select(preserved).to_pylist()
        )
        assert all(
            row["source_object_sha256"] == request.expected_sha256
            for row in lineage.to_pylist()
        )
        assert (
            receipt["lineage_completion"]["legacy_lineage_sha256"]
            == hashlib.sha256(_legacy_bytes(expected_lineage)).hexdigest()
        )
        assert all(row["record_id"] is None for row in expected_lineage.to_pylist())
    else:
        assert _bytes(lineage) == _bytes(expected_lineage)
        assert receipt["lineage_completion"] is None
    assert receipt["source_manifest_sha256"] == pin
    assert (
        receipt["source_manifest_schema_version"]
        == "archive-govt-nz.health-context-operation/v1"
    )
    assert (
        receipt["common_evidence_sha256"]
        == hashlib.sha256(
            encode_json(asdict(seen[-1].common_output)).encode()
        ).hexdigest()
    )
    assert receipt["output_records"] == facts.num_rows
    assert receipt["lineage_records"] == lineage.num_rows
    assert receipt["rights_state"] == "not_evaluated"
    assert receipt["denominator_selection"] == "not_performed"
    assert receipt["currency_admission"] == "not_performed"
    assert receipt["approved_joins"] == "none"
    assert {p.name: p.read_bytes() for p in request.output_dir.iterdir()} == before
    repeated = projection.project_context_operation(
        request.source,
        request.output_dir,
        manifest_sha256=pin,
        profile=case.profile,
        **_context(request),
    )
    assert _bytes(repeated[0]) == _bytes(facts)
    assert _bytes(repeated[1]) == _bytes(lineage)
    assert repeated[2] == receipt


@pytest.mark.parametrize(
    "changed",
    [
        "source",
        "locator",
        "vintage",
        "observation",
        "profile",
        "pin",
        "evidence",
        "table",
    ],
)
def test_rejects_unqualified_context_or_changed_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changed: str,
) -> None:
    request, _, _, _ = _fixture(tmp_path, monkeypatch, CASES[0])
    options = {
        **_context(request),
        "profile": request.profile,
        "manifest_sha256": _pin(request.output_dir),
    }
    if changed == "evidence":
        path = request.output_dir / "MANIFEST.json"
        receipt = json.loads(path.read_text())
        receipt["common_output"]["dimensions"] = []
        path.write_text(encode_json(receipt) + "\n")
        options["manifest_sha256"] = _pin(request.output_dir)
    elif changed == "table":
        with (request.output_dir / "cpi_facts.parquet").open("ab") as stream:
            stream.write(b"tamper")
    else:
        key, value = {
            "source": ("expected_sha256", "a" * 64),
            "locator": ("source_locator", "https://example.test/other"),
            "vintage": ("source_vintage", "2026-Q2"),
            "observation": ("observed_at", "2026-10-17T00:00:00+00:00"),
            "profile": ("profile", "unknown/v1"),
            "pin": ("manifest_sha256", "a" * 64),
        }[changed]
        options[key] = value
    with pytest.raises(
        ValueError,
        match=r"invalid_context_operation|context_operation_canonical_invalid|source_hash_mismatch|source_byte_limit",
    ):
        projection.project_context_operation(
            request.source, request.output_dir, **options
        )
