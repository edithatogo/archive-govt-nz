"""Fresh Bronze recovery of supported analytical products and local metadata."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_recovery as fiscal,
)
from archive_govt_nz.domains.health_appropriations import (
    gold_discovery_profiles as discovery,
)
from archive_govt_nz.domains.health_appropriations import gold_metadata as metadata
from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)
from archive_govt_nz.domains.health_appropriations.budget_comparison_gold import (
    export_budget_comparison,
)
from archive_govt_nz.domains.health_appropriations.budget_vintage_comparison import (
    SOURCE_PINS,
    BudgetComparisonInput,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.analytical-metadata-recovery/v1"
# Reproduce retained capture context; neither locator nor timestamp is a new capture.
_BUDGET_CONTEXT = {
    "Budget-2025": ("data/raw/b25-expenditure-data.xlsx", "2026-08-30T00:00:00+00:00"),
    "Budget-2026": (
        "https://budget.govt.nz/budget/excel/data/b26-expenditure-data.xlsx",
        "2026-08-31T05:50:00+00:00",
    ),
}


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _snapshot(archive: Path) -> dict[str, str]:
    budgets = {
        vintage: hashlib.sha256(
            verified_snapshot(
                archive / "bronze-cas/sha256" / pin[:2] / pin,
                pin,
                max_bytes=64 * 1024 * 1024,
            )
        ).hexdigest()
        for vintage, pin in SOURCE_PINS.items()
    }
    # Reuse the exact source and definition bounds of the existing recovery lane.
    return {**fiscal._source_snapshot(archive), **budgets}  # noqa: SLF001


def _complete_run(archive: Path, root: Path, fiscal_pin: str) -> dict[str, Any]:
    inputs = []
    for vintage, pin in SOURCE_PINS.items():
        source = archive / "bronze-cas/sha256" / pin[:2] / pin
        package = root / vintage
        locator, observed = _BUDGET_CONTEXT[vintage]
        normalize_budget_workbook(
            source,
            package,
            expected_sha256=pin,
            source_vintage=vintage,
            source_locator=locator,
            observed_at=observed,
        )
        marker = hashlib.sha256((package / "MANIFEST.json").read_bytes()).hexdigest()
        inputs.append(BudgetComparisonInput(source, package, marker))
    budget = export_budget_comparison(
        inputs[0], inputs[1], root / "budget-gold", write=True
    )
    values = (
        metadata.GoldInput("fiscal_analytical", root / "gold", fiscal_pin),
        metadata.GoldInput(
            "budget_comparison", root / "budget-gold", budget["manifest_sha256"]
        ),
    )
    catalogue = metadata.export_gold_metadata(values, root / "metadata", write=True)
    profiles = discovery.export_profiles(values, root / "discovery", write=True)
    return {
        "budget": budget,
        "metadata": catalogue,
        "metadata_verification": metadata.verify_gold_metadata(
            values,
            root / "metadata",
            catalogue["manifest_sha256"],
        ),
        "discovery": profiles,
        "discovery_verification": discovery.verify_profiles(
            values,
            root / "discovery",
            profiles["manifest_sha256"],
        ),
    }


def recover_analytical_metadata(
    archive: Path,
    output: Path,
    *,
    write: bool = False,
) -> dict[str, Any]:
    """Keep two complete builds and partial failures; consume no retained derivatives.

    Hash-check five originals and three definition observations before any output
    is created and after all builds. Reuse the existing Fiscal CLI/MCP/report
    readbacks, then rebuild Budget comparison and both local metadata projections.
    Metadata reconstruction is verified, while full standards conformance,
    rights, publication, other source families and whole-track recovery stay open.
    """
    _require(
        not output.resolve().is_relative_to(archive.resolve())
        and not archive.resolve().is_relative_to(output.resolve()),
        "analytical_metadata_recovery_output_overlap",
    )
    before = _snapshot(archive)
    base = {
        "schema_version": VERSION,
        "source_inputs": before,
        "rights": "not_evaluated",
        "publication": "not_performed",
        "full_standards_conformance": "not_asserted",
        "full_health_completion": "not_asserted",
    }
    if not write:
        return {**base, "status": "dry_run"}
    fiscal_receipt = fiscal.recover_fiscal_analytical_products(archive, output)
    fiscal_pin = fiscal_receipt["products"]["gold"]["manifest_sha256"]
    first, second = output / "first", output / "second"
    additions = [_complete_run(archive, root, fiscal_pin) for root in (first, second)]
    inventory = fiscal._inventory(first)  # noqa: SLF001 - same owned-output bounds.
    _require(
        inventory == fiscal._inventory(second) and additions[0] == additions[1],  # noqa: SLF001
        "analytical_metadata_recovery_repeat_mismatch",
    )
    _require(
        _snapshot(archive) == before, "analytical_metadata_recovery_input_mutation"
    )
    return {
        **base,
        "status": "verified",
        "fresh_bronze_builds": 2,
        "retained_derivatives_consumed": False,
        "repeat_identical": True,
        "originals_and_definitions_unchanged": True,
        "output_inventory": inventory,
        "fiscal_recovery": fiscal_receipt,
        "products": additions[0],
    }
