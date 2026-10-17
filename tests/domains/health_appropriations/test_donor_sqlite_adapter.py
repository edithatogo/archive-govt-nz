"""Pinned donor dispatch must reuse the existing SQLite and Silver contracts."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_silver import _database

from archive_govt_nz.domains.health_appropriations import (
    donor_sqlite_adapter as adapter,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)
from archive_govt_nz.domains.health_appropriations.donor_sqlite import (
    read_rows,
    read_snapshot,
)
from archive_govt_nz.domains.health_appropriations.silver import normalize_donor_sqlite

if TYPE_CHECKING:
    from tests.domains.health_appropriations.adapter_context_fixtures import (
        RequiredContexts,
    )


def test_dispatch_preserves_native_facts_lineage_and_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "donor.sqlite"
    _database(source)
    payload = source.read_bytes()
    pin = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(adapter, "SOURCE_SHA256", pin)
    assert read_snapshot(payload, pin) == read_rows(source, pin)
    context = adapter.DonorSQLiteContext("obs-1", "2026-08-29T00:00:00Z")
    registration = adapter.donor_sqlite_registration(context)
    result = dispatch_bronze(
        payload,
        source_sha256=pin,
        media_type="application/vnd.sqlite3",
        registrations=(registration,),
    )
    output = tmp_path / "native"
    normalize_donor_sqlite(
        source,
        output,
        source_sha256=pin,
        observation_id=context.observation_id,
        observed_at=context.observed_at,
    )
    assert result.output.records == tuple(
        pq.read_table(output / "donor_facts.parquet").to_pylist()
    )
    links = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert [asdict(row) for row in result.output.lineage] == [
        {
            key: value
            for key, value in row.items()
            if key in asdict(result.output.lineage[0])
        }
        for row in links
    ]
    assert len(result.output.losses) == 5
    assert result == dispatch_bronze(
        payload,
        source_sha256=pin,
        media_type="application/vnd.sqlite3",
        registrations=(registration,),
    )
    altered = payload + b"changed"
    rejected = dispatch_bronze(
        altered,
        source_sha256=hashlib.sha256(altered).hexdigest(),
        media_type="application/vnd.sqlite3",
        registrations=(registration,),
    )
    assert rejected.selection.status == "preserved_only"
    assert not rejected.output.records
    assert source.read_bytes() == payload


def test_snapshot_retains_byte_and_row_bounds(tmp_path: Path) -> None:
    source = tmp_path / "donor.sqlite"
    _database(source)
    payload = source.read_bytes()
    pin = hashlib.sha256(payload).hexdigest()
    with pytest.raises(ValueError, match="database_size_limit"):
        read_snapshot(payload, pin, max_bytes=len(payload) - 1)
    with pytest.raises(ValueError, match="database_row_limit"):
        read_snapshot(payload, pin, max_rows=4)
    with pytest.raises(ValueError, match="database_fixity"):
        read_snapshot(payload, "0" * 64)


def test_registry_opt_in_keeps_existing_default_profiles() -> None:
    observed = "2026-08-29T00:00:00Z"
    base: RequiredContexts = {
        "cpi": AdapterContext("cpi", "2026-Q2", observed),
        "population": AdapterContext("population", "2026-08-18", observed),
        "qes": AdapterContext("qes", "QES-2026-Q2", observed),
        "gdp": AdapterContext("gdp", "StatsNZ-GDP-2026-Q2", observed),
    }
    defaults = context_adapter_registrations(**base)
    expanded = context_adapter_registrations(
        **base, donor_sqlite=adapter.DonorSQLiteContext("obs-1", observed)
    )
    assert len(defaults) == 4
    assert len(expanded) == 5
    assert [
        (row.adapter_id, row.version, row.media_type)
        for row in expanded
        if row.adapter_id != "nz-health-donor-sqlite-parity"
    ] == [(row.adapter_id, row.version, row.media_type) for row in defaults]
    assert [row.adapter_id for row in expanded] == sorted(
        row.adapter_id for row in expanded
    )


def test_direct_adapter_checks_declared_fixity_and_preserves_unknown_bytes() -> None:
    payload = b"unsupported"
    handler = adapter.DonorSQLiteAdapter(
        adapter.DonorSQLiteContext("obs-1", "2026-08-29T00:00:00Z")
    )
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        handler.extract(payload, source_sha256="0" * 64)
    retained = handler.extract(
        payload, source_sha256=hashlib.sha256(payload).hexdigest()
    )
    assert not retained.records
    assert retained.losses[0].disposition == "preserved_only"
