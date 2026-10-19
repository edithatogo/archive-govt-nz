"""Bounded BIFF8 snapshots and replayable stored-integer cell witnesses."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

import xlrd
from xlrd.compdoc import CompDoc

from archive_govt_nz.domains.health_appropriations import (
    biff8_numeric,
    legacy_inspection,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import identity

if TYPE_CHECKING:
    from collections.abc import Mapping

_MAX_SOURCE_BYTES = 8 * 1024 * 1024
_MAX_RECORDS = 500_000
_MAX_RECORD_BYTES = 8224
_MAX_DIRECTORY_ENTRIES = 65_536
_MAX_SHEETS = 256
_MAX_ROWS = 20_000
_MAX_COLUMNS = 50
_CFB_VERSION = 3
_CFB_ENDIAN = 0xFFFE
_CFB_SHIFT = 9
_CFB_MINI_SHIFT = 6
_CFB_CUTOFF = 4096
_STREAM_OBJECT = 2
_END_SECTOR = -2
_BIFF_VERSION = 0x0600
_BOF_BYTES = 16
_BOUND = 0x0085
_BOUND_HEADER_BYTES = 8
_MAX_NAME_CHARS = 31
_NUMBER = 0x0203
_MULRK = 0x00BD
_WSBOOL = 0x0081
_WORD_BYTES = 2
_CELL_HEADER_BYTES = 6
_FORMULA_BYTES = 22
_MAX_BIFF_ROW = 65536
_MAX_BIFF_COLUMN = 256
_BLOCK = 512
_ENTRY = 128
_BOF = 0x0809
_EOF = 0x000A
_FORMULA = 0x0006
_NUMERIC = frozenset({0x0203, 0x027E, 0x00BD})
_SINGLE_CELLS = frozenset({0x00FD, 0x0204, 0x00D6, 0x0205, 0x0201, _FORMULA})
_OLD_CELL_KINDS = frozenset({0x0206, 0x0406, 0x007E, 0x0002, 0x0003, 0x0004, 0x0005})
_INVALID = "invalid_biff8_snapshot"
_BASIS = "biff8_stored_integer/v1"
_WITNESS = "archive-govt-nz.biff8-numeric-witness/v1"
_DECODER = "archive-govt-nz.biff8-numeric/v1"


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_INVALID)


def _uint(data: bytes, offset: int, width: int) -> int:
    _require(0 <= offset <= len(data) - width)
    return int.from_bytes(data[offset : offset + width], "little")


@dataclass(frozen=True, slots=True)
class SheetBinding:
    """A source-declared sheet pointer, without interpretation of other sheets."""

    name: str
    offset: int
    kind: int
    visibility: int


@dataclass(frozen=True, slots=True)
class NumericWitness:
    """An exact source-cell encoding; synthesized integers are never text tokens."""

    schema_version: str
    value_basis: str
    decoder_version: str
    numeric_evidence_id: str
    source_sha256: str
    stream_sha256: str
    sheet: str
    sheet_bof_offset: int
    source_row: int
    source_column: int
    record_offset: int
    record_type: int
    member_index: int | None
    record_payload_sha256: str
    encoded_value_hex: str
    canonical_stored_integer: str

    def to_record(self) -> dict[str, Any]:
        """Return a detached flat record suitable for a typed evidence table."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _EncodedCell:
    kind: int
    offset: int
    member: int | None
    encoded: bytes
    payload_sha256: str


