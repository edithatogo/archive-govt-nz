"""Common dispatch must preserve the already reviewed native summary products."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations import (
    test_vote_health_supplementary_2024_25 as fixture_2024,
)
from tests.domains.health_appropriations import (
    test_vote_health_supplementary_2025_26 as fixture_2025,
)

from archive_govt_nz.domains.health_appropriations import (
    supplementary_summary_adapter as adapters,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2024_25 as source_2024,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2025_26 as source_2025,
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


OBSERVED = "2026-10-18T00:00:00Z"


@pytest.mark.parametrize("edition", [2024, 2025])
def test_dispatch_matches_native_records_lineage_and_repeat_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, edition: int
) -> None:
    module = source_2024 if edition == 2024 else source_2025
    text = fixture_2024._PAGE_TEXT if edition == 2024 else fixture_2025._PAGE_TEXT  # noqa: SLF001 - reuse the existing independent parser fixtures.
    payload = b"%PDF-1.4\ncontrolled supplementary fixture"
    pin = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(module, "SOURCE_SHA256", pin)

    class Page:
        def extract_text(self) -> str:
            return text

    class Reader:
        is_encrypted = False

        def __init__(self) -> None:
            self.pages = [Page() for _ in range(module.PAGE_COUNT)]

    monkeypatch.setattr(module, "PdfReader", lambda *_args, **_kwargs: Reader())
    registration = adapters.supplementary_summary_registration(
        source_locator=module.SOURCE_LOCATOR,
        source_vintage=module.VINTAGE,
        observed_at=OBSERVED,
    )
    dispatched = dispatch_bronze(
        payload,
        source_sha256=pin,
        media_type="application/pdf",
        registrations=(registration,),
    )
    source = tmp_path / "source.pdf"
    source.write_bytes(payload)
    output = tmp_path / "native"
    module.normalize(
        source,
        output,
        expected_sha256=pin,
        source_locator=module.SOURCE_LOCATOR,
        source_vintage=module.VINTAGE,
        observed_at=OBSERVED,
        dry_run=False,
    )
    native = pq.read_table(
        output / "vote_health_supplementary_summary_facts.parquet"
    ).to_pylist()
    assert dispatched.output.records == tuple(native)
    expected_lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert [asdict(row) for row in dispatched.output.lineage] == [
        {
            key: value
            for key, value in row.items()
            if key in asdict(dispatched.output.lineage[0])
        }
        for row in expected_lineage
    ]
    assert len(dispatched.output.losses) == module.PAGE_COUNT
    assert (
        sum(row.disposition == "preserved_only" for row in dispatched.output.losses)
        == module.PAGE_COUNT - 1
    )
    assert dispatched.output.records[-1]["estimates_budget"] is None
    flags = dispatched.output.records[-1]["quality_flags"]
    assert isinstance(flags, list)
    assert "source_reported_capital_injection_authorisation" in flags
    repeated = dispatch_bronze(
        payload,
        source_sha256=pin,
        media_type="application/pdf",
        registrations=(registration,),
    )
    assert repeated == dispatched
    assert source.read_bytes() == payload
    rejected = dispatch_bronze(
        payload + b" changed",
        source_sha256=hashlib.sha256(payload + b" changed").hexdigest(),
        media_type="application/pdf",
        registrations=(registration,),
    )
    assert rejected.selection.status == "preserved_only"
    assert rejected.output.records == ()


def test_registry_adds_only_requested_supplementary_profiles() -> None:
    contexts: RequiredContexts = {
        "cpi": AdapterContext("cpi", "2026-Q2", OBSERVED),
        "population": AdapterContext("population", "2026-08-18", OBSERVED),
        "qes": AdapterContext("qes", "QES-2026-Q2", OBSERVED),
        "gdp": AdapterContext("gdp", "StatsNZ-GDP-2026Q1", OBSERVED),
    }
    supplied = tuple(
        AdapterContext(module.SOURCE_LOCATOR, module.VINTAGE, OBSERVED)
        for module in [source_2024, source_2025]
    )
    registrations = context_adapter_registrations(
        **contexts, vote_health_supplementary_summaries=supplied
    )
    assert len(registrations) == 6
    assert len({row.adapter_id for row in registrations}) == 6
    assert [row.adapter_id for row in registrations] == sorted(
        row.adapter_id for row in registrations
    )
    with pytest.raises(ValueError, match="duplicate reviewed adapter identity"):
        context_adapter_registrations(
            **contexts, vote_health_supplementary_summaries=(supplied[0], supplied[0])
        )


@pytest.mark.parametrize("field", ["source_vintage", "source_locator"])
def test_registration_refuses_unreviewed_identity(field: str) -> None:
    context = {
        "source_locator": source_2024.SOURCE_LOCATOR,
        "source_vintage": source_2024.VINTAGE,
        "observed_at": OBSERVED,
    }
    context[field] = "unreviewed"
    with pytest.raises(ValueError, match="unsupported_supplementary_summary_context"):
        adapters.supplementary_summary_registration(**context)
