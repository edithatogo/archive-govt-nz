"""SOC02 strict retained-CSV adapter; profiles describe real source schemas explicitly.

No Stats NZ column names or confidentiality codes are guessed here. A profile
selects exactly one metric/period/population and must be independently reviewed.
"""
from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from hashlib import sha256

from archive_govt_nz.domains.elections.soc_contracts import (
    MISSING, PRESENT, Cell, Series, Source, decimal_text, require, text,
)


@dataclass(frozen=True, slots=True)
class CsvProfile:
    """Explicit column roles, exhaustive dimension selectors and source-specific codes."""

    source: Source
    metric: str
    period_start: date
    period_end: date
    geography_system: str
    boundary_vintage: str
    universe: str
    measure_kind: str
    unit: str
    period_label: str
    unit_label: str
    columns: tuple[str, str, str, str, str]
    selectors: tuple[tuple[str, str], ...]
    statuses: tuple[tuple[str, str], ...]
    unit_exponent: int = 0
    missing_tokens: tuple[str, ...] = ('',)

    def __post_init__(self) -> None:
        require(isinstance(self.columns, tuple) and len(self.columns) == 5
                and len(set(self.columns)) == 5, 'invalid column roles')
        for column in self.columns:
            text(column, 'column')
        for name in ('period_label', 'unit_label'):
            text(getattr(self, name), name)
        selector_names = [k for k, _ in self.selectors]
        require(len(set(selector_names)) == len(selector_names)
                and not set(selector_names).intersection(self.columns),
                'duplicate/overlapping selectors')
        require(bool(self.statuses) and len(dict(self.statuses)) == len(self.statuses)
                and all(v in PRESENT | MISSING for _, v in self.statuses),
                'invalid status mapping')
        require(type(self.unit_exponent) is int and -12 <= self.unit_exponent <= 12,
                'invalid unit exponent')
        require(isinstance(self.missing_tokens, tuple)
                and all(isinstance(v, str) for v in self.missing_tokens),
                'invalid missing tokens')
        # Validate all target metadata without inventing observations.
        self.series(())

    def series(self, cells: tuple[Cell, ...], lineage: tuple[str, ...] = ()) -> Series:
        """Construct the canonical single-stratum result for existing ETL consumers."""
        return Series(self.metric, self.period_start, self.period_end,
                      self.geography_system, self.boundary_vintage, self.universe,
                      self.measure_kind, self.unit, (self.source,), cells,
                      lineage=lineage)

    @property
    def digest(self) -> str:
        """Bind source identity, all selectors and interpretation rules to output."""
        payload = {'target': self.series(()).public(), 'columns': self.columns,
                   'selectors': sorted(self.selectors), 'statuses': sorted(self.statuses),
                   'period_label': self.period_label, 'unit_label': self.unit_label,
                   'unit_exponent': self.unit_exponent,
                   'missing_tokens': sorted(self.missing_tokens)}
        return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                 separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Retain observed input/filter counts and the exact reviewed profile identity."""

    series: Series
    rows_read: int
    rows_selected: int
    rows_excluded: int
    profile_sha256: str


def _value(raw: str, status: str, profile: CsvProfile) -> Decimal | None:
    if status in MISSING:
        require(raw in profile.missing_tokens, 'confidential/missing payload mismatch')
        return None
    require(len(raw) <= 64 and bool(re.fullmatch(
        r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', raw)),
        'invalid numeric token')
    parsed = Decimal(raw)
    decimal_text(parsed)
    with localcontext() as context:
        context.prec = 80
        value = parsed.scaleb(profile.unit_exponent)
    decimal_text(value)
    return value


def normalise_csv(raw: bytes, profile: CsvProfile, *, allow_synthetic: bool = False,
                  max_bytes: int = 16 * 1024 * 1024,
                  max_rows: int = 100_000) -> ImportResult:
    """Parse pinned bytes; reject unmapped dimensions, duplicates and hidden values."""
    require(type(max_bytes) is int and max_bytes > 0
            and type(max_rows) is int and max_rows > 0, 'invalid resource limits')
    require(len(raw) <= max_bytes, 'byte limit exceeded')
    require(len(raw) == profile.source.byte_count
            and sha256(raw).hexdigest() == profile.source.sha256, 'source hash mismatch')
    require(not profile.source.synthetic or allow_synthetic, 'synthetic input not allowed')
    try:
        decoded = raw.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(decoded, newline=''), strict=True)
        header = next(reader, [])
        expected = set(profile.columns) | {key for key, _ in profile.selectors}
        require(len(header) == len(set(header)) and set(header) == expected,
                'CSV headers differ from exhaustive profile')
        selected: list[Cell] = []
        seen: set[str] = set()
        total = 0
        geo_col, period_col, unit_col, value_col, status_col = profile.columns
        statuses = dict(profile.statuses)
        for number, values in enumerate(reader, start=2):
            total += 1
            require(total <= max_rows, 'row limit exceeded')
            require(len(values) == len(header), 'CSV row shape mismatch')
            row = dict(zip(header, values, strict=True))
            if row[period_col] != profile.period_label or any(
                row[key] != value for key, value in profile.selectors
            ):
                continue
            require(row[unit_col] == profile.unit_label, 'source unit mismatch')
            require(row[status_col] in statuses, 'unmapped source status')
            geography = row[geo_col]
            require(geography not in seen, 'duplicate selected geography')
            seen.add(geography)
            status = statuses[row[status_col]]
            selected.append(Cell(geography, _value(row[value_col], status, profile),
                                 status, 'csv-record:' + str(number)))
    except (UnicodeError, csv.Error) as error:
        raise ValueError('invalid CSV encoding or syntax') from error
    require(bool(selected), 'empty selected cohort')
    result = profile.series(tuple(sorted(selected, key=lambda c: c.geography_id)),
                            (profile.digest,))
    return ImportResult(result, total, len(selected), total - len(selected), profile.digest)
