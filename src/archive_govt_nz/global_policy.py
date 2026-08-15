"""Automated rights and resource policy evaluation for global CKAN catalogues."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

_OPEN_LICENSE_PREFIXES = (
    "cc-by",
    "cc0",
    "cc-zero",
    "nzgoal",
    "odc-pddl",
    "odc-by",
    "other-pd",
    "other-open",
    "uk-ogl",
    "mit",
    "apache",
    "bsd",
)

_OPEN_TITLE_KEYWORDS = (
    "creative commons attribution",
    "cc-by",
    "cc0",
    "public domain",
    "open access licensing",
    "nzgoal",
    "open government licence",
)

_CLOSED_KEYWORDS = (
    "all rights reserved",
    "closed",
    "restricted",
    "proprietary",
    "commercial",
    "confidential",
    "notspecified",
)


class GlobalResourceClassification(StrEnum):
    """Disposition outcomes for global resources."""

    ELIGIBLE = "eligible"
    RIGHTS_RESTRICTED = "rights_restricted"
    UNKNOWN_RIGHTS = "unknown_rights"
    UNSAFE_SCHEME = "unsafe_scheme"
    OVERSIZED = "oversized"
    DATASTORE_ONLY = "datastore_only"


@dataclass(frozen=True, slots=True)
class GlobalResourcePolicyDecision:
    """Policy decision for one resource."""

    dataset_id: str
    resource_id: str
    disposition: GlobalResourceClassification
    reason: str
    download_authorized: bool
    url: str
    format: str | None
    size: int | None
    datastore_active: bool


def is_open_license(license_id: str | None, license_title: str | None = None) -> bool:
    """Return True if the license string matches an open / reusable data policy."""
    lic_id = (license_id or "").strip().lower()
    lic_title = (license_title or "").strip().lower()

    if not lic_id and not lic_title:
        return False

    for closed_term in _CLOSED_KEYWORDS:
        if closed_term in lic_id or closed_term in lic_title:
            return False

    for prefix in _OPEN_LICENSE_PREFIXES:
        if lic_id.startswith(prefix) or prefix in lic_id:
            return True

    return any(keyword in lic_title for keyword in _OPEN_TITLE_KEYWORDS)


def classify_dataset_resource(
    dataset: dict[str, Any],
    resource: dict[str, Any],
    max_bytes: int = 512 * 1024 * 1024,
) -> GlobalResourcePolicyDecision:
    """Evaluate one resource against rights, size, and URL security policies."""
    dataset_id = str(dataset.get("id") or "")
    resource_id = str(resource.get("id") or "")
    url = str(resource.get("url") or "")
    fmt = resource.get("format")
    size = resource.get("size")
    ds_active = bool(resource.get("datastore_active", False))

    effective_license_id = resource.get("license_id") or dataset.get("license_id")
    effective_license_title = dataset.get("license_title")

    # 1. Scheme Check
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return GlobalResourcePolicyDecision(
            dataset_id=dataset_id,
            resource_id=resource_id,
            disposition=GlobalResourceClassification.UNSAFE_SCHEME,
            reason="url_scheme_is_not_https",
            download_authorized=False,
            url=url,
            format=fmt,
            size=size,
            datastore_active=ds_active,
        )

    # 2. Rights Check
    if not effective_license_id and not effective_license_title:
        return GlobalResourcePolicyDecision(
            dataset_id=dataset_id,
            resource_id=resource_id,
            disposition=GlobalResourceClassification.UNKNOWN_RIGHTS,
            reason="no_license_metadata_declared",
            download_authorized=False,
            url=url,
            format=fmt,
            size=size,
            datastore_active=ds_active,
        )

    if not is_open_license(effective_license_id, effective_license_title):
        return GlobalResourcePolicyDecision(
            dataset_id=dataset_id,
            resource_id=resource_id,
            disposition=GlobalResourceClassification.RIGHTS_RESTRICTED,
            reason="license_is_closed_or_unrecognized",
            download_authorized=False,
            url=url,
            format=fmt,
            size=size,
            datastore_active=ds_active,
        )

    # 3. Size Check
    if isinstance(size, int) and size > max_bytes:
        return GlobalResourcePolicyDecision(
            dataset_id=dataset_id,
            resource_id=resource_id,
            disposition=GlobalResourceClassification.OVERSIZED,
            reason="declared_size_exceeds_budget",
            download_authorized=False,
            url=url,
            format=fmt,
            size=size,
            datastore_active=ds_active,
        )

    # 4. Eligible
    return GlobalResourcePolicyDecision(
        dataset_id=dataset_id,
        resource_id=resource_id,
        disposition=GlobalResourceClassification.ELIGIBLE,
        reason="open_license_https_within_budget",
        download_authorized=True,
        url=url,
        format=fmt,
        size=size,
        datastore_active=ds_active,
    )


def classify_global_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Classify all resources in a discovered global CKAN manifest."""
    datasets = manifest.get("datasets", [])
    records: list[dict[str, Any]] = []
    counts: dict[str, int] = {}

    for ds in datasets:
        if not isinstance(ds, dict):
            continue
        resources = ds.get("resources", [])
        for res in resources:
            if not isinstance(res, dict):
                continue
            decision = classify_dataset_resource(ds, res)
            disp_str = decision.disposition.value
            counts[disp_str] = counts.get(disp_str, 0) + 1
            records.append(
                {
                    "dataset_id": decision.dataset_id,
                    "resource_id": decision.resource_id,
                    "url": decision.url,
                    "format": decision.format,
                    "size": decision.size,
                    "classification": disp_str,
                    "reason": decision.reason,
                    "download_authorized": decision.download_authorized,
                    "datastore_active": decision.datastore_active,
                }
            )

    return {
        "schema_version": "archive-govt-nz.global-rights-classification/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_resources_evaluated": len(records),
        "counts": counts,
        "records": records,
    }
