"""Read-only fixity verification for canonical Health Gold packages."""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from pathlib import Path

from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_PACKAGE_BYTES = 128 * 1024 * 1024
MAX_OUTPUTS = 512
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA_VERSION = "archive-govt-nz.health-canonical-gold/v2"
_REVISION_KEY_FIELDS = (
    "recordset",
    "measure",
    "source_label",
    "unit",
    "currency",
    "price_basis",
    "base_period",
    "denominator_definition",
    "institutional_coverage",
    "accounting_basis",
    "period_token",
)
_PRODUCT_REVISION_KEY_FIELDS = {
    "budget": (
        "period_token",
        "amount_type",
        "unit",
        "vote",
        "department",
        "portfolio",
        "source_label",
    ),
    "revenue": (
        "period_token",
        "amount_type",
        "unit",
        "vote",
        "department",
        "revenue_type",
        "source_label",
    ),
    "biff8_budget": (
        "period_token",
        "measure",
        "amount_type",
        "unit",
        "currency",
        "price_basis",
        "base_period",
        "denominator_definition",
        "source_label",
        "vote",
        "appropriation",
        "department",
        "portfolio",
        "value_basis",
    ),
    "biff8_revenue": (
        "period_token",
        "measure",
        "amount_type",
        "unit",
        "currency",
        "price_basis",
        "base_period",
        "denominator_definition",
        "source_label",
        "vote",
        "department",
        "revenue_type",
        "source_application_id",
        "value_basis",
    ),
    "pharmac": (
        "period_token",
        "measure",
        "unit",
        "currency",
        "price_basis",
        "base_period",
        "denominator_definition",
        "amount_type",
        "source_label",
        "budget_scope",
        "funding_regime",
    ),
    "moh": (
        "period_token",
        "profile",
        "source_label",
        "price_basis",
        "per_capita",
        "unit",
        "price_base",
        "denominator",
    ),
    "crown": (
        "period_token",
        "measure",
        "amount_type",
        "unit",
        "currency",
        "price_basis",
        "base_period",
        "denominator_definition",
        "source_label",
        "institutional_coverage",
        "accounting_basis",
    ),
}
_LEGACY_PRODUCT_REVISION_KEY_FIELDS = {
    name: key_fields
    for name, key_fields in _PRODUCT_REVISION_KEY_FIELDS.items()
    if name not in {"biff8_budget", "biff8_revenue"}
}
_MIN_OVERLAP_PRODUCTS = 2
_MOH_PROFILE_COUNT = 2
_MOH_PROFILE_ROWS = 40
_MOH_TOTAL_ROWS = _MOH_PROFILE_COUNT * _MOH_PROFILE_ROWS
_ALLOWED_OVERLAP_PRODUCTS = {
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
}
_COMMON = {
    "schema_version": "archive-govt-nz.health-canonical-gold-verification/v1",
    "verification_scope": "manifest_declared_output_fixity",
    "rights_state": "not_evaluated",
    "publication": "not_performed",
}


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


def _fail_type(message: str) -> NoReturn:
    raise TypeError(message)


