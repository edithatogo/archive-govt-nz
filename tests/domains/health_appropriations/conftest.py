"""Synthetic hash-pinned raw runs shared by health derivative tests."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import rebuild
from archive_govt_nz.object_store import ContentAddressedStore


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def raw_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, str]:
    store = ContentAddressedStore(tmp_path / "bronze")
    sources = {}
    for name, profile in rebuild.PROFILES.items():
        item = store.put_bytes(name.encode())
        sources[name] = {
            "object_id": item.object_id,
            "sha256": item.sha256,
            "locator": "data/raw/" + profile.filename,
            "vintage": profile.vintage,
        }
    plan = {
        "schema_version": "archive-govt-nz.health-raw-rebuild/v1",
        "donor_manifest_sha256": "a" * 64,
        "observed_at": "2026-08-30T00:00:00+00:00",
        "sources": sources,
    }

    def adapter(source: Path, output: Path, **context: str) -> None:
        name = source.read_text()
        profile = rebuild.PROFILES[name]
        measures = (
            ["health_spending", "nominal_gdp"]
            if name == "historical"
            else ["appropriation_amount" if name == "budget" else "health_spending"]
        )
        facts, lineage = [], []
        for measure in measures:
            record = "sha256:" + hashlib.sha256((name + measure).encode()).hexdigest()
            amount = (
                Decimal("605.70000000000005")
                if name == "historical" and measure == "health_spending"
                else Decimal(123)
            )
            facts.append(
                {
                    "record_id": record,
                    "source_object_sha256": context["expected_sha256"],
                    "source_locator": context["source_locator"],
                    "source_vintage": context["source_vintage"],
                    "year": 1976,
                    "period_end_month": 6,
                    "valid_time_end": date(1976, 6, 30),
                    "accounting_basis": "Cash"
                    if measure == "health_spending"
                    else None,
                    "quality_flags": ["period_start_not_provided"],
                    "measure": measure,
                    "unit": "NZD_thousands" if name == "budget" else "NZD_millions",
                    "amount": amount,
                    "department": "Ministry",
                    "appropriation_name": "Services",
                    "functional_classification": "Health",
                    "amount_type": "Actual",
                    "portfolio_name": "Health",
                }
            )
            lineage.append(
                {
                    "record_id": record,
                    "field": "amount",
                    "source_object_sha256": context["expected_sha256"],
                    "source_locator": context["source_locator"],
                    "source_coordinate": "'Sheet'!B2",
                    "normalized_value": str(amount),
                }
            )
        output.mkdir()
        for filename, rows in zip(
            profile.outputs,
            (facts, lineage, [{"disposition": "selected"}]),
            strict=True,
        ):
            pq.write_table(pa.Table.from_pylist(rows), output / filename)
        receipt = {
            "schema_version": profile.schema,
            "status": "passed",
            "source_object_sha256": context["expected_sha256"],
            "source_locator": context["source_locator"],
            "source_vintage": context["source_vintage"],
            "observed_at": context["observed_at"],
            "output_sha256": {f: _hash(output / f) for f in profile.outputs},
        }
        (output / "MANIFEST.json").write_text(json.dumps(receipt))

    for name in (
        "normalize_budget_workbook",
        "normalize_forecast_workbook",
        "normalize_historical_workbook",
    ):
        monkeypatch.setattr(rebuild, name, adapter)
    root = tmp_path / "raw"
    rebuild.execute_rebuild(plan, tmp_path / "bronze", root)
    return root, tmp_path / "bronze", _hash(root / "MANIFEST.json")
