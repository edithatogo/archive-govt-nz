"""Bounded official PCO Act enumeration and explicit missing-format targets."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol
from urllib.parse import urlsplit

from archive_govt_nz.domains.legislation.corpus import (
    ExpressionTarget,
    ManifestationTarget,
    WorkTarget,
)

MAX_PAGE = 100
MAX_VERSION_PAGES = 10
MAX_MANIFESTATIONS = 200
MIN_YEAR = 1200
LATEST_YEAR = 2008

FORMATS = {
    "xml": "application/xml",
    "html": "text/html",
    "pdf": "application/pdf",
    "pdf_original_scan": "application/pdf",
}
WORK = re.compile(
    r"act_(?:public|private|local|imperial|provincial)_[0-9]{4}_[A-Za-z0-9~-]+"
)


class Catalogue(Protocol):
    """The qualified official API transport, never a generic URL fetcher."""

    def get_catalogue_page(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """Read one bounded page."""
        ...


@dataclass(frozen=True)
class Bounds:
    """A finite independently resumable historical packet."""

    start_page: int = 1
    page_size: int = 100
    max_works: int = 5
    version_pages: int = 10
    max_manifestations: int = 200
    before_year: int = 1901

    def validate(self) -> None:
        """Reject unbounded or internally inconsistent invocation inputs."""
        if not (
            self.start_page >= 1
            and 1 <= self.page_size <= MAX_PAGE
            and 1 <= self.max_works <= self.page_size
            and 1 <= self.version_pages <= MAX_VERSION_PAGES
            and 1 <= self.max_manifestations <= MAX_MANIFESTATIONS
            and MIN_YEAR <= self.before_year <= LATEST_YEAR
        ):
            message = "invalid historical packet bounds"
            raise ValueError(message)


def encoded(value: object) -> bytes:
    """Encode source inventories deterministically."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def page_results(
    payload: dict[str, Any], page: int, size: int
) -> tuple[list[dict[str, Any]], bool]:
    """Require exact accounting rather than infer completeness from a short page."""
    rows = payload.get("results")
    total = payload.get("total")
    if (
        not isinstance(rows, list)
        or not all(isinstance(row, dict) for row in rows)
        or type(total) is not int
        or total < 0
        or payload.get("page") != page
        or payload.get("per_page") != size
        or len(rows) != min(size, max(0, total - (page - 1) * size))
    ):
        message = "historical catalogue page contract mismatch"
        raise ValueError(message)
    return rows, page * size >= total


def official_url(url: str) -> str:
    """Limit new redistribution to official primary Acts, not agency documents."""
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname not in {"www.legislation.govt.nz", "legislation.govt.nz"}
        or parts.username
        or parts.password
        or parts.port not in {None, 443}
        or parts.query
        or parts.fragment
        or not parts.path.startswith("/act/")
        or "/latest" in parts.path
        or not url.isprintable()
    ):
        message = "unqualified historical manifestation URL"
        raise ValueError(message)
    return url


