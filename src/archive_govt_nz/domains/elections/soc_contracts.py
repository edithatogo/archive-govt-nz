"""Immutable source-native socioeconomic records; no acquisition or admission grant.

Digests prove byte identity, not authenticity, source rights or scientific validity.
Callers must separately qualify the evidence identified by rights_receipt.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
from urllib.parse import urlsplit

PRESENT = frozenset({'observed', 'provisional', 'estimated'})
MISSING = frozenset({'suppressed', 'missing', 'unavailable'})
GEOGRAPHIES = frozenset({'general_electorate', 'maori_electorate', 'sa1', 'sa2',
                         'region', 'national'})
KINDS = frozenset({'count', 'rate', 'median', 'mean', 'index'})


def require(condition: bool, message: str) -> None:
    """Reject invalid contracts with a stable, value-free diagnostic."""
    if not condition:
        raise ValueError(message)


def text(value: str, name: str) -> None:
    """Validate a bounded public metadata string without echoing its value."""
    require(isinstance(value, str) and 0 < len(value) <= 4096
            and value == value.strip() and not any(ord(c) < 32 for c in value),
            'invalid ' + name)


def digest(value: str) -> None:
    """Validate a SHA-256 hex digest, not a self-declared verification claim."""
    require(isinstance(value, str) and bool(re.fullmatch('[0-9a-f]{64}', value)),
            'invalid sha256')


def aware(value: datetime) -> None:
    """Require an aware timestamp for comparisons and exported evidence."""
    require(isinstance(value, datetime) and value.utcoffset() is not None,
            'timezone required')


def decimal_text(value: Decimal) -> str:
    """Encode finite bounded decimal values without dependence on ambient context."""
    require(isinstance(value, Decimal) and value.is_finite(), 'invalid decimal')
    require(len(value.as_tuple().digits) <= 64 and abs(value.adjusted()) <= 100,
            'decimal outside bounds')
    rendered = format(value, 'f')
    return rendered.rstrip('0').rstrip('.') if '.' in rendered else rendered


@dataclass(frozen=True, slots=True)
class Source:
    """A reference to retained original bytes and separately reviewed source rights."""

    source_id: str
    source_url: str
    revision: str
    sha256: str
    byte_count: int
    published_at: datetime
    captured_at: datetime
    rights_receipt: str
    synthetic: bool

    def __post_init__(self) -> None:
        for name in ('source_id', 'source_url', 'revision', 'rights_receipt'):
            text(getattr(self, name), name)
        url = urlsplit(self.source_url)
        require(url.scheme == 'https' and bool(url.hostname) and not url.username
                and not url.password and not url.query and not url.fragment,
                'invalid source_url')
        digest(self.sha256)
        require(type(self.byte_count) is int and self.byte_count >= 0, 'invalid size')
        require(type(self.synthetic) is bool, 'explicit synthetic status required')
        aware(self.published_at)
        aware(self.captured_at)
        require(self.published_at <= self.captured_at, 'invalid source chronology')

    def public(self) -> dict[str, str | int | bool]:
        """Expose public metadata, never credentials or a local object-store path."""
        return {'source_id': self.source_id, 'source_url': self.source_url,
                'revision': self.revision, 'sha256': self.sha256,
                'byte_count': self.byte_count,
                'published_at': self.published_at.isoformat(),
                'captured_at': self.captured_at.isoformat(),
                'rights_receipt': self.rights_receipt, 'synthetic': self.synthetic}


@dataclass(frozen=True, slots=True)
class Cell:
    """One cell after selecting a single metric, period and statistical universe."""

    geography_id: str
    value: Decimal | None
    status: str
    locator: str
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        text(self.geography_id, 'geography_id')
        text(self.locator, 'locator')
        require(self.status in PRESENT | MISSING, 'invalid status')
        require((self.value is None) == (self.status in MISSING),
                'value/missing status mismatch')
        if self.value is not None:
            decimal_text(self.value)
        require(isinstance(self.flags, tuple) and len(set(self.flags)) == len(self.flags)
                and all(isinstance(f, str) and re.fullmatch('[a-z0-9_:-]{1,80}', f)
                        for f in self.flags), 'invalid quality flags')

    def public(self) -> dict[str, str | list[str] | None]:
        """Serialize a cell without recovering a confidential source value."""
        return {'geography_id': self.geography_id,
                'value': None if self.value is None else decimal_text(self.value),
                'status': self.status, 'locator': self.locator,
                'flags': sorted(self.flags)}


@dataclass(frozen=True, slots=True)
class Series:
    """A source-defined single-stratum series on exactly one boundary system."""

    metric: str
    period_start: date
    period_end: date
    geography_system: str
    boundary_vintage: str
    universe: str
    measure_kind: str
    unit: str
    sources: tuple[Source, ...]
    cells: tuple[Cell, ...]
    method: str = 'source'
    lineage: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ('metric', 'boundary_vintage', 'universe', 'unit', 'method'):
            text(getattr(self, name), name)
        require(type(self.period_start) is date and type(self.period_end) is date
                and self.period_start <= self.period_end, 'invalid reference period')
        require(self.geography_system in GEOGRAPHIES, 'invalid geography system')
        require(self.measure_kind in KINDS, 'invalid measure kind')
        require(isinstance(self.sources, tuple) and bool(self.sources)
                and all(isinstance(s, Source) for s in self.sources), 'sources required')
        require(len({s.source_id for s in self.sources}) == len(self.sources),
                'duplicate source identity')
        require(len({s.synthetic for s in self.sources}) == 1,
                'mixed synthetic/empirical sources')
        require(isinstance(self.cells, tuple) and all(isinstance(c, Cell) for c in self.cells),
                'invalid cells')
        require(len({c.geography_id for c in self.cells}) == len(self.cells),
                'duplicate geography')
        require(isinstance(self.lineage, tuple), 'invalid lineage')
        for identity in self.lineage:
            digest(identity)
        require(self.method == 'source' or bool(self.lineage), 'derived lineage required')
        for cell in self.cells:
            if cell.value is not None and self.measure_kind == 'count':
                require(cell.value >= 0 and (cell.status == 'estimated'
                        or cell.value == cell.value.to_integral_value()), 'invalid count')
            if cell.value is not None and self.unit == 'percent':
                require(0 <= cell.value <= 100, 'invalid percentage')

    @property
    def synthetic(self) -> bool:
        """Return the homogeneous evidence class retained through transformations."""
        return self.sources[0].synthetic

    def public(self) -> dict[str, object]:
        """Return canonical public data suitable for existing columnar consumers."""
        return {'schema_version': 'soc-series-v1', 'metric': self.metric,
                'period_start': self.period_start.isoformat(),
                'period_end': self.period_end.isoformat(),
                'geography_system': self.geography_system,
                'boundary_vintage': self.boundary_vintage, 'universe': self.universe,
                'measure_kind': self.measure_kind, 'unit': self.unit,
                'sources': [s.public() for s in sorted(self.sources, key=lambda s: s.source_id)],
                'cells': [c.public() for c in sorted(self.cells, key=lambda c: c.geography_id)],
                'method': self.method, 'lineage': sorted(self.lineage)}

    @property
    def digest(self) -> str:
        """Bind all observations and metadata, independently of input row order."""
        return sha256(json.dumps(self.public(), sort_keys=True, ensure_ascii=False,
                                 separators=(',', ':'), allow_nan=False).encode()).hexdigest()
