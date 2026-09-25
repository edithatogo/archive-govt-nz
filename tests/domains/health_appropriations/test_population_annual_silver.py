"""Typed Silver output retains annual population context without selection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pyarrow.parquet as pq
from tests.domains.health_appropriations.test_population_annual_export import payload

from archive_govt_nz.domains.health_appropriations.population_annual_silver import (
    normalize_population_annual,
)


def test_preflight_and_written_silver_package(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    content = payload()
    source.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    output = tmp_path / "silver"
    observed_at = "2026-09-25T09:37:50Z"
    source_vintage = "2026-08-18"
    source_locator = "https://infoshare.stats.govt.nz/ExportDirect.aspx"
    planned = normalize_population_annual(
        source,
        output,
        expected_sha256=digest,
        observed_at=observed_at,
        source_vintage=source_vintage,
        source_locator=source_locator,
    )
    assert planned["status"] == "planned"
    assert planned["counts"] == {
        "input": 36,
        "facts": 36,
        "numeric": 35,
        "missing": 1,
        "provisional": 2,
        "lineage": 72,
    }
    assert not output.exists()

    manifest = normalize_population_annual(
        source,
        output,
        expected_sha256=digest,
        observed_at=observed_at,
        source_vintage=source_vintage,
        source_locator=source_locator,
        dry_run=False,
    )
    assert manifest["status"] == "passed"
    output_hashes = cast("dict[str, str]", manifest["output_sha256"])
    assert set(output_hashes) == {
        "population_facts.parquet",
        "field_lineage.parquet",
        "row_dispositions.parquet",
    }
    facts = pq.read_table(output / "population_facts.parquet")
    first = facts.to_pylist()[0]
    assert first["amount"] is None
    assert first["null_reason"] == "figure_not_available"
    assert first["valid_time_start"].isoformat() == "1990-07-01"
    assert first["valid_time_end"].isoformat() == "1991-06-30"
    assert first["rights_state"] == "not_evaluated"
    assert "context_only_not_selected_as_denominator" in first["quality_flags"]
    assert "denominator not selected" in first["observation_context"]
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert len(lineage) == 72
    disposition_rows = pq.read_table(output / "row_dispositions.parquet").to_pylist()
    assert [json.loads(row["raw_values_json"]) for row in disposition_rows[-2:]] == [
        {"status": "P", "value": "3502025", "year": "2025"},
        {"status": "P", "value": "3502026", "year": "2026"},
    ]
    assert pq.read_table(output / "row_dispositions.parquet").num_rows == 36
    for name, expected in output_hashes.items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected
    disk_manifest = json.loads((output / "MANIFEST.json").read_text())
    assert disk_manifest == manifest
