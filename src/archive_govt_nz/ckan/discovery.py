"""Drift-aware, evidence-preserving Treasury dataset discovery."""

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
_ERROR_ORGANIZATION_MISMATCH = "organization_mismatch"
_ERROR_ORGANIZATION_PROTOCOL = "organization_protocol"
_ERROR_PAGE_SIZE = "page_size"
_ERROR_SEARCH_PROTOCOL = "search_protocol"
_TREASURY_SLUG = "the-treasury"
_SCOPE_SCHEMA_VERSION = "archive-govt-nz.treasury-scope/v1"


class TreasuryDiscoveryError(Exception):
    """A bounded discovery failure that excludes source payload detail."""

    def __init__(self, error_class: str) -> None:
        """Create a stable diagnostic class."""
        self.error_class = error_class
        super().__init__(f"Treasury discovery failed: {error_class}")


class ActionClient(Protocol):
    """The narrow Action transport required by discovery."""

    async def action(
        self,
        action: str,
        params: dict[str, object] | None = None,
    ) -> ActionObservation:
        """Return one bounded Action observation."""
        ...


@dataclass(frozen=True, slots=True)
class OrganizationObservation:
    """Resolved Treasury identity with its exact source observation."""

    id: str
    name: str
    title: str
    raw_body: bytes
    raw_sha256: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class DatasetReference:
    """Minimal stable dataset identity retained in the scope."""

    id: str
    name: str | None
    metadata_modified: str | None


@dataclass(frozen=True, slots=True)
class DiscoveryPage:
    """One exact package-search page and bounded reconciliation metadata."""

    start: int
    reported_count: int
    dataset_ids: tuple[str, ...]
    raw_body: bytes
    raw_sha256: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class TreasuryScope:
    """A reconciled Treasury organisation-filtered dataset scope."""

    organization: OrganizationObservation
    datasets: tuple[DatasetReference, ...]
    pages: tuple[DiscoveryPage, ...]

    @property
    def dataset_ids(self) -> tuple[str, ...]:
        """Return stable dataset identifiers in observed API sort order."""
        return tuple(dataset.id for dataset in self.datasets)

    @property
    def reported_counts(self) -> tuple[int, ...]:
        """Return every live count reported during pagination."""
        return tuple(page.reported_count for page in self.pages)

    @property
    def discovered_count(self) -> int:
        """Return the reconciled unique dataset count."""
        return len(self.datasets)


