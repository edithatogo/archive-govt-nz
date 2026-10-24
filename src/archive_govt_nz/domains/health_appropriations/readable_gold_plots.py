"""Additive paged displays of verified Gold, with exact typed point sidecars."""

from __future__ import annotations

import hashlib
import json
import math
import os
import textwrap
from contextlib import suppress
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

import matplotlib as mpl
import PIL
import pyarrow as pa
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from matplotlib.ft2font import __freetype_version__

mpl.use("Agg")
from matplotlib import pyplot as plt

from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_queries as reader,
)
from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_verification as verifier,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

    from matplotlib.backends.backend_agg import FigureCanvasAgg

from archive_govt_nz.domains.health_appropriations.budget_export import (
    _json as encode_json,
)
from archive_govt_nz.domains.health_appropriations.budget_export import (
    _owned as check_owned,
)
from archive_govt_nz.domains.health_appropriations.budget_export import (
    _reserve as reserve_directory,
)
from archive_govt_nz.domains.health_appropriations.budget_export import (
    _write as write_exclusive,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_plots import (
    _context as plot_context,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_plots import (
    _label as source_label,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_plots import (
    _value as source_value,
)

SCHEMA = "archive-govt-nz.health-readable-canonical-plots/v1"
MAX_GROUPS = 32
MAX_POINTS = 500
MAX_TOTAL_POINTS = 4000
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
PAGE_POINTS = 8
_PRODUCTS = (
    "historical",
    "budget",
    "revenue",
    "pharmac",
    "moh",
    "crown_befu",
    "crown_hyefu",
    "fiscal_crown",
)
_ERROR = "readable_gold_plot_invalid"

SCHEMA_DOCUMENT: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://archive-govt-nz.example/schemas/health-readable-canonical-plots-v1",
    "title": "Additive readable canonical Gold plot package and point sidecar",
    "oneOf": [{"$ref": "#/$defs/manifest"}, {"$ref": "#/$defs/sidecar"}],
    "$defs": {
        "point": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "ordinal",
                "caption",
                "amount",
                "input_record_ids",
                "source_row",
            ],
            "properties": {
                "ordinal": {"type": "integer", "minimum": 1, "maximum": 500},
                "caption": {"type": "string", "minLength": 1},
                "amount": {
                    "type": "string",
                    "pattern": "^-?\\d+(\\.\\d+)?([eE][+-]?\\d+)?$",
                },
                "input_record_ids": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                    "minItems": 1,
                },
                "source_row": {"type": "object"},
            },
        },
        "page": {
            "type": "object",
            "additionalProperties": False,
            "required": ["path", "product", "context", "context_sha256", "points"],
            "properties": {
                "path": {
                    "type": "string",
                    "pattern": "^plot_[a-z_]+_[a-f0-9]{20}_\\d{3}\\.png$",
                },
                "product": {
                    "enum": [
                        "historical",
                        "budget",
                        "revenue",
                        "pharmac",
                        "moh",
                        "crown_befu",
                        "crown_hyefu",
                        "fiscal_crown",
                        "biff8_budget",
                        "biff8_revenue",
                    ]
                },
                "context": {"type": "object"},
                "context_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "points": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 8,
                    "items": {"$ref": "#/$defs/point"},
                },
            },
        },
        "omission": {
            "type": "object",
            "additionalProperties": False,
            "required": ["product", "reason", "input_record_ids"],
            "properties": {
                "product": {
                    "enum": [
                        "historical",
                        "budget",
                        "revenue",
                        "pharmac",
                        "moh",
                        "crown_befu",
                        "crown_hyefu",
                        "fiscal_crown",
                        "biff8_budget",
                        "biff8_revenue",
                    ]
                },
                "reason": {
                    "enum": ["group_limit", "point_limit", "biff8_display_excluded"]
                },
                "input_record_ids": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
                "context": {"type": "object"},
            },
        },
        "sidecar": {
            "type": "object",
            "additionalProperties": False,
            "required": ["schema_version", "pages", "omissions"],
            "properties": {
                "schema_version": {
                    "const": "archive-govt-nz.health-readable-canonical-plots/v1"
                },
                "pages": {
                    "type": "array",
                    "maxItems": 4000,
                    "items": {"$ref": "#/$defs/page"},
                },
                "omissions": {"type": "array", "items": {"$ref": "#/$defs/omission"}},
            },
        },
        "manifest": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "status",
                "point_count",
                "page_count",
                "omissions",
                "geometry",
                "numeric_conversion",
                "rights",
                "publication",
                "parent_manifest_sha256",
                "renderer",
                "outputs",
                "schema_sha256",
            ],
            "properties": {
                "schema_version": {
                    "const": "archive-govt-nz.health-readable-canonical-plots/v1"
                },
                "status": {"enum": ["planned", "complete", "complete_with_omissions"]},
                "point_count": {"type": "integer", "minimum": 0, "maximum": 4000},
                "page_count": {"type": "integer", "minimum": 0, "maximum": 4000},
                "omissions": {"type": "array", "items": {"$ref": "#/$defs/omission"}},
                "geometry": {"const": "all_visible_text_inside_canvas"},
                "numeric_conversion": {"const": "float_for_display_only"},
                "rights": {"const": "not_evaluated"},
                "publication": {"const": "not_performed"},
                "parent_manifest_sha256": {
                    "type": "string",
                    "pattern": "^[a-f0-9]{64}$",
                },
                "renderer": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["matplotlib", "pillow", "freetype", "backend"],
                    "properties": {
                        "matplotlib": {"type": "string", "minLength": 1},
                        "pillow": {"type": "string", "minLength": 1},
                        "freetype": {"type": "string", "minLength": 1},
                        "backend": {"const": "Agg"},
                    },
                },
                "outputs": {
                    "type": "object",
                    "minProperties": 1,
                    "maxProperties": 4002,
                    "required": ["plot-points.json", "plot-schema.json"],
                    "propertyNames": {
                        "pattern": (
                            "^(plot-(points|schema)\\.json|plot_[a-z_]+_"
                            "[a-f0-9]{20}_\\d{3}\\.png)$"
                        )
                    },
                    "additionalProperties": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["sha256", "bytes"],
                        "properties": {
                            "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                            "bytes": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 33554432,
                            },
                        },
                    },
                },
                "schema_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            },
        },
    },
}


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _json_value(value: object) -> object:
    if isinstance(value, Decimal):
        _require(value.is_finite())
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _encoded(value: object) -> bytes:
    return encode_json(_json_value(value), max_bytes=MAX_OUTPUT_BYTES)


