"""Historical dispatch retains native facts and complete loss descriptors."""

from __future__ import annotations

import builtins
import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_historical import _source

from archive_govt_nz.domains.health_appropriations import historical
from archive_govt_nz.domains.health_appropriations import (
    historical_source_adapter as adapter,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)

if TYPE_CHECKING:
    from tests.domains.health_appropriations.adapter_context_fixtures import (
        RequiredContexts,
    )


OBSERVED = "2026-08-30T08:58:00+00:00"
MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_dispatch_preserves_native_rows_and_every_cell_and_sheet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source(tmp_path)
    bronze = source.read_bytes()
    pin = hashlib.sha256(bronze).hexdigest()
    monkeypatch.setattr(adapter, "SOURCE_SHA256", pin)
    context = {
        "source_locator": adapter.SOURCE_LOCATOR,
        "source_vintage": adapter.VINTAGE,
        "observed_at": OBSERVED,
    }
    native = tmp_path / "native"
    receipt = historical.normalize_historical_workbook(
        source, native, expected_sha256=pin, **context
    )
    facts = pq.read_table(native / "historical_facts.parquet").to_pylist()
    links = pq.read_table(native / "field_lineage.parquet").to_pylist()
    cells = pq.read_table(native / "cell_dispositions.parquet").to_pylist()
    registration = adapter.historical_source_registration(**context)
    first = dispatch_bronze(
        bronze, source_sha256=pin, media_type=MEDIA_TYPE, registrations=(registration,)
    )
    assert list(first.output.records) == facts
    assert [
        {
            "record_id": r.record_id,
            "field": r.field,
            "source_coordinate": r.source_coordinate,
            "raw_value": r.raw_value,
            "normalized_value": r.normalized_value,
            "rule": r.rule,
        }
        for r in first.output.lineage
    ] == [
        {
            k: row[k]
            for k in (
                "record_id",
                "field",
                "source_coordinate",
                "raw_value",
                "normalized_value",
                "rule",
            )
        }
        for row in links
    ]
    decoded_cells = [
        json.loads(r.source_coordinate.removeprefix(adapter.CELL_COORDINATE_PREFIX))
        for r in first.output.losses
        if r.source_coordinate.startswith(adapter.CELL_COORDINATE_PREFIX)
    ]
    assert decoded_cells == cells
    assert [(r.disposition, r.reason) for r in first.output.losses[: len(cells)]] == [
        (row["disposition"], row["reason"]) for row in cells
    ]
    decoded_sheets = [
        json.loads(r.source_coordinate.removeprefix(adapter.SHEET_COORDINATE_PREFIX))
        for r in first.output.losses
        if r.source_coordinate.startswith(adapter.SHEET_COORDINATE_PREFIX)
    ]
    excluded = cast("list[dict[str, str]]", receipt["excluded_sheets"])
    assert decoded_sheets == [{"source_object_sha256": pin, **row} for row in excluded]
    by_id = {row["record_id"]: row for row in facts}
    for link in links:
        for field in ("lineage_id", "source_object_sha256", "source_locator"):
            assert link[field] == by_id[link["record_id"]][field]
    assert len(facts) == 10
    assert str(facts[0]["amount"]) == "605.70000000000005000"

    def deny(*_args: object, **_kwargs: object) -> None:
        message = "dispatch attempted Python file access"
        raise AssertionError(message)

    with monkeypatch.context() as guarded:
        guarded.setattr(builtins, "open", deny)
        guarded.setattr(Path, "open", deny)
        guarded.setattr(os, "open", deny)
        second = dispatch_bronze(
            bronze,
            source_sha256=pin,
            media_type=MEDIA_TYPE,
            registrations=(registration,),
        )
    assert first == second
    assert source.read_bytes() == bronze


def test_unknown_bytes_and_native_header_drift_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source(tmp_path, ("Spending", "A3", "changed units"))
    bronze = source.read_bytes()
    pin = hashlib.sha256(bronze).hexdigest()
    monkeypatch.setattr(adapter, "SOURCE_SHA256", pin)
    registration = adapter.historical_source_registration(
        source_locator=adapter.SOURCE_LOCATOR,
        source_vintage=adapter.VINTAGE,
        observed_at=OBSERVED,
    )
    result = dispatch_bronze(
        bronze, source_sha256=pin, media_type=MEDIA_TYPE, registrations=(registration,)
    )
    assert not result.output.records
    assert not result.output.lineage
    assert result.output.losses[0].disposition == "preserved_only"
    changed = bronze + b"changed"
    result = dispatch_bronze(
        changed,
        source_sha256=hashlib.sha256(changed).hexdigest(),
        media_type=MEDIA_TYPE,
        registrations=(registration,),
    )
    assert not result.output.records
    assert not result.output.lineage
    assert result.output.losses[0].disposition == "preserved_only"
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        registration.adapter.extract(bronze, source_sha256="0" * 64)


def test_closed_context_and_optional_registry() -> None:
    required_contexts: RequiredContexts = {
        "cpi": AdapterContext("cpi", "2026-Q2", OBSERVED),
        "population": AdapterContext("population", "2026-08-18", OBSERVED),
        "qes": AdapterContext("qes", "QES-2026-Q2", OBSERVED),
        "gdp": AdapterContext("gdp", "StatsNZ-GDP-2026-Q2", OBSERVED),
    }
    context = AdapterContext(adapter.SOURCE_LOCATOR, adapter.VINTAGE, OBSERVED)
    original = context_adapter_registrations(**required_contexts)
    expanded = context_adapter_registrations(
        **required_contexts, historical_workbook=context
    )
    assert tuple(
        (r.adapter_id, r.version, r.media_type, r.adapter)
        for r in expanded
        if r.adapter_id != adapter.ADAPTER_ID
    ) == tuple((r.adapter_id, r.version, r.media_type, r.adapter) for r in original)
    assert len(expanded) == len(original) + 1
    assert sum(r.adapter_id == adapter.ADAPTER_ID for r in expanded) == 1
    with pytest.raises(ValueError, match="unsupported_historical_source_context"):
        adapter.historical_source_registration(
            source_locator=adapter.SOURCE_LOCATOR,
            source_vintage="fiscal-2025",
            observed_at=OBSERVED,
        )
    with pytest.raises(ValueError, match="Invalid isoformat"):
        adapter.historical_source_registration(
            source_locator=adapter.SOURCE_LOCATOR,
            source_vintage=adapter.VINTAGE,
            observed_at="not-a-time",
        )
