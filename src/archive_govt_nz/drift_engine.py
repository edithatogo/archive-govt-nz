"""Continuous catalogue drift detection and delta evaluation engine."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class CatalogueDriftReport:
    """Reconciled drift and delta between two catalogue snapshots."""

    previous_observed: str
    current_observed: str
    previous_datasets: int
    current_datasets: int
    previous_resources: int
    current_resources: int
    added_dataset_ids: tuple[str, ...]
    removed_dataset_ids: tuple[str, ...]
    modified_dataset_ids: tuple[str, ...]
    added_resource_ids: tuple[str, ...]
    removed_resource_ids: tuple[str, ...]
    license_mutations: tuple[dict[str, str], ...]
    is_stable: bool


def detect_catalogue_drift(
    previous_manifest: dict[str, Any],
    current_manifest: dict[str, Any],
) -> CatalogueDriftReport:
    """Compute exact structural and metadata deltas between two catalogue manifests."""
    prev_observed = str(
        previous_manifest.get("observed_at")
        or previous_manifest.get("generated_at")
        or ""
    )
    curr_observed = str(
        current_manifest.get("observed_at")
        or current_manifest.get("generated_at")
        or ""
    )

    prev_ds_list = previous_manifest.get("datasets", [])
    curr_ds_list = current_manifest.get("datasets", [])

    prev_datasets: dict[str, dict[str, Any]] = {
        str(ds.get("id")): ds
        for ds in prev_ds_list
        if isinstance(ds, dict) and ds.get("id")
    }
    curr_datasets: dict[str, dict[str, Any]] = {
        str(ds.get("id")): ds
        for ds in curr_ds_list
        if isinstance(ds, dict) and ds.get("id")
    }

    prev_ids = set(prev_datasets.keys())
    curr_ids = set(curr_datasets.keys())

    added_ds = sorted(curr_ids - prev_ids)
    removed_ds = sorted(prev_ids - curr_ids)
    common_ds = prev_ids & curr_ids

    modified_ds: list[str] = []
    license_mutations: list[dict[str, str]] = []

    prev_resources: dict[str, dict[str, Any]] = {}
    curr_resources: dict[str, dict[str, Any]] = {}

    for ds_id in common_ds:
        p_ds = prev_datasets[ds_id]
        c_ds = curr_datasets[ds_id]

        p_mod = p_ds.get("metadata_modified")
        c_mod = c_ds.get("metadata_modified")
        p_res = p_ds.get("resources", [])
        c_res = c_ds.get("resources", [])

        if p_mod != c_mod or len(p_res) != len(c_res):
            modified_ds.append(ds_id)

        p_lic = p_ds.get("license_id")
        c_lic = c_ds.get("license_id")
        if p_lic != c_lic:
            license_mutations.append(
                {
                    "dataset_id": ds_id,
                    "previous_license": str(p_lic),
                    "current_license": str(c_lic),
                }
            )

    for ds in prev_datasets.values():
        for r in ds.get("resources", []):
            if isinstance(r, dict) and r.get("id"):
                prev_resources[str(r["id"])] = r

    for ds in curr_datasets.values():
        for r in ds.get("resources", []):
            if isinstance(r, dict) and r.get("id"):
                curr_resources[str(r["id"])] = r

    prev_res_ids = set(prev_resources.keys())
    curr_res_ids = set(curr_resources.keys())

    added_res = sorted(curr_res_ids - prev_res_ids)
    removed_res = sorted(prev_res_ids - curr_res_ids)

    modified_ds.sort()
    is_stable = not (
        added_ds
        or removed_ds
        or modified_ds
        or added_res
        or removed_res
        or license_mutations
    )

    return CatalogueDriftReport(
        previous_observed=prev_observed,
        current_observed=curr_observed,
        previous_datasets=len(prev_datasets),
        current_datasets=len(curr_datasets),
        previous_resources=len(prev_resources),
        current_resources=len(curr_resources),
        added_dataset_ids=tuple(added_ds),
        removed_dataset_ids=tuple(removed_ds),
        modified_dataset_ids=tuple(modified_ds),
        added_resource_ids=tuple(added_res),
        removed_resource_ids=tuple(removed_res),
        license_mutations=tuple(license_mutations),
        is_stable=is_stable,
    )


def serialize_drift_report(report: CatalogueDriftReport) -> dict[str, Any]:
    """Serialize drift report into canonical JSON receipt."""
    return {
        "schema_version": "archive-govt-nz.catalogue-drift/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "is_stable": report.is_stable,
        "summary": {
            "previous_observed": report.previous_observed,
            "current_observed": report.current_observed,
            "previous_dataset_count": report.previous_datasets,
            "current_dataset_count": report.current_datasets,
            "previous_resource_count": report.previous_resources,
            "current_resource_count": report.current_resources,
            "added_datasets_count": len(report.added_dataset_ids),
            "removed_datasets_count": len(report.removed_dataset_ids),
            "modified_datasets_count": len(report.modified_dataset_ids),
            "added_resources_count": len(report.added_resource_ids),
            "removed_resources_count": len(report.removed_resource_ids),
            "license_mutations_count": len(report.license_mutations),
        },
        "deltas": {
            "added_dataset_ids": list(report.added_dataset_ids),
            "removed_dataset_ids": list(report.removed_dataset_ids),
            "modified_dataset_ids": list(report.modified_dataset_ids),
            "added_resource_ids": list(report.added_resource_ids),
            "removed_resource_ids": list(report.removed_resource_ids),
            "license_mutations": list(report.license_mutations),
        },
    }