def versions(
    client: Catalogue, work_id: str, bounds: Bounds
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Traverse every page or stop without claiming a complete work."""
    rows: dict[str, dict[str, Any]] = {}
    receipts = []
    for page in range(1, bounds.version_pages + 1):
        payload = client.get_catalogue_page(
            f"works/{work_id}/versions/", {"page": page, "per_page": 100, "sort": "asc"}
        )
        items, exhausted = page_results(payload, page, 100)
        receipts.append(
            {
                "page": page,
                "canonical_sha256": hashlib.sha256(encoded(payload)).hexdigest(),
                "total": payload["total"],
            }
        )
        for item in items:
            identifier = item.get("version_id", "")
            if (
                not isinstance(identifier, str)
                or not identifier.startswith(work_id + "_en_")
                or identifier in rows
                or item.get("work_id", work_id) != work_id
            ):
                message = "duplicate or mismatched historical version"
                raise ValueError(message)
            rows[identifier] = item
        if exhausted:
            return list(rows.values()), receipts
    message = "historical version bound exhausted; work not admitted"
    raise ValueError(message)


def dated_url(identifier: str, url: str) -> str:
    """Pin an API-advertised latest alias to its explicit expression date."""
    work, separator, stamp = identifier.partition("_en_")
    parts = urlsplit(url)
    if (
        not separator
        or not WORK.fullmatch(work)
        or date.fromisoformat(stamp).isoformat() != stamp
        or not parts.path.startswith("/" + work.replace("_", "/") + "/en/")
    ):
        message = "historical format does not match its expression identity"
        raise ValueError(message)
    path = re.sub(r"/latest(?=[/.]|$)", "/" + stamp, parts.path, count=1)
    return official_url(parts._replace(path=path).geturl())


def missing_expressions(
    graph: list[dict[str, Any]], prior: set[str]
) -> tuple[list[ExpressionTarget], int]:
    """Retain every explicitly offered encoding, with no fallback substitution."""
    expressions = []
    offered = 0
    for version in graph:
        manifestations = []
        formats = version.get("formats")
        if not isinstance(formats, list) or not formats:
            message = "historical version lacks an explicit format inventory"
            raise ValueError(message)
        for fmt in formats:
            if not isinstance(fmt, dict) or fmt.get("type") not in FORMATS:
                message = "unsupported historical format"
                raise ValueError(message)
            url = dated_url(version["version_id"], str(fmt.get("url", "")))
            offered += 1
            if url not in prior:
                manifestations.append(
                    ManifestationTarget(url, FORMATS[fmt["type"]], url)
                )
        if manifestations:
            identifier = version["version_id"]
            expressions.append(
                ExpressionTarget(
                    expression_id=identifier,
                    version_date=identifier.split("_en_", 1)[1][:10],
                    manifestations=manifestations,
                )
            )
    return expressions, offered


def missing_targets(
    client: Catalogue, parent: dict[str, Any], bounds: Bounds
) -> tuple[list[WorkTarget], dict[str, Any]]:
    """Enumerate an explicit oldest-first page, then complete selected work graphs."""
    bounds.validate()
    params = {
        "legislation_type": "act",
        "publisher": "Parliamentary Counsel Office",
        "sort_by": "year_asc",
        "page": bounds.start_page,
        "per_page": bounds.page_size,
    }
    payload = client.get_catalogue_page("works/", params)
    candidates, exhausted = page_results(payload, bounds.start_page, bounds.page_size)
    ids = [item.get("work_id", "") for item in candidates]
    if any(
        not isinstance(work, str) or not WORK.fullmatch(work) for work in ids
    ) or len(ids) != len(set(ids)):
        message = "invalid or duplicate historical work identity"
        raise ValueError(message)
    prior = {str(row["manifestation_id"]) for row in parent["records"]}
    prior_works = set(parent["discovered_work_ids"])
    historical = [
        item
        for item in candidates
        if int(item["work_id"].split("_")[2]) < bounds.before_year
    ]
    # Fill missing works before augmenting an already preserved work.
    historical.sort(
        key=lambda item: (item["work_id"] in prior_works, ids.index(item["work_id"]))
    )
    targets = []
    selected = []
    count = 0
    accounted = set()
    for item in historical:
        if len(targets) >= bounds.max_works:
            break
        work_id = item["work_id"]
        graph, pages = versions(client, work_id, bounds)
        expressions, offered = missing_expressions(graph, prior)
        count += sum(len(expression.manifestations) for expression in expressions)
        if count > bounds.max_manifestations:
            message = "historical manifestation budget exceeded"
            raise ValueError(message)
        accounted.add(work_id)
        if expressions:
            title = str(
                graph[0].get("title")
                or item.get("latest_matching_version", {}).get("title")
                or work_id
            )
            targets.append(
                WorkTarget(
                    work_id=work_id,
                    title=title,
                    expression_targets=expressions,
                )
            )
            selected.append(
                {
                    "work_id": work_id,
                    "versions_listed": len(graph),
                    "formats_offered": offered,
                    "missing_formats": sum(len(e.manifestations) for e in expressions),
                    "version_pages": pages,
                    "versions": graph,
                    "url_projections": [
                        {
                            "version_id": version["version_id"],
                            "advertised_url": fmt["url"],
                            "dated_url": dated_url(version["version_id"], fmt["url"]),
                        }
                        for version in graph
                        for fmt in version["formats"]
                        if "/latest" in fmt["url"]
                    ],
                }
            )
    return targets, {
        "schema_version": "archive-govt-nz.historical-packet-inventory/v1",
        "query": params,
        "source_total": payload["total"],
        "work_ids": ids,
        "source_page_canonical_sha256": hashlib.sha256(encoded(payload)).hexdigest(),
        "next_page": None if exhausted else bounds.start_page + 1,
        "selected": selected,
        "pending_work_ids": [
            item["work_id"] for item in historical if item["work_id"] not in accounted
        ],
        "capture_resume_page": bounds.start_page
        if len(accounted) < len(historical)
        else (None if exhausted else bounds.start_page + 1),
        "missing_manifestations": count,
        "source_completeness_claim": False,
    }
