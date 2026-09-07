"""Pinned population metadata profile, independent of analytical admission."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import model_validator

from archive_govt_nz.domains.health_appropriations.source_context_census import (
    Contract,
    Digest,
)


class Estimate(Contract):
    """Publisher query code and label; no derived population calculation."""

    code: Literal["1", "2"]
    label: Literal["As at", "Mean year ended"]


class QueryExport(Contract):
    """Recorded metadata response, not an assertion about a data download."""

    http_status: Literal[200]
    response_kind: Literal["tqx_selection_metadata"]
    media_type: Literal["text/plain"]
    byte_count: Literal[798]
    sha256: Digest
    selected_time_code: Literal["20262"]
    contains_observations: Literal[False]


class PopulationContext(Contract):
    """Exact June-2026 profile supported by the recorded official metadata.

    This validates the receipt's consistency, not live endpoint availability.
    New vintages or analytical policies require a separately reviewed profile.
    """

    schema_version: Literal["archive-govt-nz.population-context/v1"]
    table_id: Literal["DPE054AA"]
    table_title: Literal[
        "Estimated Resident Population by Age and Sex (1991+) (Qrtly-Mar/Jun/Sep/Dec)"
    ]
    legacy_identifiers_found: list[Literal["DPEQ.SG1CTOT", "DPEQ.SG2CTOT"]]
    population_code: Literal["C"]
    population_label: Literal["Total"]
    age_code: Literal["DPE054FF"]
    age_label: Literal["Total All Ages"]
    unit: Literal["persons"]
    frequency: Literal["quarterly"]
    reference_period: Literal["2026Q2"]
    reference_date: Literal["2026-06-30"]
    basis_date: Literal["2023-06-30"]
    release_date: Literal["2026-08-18"]
    available_period_start: Literal["1991Q1"]
    available_period_end: Literal["2026Q2"]
    estimates: list[Estimate]
    metadata_url: Literal[
        "https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/"
        "4c9f3523-5386-4ce0-a8bd-993bb905f119"
    ]
    release_url: Literal[
        "https://www.stats.govt.nz/information-releases/"
        "national-population-estimates-at-30-june-2026/"
    ]
    export_entry_url: Literal["https://infoshare.stats.govt.nz/ExportDirect.aspx"]
    query_entry_url: Literal["https://infoshare.stats.govt.nz/QueryUpload.aspx"]
    query_export: QueryExport
    numeric_export_response: Literal["not_verified"]
    analytical_selection: Literal["not_selected"]
    rights: Literal["not_evaluated"]

    @model_validator(mode="after")
    def exact_selections(self) -> Self:
        """Reject missing or contradictory official selector identities."""
        pairs = [(item.code, item.label) for item in self.estimates]
        if sorted(pairs) != [("1", "As at"), ("2", "Mean year ended")]:
            message = "population estimate code and label mismatch"
            raise ValueError(message)
        if sorted(self.legacy_identifiers_found) != [
            "DPEQ.SG1CTOT",
            "DPEQ.SG2CTOT",
        ]:
            message = "population legacy identifier enumeration mismatch"
            raise ValueError(message)
        return self


def qualification(context: PopulationContext) -> dict[str, str]:
    """Report independent stages without choosing a spending denominator."""
    return {
        "definition_enumeration": "complete",
        "query_metadata_export": "verified",
        "numeric_export_response": context.numeric_export_response,
        "analytical_selection": context.analytical_selection,
        "rights": context.rights,
    }
