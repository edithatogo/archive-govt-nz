"""Health-appropriations source census and format contracts."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from zipfile import ZipFile

import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations.formats import (
    inventory_pdf,
    inventory_sqlite,
    inventory_workbook,
)
from archive_govt_nz.domains.health_appropriations.inventory import (
    Disposition,
    SourceInventoryRecord,
    normalize_url,
    validate_inventory,
)


def _record(source_id: str, **values: object) -> SourceInventoryRecord:
    defaults: dict[str, object] = {
        "source_id": source_id,
        "family": "treasury_vote_health",
        "title": "Vote Health",
        "url": "HTTPS://Treasury.govt.nz/item#fragment",
        "observed_at": "2026-08-29T00:00:00Z",
        "cutoff": "2026-08-29",
        "disposition": Disposition.DISCOVERED,
        "reason": "metadata observed; capture pending",
    }
    defaults.update(values)
    return SourceInventoryRecord(**defaults)  # type: ignore[arg-type]


def test_inventory_normalizes_urls_and_has_stable_identity() -> None:
    record = _record("vote-2026")
    assert record.url == "https://treasury.govt.nz/item"
    assert record.record_id == _record("vote-2026").record_id
    assert normalize_url("https://EXAMPLE.nz:443/a?q=1#x") == "https://example.nz/a?q=1"


@pytest.mark.parametrize("url", ["file:///tmp/a", "javascript:x", "https:///x"])
def test_inventory_rejects_non_public_urls(url: str) -> None:
    with pytest.raises(ValueError, match="invalid_source_url"):
        _record("bad", url=url)


def test_inventory_requires_one_disposition_and_known_predecessor() -> None:
    with pytest.raises(ValueError, match="duplicate_source_disposition"):
        validate_inventory([_record("same"), _record("same")])
    with pytest.raises(ValueError, match="unknown_predecessor"):
        validate_inventory(
            [
                _record(
                    "new",
                    disposition=Disposition.SUPERSEDED,
                    predecessor_source_id="missing",
                    reason="replacement observed",
                )
            ]
        )


def test_captured_inventory_requires_sha256() -> None:
    with pytest.raises(ValueError, match="captured_source_missing_digest"):
        _record("captured", disposition=Disposition.CAPTURED, reason=None)


def test_workbook_inventory_preserves_structure(tmp_path: Path) -> None:
    path = tmp_path / "fixture.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Raw Data"
    sheet["A1"] = "Year"
    sheet["B1"] = "Amount"
    sheet["A2"] = 2026
    sheet["B2"] = "=1+2"
    sheet.merge_cells("C1:D1")
    workbook.create_sheet("Hidden").sheet_state = "hidden"
    workbook.save(path)
    before = path.read_bytes()
    result = inventory_workbook(path)
    assert result["kind"] == "xlsx"
    sheets = result["sheets"]
    assert isinstance(sheets, list)
    assert sheets[0]["formula_cells"] == 1
    assert sheets[1]["state"] == "hidden"
    assert path.read_bytes() == before


def test_workbook_inventory_rejects_traversal_member(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.xlsx"
    with ZipFile(path, "w") as package:
        package.writestr("../escape", b"x")
    with pytest.raises(ValueError, match="unsafe_workbook_member"):
        inventory_workbook(path)


def test_pdf_and_sqlite_inventory(tmp_path: Path) -> None:
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF-1.4\n/Type /Page\n/Type /Pages\n%%EOF")
    assert inventory_pdf(pdf)["page_count"] == 1
    database = tmp_path / "a.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE facts (value INTEGER)")
        connection.executemany("INSERT INTO facts VALUES (?)", [(1,), (2,)])
    result = inventory_sqlite(database)
    assert result["integrity"] == "ok"
    assert result["tables"][0]["row_count"] == 2