def _ids(row: dict[str, Any]) -> list[str]:
    values = row.get("input_record_ids")
    if values is None:
        values = [row.get("input_record_id", row.get("record_id"))]
    _require(isinstance(values, list) and bool(values))
    _require(all(isinstance(value, str) and value for value in values))
    return sorted(cast("list[str]", values))


def _render(
    context: dict[str, Any], points: list[dict[str, Any]], *, title: str
) -> bytes:
    with mpl.rc_context(
        {"text.usetex": False, "text.parse_math": False, "font.family": "DejaVu Sans"}
    ):
        figure, axis = plt.subplots(figsize=(14, 8), dpi=100, layout="constrained")
        try:
            values = [float(point["amount"]) for point in points]
            _require(all(math.isfinite(value) for value in values))
            captions = [
                textwrap.fill(
                    textwrap.shorten(
                        point["caption"], width=170, placeholder=" … [see sidecar]"
                    ),
                    width=48,
                )
                for point in points
            ]
            axis.barh(range(len(points)), values, color="#347a67")
            axis.set_yticks(range(len(points)), captions, fontsize=9)
            axis.invert_yaxis()
            axis.set_title(
                textwrap.fill(
                    textwrap.shorten(
                        title,
                        width=110,
                    ),
                    width=65,
                )
            )
            axis.set_xlabel(
                textwrap.fill(
                    "Amount in literal source unit "
                    + str(context.get("unit") or "not stated; see sidecar")
                    + "; display only",
                    width=100,
                )
            )
            axis.grid(axis="x", alpha=0.2)
            figure.canvas.draw()
            renderer = cast("FigureCanvasAgg", figure.canvas).get_renderer()
            width, height = figure.canvas.get_width_height()
            visible_ticks = [
                label
                for value, label in zip(
                    axis.get_xticks(), axis.get_xticklabels(), strict=True
                )
                if axis.get_xlim()[0] <= value <= axis.get_xlim()[1]
            ]
            for label in [
                axis.title,
                axis.xaxis.label,
                axis.xaxis.get_offset_text(),
                *visible_ticks,
                *axis.get_yticklabels(),
            ]:
                if label.get_visible() and label.get_text():
                    box = label.get_window_extent(renderer)
                    _require(
                        box.x0 >= 0
                        and box.y0 >= 0
                        and box.x1 <= width
                        and box.y1 <= height
                    )
            buffer = BytesIO()
            figure.savefig(
                buffer,
                format="png",
                metadata={"Software": "archive-govt-nz readable plots/v1"},
            )
            return buffer.getvalue()
        finally:
            plt.close(figure)