@dataclass(frozen=True, slots=True)
class BiffSheet:
    """Materialized immutable source values; no live workbook or global cache."""

    source_sha256: str
    stream_sha256: str
    binding: SheetBinding
    bindings: tuple[SheetBinding, ...]
    values: tuple[tuple[object, ...], ...]
    cell_types: tuple[tuple[int, ...], ...]
    formula_rows: frozenset[int]
    error_rows: frozenset[int]
    _numeric: Mapping[tuple[int, int], _EncodedCell]
    _origins: Mapping[tuple[int, int], int]
    _inventory_json: str

    @property
    def inventory(self) -> dict[str, Any]:
        """Return a defensive copy of the unchanged legacy inventory."""
        return cast("dict[str, Any]", json.loads(self._inventory_json))

    def integer_cell(self, row: int, column: int) -> NumericWitness:
        """Resolve a one-based cell to original encoded bytes and exact integer."""
        key = (row, column)
        if type(row) is not int or type(column) is not int or key not in self._origins:
            message = "missing_biff8_numeric_cell"
            raise ValueError(message)
        if self._origins[key] == _FORMULA:
            message = "formula_not_a_biff8_constant"
            raise ValueError(message)
        if key not in self._numeric:
            message = "not_a_biff8_numeric_constant"
            raise ValueError(message)
        cell = self._numeric[key]
        value = biff8_numeric.stored_integer(cell.kind, cell.encoded)
        _require(
            1 <= row <= len(self.values) and 1 <= column <= len(self.values[row - 1])
        )
        decoded = self.values[row - 1][column - 1]
        _require(self.cell_types[row - 1][column - 1] == xlrd.XL_CELL_NUMBER)
        _require(type(decoded) is float and decoded.as_integer_ratio() == (value, 1))
        encoded = cell.encoded.hex()
        evidence_id = identity(
            _WITNESS,
            _BASIS,
            _DECODER,
            self.source_sha256,
            self.stream_sha256,
            self.binding.name,
            self.binding.offset,
            row,
            column,
            cell.offset,
            cell.kind,
            cell.member,
            cell.payload_sha256,
            encoded,
        )
        return NumericWitness(
            _WITNESS,
            _BASIS,
            _DECODER,
            evidence_id,
            self.source_sha256,
            self.stream_sha256,
            self.binding.name,
            self.binding.offset,
            row,
            column,
            cell.offset,
            cell.kind,
            cell.member,
            cell.payload_sha256,
            encoded,
            str(value),
        )

    def verify_integer(self, witness: NumericWitness, *, row: int, column: int) -> int:
        """Replay against this verified snapshot and the caller's required cell."""
        expected = self.integer_cell(row, column)
        if type(witness) is not NumericWitness or any(
            type(getattr(witness, field.name))
            is not type(getattr(expected, field.name))
            or getattr(witness, field.name) != getattr(expected, field.name)
            for field in fields(NumericWitness)
        ):
            message = "invalid_biff8_numeric_witness"
            raise ValueError(message)
        return int(witness.canonical_stored_integer)


@dataclass(frozen=True, slots=True)
class _Record:
    kind: int
    offset: int
    data: bytes
    end: int


class _Reader:
    def __init__(self, stream: bytes) -> None:
        self.stream = stream
        self.count = 0

    def record(self, offset: int) -> _Record:
        self.count += 1
        _require(self.count <= _MAX_RECORDS and 0 <= offset <= len(self.stream) - 4)
        kind, size = _uint(self.stream, offset, 2), _uint(self.stream, offset + 2, 2)
        end = offset + 4 + size
        _require(size <= _MAX_RECORD_BYTES and end <= len(self.stream))
        return _Record(kind, offset, self.stream[offset + 4 : end], end)

    def bof(self, offset: int, kind: int) -> int:
        record = self.record(offset)
        _require(record.kind == _BOF and len(record.data) == _BOF_BYTES)
        _require(
            _uint(record.data, 0, 2) == _BIFF_VERSION
            and _uint(record.data, 2, 2) == kind
        )
        return record.end


