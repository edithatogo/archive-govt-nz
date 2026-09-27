"""Exact-layout dispatch contracts for Pharmac's CPB source table."""

from __future__ import annotations

import hashlib

import pytest

from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.pharmac import (
    CONTEXT,
    HEADERS,
)
from archive_govt_nz.domains.health_appropriations.pharmac_adapter import (
    PharmacBudgetAdapter,
    pharmac_budget_registration,
)


def payload() -> bytes:
    parts = ["<html>", *[f"<p>{value}</p>" for value in CONTEXT], "<table><tr>"]
    for index, label in enumerate(HEADERS):
        span = ' colspan="2"' if index == 3 else ""
        parts.append(f"<th{span}>{label}</th>")
    parts.append("</tr>")
    for year in range(2026, 2012, -1):
        values = [f"{year}/{(year + 1) % 100:02}", "1,234.5", "4.5", "0.6%"]
        if year <= 2016:
            values.append("")
        parts.append("<tr>")
        for index, value in enumerate(values):
            span = ' colspan="2"' if index == 3 and year > 2016 else ""
            parts.append(f"<td{span}>{value}</td>")
        parts.append("</tr>")
    parts.append("</table></html>")
    return "".join(parts).encode()


def registration() -> AdapterRegistration:
    return pharmac_budget_registration(
        source_locator="https://www.pharmac.govt.nz/cpb",
        source_vintage="Pharmac-CPB-2026-08-07",
        observed_at="2026-08-29T09:00:00Z",
    )


def test_dispatch_emits_only_exact_pharmac_table_facts_and_lineage() -> None:
    bronze = payload()
    result = dispatch_bronze(
        bronze,
        source_sha256=hashlib.sha256(bronze).hexdigest(),
        media_type="text/html",
        registrations=(registration(),),
    )
    assert result.selection.status == "selected"
    assert result.output.layout == "pharmac-published-budget-20260807/v1"
    assert len(result.output.records) == 14
    assert result.output.records[0]["amount_type"] == "published_budget_allocation"
    assert result.output.records[0]["rights_state"] == "not_evaluated"
    assert len(result.output.lineage) == 186
    assert result.output.losses
    assert all(
        loss.disposition not in ("normalized", "context")
        for loss in result.output.losses
    )


def test_pharmac_dispatch_fails_closed_on_layout_drift() -> None:
    bronze = payload().replace(b"FINANCIAL YEAR", b"FINANCIAL PERIOD", 1)
    result = dispatch_bronze(
        bronze,
        source_sha256=hashlib.sha256(bronze).hexdigest(),
        media_type="text/html",
        registrations=(registration(),),
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.reason == "no_matching_layout"
    assert result.output.records == ()


def test_pharmac_dispatch_requires_exact_media_type() -> None:
    bronze = payload()
    result = dispatch_bronze(
        bronze,
        source_sha256=hashlib.sha256(bronze).hexdigest(),
        media_type="application/octet-stream",
        registrations=(registration(),),
    )
    assert result.selection.status == "preserved_only"


def test_pharmac_adapter_rejects_hash_vintage_and_malformed_html() -> None:
    bronze = payload()
    adapter = PharmacBudgetAdapter("source", "Pharmac-CPB-2026-08-07", "now")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        adapter.extract(bronze, source_sha256="0" * 64)
    assert adapter.matches_layout(bronze)
    assert not PharmacBudgetAdapter("source", "wrong", "now").matches_layout(bronze)
    assert not adapter.matches_layout(b"<html>\xff</html>")
    assert not adapter.matches_layout(b"")
    drifted = bronze.replace(b"FINANCIAL YEAR", b"FINANCIAL PERIOD", 1)
    output = adapter.extract(drifted, source_sha256=hashlib.sha256(drifted).hexdigest())
    assert output.losses[0].reason == "unsupported_pharmac_budget_html_layout"
