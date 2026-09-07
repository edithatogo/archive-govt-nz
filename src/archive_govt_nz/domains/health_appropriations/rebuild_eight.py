"""Opt-in eight-stage raw orchestration; legacy v1 registries stay unchanged."""

# ruff: noqa: SLF001 -- reuse package-internal v1 transports without changing v1.

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations import rebuild as legacy
from archive_govt_nz.domains.health_appropriations.budget_revenue import (
    normalize_budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.crown_receipt import (
    parse_crown_receipt,
    read_crown_receipt,
)
from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_SHA256,
)
from archive_govt_nz.domains.health_appropriations.literal_packages import (
    package_admitted_source,
)
from archive_govt_nz.domains.health_appropriations.verified_coverage import (
    verify_stage_coverage,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    verified_snapshot,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = "archive-govt-nz.health-raw-rebuild/v2"
STAGES = (*legacy.PROFILES, "revenue", "befu-detail", "hyefu-detail", "crown")
EXTRA_FILES = {
    "revenue": "b25-revenue-data.xlsx",
    "befu-detail": "befu25-data-expense-tables.xlsx",
    "hyefu-detail": "hyefu24-data-expense-tables.xlsx",
}
MAX_PLAN_BYTES = 4 * 1024 * 1024


def require(condition: object) -> None:
    """Fail closed at the versioned run boundary."""
    if not condition:
        message = "eight_stage_contract"
        raise ValueError(message)


def plan_eight(  # noqa: PLR0913 -- independently pinned donor and direct-source inputs.
    donor_manifest: Path,
    store: Path,
    pin: str,
    observed_at: str,
    crown_source_sha256: str,
    *,
    crown_receipt: Path,
    crown_receipt_sha256: str,
) -> dict[str, Any]:
    """Pin donor selections separately from the explicit direct Crown object."""
    require(crown_source_sha256 == SOURCE_SHA256)
    payload = verified_snapshot(donor_manifest, pin, max_bytes=MAX_PLAN_BYTES)
    base = legacy.plan_rebuild(donor_manifest, store, pin, observed_at)
    result = {
        "schema_version": SCHEMA,
        "legacy_plan": base,
        "donor_manifest_json": payload.decode("utf-8"),
        "crown_source_sha256": crown_source_sha256,
        "crown_receipt_json": read_crown_receipt(crown_receipt, crown_receipt_sha256),
        "crown_receipt_sha256": crown_receipt_sha256,
    }
    _sources(result, store)
    return result


def _sources(plan: dict[str, Any], store: Path) -> dict[str, dict[str, Any]]:
    require(
        set(plan)
        == {
            "schema_version",
            "legacy_plan",
            "donor_manifest_json",
            "crown_source_sha256",
            "crown_receipt_json",
            "crown_receipt_sha256",
        }
        and plan["schema_version"] == SCHEMA
    )
    base = plan["legacy_plan"]
    payload = plan["donor_manifest_json"].encode("utf-8")
    require(
        len(payload) <= MAX_PLAN_BYTES
        and hashlib.sha256(payload).hexdigest() == base["donor_manifest_sha256"]
    )
    donor = legacy._json(payload)
    require(donor["schema_version"] == "archive-govt-nz.health-donor-manifest/v1")
    paths = legacy._verify_plan(base, store)
    objects = donor["objects"]
    require(len({r["path"] for r in objects}) == len(objects))
    rows = {r["path"]: r for r in objects}
    sources = {}
    cas = ContentAddressedStore(store, create=False)
    require(plan["crown_source_sha256"] == SOURCE_SHA256)
    crown = parse_crown_receipt(
        plan["crown_receipt_json"].encode("utf-8"),
        plan["crown_receipt_sha256"],
        plan["crown_source_sha256"],
    )
    for name in STAGES:
        if name in legacy.PROFILES:
            context = base["sources"][name]
            path = paths[name]
        elif name == "crown":
            require(plan["crown_source_sha256"] == SOURCE_SHA256)
            context = crown
            path = cas.verify(context["object_id"]).path
        else:
            locator = "data/raw/" + EXTRA_FILES[name]
            row = rows[locator]
            context = {
                "sha256": row["sha256"],
                "object_id": row["object_id"],
                "locator": locator,
                "vintage": "Budget-2025"
                if name == "revenue"
                else "BEFU-2025"
                if name == "befu-detail"
                else "HYEFU-2024",
            }
            path = cas.verify(context["object_id"]).path
        if name != "crown":
            row = rows[context["locator"]]
            require(
                row["sha256"] == context["sha256"]
                and row["object_id"] == context["object_id"]
            )
        require(context["object_id"] == "sha256:" + context["sha256"])
        sources[name] = {
            **context,
            "path": path,
            "observed_at": crown["observed_at"]
            if name == "crown"
            else base["observed_at"],
        }
    return sources


def _dispatch(
    name: str, source: dict[str, Any], root: Path, plan: dict[str, Any]
) -> None:
    if name in legacy.PROFILES:
        legacy._extract(name, source["path"], root, plan["legacy_plan"])
    elif name == "revenue":
        normalize_budget_revenue(
            source["path"],
            root / name,
            expected_sha256=source["sha256"],
            source_locator=source["locator"],
            observed_at=source["observed_at"],
        )
    else:
        package_admitted_source(
            source["path"],
            root / name,
            profile=name,
            context={
                "source_object_sha256": source["sha256"],
                "source_locator": source["locator"],
                "source_vintage": source["vintage"],
                "observed_at": source["observed_at"],
            },
        )


def _completion(
    root: Path, plan: dict[str, Any], sources: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    stages, coverage = {}, []
    identities: set[str] = set()
    for name in STAGES:
        if name in legacy.PROFILES:
            legacy._stage_receipt(root, name, plan["legacy_plan"])
        entry = verify_stage_coverage(root / name, name, sources[name])
        current = set(entry["record_ids"])
        require(not current & identities)
        identities.update(current)
        stages[name] = entry["manifest_sha256"]
        coverage.append(entry)
    return {
        "schema_version": SCHEMA,
        "status": "passed",
        "plan_sha256": hashlib.sha256(encode_json(plan).encode()).hexdigest(),
        "stages": stages,
        "coverage": coverage,
        "coverage_scope": "adapter_selections_and_explicit_remainders",
        "rights_state": "not_evaluated",
        "gold_selection": "not_performed",
        "publication": "not_performed",
    }


def verify_eight(root: Path, store: Path, pin: str) -> dict[str, Any]:
    """Verify the pinned completed eight-stage run without producing new files."""
    try:
        result = _verify_eight(root, store, pin)
    except Exception as error:  # noqa: BLE001 -- read-only protocol redaction boundary.
        message = "eight_stage_verification_failed:" + type(error).__name__
        raise ValueError(message) from None
    else:
        return result


def _verify_eight(root: Path, store: Path, pin: str) -> dict[str, Any]:
    """Validate retained state inside the public exception-redaction boundary."""
    require(not root.is_symlink() and legacy._hash(root / "MANIFEST.json") == pin)
    require({p.name for p in root.iterdir()} == {*STAGES, "PLAN.json", "MANIFEST.json"})
    plan = legacy._read(root / "PLAN.json")
    result = _completion(root, plan, _sources(plan, store))
    require(result == legacy._read(root / "MANIFEST.json"))
    require(legacy._hash(root / "MANIFEST.json") == pin)
    return result


def execute_eight(plan: dict[str, Any], store: Path, root: Path) -> dict[str, Any]:
    """Execute explicit stages in a new directory; never resume v1 or partial runs."""
    sources = _sources(plan, store)
    require(
        not root.is_symlink() and not root.resolve().is_relative_to(store.resolve())
    )
    if root.exists():
        require(legacy._read(root / "PLAN.json") == plan)
        return verify_eight(root, store, legacy._hash(root / "MANIFEST.json"))
    root.mkdir(parents=True, exist_ok=False)
    legacy._write(root / "PLAN.json", plan)
    try:
        for name in STAGES:
            _dispatch(name, sources[name], root, plan)
        result = _completion(root, plan, sources)
    except Exception as error:  # noqa: BLE001 -- retain redacted failure receipt
        legacy._write(
            root / "FAILURE.json",
            {
                "schema_version": SCHEMA,
                "status": "failed",
                "error_class": type(error).__name__,
            },
        )
        message = "eight_stage_failed"
        raise ValueError(message) from None
    legacy._write(root / "MANIFEST.json", result)
    return result