def _directory_sizes(compound: CompDoc, payload: bytes) -> None:
    # xlrd exposes only the low 32 bits of stream sizes: check original entries.
    fat = cast("list[int]", compound.SAT)
    sector = int.from_bytes(payload[48:52], "little", signed=True)
    seen: set[int] = set()
    while sector >= 0:
        _require(sector < len(fat) and sector not in seen)
        seen.add(sector)
        _require(len(seen) * (_BLOCK // _ENTRY) <= _MAX_DIRECTORY_ENTRIES)
        offset = (sector + 1) * _BLOCK
        _require(offset + _BLOCK <= len(payload))
        block = payload[offset : offset + _BLOCK]
        for entry in range(0, _BLOCK, _ENTRY):
            if block[entry + 66] in {2, 5}:
                size = _uint(block, entry + 120, 8)
                _require(size <= len(payload) and size < 2**31)
        sector = fat[sector]
    _require(sector == _END_SECTOR)


def _workbook_stream(payload: bytes) -> bytes:
    _require(len(payload) >= _BLOCK and len(payload) % _BLOCK == 0)
    _require(payload[:8] == bytes.fromhex("d0cf11e0a1b11ae1"))
    # This source profile qualifies CFB v3 geometry; do not accept library repairs.
    _require(
        _uint(payload, 26, 2) == _CFB_VERSION and _uint(payload, 28, 2) == _CFB_ENDIAN
    )
    _require(
        _uint(payload, 30, 2) == _CFB_SHIFT and _uint(payload, 32, 2) == _CFB_MINI_SHIFT
    )
    _require(_uint(payload, 40, 4) == 0 and _uint(payload, 56, 4) == _CFB_CUTOFF)
    compound = CompDoc(
        payload,
        logfile=legacy_inspection._DiscardDiagnostics(),  # noqa: SLF001 - existing redacted reader sink.
        DEBUG=0,
        ignore_workbook_corruption=False,
    )
    _require(len(compound.dirlist) <= _MAX_DIRECTORY_ENTRIES)
    _directory_sizes(compound, payload)
    entries = [
        d
        for d in compound.dirlist
        if d.parent == 0
        and d.etype == _STREAM_OBJECT
        and d.name.casefold() in {"workbook", "book"}
    ]
    _require(len(entries) == 1 and entries[0].name.casefold() == "workbook")
    size = cast("int", entries[0].tot_size)
    _require(0 < size <= min(len(payload), _MAX_SOURCE_BYTES))
    memory, start, length = compound.locate_named_stream(entries[0].name)
    _require(type(memory) is bytes and length == size and start >= 0)
    buffer = cast("bytes", memory)
    _require(start + length <= len(buffer))
    return buffer[start : start + length]


def _binding(record: _Record) -> SheetBinding:
    data = record.data
    _require(len(data) >= _BOUND_HEADER_BYTES)
    count, flag = data[6], data[7]
    _require(1 <= count <= _MAX_NAME_CHARS and flag in {0, 1})
    _require(len(data) == 8 + count * (2 if flag else 1))
    name = data[8:].decode("utf-16le" if flag else "latin1")
    _require(not any(c in name for c in "\x00\x03:\\*?/[]"))
    _require(not name.startswith("'") and not name.endswith("'"))
    _require(data[4] & 3 in {0, 1, 2})
    return SheetBinding(name, _uint(data, 0, 4), data[5], data[4] & 3)


def _bindings(reader: _Reader) -> tuple[SheetBinding, ...]:
    offset = reader.bof(0, 5)
    bindings: list[SheetBinding] = []
    while True:
        record = reader.record(offset)
        _require(record.kind not in {_BOF, 0x002F})
        if record.kind == _BOUND:
            bindings.append(_binding(record))
            _require(len(bindings) <= _MAX_SHEETS)
        if record.kind == _EOF:
            _require(not record.data)
            break
        offset = record.end
    _require(bindings)
    _require(len({b.name.casefold() for b in bindings}) == len(bindings))
    _require(len({b.offset for b in bindings}) == len(bindings))
    _require(all(record.end <= b.offset <= len(reader.stream) - 20 for b in bindings))
    return tuple(bindings)


def _cell_coordinates(
    record: _Record,
) -> list[tuple[int, int, int | None, bytes | None]]:
    kind, data = record.kind, record.data
    if kind in {0x0203, 0x027E}:
        _require(len(data) == (14 if kind == _NUMBER else 10))
        return [(_uint(data, 0, 2) + 1, _uint(data, 2, 2) + 1, None, data[6:])]
    if kind in {0x00BD, 0x00BE}:
        width = 6 if kind == _MULRK else 2
        _require(
            len(data) >= _CELL_HEADER_BYTES + width and (len(data) - 6) % width == 0
        )
        row, first, last = (
            _uint(data, 0, 2) + 1,
            _uint(data, 2, 2),
            _uint(data, len(data) - 2, 2),
        )
        _require(
            first <= last < _MAX_BIFF_COLUMN
            and last - first + 1 == (len(data) - 6) // width
        )
        _require(kind != _MULRK or first < last)
        return [
            (
                row,
                col + 1,
                member,
                data[6 + width * member : 10 + width * member]
                if kind == _MULRK
                else None,
            )
            for member, col in enumerate(range(first, last + 1))
        ]
    if kind in _SINGLE_CELLS:
        _require(len(data) >= _CELL_HEADER_BYTES)
        if kind == _FORMULA:
            _require(
                len(data) >= _FORMULA_BYTES
                and len(data) >= _FORMULA_BYTES + _uint(data, 20, 2)
            )
        return [(_uint(data, 0, 2) + 1, _uint(data, 2, 2) + 1, None, None)]
    _require(kind not in _OLD_CELL_KINDS)
    return []


def _index_cells(
    reader: _Reader, binding: SheetBinding, bindings: tuple[SheetBinding, ...]
) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], _EncodedCell]]:
    offset = reader.bof(binding.offset, 0x10)
    limit = min(
        (b.offset for b in bindings if b.offset > binding.offset),
        default=len(reader.stream),
    )
    origins: dict[tuple[int, int], int] = {}
    numeric: dict[tuple[int, int], _EncodedCell] = {}
    worksheet_flags: list[int] = []
    while True:
        record = reader.record(offset)
        _require(record.end <= limit and record.kind not in {_BOF, 0x002F})
        if record.kind == _EOF:
            _require(not record.data)
            break
        if record.kind == _WSBOOL:
            _require(len(record.data) == _WORD_BYTES)
            worksheet_flags.append(_uint(record.data, 0, 2))
        cells = _cell_coordinates(record)
        digest = (
            hashlib.sha256(record.data).hexdigest() if record.kind in _NUMERIC else ""
        )
        for row, column, member, encoded in cells:
            key = (row, column)
            _require(
                1 <= row <= _MAX_BIFF_ROW
                and 1 <= column <= _MAX_BIFF_COLUMN
                and key not in origins
            )
            origins[key] = record.kind
            if encoded is not None:
                numeric[key] = _EncodedCell(
                    record.kind, record.offset, member, encoded, digest
                )
        offset = record.end
    _require(len(worksheet_flags) == 1 and not worksheet_flags[0] & 0x0010)
    return origins, numeric


