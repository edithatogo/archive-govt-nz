"""Drift-aware, evidence-preserving global CKAN catalogue discovery."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from datetime import datetime

    from archive_govt_nz.ckan.client import ActionObservation
    from archive_govt_nz.ckan.envelope import JsonObject

_ERROR_COUNT_RECONCILIATION = "count_reconciliation"
_ERROR_DATASET_ORDER = "dataset_order"
_ERROR_DUPLICATE_DATASET_ID = "duplicate_dataset_id"
_ERROR_MISSING_DATASET_ID = "missing_dataset_id"
_ERROR_PAGE_SIZE = "page_size"
_ERROR_SEARCH_PROTOCOL = "search_protocol"
_GLOBAL_SCOPE_SCHEMA_VERSION = "archive-govt-nz.global-ckan-scope/v1"


class GlobalCkanDiscoveryError(Exception):
    """A bounded discovery failure during global catalogue crawling."""

    def __init__(self, error_class: str) -> None:
        """Initialize error with stable error class."""
        self.error_class = error_class
        super().__init__(f"Global CKAN discovery failed: {error_class}")


class ActionClient(Protocol):
    """The narrow Action transport required by global discovery."""

    async def action(
        self,
        action: str,
        params: dict[str, object] | None = None,
    ) -> ActionObservation:
        """Return one bounded Action observation."""
        ...


@dataclass(frozen=True, slots=True)
class GlobalResourceReference:
    """Minimal stable resource identity and transport metadata."""

    id: str
    name: str | None
    url: str
    format: str | None
    size: int | None
    license_id: str | None
    created: str | None
    last_modified: str | None
    datastore_active: bool


@dataclass(frozen=True, slots=True)
class GlobalDatasetReference:
    """Minimal stable dataset identity retained in the global scope."""

    id: str
    name: str | None
    title: str | None
    organization_name: str | None
    organization_title: str | None
    license_id: str | None
    license_title: str | None
    metadata_created: str | None
    metadata_modified: str | None
    resources: tuple[GlobalResourceReference, ...]


@dataclass(frozen=True, slots=True)
class GlobalDiscoveryPage:
    """One exact package-search page and bounded reconciliation metadata."""

    start: int
    reported_count: int
    dataset_ids: tuple[str, ...]
    raw_body: bytes
    raw_sha256: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class GlobalCkanScope:
    """A reconciled global CKAN catalogue dataset and resource scope."""

    datasets: tuple[GlobalDatasetReference, ...]
    pages: tuple[GlobalDiscoveryPage, ...]

    @property
    def dataset_ids(self) -> tuple[str, ...]:
        """Return stable dataset identifiers in observed API sort order."""
        return tuple(dataset.id for dataset in self.datasets)

    @property
    def reported_counts(self) -> tuple[int, ...]:
        """Return every live count reported during pagination."""
        return tuple(page.reported_count for page in self.pages)

    @property
    def discovered_dataset_count(self) -> int:
        """Return the reconciled unique dataset count."""
        return len(self.datasets)

    @property
    def discovered_resource_count(self) -> int:
        """Return the reconciled unique resource count across all datasets."""
        return sum(len(dataset.resources) for dataset in self.datasets)


class GlobalCkanDiscovery:
    """Resolve and enumerate the complete live CKAN catalogue scope."""

    def __init__(self, client: ActionClient, *, page_size: int = 100) -> None:
        """Initialize global discovery client with deterministic page size."""
        if page_size < 1:
            raise GlobalCkanDiscoveryError(_ERROR_PAGE_SIZE)
        self._client = client
        self._page_size = page_size

    async def discover(self) -> GlobalCkanScope:
        """Enumerate and reconcile all datasets across the entire CKAN catalogue."""
        datasets: list[GlobalDatasetReference] = []
        pages: list[GlobalDiscoveryPage] = []
        seen_ids: set[str] = set()
        previous_id: str | None = None
        start = 0

        while True:
            page_action = await self._client.action(
                "package_search",
                {
                    "q": "*:*",
                    "rows": self._page_size,
                    "sort": "id asc",
                    "start": start,
                },
            )
            reported_count, results = self._parse_search_result(page_action)
            page_ids: list[str] = []
            for result in results:
                dataset = self._parse_dataset(result)
                if dataset.id in seen_ids:
                    raise GlobalCkanDiscoveryError(_ERROR_DUPLICATE_DATASET_ID)
                if previous_id is not None and dataset.id <= previous_id:
                    raise GlobalCkanDiscoveryError(_ERROR_DATASET_ORDER)
                seen_ids.add(dataset.id)
                previous_id = dataset.id
                datasets.append(dataset)
                page_ids.append(dataset.id)

            pages.append(
                GlobalDiscoveryPage(
                    start=start,
                    reported_count=reported_count,
                    dataset_ids=tuple(page_ids),
                    raw_body=page_action.raw_body,
                    raw_sha256=page_action.raw_sha256,
                    observed_at=page_action.observed_at,
                )
            )

            discovered_count = len(datasets)
            if discovered_count > reported_count:
                raise GlobalCkanDiscoveryError(_ERROR_COUNT_RECONCILIATION)
            if discovered_count == reported_count:
                break
            if not results:
                raise GlobalCkanDiscoveryError(_ERROR_COUNT_RECONCILIATION)
            start += len(results)

        return GlobalCkanScope(
            datasets=tuple(datasets),
            pages=tuple(pages),
        )

    @staticmethod
    def _parse_search_result(
        observation: ActionObservation,
    ) -> tuple[int, list[JsonObject]]:
        result = observation.response.result
        count = result.get("count")
        raw_results = result.get("results")
        if (
            not isinstance(count, int)
            or isinstance(count, bool)
            or count < 0
            or not isinstance(raw_results, list)
        ):
            raise GlobalCkanDiscoveryError(_ERROR_SEARCH_PROTOCOL)
        items = cast("list[object]", raw_results)
        if not all(isinstance(item, dict) for item in items):
            raise GlobalCkanDiscoveryError(_ERROR_SEARCH_PROTOCOL)
        return count, cast("list[JsonObject]", raw_results)

    @staticmethod
    def _parse_dataset(result: JsonObject) -> GlobalDatasetReference:
        identifier = result.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise GlobalCkanDiscoveryError(_ERROR_MISSING_DATASET_ID)

        raw_name = result.get("name")
        name = raw_name if isinstance(raw_name, str) else None

        raw_title = result.get("title")
        title = raw_title if isinstance(raw_title, str) else None

        raw_created = result.get("metadata_created")
        created = raw_created if isinstance(raw_created, str) else None

        raw_modified = result.get("metadata_modified")
        modified = raw_modified if isinstance(raw_modified, str) else None

        raw_lic_id = result.get("license_id")
        license_id = raw_lic_id if isinstance(raw_lic_id, str) else None

        raw_lic_title = result.get("license_title")
        license_title = raw_lic_title if isinstance(raw_lic_title, str) else None

        org_dict = result.get("organization")
        org_name: str | None = None
        org_title: str | None = None
        if isinstance(org_dict, dict):
            raw_org_name = org_dict.get("name")
            org_name = raw_org_name if isinstance(raw_org_name, str) else None
            raw_org_title = org_dict.get("title")
            org_title = raw_org_title if isinstance(raw_org_title, str) else None

        raw_resources = result.get("resources")
        resources: list[GlobalResourceReference] = []
        if isinstance(raw_resources, list):
            for res in raw_resources:
                if not isinstance(res, dict):
                    continue
                res_id = res.get("id")
                res_url = res.get("url")
                if isinstance(res_id, str) and isinstance(res_url, str):
                    res_name = (
                        res.get("name") if isinstance(res.get("name"), str) else None
                    )
                    res_format = (
                        res.get("format")
                        if isinstance(res.get("format"), str)
                        else None
                    )
                    res_size = (
                        res.get("size") if isinstance(res.get("size"), int) else None
                    )
                    res_lic = (
                        res.get("license_id")
                        if isinstance(res.get("license_id"), str)
                        else None
                    )
                    res_created = (
                        res.get("created")
                        if isinstance(res.get("created"), str)
                        else None
                    )
                    res_modified = (
                        res.get("last_modified")
                        if isinstance(res.get("last_modified"), str)
                        else None
                    )
                    ds_active = bool(res.get("datastore_active", False))
                    resources.append(
                        GlobalResourceReference(
                            id=res_id,
                            name=res_name,
                            url=res_url,
                            format=res_format,
                            size=res_size,
                            license_id=res_lic,
                            created=res_created,
                            last_modified=res_modified,
                            datastore_active=ds_active,
                        )
                    )

        return GlobalDatasetReference(
            id=identifier,
            name=name,
            title=title,
            organization_name=org_name,
            organization_title=org_title,
            license_id=license_id,
            license_title=license_title,
            metadata_created=created,
            metadata_modified=modified,
            resources=tuple(resources),
        )


def _timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def global_scope_manifest(scope: GlobalCkanScope) -> dict[str, object]:
    """Build a deterministic manifest referencing exact raw catalogue evidence."""
    observed_time = (
        _timestamp(scope.pages[-1].observed_at)
        if scope.pages
        else "1970-01-01T00:00:00Z"
    )
    return {
        "schema_version": _GLOBAL_SCOPE_SCHEMA_VERSION,
        "observed_at": observed_time,
        "discovered_dataset_count": scope.discovered_dataset_count,
        "discovered_resource_count": scope.discovered_resource_count,
        "reported_counts": list(scope.reported_counts),
        "dataset_ids": list(scope.dataset_ids),
        "datasets": [
            {
                "id": ds.id,
                "name": ds.name,
                "title": ds.title,
                "organization_name": ds.organization_name,
                "organization_title": ds.organization_title,
                "license_id": ds.license_id,
                "license_title": ds.license_title,
                "metadata_created": ds.metadata_created,
                "metadata_modified": ds.metadata_modified,
                "resources": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "url": r.url,
                        "format": r.format,
                        "size": r.size,
                        "license_id": r.license_id,
                        "created": r.created,
                        "last_modified": r.last_modified,
                        "datastore_active": r.datastore_active,
                    }
                    for r in ds.resources
                ],
            }
            for ds in scope.datasets
        ],
        "pages": [
            {
                "start": page.start,
                "reported_count": page.reported_count,
                "dataset_ids": list(page.dataset_ids),
                "observed_at": _timestamp(page.observed_at),
                "raw_sha256": page.raw_sha256,
            }
            for page in scope.pages
        ],
    }


def global_scope_report_markdown(scope: GlobalCkanScope) -> bytes:
    """Render a concise human-readable companion to the JSON manifest."""
    observed_time = (
        _timestamp(scope.pages[-1].observed_at)
        if scope.pages
        else "1970-01-01T00:00:00Z"
    )
    counts = ", ".join(str(count) for count in scope.reported_counts)
    lines = [
        "# Global CKAN discovery scope",
        "",
        "Status: locally reconciled global catalogue scope",
        "",
        f"- Observed at: {observed_time}",
        f"- Discovered datasets: {scope.discovered_dataset_count}",
        f"- Discovered resources: {scope.discovered_resource_count}",
        f"- Live counts observed: {counts}",
        f"- Search pages: {len(scope.pages)}",
        "",
        "## Page evidence summary",
        "",
        "| Start | Reported count | Datasets | Raw SHA-256 |",
        "| ---: | ---: | ---: | --- |",
    ]
    lines.extend(
        (
            f"| {page.start} | {page.reported_count} | "
            f"{len(page.dataset_ids)} | `{page.raw_sha256}` |"
        )
        for page in scope.pages
    )
    lines.extend(
        [
            "",
            (
                "This report describes metadata discovery only. It does not claim "
                "resource capture or publication."
            ),
            "",
        ]
    )
    return "\n".join(lines).encode()


def canonical_global_scope_manifest(scope: GlobalCkanScope) -> bytes:
    """Serialize the scope manifest as canonical newline-terminated UTF-8 JSON."""
    document = global_scope_manifest(scope)
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()
