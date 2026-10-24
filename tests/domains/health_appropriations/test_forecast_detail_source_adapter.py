"""Two native interpretations share selection without losing standalone fidelity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_literal_source_adapters import (
    admission,
    payload,
)

from archive_govt_nz.domains.health_appropriations import forecast
from archive_govt_nz.domains.health_appropriations import (
    forecast_detail_source_adapter as adapters,
)
from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_native_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    CompoundAdapterOutput,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    compound_workbook_registrations,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    source_context,
)

OBSERVED = "2026-08-30T08:58:00+00:00"


def setup_source(
    monkeypatch: pytest.MonkeyPatch, index: int
) -> tuple[bytes, adapters.ForecastDetailSource]:
    """Mock native admission only; retain real projection, tables and validation."""
    bronze = payload()
    pin = hashlib.sha256(bronze).hexdigest()
    spec = replace(
        adapters.SOURCES[index],
        source_sha256=pin,
        summary_counts=(1, 1, 2, 2),
        detail_counts=(1, 2, 3, 0),
    )
    monkeypatch.setattr(adapters, "SOURCES", (spec,))

    def parse(data: bytes, **kwargs: str) -> forecast.ForecastExtraction:
        assert data == bronze
        assert kwargs["profile"] == spec.summary_profile
        context = source_context(
            pin, spec.source_locator, spec.source_vintage, kwargs["observed_at"]
        )
        common = {**context, "record_id": "summary-record"}
        return forecast.ForecastExtraction(
            context,
            [{**common, "amount": Decimal("1.250"), "department": "Health"}],
            [{**common, "field": "amount", "source_coordinate": "Sheet!B1"}],
            [
                {**common, "disposition": "normalized", "reason": "selected_amount"},
                {
                    **common,
                    "record_id": None,
                    "disposition": "context",
                    "reason": "label",
                },
            ],
            [
                {"sheet": "Other", "reason": "not_forecast_summary_sheet"},
                {"sheet": "Index", "reason": "not_forecast_summary_sheet"},
            ],
            {"sheet": "Sheet", "columns": [2]},
            {"sheets": [{"title": "Sheet"}, {"title": "Other"}, {"title": "Index"}]},
        )

    def admit(
        data: bytes, *, profile: str, context: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        assert data == bronze
        assert profile == spec.detail_profile
        return admission(profile, context), context

    monkeypatch.setattr(forecast, "parse_forecast_snapshot", parse)
    monkeypatch.setattr(packages, "admit_literal_snapshot", admit)
    return bronze, spec


@pytest.mark.parametrize("index", [0, 1])
def test_both_native_profiles_match_unchanged_standalone_writers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, index: int
) -> None:
    bronze, spec = setup_source(monkeypatch, index)
    entries = compound_workbook_registrations(
        (AdapterContext(spec.source_locator, spec.source_vintage, OBSERVED),)
    )
    result = dispatch_native_bronze(
        bronze,
        source_sha256=spec.source_sha256,
        media_type=adapters.MEDIA_TYPE,
        registrations=entries,
    )
    assert isinstance(result.output, CompoundAdapterOutput)
    assert result.output.status == "admitted"
    assert result.selection.adapter_version == "2"
    assert [p.profile_id for p in result.output.profiles] == [
        spec.summary_profile,
        spec.detail_profile,
    ]
    source = tmp_path / "source.xlsx"
    source.write_bytes(bronze)
    summary_dir = tmp_path / spec.summary_profile
    forecast.normalize_forecast_workbook(
        source,
        summary_dir,
        expected_sha256=spec.source_sha256,
        profile=spec.summary_profile,
        observed_at=OBSERVED,
        source_vintage=spec.source_vintage,
        source_locator=spec.source_locator,
    )
    context = {
        "source_object_sha256": spec.source_sha256,
        "source_locator": spec.source_locator,
        "source_vintage": spec.source_vintage,
        "observed_at": OBSERVED,
    }
    packages.write_literal_package(
        tmp_path / spec.detail_profile,
        admission(spec.detail_profile, context),
        profile=spec.detail_profile,
        context=context,
    )
    for profile in result.output.profiles:
        native_dir = tmp_path / profile.profile_id
        manifest = json.loads((native_dir / "MANIFEST.json").read_text())
        assert json.loads(encode_json(dict(profile.metadata))) == manifest
        hashes = profile.metadata["output_sha256"]
        assert isinstance(hashes, dict)
        for recordset, contract in zip(
            profile.recordsets,
            next(
                c
                for c in entries[0].profile_contracts
                if c.profile_id == profile.profile_id
            ).recordsets,
            strict=True,
        ):
            assert recordset.table.schema.equals(contract.schema, check_metadata=True)
            file = native_dir / recordset.name
            assert recordset.table.to_pylist() == pq.read_table(file).to_pylist()
            assert (
                hashlib.sha256(file.read_bytes()).hexdigest() == hashes[recordset.name]
            )
    assert len(result.output.profiles[0].excluded_sheets) == 2
    assert result.output.profiles[1].excluded_sheets == ()


@pytest.mark.parametrize("failure", ["summary", "detail", "count"])
def test_one_failed_sibling_holds_the_whole_physical_source(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    bronze, spec = setup_source(monkeypatch, 0)

    def fail(*_args: object, **_kwargs: object) -> None:
        message = "retained_native_admission_failure"
        raise ValueError(message)

    if failure == "summary":
        monkeypatch.setattr(forecast, "parse_forecast_snapshot", fail)
    elif failure == "detail":
        monkeypatch.setattr(packages, "admit_literal_snapshot", fail)
    else:
        spec = replace(spec, detail_counts=(2, 2, 3, 0))
    output = adapters.ForecastDetailSourceAdapter(spec, OBSERVED).extract(
        bronze, source_sha256=spec.source_sha256
    )
    assert output.status == "preserved_only"
    assert output.profiles == ()
    assert output.source_losses[0].reason == "reviewed_forecast_detail_admission_failed"


def test_explicit_registry_is_closed_and_altered_bytes_are_not_admitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bronze, spec = setup_source(monkeypatch, 0)
    context = AdapterContext(spec.source_locator, spec.source_vintage, OBSERVED)
    with pytest.raises(ValueError, match="duplicate reviewed adapter identity"):
        compound_workbook_registrations((context, context))
    with pytest.raises(ValueError, match="unsupported_forecast_detail_source_context"):
        compound_workbook_registrations((replace(context, source_vintage="unknown"),))
    entries = compound_workbook_registrations((context,))
    changed = bronze + b"changed"
    result = dispatch_native_bronze(
        changed,
        source_sha256=hashlib.sha256(changed).hexdigest(),
        media_type=adapters.MEDIA_TYPE,
        registrations=entries,
    )
    assert isinstance(result.output, AdapterOutput)
    assert result.selection.status == "preserved_only"
    assert result.output.records == ()