def build_readable_plots(
    tables: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Retain original rows; page discrete categories without joins or netting."""
    files: dict[str, bytes] = {}
    pages: list[dict[str, Any]] = []
    omissions: list[dict[str, Any]] = []
    total = 0
    for kind in _PRODUCTS:
        rows = tables.get(reader.PRODUCTS[kind][0], [])
        groups: dict[bytes, tuple[dict[str, Any], list[dict[str, Any]]]] = {}
        for row in rows:
            context = plot_context(kind, row)
            key = _encoded(context)
            groups.setdefault(key, (context, []))[1].append(row)
        for key, (context, entries) in sorted(groups.items()):
            reason = (
                "group_limit"
                if len(groups) > MAX_GROUPS
                else "point_limit"
                if len(entries) > MAX_POINTS or total + len(entries) > MAX_TOTAL_POINTS
                else None
            )
            if reason:
                omissions.append(
                    {
                        "product": kind,
                        "context": context,
                        "reason": reason,
                        "input_record_ids": sorted(
                            identity for row in entries for identity in _ids(row)
                        ),
                    }
                )
                continue
            ordered_entries = sorted(
                entries, key=lambda row: (source_label(row), _encoded(row))
            )
            identity = hashlib.sha256(key).hexdigest()
            for start in range(0, len(entries), PAGE_POINTS):
                points = []
                for ordinal, row in enumerate(
                    ordered_entries[start : start + PAGE_POINTS], start + 1
                ):
                    amount = source_value(kind, row)
                    _require(amount.is_finite())
                    points.append(
                        {
                            "ordinal": ordinal,
                            "caption": (
                                f"{ordinal}. {row['period_token']} | "
                                f"{row['source_label']}"
                            ),
                            "amount": str(amount),
                            "input_record_ids": _ids(row),
                            "source_row": _json_value(row),
                        }
                    )
                name = f"plot_{kind}_{identity[:20]}_{start // PAGE_POINTS + 1:03d}.png"
                payload = _render(
                    context,
                    points,
                    title=(
                        f"{kind} | group {identity[:12]} | "
                        f"page {start // PAGE_POINTS + 1}/"
                        f"{(len(entries) + PAGE_POINTS - 1) // PAGE_POINTS} | "
                        f"{context.get('source_vintage')}"
                    ),
                )
                _require(
                    sum(map(len, files.values())) + len(payload) <= MAX_OUTPUT_BYTES
                )
                files[name] = payload
                pages.append(
                    {
                        "path": name,
                        "product": kind,
                        "context": context,
                        "context_sha256": identity,
                        "points": points,
                    }
                )
            total += len(entries)
    for kind in ("biff8_budget", "biff8_revenue"):
        rows = tables.get(reader.PRODUCTS[kind][0], [])
        if rows:
            omissions.append(
                {
                    "product": kind,
                    "reason": "biff8_display_excluded",
                    "input_record_ids": sorted(
                        identity for row in rows for identity in _ids(row)
                    ),
                }
            )
    sidecar = _json_value(
        {"schema_version": SCHEMA, "pages": pages, "omissions": omissions}
    )
    Draft202012Validator(SCHEMA_DOCUMENT).validate(sidecar)
    files["plot-points.json"] = _encoded(sidecar)
    files["plot-schema.json"] = _encoded(SCHEMA_DOCUMENT)
    _require(sum(map(len, files.values())) <= MAX_OUTPUT_BYTES)
    return files, {
        "schema_version": SCHEMA,
        "status": "complete_with_omissions" if omissions else "complete",
        "point_count": total,
        "page_count": len(pages),
        "omissions": omissions,
        "geometry": "all_visible_text_inside_canvas",
        "numeric_conversion": "float_for_display_only",
        "schema_sha256": hashlib.sha256(files["plot-schema.json"]).hexdigest(),
        "rights": "not_evaluated",
        "publication": "not_performed",
    }


def export_readable_plots(
    parent: Path, pin: str, output: Path, *, dry_run: bool = True
) -> dict[str, Any]:
    """Verify before reserving output; persist exclusively under a trusted parent."""
    try:
        _require(
            type(dry_run) is bool and not output.exists() and not output.is_symlink()
        )
        _require(output.parent.is_dir() and not output.parent.is_symlink())
        _require(
            not output.resolve().is_relative_to(parent.resolve())
            and not parent.resolve().is_relative_to(output.resolve())
        )
        _require(
            verifier.verify_canonical_gold_package(parent, pin)["status"] == "verified"
        )
        marker = verified_snapshot(
            parent / "MANIFEST.json", pin, max_bytes=verifier.MAX_MANIFEST_BYTES
        )
        manifest = json.loads(marker)
        tables = {
            reader.PRODUCTS[kind][0]: reader.read_canonical_gold_product(
                parent, pin, kind
            ).to_pylist()
            for kind in reader.PRODUCTS
            if kind in manifest["products"]
        }
        files, report = build_readable_plots(tables)
        receipt = {
            **report,
            "parent_manifest_sha256": pin,
            "renderer": {
                "matplotlib": mpl.__version__,
                "pillow": PIL.__version__,
                "freetype": __freetype_version__,
                "backend": "Agg",
            },
            "outputs": {
                name: {
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                }
                for name, payload in sorted(files.items())
            },
        }
        Draft202012Validator(SCHEMA_DOCUMENT).validate(_json_value(receipt))
        final = _encoded(receipt)
        _require(
            len(final) <= verifier.MAX_MANIFEST_BYTES
            and sum(map(len, files.values())) + len(final) <= MAX_OUTPUT_BYTES
        )
        _require(
            verified_snapshot(
                parent / "MANIFEST.json", pin, max_bytes=verifier.MAX_MANIFEST_BYTES
            )
            == marker
        )
        _require(
            verifier.verify_canonical_gold_package(parent, pin)["status"] == "verified"
        )
        if dry_run:
            return {**receipt, "status": "planned"}
        output.mkdir()
        state = output.lstat()
        directory = reserve_directory(output, (state.st_dev, state.st_ino))
        try:
            for name, payload in files.items():
                write_exclusive(directory, name, payload)
                _require(
                    verified_snapshot(
                        output / name,
                        hashlib.sha256(payload).hexdigest(),
                        max_bytes=MAX_OUTPUT_BYTES,
                    )
                    == payload
                )
            check_owned(output, directory)
            _require({path.name for path in output.iterdir()} == set(files))
            write_exclusive(directory, "MANIFEST.json", final)
            _require(
                verified_snapshot(
                    output / "MANIFEST.json",
                    hashlib.sha256(final).hexdigest(),
                    max_bytes=verifier.MAX_MANIFEST_BYTES,
                )
                == final
            )
            check_owned(output, directory)
        except BaseException:
            with suppress(OSError, ValueError):
                write_exclusive(
                    directory, "FAILURE.json", _encoded({"status": "incomplete"})
                )
            raise
        finally:
            if directory.descriptor is not None:
                os.close(directory.descriptor)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        OverflowError,
        pa.ArrowException,
        ValidationError,
    ):
        raise ValueError(_ERROR) from None
    else:
        return receipt
