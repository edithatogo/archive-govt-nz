"""Pure accounting of detected structural units, not semantic extraction proof."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, cast

MAX_BYTES = 4 * 1024 * 1024
MAX_UNITS = 10_000
MAX_RECEIPTS = 16
MAX_TEXT = 256
MAX_COUNT = 1_000_000_000
_CONTROL = 32
_MAX_ROW = 1_048_576
_MAX_COLUMN = 16_384
SCHEMA = "archive-govt-nz.health-area-accounting/v1"
_LEGACY = {
    "title",
    "state",
    "max_row",
    "max_column",
    "formula_cells",
    "merged_ranges",
    "table_names",
    "chart_count",
}
_RICH = {
    "dimension",
    "formula_coordinates",
    "comment_coordinates",
    "merged_range_refs",
    "table_ranges",
    "hidden_rows",
    "hidden_columns",
    "defined_names",
    "formula_cache",
}
_PROFILES = {
    "archive-govt-nz.health-budget-extraction/v1": "budget-expenditure/v1",
    "archive-govt-nz.health-forecast-extraction/v1": (
        "treasury-health-expense-summary/v1"
    ),
    "archive-govt-nz.health-historical-extraction/v1": (
        "treasury-historical-health-gdp/v1"
    ),
}


@dataclass(frozen=True)
class PinnedMetadata:
    """Caller-supplied immutable bytes and their independently selected pin."""

    payload: bytes
    sha256: str


def _require(condition: object) -> None:
    if not condition:
        message = "area_accounting_contract"
        raise ValueError(message)


def _encoded(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False
    ).encode()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _constant(_value: str) -> None:
    message = "area_accounting_nonfinite_json"
    raise ValueError(message)


def _load(snapshot: PinnedMetadata) -> dict[str, Any]:
    _require(type(snapshot.payload) is bytes and len(snapshot.payload) <= MAX_BYTES)
    _require(hashlib.sha256(snapshot.payload).hexdigest() == snapshot.sha256)
    value = json.loads(
        snapshot.payload, object_pairs_hook=_pairs, parse_constant=_constant
    )
    _require(isinstance(value, dict))
    return value


def _text(value: object) -> str:
    _require(isinstance(value, str) and 0 < len(value) <= MAX_TEXT)
    text = cast("str", value)
    _require(not any(ord(char) < _CONTROL for char in text))
    return text


def _number(value: object) -> int:
    _require(type(value) is int and 0 <= value <= MAX_COUNT)
    return cast("int", value)


def _unique(values: list[str]) -> None:
    _require(len(values) == len({value.casefold() for value in values}))


def _coordinate(value: object, structure: dict[str, Any]) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]*)", _text(value))
    _require(match)
    letters, number = cast("re.Match[str]", match).groups()
    column = 0
    for letter in letters:
        column = column * 26 + ord(letter) - ord("A") + 1
    row = int(number)
    _require(1 <= row <= min(_MAX_ROW, structure["max_row"]))
    _require(1 <= column <= min(_MAX_COLUMN, structure["max_column"]))
    return row, column


def _unit(path: str, digest: str, kind: str, selector: list[str]) -> dict[str, Any]:
    identity = [SCHEMA, path, digest, kind, selector]
    return {
        "unit_id": hashlib.sha256(_encoded(identity)).hexdigest(),
        "donor_path": path,
        "source_object_sha256": digest,
        "kind": kind,
        "selector": selector,
        "state": "unresolved",
        "contexts": [],
    }


def _workbook(item: dict[str, Any], path: str, digest: str) -> list[dict[str, Any]]:
    rich = item.get("schema_version") == "archive-govt-nz.workbook-inventory/v1"
    _require("schema_version" not in item or rich)
    sheets = item["sheets"]
    _require(isinstance(sheets, list) and len(sheets) <= MAX_UNITS)
    _unique([_text(sheet["title"]) for sheet in sheets])
    units: list[dict[str, Any]] = []
    for sheet in sheets:
        _require(set(sheet) == (_LEGACY | _RICH if rich else _LEGACY))
        _require(sheet["state"] in {"visible", "hidden", "veryHidden"})
        for key in (
            "max_row",
            "max_column",
            "formula_cells",
            "merged_ranges",
            "chart_count",
        ):
            _number(sheet[key])
        _require(isinstance(sheet["table_names"], list))
        names = [_text(name) for name in sheet["table_names"]]
        _unique(names)
        ranges = dict(sheet["table_ranges"]) if rich else {}
        if rich:
            _require(
                len(ranges) == len(sheet["table_ranges"]) and set(ranges) == set(names)
            )
            for area in ranges.values():
                _require(_text(area).count(":") == 1)
                start, end = area.split(":")
                top, left = _coordinate(start, sheet)
                bottom, right = _coordinate(end, sheet)
                _require(top <= bottom and left <= right)
        title = sheet["title"]
        units.append(
            {
                **_unit(path, digest, "workbook_sheet", [title]),
                "inventory_shape": "rich" if rich else "legacy",
                "structural_metadata": {
                    **{
                        key: sheet[key]
                        for key in sorted(_LEGACY - {"title", "table_names"})
                    },
                    "table_names": sorted(names),
                },
            }
        )
        units.extend(
            {
                **_unit(path, digest, "workbook_table", [title, name]),
                "range": ranges.get(name),
            }
            for name in names
        )
    return units


def _inventory(donor: dict[str, Any], census: dict[str, Any]) -> list[dict[str, Any]]:
    _require(donor["schema_version"] == "archive-govt-nz.health-donor-manifest/v1")
    _require(census["schema_version"] == "archive-govt-nz.health-format-census/v1")
    objects = donor["objects"]
    _require(_number(donor["file_count"]) == len(objects))
    paths = [_text(row["path"]) for row in objects]
    _unique(paths)
    for path in paths:
        _require(not any(part in {"", ".", ".."} for part in path.split("/")))
        _require("\\" not in path and ":" not in path)
    identities = {row["path"]: row["sha256"] for row in objects}
    for row in objects:
        _require(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]))
        _require(row["object_id"] == "sha256:" + row["sha256"])
    expected = {path for path in paths if path.endswith((".xlsx", ".pdf", ".sqlite"))}
    items = census["items"]
    _unique([_text(item["path"]) for item in items])
    _require({item["path"] for item in items} == expected)
    units: list[dict[str, Any]] = []
    for item in items:
        path = item["path"]
        digest = identities[path]
        _require(item["object_id"] == "sha256:" + digest)
        kind = item["kind"]
        _require(
            path.endswith(
                "." + {"xlsx": "xlsx", "pdf": "pdf", "sqlite": "sqlite"}[kind]
            )
        )
        if kind == "xlsx":
            units.extend(_workbook(item, path, digest))
        elif kind == "pdf":
            units.append(
                {
                    **_unit(path, digest, "pdf_structure", []),
                    "page_count_observation": _number(item["page_count"]),
                    "table_detection": "not_performed",
                }
            )
        else:
            _require(item["integrity"] == "ok")
            _unique([_text(table["name"]) for table in item["tables"]])
            units.extend(
                {
                    **_unit(path, digest, "sqlite_oracle_table", [table["name"]]),
                    "row_count_observation": _number(table["row_count"]),
                }
                for table in item["tables"]
            )
        _require(len(units) <= MAX_UNITS)
    return units


def _receipts(
    snapshots: tuple[PinnedMetadata, ...], units: list[dict[str, Any]]
) -> dict[str, Any]:
    receipts: dict[str, Any] = {}
    for snapshot in snapshots:
        _require(snapshot.sha256 not in receipts)
        receipt = _load(snapshot)
        _require(receipt["transformation_id"] == _PROFILES[receipt["schema_version"]])
        _require(receipt["status"] in {"passed", "partial", "empty"})
        _text(receipt["source_vintage"])
        path, digest = receipt["source_locator"], receipt["source_object_sha256"]
        available = {
            row["selector"][0]: row
            for row in units
            if row["kind"] == "workbook_sheet"
            and row["donor_path"] == path
            and row["source_object_sha256"] == digest
        }
        _require(available)
        observed = _workbook(receipt["workbook_inventory"], path, digest)
        _require(
            {row["unit_id"] for row in observed}
            == {row["unit_id"] for row in units if row["donor_path"] == path}
        )
        by_id = {row["unit_id"]: row for row in units}
        for observed_unit in observed:
            previous = by_id[observed_unit["unit_id"]]
            if observed_unit["kind"] == "workbook_sheet":
                _require(
                    observed_unit["structural_metadata"]
                    == previous["structural_metadata"]
                )
            elif previous["range"] is not None and observed_unit["range"] is not None:
                _require(previous["range"] == observed_unit["range"])
        exclusions = receipt["excluded_sheets"]
        _unique([_text(row["sheet"]) for row in exclusions])
        for exclusion in exclusions:
            _require(exclusion["sheet"] in available)
            reason = _text(exclusion["reason"])
            _require(re.fullmatch(r"[a-z][a-z0-9_]{0,127}", reason))
            available[exclusion["sheet"]]["contexts"].append(
                {
                    "manifest_sha256": snapshot.sha256,
                    "state": "excluded",
                    "coverage": "whole_unit",
                    "reason": reason,
                    "scope": "adapter_context_only",
                    "mapping_assurance": "not_performed",
                }
            )
        receipts[snapshot.sha256] = receipt
    return receipts


def _selection(
    receipt: dict[str, Any], units: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if receipt["schema_version"] != "archive-govt-nz.health-forecast-extraction/v1":
        return None
    selection = receipt["selection"]
    _require(
        set(selection)
        == {
            "sheet",
            "label_cell",
            "unit_cell",
            "year_row",
            "amount_type_row",
            "columns",
        }
    )
    sheets = {
        row["selector"][0]: row
        for row in units
        if row["kind"] == "workbook_sheet"
        and row["donor_path"] == receipt["source_locator"]
    }
    sheet = sheets[selection["sheet"]]["structural_metadata"]
    _require(
        selection["sheet"] not in {row["sheet"] for row in receipt["excluded_sheets"]}
    )
    for key in ("label_cell", "unit_cell"):
        _coordinate(selection[key], sheet)
    for key in ("year_row", "amount_type_row"):
        _require(1 <= _number(selection[key]) <= min(_MAX_ROW, sheet["max_row"]))
    columns = selection["columns"]
    _require(isinstance(columns, list) and 0 < len(columns) <= MAX_UNITS)
    _require(
        all(
            1 <= _number(column) <= min(_MAX_COLUMN, sheet["max_column"])
            for column in columns
        )
    )
    _require(len(set(columns)) == len(columns))
    return {**selection, "columns": list(columns)}


def reconcile_areas(
    donor: PinnedMetadata,
    census: PinnedMetadata,
    extractions: tuple[PinnedMetadata, ...] = (),
    *,
    assertions: tuple[dict[str, str], ...] = (),
) -> dict[str, Any]:
    """Account only detected units; callers retain responsibility for evidence.

    Pins verify supplied metadata bytes, not source files or extraction outputs.
    Mappings are assertions only. Adapter exclusions never resolve the global
    unit, and partial mappings cannot resolve a whole-sheet remainder.
    """
    _require(len(extractions) <= MAX_RECEIPTS and len(assertions) <= MAX_UNITS)
    units = _inventory(_load(donor), _load(census))
    receipts = _receipts(extractions, units)
    indexed = {row["unit_id"]: row for row in units}
    for assertion in assertions:
        _require(
            set(assertion)
            == {"unit_id", "manifest_sha256", "state", "coverage", "reason"}
        )
        row = indexed[assertion["unit_id"]]
        receipt = receipts[assertion["manifest_sha256"]]
        _require(
            row["source_object_sha256"] == receipt["source_object_sha256"]
            and row["donor_path"] == receipt["source_locator"]
        )
        _require(row["kind"] in {"workbook_sheet", "workbook_table"})
        _require(assertion["state"] in {"mapped", "excluded", "unresolved"})
        _require(assertion["coverage"] in {"whole_unit", "partial"})
        _require(re.fullmatch(r"[a-z][a-z0-9_]{0,127}", assertion["reason"]))
        _require(
            not any(
                context["manifest_sha256"] == assertion["manifest_sha256"]
                for context in row["contexts"]
            )
        )
        if assertion["state"] == "mapped":
            _require(receipt["status"] == "passed")
        row["contexts"].append(
            {
                **{key: value for key, value in assertion.items() if key != "unit_id"},
                "scope": "adapter_context_only",
                "mapping_assurance": "assertion_only",
            }
        )
    for row in units:
        row["contexts"].sort(key=lambda context: context["manifest_sha256"])
        if any(
            context["state"] == "mapped" and context["coverage"] == "whole_unit"
            for context in row["contexts"]
        ):
            row["state"] = "mapped_assertion_only"
    return {
        "schema_version": SCHEMA,
        "scope": "detected_structural_units_only",
        "normalization_verification": "not_performed",
        "rights_state": "not_evaluated",
        "source_fixity": "not_performed",
        "metadata_fixity": "verified",
        "donor_manifest_sha256": donor.sha256,
        "census_sha256": census.sha256,
        "extraction_manifest_sha256": sorted(receipts),
        "extractions": [
            {
                "manifest_sha256": pin,
                "source_vintage": receipt["source_vintage"],
                "selection_scope": "partial_adapter_selection",
                "selection": _selection(receipt, units),
            }
            for pin, receipt in sorted(receipts.items())
        ],
        "units": sorted(units, key=lambda row: row["unit_id"]),
    }
