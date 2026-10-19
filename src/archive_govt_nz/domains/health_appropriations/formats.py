"""Safe, non-mutating inventory of donor workbooks, PDFs, and SQLite."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from io import BytesIO
from typing import TYPE_CHECKING, Literal
from zipfile import BadZipFile, ZipFile

from openpyxl import load_workbook

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from openpyxl.workbook.workbook import Workbook
    from openpyxl.worksheet.worksheet import Worksheet

_PDF_PAGE = re.compile(rb"/Type\s*/Page\b")
_MAX_MEMBERS = 20_000
_MAX_EXPANDED_BYTES = 512 * 1024 * 1024
_MAX_SCAN_CELLS = 2_000_000


@dataclass(frozen=True, slots=True)
class FormulaCacheInventory:
    """Presence and type only; neither contents nor freshness are asserted."""

    coordinate: str
    state: Literal["stored_value", "stored_error", "missing_or_empty"]
    data_type: str


@dataclass(frozen=True, slots=True)
class SheetInventory:
    """Structural workbook evidence for one sheet."""

    title: str
    state: str
    max_row: int
    max_column: int
    formula_cells: int
    merged_ranges: int
    table_names: tuple[str, ...]
    chart_count: int
    dimension: str
    formula_coordinates: tuple[str, ...]
    comment_coordinates: tuple[str, ...]
    merged_range_refs: tuple[str, ...]
    table_ranges: tuple[tuple[str, str], ...]
    hidden_rows: tuple[int, ...]
    hidden_columns: tuple[tuple[str, int | None, int | None], ...]
    defined_names: tuple[str, ...]
    formula_cache: tuple[FormulaCacheInventory, ...] = ()


def _formula_cache(sheet: Worksheet, coordinate: str) -> FormulaCacheInventory:
    cell = sheet[coordinate]
    state: Literal["stored_value", "stored_error", "missing_or_empty"]
    if cell.value is None:
        state = "missing_or_empty"
    elif cell.data_type == "e":
        state = "stored_error"
    else:
        state = "stored_value"
    return FormulaCacheInventory(coordinate, state, cell.data_type)


def _inventory_sheet(sheet: Worksheet) -> SheetInventory:
    formulas: list[str] = []
    comments: list[str] = []
    for row in sheet.iter_rows():
        for cell in row:
            if cell.data_type == "f":
                formulas.append(cell.coordinate)
            if cell.comment is not None:
                comments.append(cell.coordinate)
    merged = tuple(sorted(str(area) for area in sheet.merged_cells.ranges))
    return SheetInventory(
        title=sheet.title,
        state=sheet.sheet_state,
        max_row=sheet.max_row,
        max_column=sheet.max_column,
        formula_cells=len(formulas),
        merged_ranges=len(merged),
        table_names=tuple(sorted(sheet.tables)),
        chart_count=len(getattr(sheet, "_charts", ())),
        dimension=sheet.calculate_dimension(),
        formula_coordinates=tuple(formulas),
        comment_coordinates=tuple(comments),
        merged_range_refs=merged,
        table_ranges=tuple(
            (name, sheet.tables[name].ref) for name in sorted(sheet.tables)
        ),
        hidden_rows=tuple(
            sorted(index for index, dim in sheet.row_dimensions.items() if dim.hidden)
        ),
        hidden_columns=tuple(
            sorted(
                (name, dim.min, dim.max)
                for name, dim in sheet.column_dimensions.items()
                if dim.hidden
            )
        ),
        defined_names=tuple(sorted(sheet.defined_names)),
    )


@contextmanager
def _open_inspection(
    path: Path | BytesIO,
) -> Iterator[tuple[dict[str, object], Workbook]]:
    """Inventory an XLSX package while leaving its original bytes untouched."""
    try:
        with ZipFile(path) as package:
            members = package.infolist()
            if len(members) > _MAX_MEMBERS:
                raise ValueError("workbook_member_limit")
            if any(
                member.filename.startswith("/")
                or "\\" in member.filename
                or ":" in member.filename
                or any(
                    part in ("", ".", "..")
                    for part in member.filename.removesuffix("/").split("/")
                )
                for member in members
            ):
                raise ValueError("unsafe_workbook_member")
            if len({member.filename for member in members}) != len(members):
                raise ValueError("duplicate_workbook_member")
            expanded = sum(member.file_size for member in members)
            if expanded > _MAX_EXPANDED_BYTES:
                raise ValueError("workbook_expansion_limit")
            package_members = tuple(sorted(member.filename for member in members))
    except BadZipFile:
        raise ValueError("invalid_workbook_package") from None

    workbook = load_workbook(path, read_only=False, data_only=False, keep_links=True)
    sheets: list[SheetInventory] = []
    try:
        # Sparse sheets can have a huge rectangular extent despite tiny XML.
        # Bound the total traversal before iter_rows materializes empty cells.
        scan_cells = sum(
            sheet.max_row * sheet.max_column for sheet in workbook.worksheets
        )
        if scan_cells > _MAX_SCAN_CELLS:
            raise ValueError("workbook_cell_scan_limit")
        sheets = [_inventory_sheet(sheet) for sheet in workbook.worksheets]
        external_links = len(getattr(workbook, "_external_links", ()))
        defined_names = tuple(sorted(workbook.defined_names))
        if any(sheet.formula_coordinates for sheet in sheets):
            cached = load_workbook(
                path, read_only=False, data_only=True, keep_links=True
            )
            try:
                cached_sheets = {sheet.title: sheet for sheet in cached.worksheets}
                sheets = [
                    replace(
                        sheet,
                        formula_cache=tuple(
                            _formula_cache(cached_sheets[sheet.title], coordinate)
                            for coordinate in sheet.formula_coordinates
                        ),
                    )
                    for sheet in sheets
                ]
            finally:
                cached.close()
        inventory: dict[str, object] = {
            "schema_version": "archive-govt-nz.workbook-inventory/v1",
            "kind": "xlsx",
            "package_member_count": len(package_members),
            "package_members": package_members,
            "expanded_bytes": expanded,
            "has_macros": any(
                name.rsplit("/", 1)[-1].lower() == "vbaproject.bin"
                for name in package_members
            ),
            "external_link_count": external_links,
            "named_range_count": len(defined_names),
            "defined_names": defined_names,
            "formula_cache_freshness": "not_verified",
            "sheets": [asdict(sheet) for sheet in sheets],
        }

        yield inventory, workbook
    finally:
        workbook.close()


@dataclass(frozen=True, slots=True)
class WorkbookInspection:
    """One operation's exact bytes, decoded workbook and checked metadata."""

    source_sha256: str
    workbook: Workbook
    _payload: bytes
    _inventory: dict[str, object]

    def matches_bytes(self, payload: bytes) -> bool:
        """Require identical bytes, never a path or a caller-provided digest."""
        return self._payload == payload

    @property
    def inventory(self) -> dict[str, object]:
        """Return independent metadata so callers cannot poison later detection."""
        return deepcopy(self._inventory)