def _valid_product_revision_reports(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if set(value) == set(_PRODUCT_REVISION_KEY_FIELDS):
        key_fields_by_product = _PRODUCT_REVISION_KEY_FIELDS
    elif set(value) == set(_LEGACY_PRODUCT_REVISION_KEY_FIELDS):
        key_fields_by_product = _LEGACY_PRODUCT_REVISION_KEY_FIELDS
    else:
        return False
    for name, key_fields in key_fields_by_product.items():
        report = value.get(name)
        if (
            not isinstance(report, dict)
            or report.get("scope")
            != "same_literal_source_dimensions_and_period_token_within_product"
            or report.get("key_fields") != list(key_fields)
            or report.get("completeness") != "observed_rows_only"
            or report.get("interpretation") != "not_assessed"
            or not isinstance(report.get("candidates"), list)
        ):
            return False
        counts = (
            report.get("shared_series_period_count"),
            report.get("unchanged_series_period_count"),
            report.get("ambiguous_series_period_count"),
            report.get("changed_candidate_count"),
        )
        if any(type(count) is not int or count < 0 for count in counts):
            return False
        if counts[3] != len(report["candidates"]):
            return False
    return True


def _valid_budget_input_total_reconciliation(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    groups = value.get("groups")
    pins = value.get("source_package_marker_sha256")
    if (
        value.get("schema_version")
        != "archive-govt-nz.health-budget-input-total-reconciliation/v1"
        or value.get("scope")
        != "pinned_canonical_appropriation_facts_to_budget_gold_rows"
        or value.get("period_basis") != "literal_source_token_only"
        or value.get("unit_currency_and_price_basis")
        != "source_context_preserved_currency_unknown"
        or value.get("vintage_pooling") != "not_performed"
        or value.get("donor_control") != "not_performed"
        or value.get("official_source_control") != "not_performed"
        or value.get("cross_source_comparison") != "not_performed"
        or value.get("status") != "exact_canonical_input_totals_reconciled"
        or type(value.get("group_count")) is not int
        or type(value.get("input_record_count")) is not int
        or not isinstance(groups, list)
        or not groups
        or value["group_count"] != len(groups)
        or not isinstance(pins, list)
        or not pins
        or any(type(pin) is not str or _DIGEST.fullmatch(pin) is None for pin in pins)
        or pins != sorted(set(pins))
    ):
        return False
    all_ids: set[str] = set()
    total_records = 0
    fields = (
        "source_vintage",
        "period_token",
        "amount_type",
        "unit",
        "vote",
        "department",
        "portfolio",
        "source_label",
    )
    for group in groups:
        if (
            not isinstance(group, dict)
            or any(
                type(group.get(field)) is not str or not group[field]
                for field in fields
            )
            or group.get("status") != "exact_match"
            or type(group.get("input_record_count")) is not int
            or group["input_record_count"] <= 0
            or not isinstance(group.get("input_record_ids"), list)
            or len(group["input_record_ids"]) != group["input_record_count"]
            or group["input_record_ids"] != sorted(set(group["input_record_ids"]))
            or any(
                type(record_id) is not str or not record_id
                for record_id in group["input_record_ids"]
            )
            or all_ids.intersection(group["input_record_ids"])
        ):
            return False
        try:
            input_total = Decimal(group["canonical_input_total"])
            output_total = Decimal(group["gold_output_total"])
        except InvalidOperation, KeyError, TypeError:
            return False
        if not input_total.is_finite() or input_total != output_total:
            return False
        all_ids.update(group["input_record_ids"])
        total_records += group["input_record_count"]
    return total_records == value["input_record_count"] == len(all_ids)


def _budget_reconciliation_matches_manifest(
    value: object, package_markers: object, products: object
) -> bool:
    """Bind the Budget control to package provenance and its product copy."""
    if (
        not _valid_budget_input_total_reconciliation(value)
        or not isinstance(package_markers, list)
        or any(
            type(marker) is not str or _DIGEST.fullmatch(marker) is None
            for marker in package_markers
        )
        or not isinstance(products, dict)
    ):
        return False
    budget_product = products.get("budget")
    if not isinstance(value, dict) or not isinstance(budget_product, dict):
        return False
    return (
        set(value["source_package_marker_sha256"]).issubset(set(package_markers))
        and budget_product.get("input_total_reconciliation") == value
    )


def _valid_revenue_input_total_reconciliation(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    groups = value.get("groups")
    pins = value.get("source_package_marker_sha256")
    fields = (
        "source_vintage",
        "period_token",
        "amount_type",
        "unit",
        "vote",
        "department",
        "revenue_type",
        "source_label",
    )
    if (
        value.get("schema_version")
        != "archive-govt-nz.health-revenue-input-total-reconciliation/v1"
        or value.get("scope") != "pinned_canonical_revenue_facts_to_revenue_gold_rows"
        or value.get("period_basis") != "literal_source_token_only"
        or value.get("unit_currency_and_price_basis")
        != "source_context_preserved_currency_unknown"
        or value.get("revenue_netting") != "not_performed"
        or value.get("vintage_pooling") != "not_performed"
        or value.get("donor_control") != "not_performed"
        or value.get("official_source_control") != "not_performed"
        or value.get("cross_source_comparison") != "not_performed"
        or value.get("status") != "exact_canonical_input_totals_reconciled"
        or type(value.get("group_count")) is not int
        or type(value.get("input_record_count")) is not int
        or not isinstance(groups, list)
        or not groups
        or value["input_record_count"] <= 0
        or value["group_count"] != len(groups)
        or not isinstance(pins, list)
        or not pins
        or any(type(pin) is not str or _DIGEST.fullmatch(pin) is None for pin in pins)
        or pins != sorted(set(pins))
    ):
        return False
    all_ids: set[str] = set()
    total_records = 0
    previous_key: tuple[str, ...] | None = None
    for group in groups:
        parsed = _parse_revenue_input_total_group(group, fields)
        if parsed is None:
            return False
        key, record_ids, record_count = parsed
        if previous_key is not None and key <= previous_key:
            return False
        if all_ids.intersection(record_ids):
            return False
        previous_key = key
        all_ids.update(record_ids)
        total_records += record_count
    return total_records == value["input_record_count"] == len(all_ids)


def _parse_revenue_input_total_group(
    group: object, fields: tuple[str, ...]
) -> tuple[tuple[str, ...], list[str], int] | None:
    if not isinstance(group, dict) or any(
        type(group.get(field)) is not str or not group[field] for field in fields
    ):
        return None
    record_ids = group.get("input_record_ids")
    record_count = group.get("input_record_count")
    if (
        group.get("status") != "exact_match"
        or type(record_count) is not int
        or record_count <= 0
        or not isinstance(record_ids, list)
        or len(record_ids) != record_count
        or record_ids != sorted(set(record_ids))
        or any(type(record_id) is not str or not record_id for record_id in record_ids)
    ):
        return None
    try:
        input_total = Decimal(group["canonical_input_total"])
        output_total = Decimal(group["gold_output_total"])
    except InvalidOperation, KeyError, TypeError:
        return None
    if (
        not input_total.is_finite()
        or not output_total.is_finite()
        or input_total != output_total
    ):
        return None
    return tuple(group[field] for field in fields), record_ids, record_count


def _revenue_reconciliation_matches_manifest(
    value: object, package_markers: object, products: object
) -> bool:
    if (
        not _valid_revenue_input_total_reconciliation(value)
        or not isinstance(package_markers, list)
        or any(
            type(marker) is not str or _DIGEST.fullmatch(marker) is None
            for marker in package_markers
        )
        or not isinstance(products, dict)
        or not isinstance(value, dict)
    ):
        return False
    revenue_product = products.get("revenue")
    return (
        isinstance(revenue_product, dict)
        and set(value["source_package_marker_sha256"]).issubset(set(package_markers))
        and revenue_product.get("input_total_reconciliation") == value
    )


def _input_total_controls_match_manifest(
    root: Path, manifest: dict[str, Any], products: object
) -> bool:
    markers = manifest.get("package_marker_sha256")
    if not isinstance(products, dict):
        return False
    for product_name, report_name, output_name, matches_manifest in (
        (
            "budget",
            "budget_input_total_reconciliation_report",
            "budget_input_total_reconciliation.json",
            _budget_reconciliation_matches_manifest,
        ),
        (
            "revenue",
            "revenue_input_total_reconciliation_report",
            "revenue_input_total_reconciliation.json",
            _revenue_reconciliation_matches_manifest,
        ),
    ):
        product = products.get(product_name)
        nested_control = (
            product.get("input_total_reconciliation")
            if isinstance(product, dict)
            else None
        )
        control = manifest.get(report_name)
        output_path = root / output_name
        if control is None and nested_control is None and not output_path.exists():
            continue
        if control is None or nested_control is None or not output_path.is_file():
            return False
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except OSError, UnicodeDecodeError, json.JSONDecodeError:
            return False
        if (
            control != nested_control
            or payload != control
            or not matches_manifest(control, markers, products)
        ):
            return False
    return _pharmac_control_copies_match(
        root, manifest, markers, products
    ) and _moh_control_copies_match(root, manifest, markers, products)


def _moh_control_copies_match(
    root: Path, manifest: dict[str, Any], markers: object, products: object
) -> bool:
    product = products.get("moh") if isinstance(products, dict) else None
    nested = (
        product.get("input_gold_reconciliation") if isinstance(product, dict) else None
    )
    control = manifest.get("moh_input_gold_reconciliation_report")
    path = root / "moh_input_gold_reconciliation.json"
    if nested is None and control is None and not path.exists():
        return True
    if (
        nested is None
        or control is None
        or not path.is_file()
        or not isinstance(markers, list)
    ):
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError, UnicodeDecodeError, json.JSONDecodeError:
        return False
    projection = manifest.get("moh_projection")
    if not isinstance(projection, dict):
        return False
    profiles = projection.get("profiles")
    if not isinstance(profiles, list) or any(
        not isinstance(item, dict) or type(item.get("source_sha256")) is not str
        for item in profiles
    ):
        return False
    return (
        nested == control == payload
        and _valid_moh_input_gold_reconciliation(control)
        and control["source_package_marker_sha256"]
        == sorted(
            item for item in markers if item in control["source_package_marker_sha256"]
        )
        and control["source_object_sha256"]
        == sorted(item["source_sha256"] for item in profiles)
        and control["row_count"] == projection.get("input_records")
    )


def _valid_moh_input_gold_reconciliation(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    markers = value.get("source_package_marker_sha256")
    sources = value.get("source_object_sha256")
    profiles = value.get("profiles")
    if (
        value.get("schema_version")
        != "archive-govt-nz.health-moh-input-gold-reconciliation/v1"
        or value.get("scope") != "pinned_moh_silver_facts_to_gold_rows"
        or value.get("measure_pooling") != "not_performed"
        or value.get("period_alignment") != "literal_source_token_only"
        or value.get("cross_source_comparison") != "not_performed"
        or value.get("rights_state") != "not_evaluated"
        or value.get("status") != "exact_source_rows_preserved"
        or type(value.get("row_count")) is not int
        or value["row_count"] != _MOH_TOTAL_ROWS
        or not isinstance(markers, list)
        or len(markers) != _MOH_PROFILE_COUNT
        or markers != sorted(set(markers))
        or any(
            type(item) is not str or _DIGEST.fullmatch(item) is None for item in markers
        )
        or not isinstance(sources, list)
        or len(sources) != _MOH_PROFILE_COUNT
        or sources != sorted(set(sources))
        or any(
            type(item) is not str or _DIGEST.fullmatch(item) is None for item in sources
        )
        or not isinstance(profiles, list)
        or len(profiles) != _MOH_PROFILE_COUNT
    ):
        return False
    expected = {"fig27/v1", "fig28/v1"}
    observed: set[str] = set()
    total = 0
    for profile in profiles:
        if not isinstance(profile, dict):
            return False
        name = profile.get("profile")
        ids = profile.get("record_ids")
        count = profile.get("row_count")
        if (
            type(name) is not str
            or name not in expected - observed
            or profile.get("status") != "exact_row_match"
            or type(count) is not int
            or count != _MOH_PROFILE_ROWS
            or not isinstance(ids, list)
            or len(ids) != count
            or ids != sorted(set(ids))
            or any(type(item) is not str or not item for item in ids)
        ):
            return False
        observed.add(name)
        total += count
    return observed == expected and total == value["row_count"]


def _pharmac_control_copies_match(
    root: Path, manifest: dict[str, Any], markers: object, products: object
) -> bool:
    product = products.get("pharmac") if isinstance(products, dict) else None
    nested = (
        product.get("input_total_reconciliation") if isinstance(product, dict) else None
    )
    control = manifest.get("pharmac_input_total_reconciliation_report")
    path = root / "pharmac_input_total_reconciliation.json"
    if nested is None and control is None and not path.exists():
        return True
    if nested is None or control is None or not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError, UnicodeDecodeError, json.JSONDecodeError:
        return False
    return (
        nested == control
        and payload == control
        and _pharmac_reconciliation_matches_manifest(
            control, markers, products, manifest.get("pharmac_projection")
        )
    )


def _pharmac_reconciliation_matches_manifest(
    value: object,
    package_markers: object,
    products: object,
    projection: object,
) -> bool:
    if (
        not _valid_pharmac_input_total_reconciliation(value)
        or not isinstance(value, dict)
        or not isinstance(package_markers, list)
        or any(
            type(marker) is not str or _DIGEST.fullmatch(marker) is None
            for marker in package_markers
        )
        or not isinstance(products, dict)
        or not isinstance(projection, dict)
    ):
        return False
    pharmac_product = products.get("pharmac")
    return (
        isinstance(pharmac_product, dict)
        and set(value["source_package_marker_sha256"]).issubset(set(package_markers))
        and value["source_object_sha256"] == projection.get("source_object_sha256")
        and pharmac_product.get("input_total_reconciliation") == value
    )


def _valid_pharmac_input_total_reconciliation(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    groups = value.get("groups")
    pins = value.get("source_package_marker_sha256")
    if (
        value.get("schema_version")
        != "archive-govt-nz.health-pharmac-input-total-reconciliation/v1"
        or value.get("scope") != "pinned_pharmac_silver_facts_to_pharmac_gold_rows"
        or type(value.get("source_object_sha256")) is not str
        or _DIGEST.fullmatch(value["source_object_sha256"]) is None
        or value.get("period_basis") != "literal_source_token_only"
        or value.get("unit_currency_and_price_basis")
        != "source_context_preserved_currency_and_price_basis_unqualified"
        or value.get("published_change_recalculation") != "not_performed"
        or value.get("actual_expenditure") != "not_asserted"
        or value.get("funding_regime_pooling") != "not_performed"
        or value.get("donor_control") != "not_performed"
        or value.get("official_source_control") != "not_performed"
        or value.get("cross_source_comparison") != "not_performed"
        or value.get("status") != "exact_canonical_input_totals_reconciled"
        or type(value.get("group_count")) is not int
        or type(value.get("input_record_count")) is not int
        or not isinstance(groups, list)
        or not groups
        or value["input_record_count"] <= 0
        or value["group_count"] != len(groups)
        or not isinstance(pins, list)
        or len(pins) != 1
        or any(type(pin) is not str or _DIGEST.fullmatch(pin) is None for pin in pins)
    ):
        return False
    all_input_ids: set[str] = set()
    all_gold_ids: set[str] = set()
    total_records = 0
    previous_key: tuple[str, ...] | None = None
    for group in groups:
        parsed = _parse_pharmac_reconciliation_group(group)
        if parsed is None:
            return False
        key, input_ids, gold_ids, count = parsed
        if (
            (previous_key is not None and key <= previous_key)
            or all_input_ids.intersection(input_ids)
            or all_gold_ids.intersection(gold_ids)
        ):
            return False
        previous_key = key
        all_input_ids.update(input_ids)
        all_gold_ids.update(gold_ids)
        total_records += count
    return (
        total_records == value["input_record_count"] == len(all_input_ids)
        and len(all_gold_ids) == value["input_record_count"]
    )


def _parse_pharmac_reconciliation_group(
    group: object,
) -> tuple[tuple[str, ...], list[str], list[str], int] | None:
    fields = (
        "source_vintage",
        "period_token",
        "amount_type",
        "unit",
        "source_label",
        "funding_regime",
    )
    if not isinstance(group, dict) or any(
        type(group.get(field)) is not str or not group[field] for field in fields
    ):
        return None
    input_ids = group.get("input_record_ids")
    gold_ids = group.get("gold_record_ids")
    count = group.get("input_record_count")
    if (
        group.get("status") != "exact_match"
        or type(count) is not int
        or count <= 0
        or not isinstance(input_ids, list)
        or not isinstance(gold_ids, list)
        or len(input_ids) != count
        or len(gold_ids) != count
        or input_ids != sorted(set(input_ids))
        or gold_ids != sorted(set(gold_ids))
        or any(type(item) is not str or not item for item in input_ids + gold_ids)
    ):
        return None
    try:
        input_total = Decimal(group["canonical_input_total"])
        output_total = Decimal(group["gold_output_total"])
    except InvalidOperation, KeyError, TypeError:
        return None
    if (
        not input_total.is_finite()
        or not output_total.is_finite()
        or input_total != output_total
    ):
        return None
    return tuple(group[field] for field in fields), input_ids, gold_ids, count


def _valid_overlap_product_group(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    product = value.get("product")
    row_count = value.get("row_count")
    if (
        type(product) is not str
        or product not in _ALLOWED_OVERLAP_PRODUCTS
        or type(row_count) is not int
        or row_count < 1
    ):
        return False
    for field in ("source_vintages", "units", "input_record_ids"):
        items = value.get(field)
        if not isinstance(items, list) or not items or items != sorted(set(items)):
            return False
        if any(type(item) is not str or not item for item in items):
            return False
    return True


def _valid_overlap_group(value: object, previous_period: str | None) -> bool:
    if not isinstance(value, dict):
        return False
    period = value.get("period_token")
    product_groups = value.get("product_groups")
    if (
        type(period) is not str
        or not period
        or (previous_period is not None and period <= previous_period)
        or value.get("status") != "literal_period_token_overlap_candidate"
        or value.get("comparability") != "not_assessed"
        or value.get("numeric_variance") != "not_computed"
        or not isinstance(product_groups, list)
        or len(product_groups) < _MIN_OVERLAP_PRODUCTS
        or any(not _valid_overlap_product_group(item) for item in product_groups)
    ):
        return False
    names = [item["product"] for item in product_groups]
    return names == sorted(set(names))


def _valid_cross_source_period_overlap(value: object) -> bool:
    required = {
        "schema_version": "archive-govt-nz.health-cross-source-period-overlap/v1",
        "scope": "observed_canonical_product_rows_only",
        "match_basis": "literal_period_token_only",
        "completeness": "observed_rows_only",
        "comparability": "not_assessed",
        "numeric_variance": "not_computed",
        "cross_source_join": "not_performed",
    }
    if not isinstance(value, dict) or any(
        value.get(key) != expected for key, expected in required.items()
    ):
        return False
    groups = value.get("groups")
    count = value.get("overlap_group_count")
    if not isinstance(groups, list) or type(count) is not int or count != len(groups):
        return False
    previous_period: str | None = None
    for group in groups:
        if not _valid_overlap_group(group, previous_period):
            return False
        previous_period = group["period_token"]
    return True


CANONICAL_GOLD_VERIFICATION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        **{key: {"const": value} for key, value in _COMMON.items()},
        "status": {"enum": ["verified", "failed"]},
        "error": {"const": "invalid_canonical_gold_package"},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "output_count": {"type": "integer", "minimum": 0},
        "output_bytes": {"type": "integer", "minimum": 0},
        "products": {"type": "array", "items": {"type": "string"}},
        "temporal_coverage_groups": {"type": "integer", "minimum": 0},
    },
    "required": [*_COMMON, "status"],
    "additionalProperties": False,
    "oneOf": [
        {
            "properties": {"status": {"const": "verified"}},
            "required": [
                "manifest_sha256",
                "output_count",
                "output_bytes",
                "products",
                "temporal_coverage_groups",
            ],
            "not": {"required": ["error"]},
        },
        {
            "properties": {"status": {"const": "failed"}},
            "required": ["error"],
            "maxProperties": len(_COMMON) + 2,
        },
    ],
}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    if len(result) != len(pairs):
        _fail("duplicate_manifest_key")
    return result


def _read_manifest(path: Path) -> tuple[bytes, dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        _fail("invalid_manifest_file")
    with path.open("rb") as stream:
        payload = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(payload) > MAX_MANIFEST_BYTES:
        _fail("manifest_byte_limit")
    value = json.loads(payload, object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        _fail_type("invalid_manifest")
    return payload, value


def _output_name_is_safe(name: object) -> bool:
    return (
        type(name) is str
        and bool(name)
        and name not in {".", "..", "MANIFEST.json", "FAILURE.json"}
        and "/" not in name
        and "\\" not in name
    )


def _verify_outputs(root: Path, outputs: object) -> tuple[int, int]:
    if not isinstance(outputs, dict) or not 0 < len(outputs) <= MAX_OUTPUTS:
        _fail("invalid_outputs")
    if any(not _output_name_is_safe(name) for name in outputs):
        _fail("invalid_output_name")
    if {path.name for path in root.iterdir()} != {*outputs, "MANIFEST.json"}:
        _fail("output_inventory_mismatch")

    total_bytes = 0
    for name, metadata in outputs.items():
        if not isinstance(metadata, dict):
            _fail("invalid_output_metadata")
        digest = metadata.get("sha256")
        size = metadata.get("bytes")
        if (
            type(digest) is not str
            or _DIGEST.fullmatch(digest) is None
            or type(size) is not int
            or not 0 <= size <= MAX_PACKAGE_BYTES
        ):
            _fail("invalid_output_metadata")
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            _fail("output_size_mismatch")
        with path.open("rb") as stream:
            actual_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual_digest != digest:
            _fail("output_digest_mismatch")
        total_bytes += size
        if total_bytes > MAX_PACKAGE_BYTES:
            _fail("package_byte_limit")
    return len(outputs), total_bytes


def read_source_drillthrough(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Resolve complete drillthrough records from a pinned package inventory.

    Legacy inline v2 remains unchanged. A v3 reference admits only the fixed
    direct-child companion, independently checks its snapshot and count, and
    preserves all v2 row, coordinate and numeric-evidence records.
    """
    reference = manifest.get("source_drillthrough", {})
    if not isinstance(reference, dict):
        _fail("invalid_source_drillthrough")
    if (
        reference.get("schema_version")
        != "archive-govt-nz.health-source-drillthrough/v3"
    ):
        return reference
    name = "source_drillthrough.json"
    binding = manifest["outputs"].get(name)
    if (
        not isinstance(binding, dict)
        or reference.get("output_name") != name
        or reference.get("scope") != "complete_v2_records_in_verified_companion"
        or reference.get("sha256") != binding.get("sha256")
        or reference.get("bytes") != binding.get("bytes")
        or type(binding.get("bytes")) is not int
        or not 0 < binding["bytes"] <= MAX_PACKAGE_BYTES
        or type(reference.get("record_count")) is not int
    ):
        _fail("invalid_source_drillthrough_reference")
    payload = verified_snapshot(
        root / name, binding["sha256"], max_bytes=binding["bytes"]
    )
    if len(payload) != binding["bytes"]:
        _fail("invalid_source_drillthrough_size")
    result = json.loads(payload)
    if (
        not isinstance(result, dict)
        or result.get("schema_version")
        != "archive-govt-nz.health-source-drillthrough/v2"
        or not isinstance(result.get("records"), list)
        or len(result["records"]) != reference["record_count"]
        or result.get("scope") != "exact_row_and_source_coordinate_lookup_only"
        or result.get("row_identity") != "output_sha256_and_zero_based_sorted_row_index"
        or result.get("cross_source_join") != "not_performed"
    ):
        _fail("invalid_source_drillthrough_companion")
    return result


def _verify(root: Path, manifest_sha256: str) -> dict[str, Any]:
    if (
        type(manifest_sha256) is not str
        or _DIGEST.fullmatch(manifest_sha256) is None
        or root.is_symlink()
        or not root.is_dir()
    ):
        _fail("invalid_package_root")
    manifest_bytes, manifest = _read_manifest(root / "MANIFEST.json")
    if hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha256:
        _fail("manifest_digest_mismatch")
    if manifest.get("schema_version") != _SCHEMA_VERSION:
        _fail("invalid_manifest_schema")
    outputs = manifest.get("outputs")
    output_count, output_bytes = _verify_outputs(root, outputs)
    read_source_drillthrough(root, manifest)
    products = manifest.get("products")
    temporal_report = manifest.get("temporal_coverage_report")
    classification_report = manifest.get("classification_drift_report")
    revision_report = manifest.get("revision_reconciliation_report")
    overlap_report = manifest.get("cross_source_period_overlap_report")
    try:
        revision_payload = json.loads(
            (root / "historical_revision_reconciliation.json").read_text(
                encoding="utf-8"
            )
        )
    except OSError, UnicodeDecodeError, json.JSONDecodeError:
        revision_payload = None
    try:
        overlap_payload = json.loads(
            (root / "cross_source_period_overlap.json").read_text(encoding="utf-8")
        )
    except OSError, UnicodeDecodeError, json.JSONDecodeError:
        overlap_payload = None
    if (
        not isinstance(products, dict)
        or not isinstance(temporal_report, dict)
        or temporal_report.get("schema_version")
        != "archive-govt-nz.health-temporal-coverage/v1"
        or not isinstance(temporal_report.get("groups"), list)
        or not isinstance(classification_report, dict)
        or classification_report.get("schema_version")
        != "archive-govt-nz.health-classification-drift/v1"
        or classification_report.get("mapping") != "not_inferred"
        or not isinstance(classification_report.get("candidates"), list)
        or not isinstance(revision_report, dict)
        or revision_report.get("schema_version")
        != "archive-govt-nz.health-revision-reconciliation/v1"
        or revision_report.get("key_fields") != list(_REVISION_KEY_FIELDS)
        or revision_report.get("completeness")
        not in {
            "historical_budget_revenue_pharmac_moh_crown_product_rows",
            (
                "historical_budget_revenue_biff8_budget_biff8_revenue_"
                "pharmac_moh_crown_product_rows"
            ),
        }
        or revision_report.get("difference_interpretation") != "not_assessed"
        or revision_report.get("other_product_revisions") != "not_assessed"
        or revision_report.get("cross_source_comparison") != "not_performed"
        or not _valid_product_revision_reports(revision_report.get("product_revisions"))
        or not isinstance(revision_report.get("candidates"), list)
        or revision_payload != revision_report
        or not _valid_cross_source_period_overlap(overlap_report)
        or overlap_payload != overlap_report
        or not _input_total_controls_match_manifest(root, manifest, products)
        or any(type(name) is not str or not name for name in products)
    ):
        _fail("invalid_gold_reports")
    return {
        **_COMMON,
        "status": "verified",
        "manifest_sha256": manifest_sha256,
        "output_count": output_count,
        "output_bytes": output_bytes,
        "products": sorted(products),
        "temporal_coverage_groups": len(temporal_report["groups"]),
    }


def verify_canonical_gold_package(root: Path, manifest_sha256: str) -> dict[str, Any]:
    """Verify a pinned manifest and every declared direct-child output.

    This checks package fixity and basic report presence only. It neither
    rereads Parquet semantics nor establishes source completeness, rights,
    analytical approval, or publication. Failures return a fixed redacted
    receipt and never create or modify local state.
    """
    try:
        return _verify(root, manifest_sha256)
    except Exception:  # noqa: BLE001 - keep paths, bytes and parser errors private
        return {
            **_COMMON,
            "status": "failed",
            "error": "invalid_canonical_gold_package",
        }