def _materialized_values(
    payload: bytes, sheet: str
) -> tuple[tuple[tuple[object, ...], ...], tuple[tuple[int, ...], ...]]:
    book = xlrd.open_workbook(
        file_contents=payload,
        formatting_info=True,
        on_demand=True,
        ragged_rows=True,
        ignore_workbook_corruption=False,
        logfile=legacy_inspection._DiscardDiagnostics(),  # noqa: SLF001 - existing redacted reader sink.
    )
    try:
        raw = book.sheet_by_name(sheet)
        _require(raw.nrows <= _MAX_ROWS and raw.ncols <= _MAX_COLUMNS)
        values, types = [], []
        for row in range(raw.nrows):
            cells = [
                raw.cell(row, col) if col < raw.row_len(row) else None
                for col in range(raw.ncols)
            ]
            values.append(
                tuple(
                    c.value if c is not None and c.ctype not in {0, 6} else None
                    for c in cells
                )
            )
            types.append(tuple(c.ctype if c is not None else 0 for c in cells))
        return tuple(values), tuple(types)
    finally:
        book.release_resources()


def read_sheet(payload: bytes, expected_sha256: str, *, sheet: str) -> BiffSheet:
    """Create an immutable snapshot without interpreting caches as constants."""
    try:
        _require(
            type(payload) is bytes
            and type(expected_sha256) is str
            and type(sheet) is str
        )
        _require(
            len(payload) <= _MAX_SOURCE_BYTES
            and hashlib.sha256(payload).hexdigest() == expected_sha256
        )
        stream = _workbook_stream(payload)
        reader = _Reader(stream)
        bindings = _bindings(reader)
        selected = [b for b in bindings if b.name == sheet]
        _require(len(selected) == 1 and selected[0].kind == 0)
        binding = selected[0]
        origins, numeric = _index_cells(reader, binding, bindings)
        inventory = legacy_inspection.inspect_legacy_bytes(
            payload, expected_sha256, rows=0
        )["inventory"]
        values, types = _materialized_values(payload, sheet)
        formula_rows = frozenset(
            row for (row, _), kind in origins.items() if kind == _FORMULA
        )
        error_rows = frozenset(
            row + 1 for row, cells in enumerate(types) if xlrd.XL_CELL_ERROR in cells
        )
        return BiffSheet(
            expected_sha256,
            hashlib.sha256(stream).hexdigest(),
            binding,
            bindings,
            values,
            types,
            formula_rows,
            error_rows,
            MappingProxyType(numeric),
            MappingProxyType(origins),
            json.dumps(inventory, sort_keys=True, ensure_ascii=False, allow_nan=False),
        )
    except Exception:  # noqa: BLE001 - source diagnostics never cross this boundary.
        raise ValueError(_INVALID) from None
