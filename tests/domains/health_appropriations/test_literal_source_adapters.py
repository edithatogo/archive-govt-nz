"""Physical literal bundles preserve native facts, JSON lineage and exclusions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations import (
    literal_source_adapter as adapters,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_payload,
)

if TYPE_CHECKING:
    from tests.domains.health_appropriations.adapter_context_fixtures import (
        RequiredContexts,
    )


def payload() -> bytes:
    book = Workbook()
    output = BytesIO()
    book.save(output)
    book.close()
    return output.getvalue()


def admission(profile: str, context: dict[str, Any]) -> dict[str, Any]:
    record = {
        **context,
        "record_id": "sha256:" + "a" * 64,
        "source_observation_id": "retained-source-observation",
        "source_coordinate": "Sheet!A1",
        "sheet": "Sheet",
        "coordinate": "A1",
        "amount": Decimal("2.5"),
        "source_number_token": "2.5",
        "currency": None,
        "observed_at": datetime(2026, 8, 29, tzinfo=UTC),
        "raw_context": {"Sheet!A2" if profile == "crown" else "A2": "year"},
        "lineage": {"amount": "Sheet!A1"},
    }
    return {
        "records": [record],
        "facts": [record],
        "workbook_inventory": {"sheets": [{"title": "Sheet"}]},
        "formula_totals": {
            "range": "A3:B3",
            "disposition": "excluded_formula_cache_not_admitted",
        },
        "excluded_formulas": [
            {
                "sheet": "Sheet",
                "coordinate": "A3",
                "reason": "formula_cache_not_admitted",
            }
        ],
    }


@pytest.mark.parametrize("index", range(5))
def test_one_physical_registration_preserves_all_native_profile_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, index: int
) -> None:
    bronze = payload()
    pin = hashlib.sha256(bronze).hexdigest()
    spec = replace(adapters.BUNDLES[index], source_sha256=pin)
    monkeypatch.setattr(adapters, "BUNDLES", (spec,))
    calls = []

    def admit_snapshot(
        data: bytes, *, profile: str, context: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        assert data == bronze
        calls.append(profile)
        return admission(profile, context), context

    monkeypatch.setattr(packages, "admit_literal_snapshot", admit_snapshot)
    registration = adapters.literal_source_registration(
        source_locator=spec.source_locator,
        source_vintage=spec.source_vintage,
        observed_at="2026-08-30T08:58:00+00:00",
    )
    result = dispatch_bronze(
        bronze,
        source_sha256=pin,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=(registration,),
    )
    expected_facts, expected_links, expected_areas = [], [], []
    for profile in spec.profiles:
        context = {
            "source_object_sha256": pin,
            "source_locator": spec.source_locator,
            "source_vintage": spec.source_vintage,
            "observed_at": "2026-08-30T08:58:00+00:00",
        }
        output = tmp_path / profile
        packages.write_literal_package(
            output, admission(profile, context), profile=profile, context=context
        )
        expected_facts.extend(
            pq.read_table(output / "literal_facts.parquet").to_pylist()
        )
        expected_links.extend(
            (
                row["record_id"],
                row["field"],
                row["source_coordinate"],
                row["raw_value_json"],
            )
            for row in pq.read_table(output / "field_lineage.parquet").to_pylist()
        )
        expected_areas.extend(
            {"profile": profile, **row}
            for row in pq.read_table(output / "area_dispositions.parquet").to_pylist()
        )
    assert result.output.records == tuple(expected_facts)
    assert [
        (r.record_id, r.field, r.source_coordinate, r.raw_value)
        for r in result.output.lineage
    ] == expected_links
    assert all(
        r.raw_value == r.normalized_value
        and r.rule == "literal_source_json_preserved/v1"
        for r in result.output.lineage
    )
    recovered_areas = [
        json.loads(row.source_coordinate.removeprefix(adapters.AREA_COORDINATE_PREFIX))
        for row in result.output.losses
    ]
    assert recovered_areas == expected_areas
    assert all(
        row.disposition == original["state"] and row.reason == original["reason"]
        for row, original in zip(result.output.losses, expected_areas, strict=True)
    )
    assert set(calls) == set(spec.profiles)
    assert len({r["record_id"] for r in result.output.records}) == len(spec.profiles)
    assert result == dispatch_bronze(
        bronze,
        source_sha256=pin,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=(registration,),
    )
    altered = bronze + b"changed"
    retained = dispatch_bronze(
        altered,
        source_sha256=hashlib.sha256(altered).hexdigest(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=(registration,),
    )
    assert retained.selection.status == "preserved_only"
    assert not retained.output.records


def test_bundle_inventory_has_five_distinct_sources_and_seven_profiles() -> None:
    assert len(adapters.BUNDLES) == 5
    assert len({s.source_sha256 for s in adapters.BUNDLES}) == 5
    profiles = [p for s in adapters.BUNDLES for p in s.profiles]
    assert sorted(profiles) == sorted(packages.PROFILES)
    assert sorted(len(s.profiles) for s in adapters.BUNDLES) == [1, 1, 1, 2, 2]


def test_registry_adds_physical_bundles_once_without_changing_defaults() -> None:
    observed = "2026-08-30T08:58:00+00:00"
    base: RequiredContexts = {
        "cpi": AdapterContext("cpi", "2026-Q2", observed),
        "population": AdapterContext("population", "2026-08-18", observed),
        "qes": AdapterContext("qes", "QES-2026-Q2", observed),
        "gdp": AdapterContext("gdp", "StatsNZ-GDP-2026-Q2", observed),
    }
    contexts = tuple(
        AdapterContext(s.source_locator, s.source_vintage, observed)
        for s in adapters.BUNDLES
    )
    registrations = context_adapter_registrations(**base, literal_workbooks=contexts)
    assert len(context_adapter_registrations(**base)) == 4
    assert len(registrations) == 9
    assert len({r.adapter_id for r in registrations}) == 9
    with pytest.raises(ValueError, match="duplicate"):
        context_adapter_registrations(
            **base, literal_workbooks=(*contexts, contexts[0])
        )


def test_sibling_failure_retains_whole_source_without_partial_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bronze = payload()
    pin = hashlib.sha256(bronze).hexdigest()
    spec = replace(
        next(s for s in adapters.BUNDLES if len(s.profiles) == 2), source_sha256=pin
    )
    monkeypatch.setattr(adapters, "BUNDLES", (spec,))

    def admit_snapshot(
        data: bytes, *, profile: str, context: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        assert data == bronze
        if profile == spec.profiles[-1]:
            message = "synthetic_sibling_failure"
            raise ValueError(message)
        return admission(profile, context), context

    monkeypatch.setattr(packages, "admit_literal_snapshot", admit_snapshot)
    handler = adapters.literal_source_registration(
        source_locator=spec.source_locator,
        source_vintage=spec.source_vintage,
        observed_at="2026-08-30T08:58:00+00:00",
    )
    result = dispatch_bronze(
        bronze,
        source_sha256=pin,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=(handler,),
    )
    assert not result.output.records
    assert not result.output.lineage
    assert result.output.losses[0].reason == "reviewed_literal_admission_failed"


def test_invalid_context_and_declared_fixity_fail_closed() -> None:
    spec = adapters.BUNDLES[0]
    with pytest.raises(ValueError, match="unsupported_literal_source_context"):
        adapters.literal_source_registration(
            source_locator=spec.source_locator + "changed",
            source_vintage=spec.source_vintage,
            observed_at="2026-08-30T08:58:00+00:00",
        )
    handler = adapters.LiteralSourceAdapter(spec, "2026-08-30T08:58:00+00:00")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        handler.extract(b"unknown", source_sha256="0" * 64)


@pytest.mark.parametrize(
    ("limit", "pin", "error"),
    [
        (0, "0" * 64, "invalid_source_limit"),
        (1, "0" * 64, "source_byte_limit"),
        (2, "0" * 64, "source_hash_mismatch"),
    ],
)
def test_in_memory_snapshot_limits_precede_workbook_decoding(
    limit: int, pin: str, error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        verified_payload(b"xx", pin, max_bytes=limit)