class TreasuryDiscovery:
    """Resolve and enumerate the complete live Treasury CKAN scope."""

    def __init__(self, client: ActionClient, *, page_size: int = 100) -> None:
        """Configure a positive deterministic page size."""
        if page_size < 1:
            raise TreasuryDiscoveryError(_ERROR_PAGE_SIZE)
        self._client = client
        self._page_size = page_size

    async def discover(self) -> TreasuryScope:
        """Resolve Treasury and reconcile all organisation-filtered datasets."""
        organization_action = await self._client.action(
            "organization_show",
            {"id": _TREASURY_SLUG},
        )
        organization = self._parse_organization(organization_action)
        datasets: list[DatasetReference] = []
        pages: list[DiscoveryPage] = []
        seen_ids: set[str] = set()
        previous_id: str | None = None
        start = 0

        while True:
            page_action = await self._client.action(
                "package_search",
                {
                    "fq": f"organization:{organization.name}",
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
                    raise TreasuryDiscoveryError(_ERROR_DUPLICATE_DATASET_ID)
                if previous_id is not None and dataset.id <= previous_id:
                    raise TreasuryDiscoveryError(_ERROR_DATASET_ORDER)
                seen_ids.add(dataset.id)
                previous_id = dataset.id
                datasets.append(dataset)
                page_ids.append(dataset.id)

            pages.append(
                DiscoveryPage(
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
                raise TreasuryDiscoveryError(_ERROR_COUNT_RECONCILIATION)
            if discovered_count == reported_count:
                break
            if not results:
                raise TreasuryDiscoveryError(_ERROR_COUNT_RECONCILIATION)
            start += len(results)

        return TreasuryScope(
            organization=organization,
            datasets=tuple(datasets),
            pages=tuple(pages),
        )

    @staticmethod
    def _parse_organization(
        observation: ActionObservation,
    ) -> OrganizationObservation:
        result = observation.response.result
        identifier = result.get("id")
        name = result.get("name")
        title = result.get("title")
        if (
            not isinstance(identifier, str)
            or not identifier
            or not isinstance(name, str)
            or not isinstance(title, str)
        ):
            raise TreasuryDiscoveryError(_ERROR_ORGANIZATION_PROTOCOL)
        if name != _TREASURY_SLUG:
            raise TreasuryDiscoveryError(_ERROR_ORGANIZATION_MISMATCH)
        return OrganizationObservation(
            id=identifier,
            name=name,
            title=title,
            raw_body=observation.raw_body,
            raw_sha256=observation.raw_sha256,
            observed_at=observation.observed_at,
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
            raise TreasuryDiscoveryError(_ERROR_SEARCH_PROTOCOL)
        items = cast("list[object]", raw_results)
        if not all(isinstance(item, dict) for item in items):
            raise TreasuryDiscoveryError(_ERROR_SEARCH_PROTOCOL)
        return count, cast("list[JsonObject]", raw_results)

    @staticmethod
    def _parse_dataset(result: JsonObject) -> DatasetReference:
        identifier = result.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise TreasuryDiscoveryError(_ERROR_MISSING_DATASET_ID)
        name_value = result.get("name")
        modified_value = result.get("metadata_modified")
        name = name_value if isinstance(name_value, str) else None
        metadata_modified = (
            modified_value if isinstance(modified_value, str) else None
        )
        return DatasetReference(
            id=identifier,
            name=name,
            metadata_modified=metadata_modified,
        )


def _timestamp(value: datetime) -> str:
    """Serialize an aware timestamp with the conventional UTC Z suffix."""
    return value.isoformat().replace("+00:00", "Z")


def scope_manifest(scope: TreasuryScope) -> dict[str, object]:
    """Build a compact deterministic manifest referencing exact raw evidence."""
    return {
        "schema_version": _SCOPE_SCHEMA_VERSION,
        "observed_at": _timestamp(scope.pages[-1].observed_at),
        "organization": {
            "id": scope.organization.id,
            "name": scope.organization.name,
            "title": scope.organization.title,
            "observed_at": _timestamp(scope.organization.observed_at),
            "raw_sha256": scope.organization.raw_sha256,
        },
        "discovered_count": scope.discovered_count,
        "reported_counts": list(scope.reported_counts),
        "dataset_ids": list(scope.dataset_ids),
        "datasets": [
            {
                "id": dataset.id,
                "name": dataset.name,
                "metadata_modified": dataset.metadata_modified,
            }
            for dataset in scope.datasets
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


def scope_report_markdown(scope: TreasuryScope) -> bytes:
    """Render a concise human-readable companion to the JSON manifest."""
    counts = ", ".join(str(count) for count in scope.reported_counts)
    lines = [
        "# Treasury discovery scope",
        "",
        "Status: locally reconciled metadata scope",
        "",
        f"- Observed at: {_timestamp(scope.pages[-1].observed_at)}",
        (
            f"- Organization: {scope.organization.title} "
            f"(`{scope.organization.name}`, `{scope.organization.id}`)"
        ),
        f"- Discovered datasets: {scope.discovered_count}",
        f"- Live counts observed: {counts}",
        f"- Search pages: {len(scope.pages)}",
        "",
        "## Page evidence",
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


def canonical_scope_manifest(scope: TreasuryScope) -> bytes:
    """Serialize the scope manifest as canonical newline-terminated UTF-8 JSON."""
    document = scope_manifest(scope)
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()
