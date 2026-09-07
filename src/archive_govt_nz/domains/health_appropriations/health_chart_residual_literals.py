"""Six pinned Health chart literals, without period or spending equivalence."""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, TypedDict

from openpyxl import load_workbook

from archive_govt_nz.domains.health_appropriations.befu_chart_literals import (
    _selected_tokens,
)
from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook
from archive_govt_nz.domains.health_appropriations.historical import _exact_amount
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path


class Profile(TypedDict):
    """Exact sheet coordinates and source semantics, bound to an original."""

    sha256: str
    locator: str
    sheet: str
    anchors: dict[str, str | int]
    selected: tuple[str, ...]
    label_cell: str
    unit_cell: str
    measure: str
    header_rows: tuple[int, ...]
    period_status: str


PROFILES: dict[str, Profile] = {
    "BEFU-2025": {
        "sha256": "cf98f5e21f60c76c7d05f788df7955fb45cfdd780c12cb18e26ff8e83615e168",
        "locator": "data/raw/befu25-charts-data.xlsx",
        "sheet": "Data 2.12",
        "anchors": {
            "B1": "Figure 2.12: Breakdown of total core Crown net capital spending",
            "B2": "Source: The Treasury",
            "B4": "Net capital spending",
            "B5": "Area",
            "C5": "$millions",
            "B8": "Health",
        },
        "selected": ("C8",),
        "label_cell": "B8",
        "unit_cell": "C5",
        "measure": "health_net_capital_spending",
        "header_rows": (),
        "period_status": "unknown_no_period_on_source_sheet",
    },
    "HYEFU-2024": {
        "sha256": "f77bdab5ef808b0e451a52b9b448a52b07899bc4523da3c02aa5725325d6203c",
        "locator": "data/raw/hyefu24-charts-data.xlsx",
        "sheet": "Table 2.10",
        "anchors": {
            "B1": "Table 2.10 - Movements in OBEGALx since the Budget Update",
            "B2": "Source: The Treasury",
            "B5": "Year ending 30 June",
            "B6": "$billions",
            "B14": "Health NZ results",
            **{
                f"{col}5": year
                for col, year in zip("DEFG", range(2025, 2029), strict=True)
            },
            **{f"{col}6": "Forecast" for col in "DEFG"},
            "H5": "Total",
            "H6": "change",
        },
        "selected": ("D14", "E14", "F14", "G14", "H14"),
        "label_cell": "B14",
        "unit_cell": "B6",
        "measure": "health_nz_obegalx_movement_not_spending",
        "header_rows": (5, 6),
        "period_status": "source_headers_preserved_no_period_projection",
    },
}


def _require(condition: object) -> None:
    if not condition:
        message = "health_chart_residual_contract"
        raise ValueError(message)


def admit_health_chart_residuals(source: Path, vintage: str) -> dict[str, Any]:
    """Return only the explicitly selected Health literals from one pinned file."""
    _require(vintage in PROFILES)
    profile = PROFILES[vintage]
    _require(source.is_file() and not source.is_symlink())
    payload = verified_snapshot(source, profile["sha256"], max_bytes=4 * 1024 * 1024)
    inventory = inventory_workbook(BytesIO(payload))
    title = profile["sheet"]
    tokens = _selected_tokens(payload, selected_sheets=frozenset({title}))[title]
    book = load_workbook(BytesIO(payload), data_only=False, keep_links=True)
    try:
        sheet = book[title]
        _require(
            all(sheet[key].value == value for key, value in profile["anchors"].items())
        )
        # Restrict context to reviewed semantic anchors, not unrelated fiscal rows.
        context = {key: sheet[key].value for key in profile["anchors"]}
        records = []
        for coordinate in profile["selected"]:
            cell = sheet[coordinate]
            token = tokens.get(coordinate, "")
            amount = _exact_amount(token)
            _require(cell.data_type == "n" and amount is not None)
            headers = [f"{cell.column_letter}{row}" for row in profile["header_rows"]]
            records.append(
                {
                    "source_sha256": profile["sha256"],
                    "source_vintage": vintage,
                    "source_locator": profile["locator"],
                    "sheet": title,
                    "coordinate": coordinate,
                    "measure": profile["measure"],
                    "label": sheet[profile["label_cell"]].value,
                    "unit": sheet[profile["unit_cell"]].value,
                    "currency": None,
                    "amount": amount,
                    "source_number_token": token,
                    "source_number_format": cell.number_format,
                    "column_headers": [sheet[key].value for key in headers],
                    "period_start": None,
                    "period_end": None,
                    "period_status": profile["period_status"],
                    "lineage": {
                        "amount": f"{title}!{coordinate}",
                        **{f"context:{key}": f"{title}!{key}" for key in context},
                    },
                    "raw_context": context,
                }
            )
        return {
            "schema_version": "health-chart-residual-literal-context/v1",
            "status": "raw_context_only",
            "records": records,
            "workbook_inventory": inventory,
            "arithmetic_or_cross_measure_equivalence": "not_performed",
            "rights_state": "not_evaluated",
        }
    finally:
        book.close()