_ACTIVE_INSPECTION: ContextVar[WorkbookInspection | None] = ContextVar(
    "health_workbook_inspection", default=None
)


@contextmanager
def inspected_workbook(payload: bytes) -> Iterator[WorkbookInspection]:
    """Reuse checks only inside the owning operation and for identical bytes.

    All existing structural, expansion, traversal and formula-cache checks run
    before establishing the scope. This is neither a path nor persistent cache.
    """
    if type(payload) is not bytes:
        raise TypeError("workbook_bytes_required")
    current = _ACTIVE_INSPECTION.get()
    if current is not None and current.matches_bytes(payload):
        yield current
        return
    with _open_inspection(BytesIO(payload)) as (inventory, workbook):
        inspection = WorkbookInspection(
            hashlib.sha256(payload).hexdigest(), workbook, payload, inventory
        )
        token = _ACTIVE_INSPECTION.set(inspection)
        try:
            yield inspection
        finally:
            _ACTIVE_INSPECTION.reset(token)


def inventory_workbook(path: Path | BytesIO) -> dict[str, object]:
    """Inventory original bytes, reusing only an exact operation-local proof."""
    current = _ACTIVE_INSPECTION.get()
    if (
        current is not None
        and isinstance(path, BytesIO)
        and current.matches_bytes(path.getvalue())
    ):
        return current.inventory
    with _open_inspection(path) as (inventory, _):
        return inventory


def inventory_pdf(path: Path) -> dict[str, object]:
    """Return a bounded structural page count without rewriting the PDF."""
    payload = path.read_bytes()
    if not payload.startswith(b"%PDF-"):
        raise ValueError("invalid_pdf")
    return {
        "kind": "pdf",
        "byte_count": len(payload),
        "page_count": len(_PDF_PAGE.findall(payload)),
    }


def _sqlite_identifier(name: str) -> str:
    """Quote a schema-provided identifier without interpreting its contents."""
    return '"' + name.replace('"', '""') + '"'


def inventory_sqlite(path: Path) -> dict[str, object]:
    """Inventory user tables, schemas, and row counts read-only."""
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return {
            "kind": "sqlite",
            "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
            "tables": [
                {
                    "name": name,
                    "sql": sql,
                    "row_count": connection.execute(
                        f"SELECT COUNT(*) FROM {_sqlite_identifier(name)}"
                    ).fetchone()[0],
                }
                for name, sql in tables
            ],
        }
    finally:
        connection.close()
