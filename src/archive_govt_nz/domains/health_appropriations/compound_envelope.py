"""Bound native descriptors without serializing, coercing or pruning their data."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    LossAccounting,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
        CompoundAdapterOutput,
        NativeProfileContract,
    )

MAX_ENVELOPE_BYTES = 4 * 1024 * 1024
MAX_ENVELOPE_NODES = 100_000
MAX_ENVELOPE_DEPTH = 16
MAX_EXCLUDED_SHEETS = 256
MAX_SOURCE_LOSSES = 64
_ASCII_CONTROL_END = 0x20
_ASCII_END = 0x80
_UTF8_TWO_END = 0x800
_SURROGATE_START = 0xD800
_SURROGATE_END = 0xDFFF
_BMP_END = 0xFFFF


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _escaped_width(character: str) -> int:
    if character in '\\"\b\f\n\r\t':
        return 2
    code = ord(character)
    if code < _ASCII_CONTROL_END:
        return 6
    if code < _ASCII_END:
        return 1
    if code < _UTF8_TWO_END:
        return 2
    _require(not _SURROGATE_START <= code <= _SURROGATE_END, "native_envelope_unicode")
    return 3 if code <= _BMP_END else 4


class _Budget:
    """Count bounded native JSON-compatible metadata without changing values."""

    def __init__(self) -> None:
        self.size = 0
        self.nodes = 0
        self.active: set[int] = set()

    def charge(self, size: int) -> None:
        """Account for representation bytes before accepting more descriptors."""
        _require(self.size + size <= MAX_ENVELOPE_BYTES, "native_envelope_size")
        self.size += size

    def _string(self, value: str) -> None:
        self.charge(2)
        _require(len(value) <= MAX_ENVELOPE_BYTES - self.size, "native_envelope_size")
        for character in value:
            self.charge(_escaped_width(character))

    def _scalar(self, value: object) -> bool:
        if value is None or type(value) is bool:
            self.charge(5)
        elif type(value) is str:
            self._string(value)
        elif type(value) is int:
            _require(
                value.bit_length() <= MAX_ENVELOPE_BYTES * 4, "native_envelope_size"
            )
            try:
                text = str(value)
            except ValueError as exc:
                message = "native_envelope_integer"
                raise ValueError(message) from exc
            self.charge(len(text))
        elif type(value) is float:
            _require(math.isfinite(value), "native_envelope_nonfinite")
            self.charge(len(repr(value)))
        elif type(value) is Decimal:
            _require(value.is_finite(), "native_envelope_nonfinite")
            _require(value.__sizeof__() <= MAX_ENVELOPE_BYTES, "native_envelope_size")
            self._string(str(value))
        elif type(value) in (datetime, date, time):
            self._string(cast("datetime | date | time", value).isoformat())
        else:
            return False
        return True

    def visit(self, value: object, depth: int = 0) -> None:
        """Traverse only supported native metadata; reject cycles and excess."""
        _require(depth <= MAX_ENVELOPE_DEPTH, "native_envelope_depth")
        self.nodes += 1
        _require(self.nodes <= MAX_ENVELOPE_NODES, "native_envelope_nodes")
        if self._scalar(value):
            return
        _require(
            isinstance(value, Mapping) or type(value) in (list, tuple),
            "native_envelope_type",
        )
        identity = id(value)
        _require(identity not in self.active, "native_envelope_cycle")
        self.active.add(identity)
        try:
            if isinstance(value, Mapping):
                _require(
                    len(value) * 2 <= MAX_ENVELOPE_NODES - self.nodes,
                    "native_envelope_nodes",
                )
                self.charge(2 + 2 * len(value) + 2 * max(0, len(value) - 1))
                for key, item in value.items():
                    _require(type(key) is str, "native_envelope_key")
                    self.visit(key, depth + 1)
                    self.visit(item, depth + 1)
            else:
                sequence = cast("list[object] | tuple[object, ...]", value)
                _require(
                    len(sequence) <= MAX_ENVELOPE_NODES - self.nodes,
                    "native_envelope_nodes",
                )
                self.charge(2 + 2 * max(0, len(sequence) - 1))
                for item in sequence:
                    self.visit(item, depth + 1)
        finally:
            self.active.remove(identity)


def validate_native_envelope(
    output: CompoundAdapterOutput, contracts: tuple[NativeProfileContract, ...]
) -> int:
    """Bound all retained non-table descriptors, including held-result losses.

    Schema sizes come from independent trusted contracts. The caller must also
    enforce actual schema equality and include the returned size in its total.
    """
    budget = _Budget()
    budget.visit((output.source_sha256, output.layout, output.status, output.kind))
    _require(
        len(output.source_losses) <= MAX_SOURCE_LOSSES, "native_envelope_loss_count"
    )
    for loss in output.source_losses:
        _require(type(loss) is LossAccounting, "native_envelope_loss_type")
        budget.visit((loss.source_coordinate, loss.disposition, loss.reason))
    _require(
        sum(len(p.excluded_sheets) for p in output.profiles) <= MAX_EXCLUDED_SHEETS,
        "native_envelope_excluded_count",
    )
    for profile in output.profiles:
        budget.visit(profile.profile_id)
        budget.visit(profile.metadata)
        budget.visit(profile.excluded_sheets)
        for recordset in profile.recordsets:
            budget.visit(
                (recordset.name, recordset.schema_id, recordset.schema_version)
            )
    for contract in contracts:
        for recordset in contract.recordsets:
            budget.charge(recordset.schema.serialize().size)
    return budget.size
