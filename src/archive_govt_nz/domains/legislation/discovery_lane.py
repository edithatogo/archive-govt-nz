"""Bounded, resumable legislation candidate discovery receipts."""

# ruff: noqa: C901, D102, EM101, PLR0912, PLR2004, TRY003, TRY004

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from archive_govt_nz.domains.legislation.accounting import HarvestAccounting

SCHEMA = "archive-govt-nz.legislation-discovery-query/v2"
LEGISLATION_TYPES = {"act", "bill", "amendment_paper", "secondary_legislation"}
SORT_ORDERS = {
    "title_asc",
    "title_desc",
    "year_asc",
    "year_desc",
    "most_recently_updated",
}
OFFICIAL_ENDPOINT = "https://api.legislation.govt.nz/v0/works/"
GENERIC_TERMS = {"act", "bill", "regulation"}
WORK_ID = re.compile(r"^[a-z][A-Za-z0-9_~./-]{2,199}$")


class PageFetcher(Protocol):
    """Fetch one explicitly numbered result page."""

    def __call__(self, params: dict[str, Any], /) -> Any: ...  # noqa: ANN401


@dataclass(frozen=True)
class DiscoveryScope:
    """Immutable query bounds and continuation identity."""

    scope_id: str
    terms: tuple[str, ...]
    legislation_types: tuple[str, ...]
    page_size: int
    max_pages: int
    max_candidates: int
    start_page: int = 1
    endpoint: str = OFFICIAL_ENDPOINT
    sort: str = "most_recently_updated"

    def validate(self) -> None:
        """Reject ambiguous, unbounded, or coverage-implying scope."""
        if self.endpoint != OFFICIAL_ENDPOINT:
            raise ValueError("discovery endpoint must be the pinned official endpoint")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", self.scope_id):
            raise ValueError("invalid discovery scope_id")
        normalized = tuple(term.strip() for term in self.terms)
        if not normalized or any(not term for term in normalized):
            raise ValueError("discovery terms must be non-empty")
        if all(term.casefold() in GENERIC_TERMS for term in normalized):
            raise ValueError("generic terms alone cannot define discovery coverage")
        if len(set(normalized)) != len(normalized):
            raise ValueError("duplicate discovery terms are not permitted")
        if not self.legislation_types or len(set(self.legislation_types)) != len(
            self.legislation_types
        ):
            raise ValueError("legislation types must be non-empty and unique")
        if not set(self.legislation_types) <= LEGISLATION_TYPES:
            raise ValueError("unsupported official legislation_type")
        if not 1 <= self.page_size <= 100:
            raise ValueError("page_size must be within 1..100")
        if not 1 <= self.max_pages <= 100:
            raise ValueError("max_pages must be within 1..100")
        if (
            not 1
            <= self.max_candidates
            <= self.page_size
            * self.max_pages
            * len(self.terms)
            * len(self.legislation_types)
        ):
            raise ValueError("max_candidates exceeds the page bound")
        if self.start_page < 1 or self.sort not in SORT_ORDERS:
            raise ValueError(
                "pagination requires positive pages and an official sort_by"
            )


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _resume_cursors(
    scope: DiscoveryScope,
    cursors: list[dict[str, Any]],
    query_sha: str,
    previous: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Validate every query cursor before making any request."""
    if previous is None:
        return cursors
    assert_same_query(previous, {"query_sha256": query_sha})
    retained = previous.get("continuations")
    if (
        previous.get("schema_version") != SCHEMA
        or not isinstance(retained, list)
        or len(retained) != len(cursors)
    ):
        raise ValueError("invalid discovery continuation")
    for cursor, old in zip(cursors, retained, strict=True):
        if (
            not isinstance(old, dict)
            or set(old) != set(cursor)
            or old["term"] != cursor["term"]
            or old["legislation_type"] != cursor["legislation_type"]
            or type(old["page"]) is not int
            or old["page"] < scope.start_page
            or type(old["offset"]) is not int
            or not 0 <= old["offset"] < scope.page_size
            or type(old["exhausted"]) is not bool
        ):
            raise ValueError("invalid discovery continuation")
    return [dict(old) for old in retained]


def _page_results(payload: object, page: int, page_size: int) -> list[Any]:
    """Reject source bounds that contradict the qualified request."""
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("partial or malformed discovery page")
    results = payload["results"]
    if (
        len(results) > page_size
        or payload.get("page", page) != page
        or payload.get("per_page", page_size) != page_size
    ):
        raise ValueError("partial or malformed discovery page bounds")
    return results


def discover(
    scope: DiscoveryScope,
    fetch: PageFetcher,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fetch bounded pages; retain a separate exact continuation for every query."""
    scope.validate()
    query = {
        "scope_id": scope.scope_id,
        "endpoint": scope.endpoint,
        "terms": list(scope.terms),
        "legislation_types": list(scope.legislation_types),
        "sort_by": scope.sort,
        "page_size": scope.page_size,
        "max_pages": scope.max_pages,
        "max_candidates": scope.max_candidates,
        "start_page": scope.start_page,
    }
    query_sha = hashlib.sha256(_canonical(query)).hexdigest()
    queries = [(term, kind) for term in scope.terms for kind in scope.legislation_types]
    cursors: list[dict[str, Any]] = [
        {
            "term": term,
            "legislation_type": kind,
            "page": scope.start_page,
            "offset": 0,
            "exhausted": False,
        }
        for term, kind in queries
    ]
    cursors = _resume_cursors(scope, cursors, query_sha, previous)
    candidates: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    for cursor in cursors:
        if cursor["exhausted"] or len(candidates) >= scope.max_candidates:
            continue
        for _ in range(scope.max_pages):
            page = cursor["page"]
            params = {
                "search_term": cursor["term"],
                "search_field": "title",
                "legislation_type": cursor["legislation_type"],
                "page": page,
                "per_page": scope.page_size,
                "sort_by": scope.sort,
            }
            payload = fetch(params)
            results = _page_results(payload, page, scope.page_size)
            offset = cursor["offset"]
            if offset > len(results):
                raise ValueError("discovery page changed before continuation offset")
            page_ids: list[str] = []
            for position in range(offset, len(results)):
                item = results[position]
                cursor["offset"] = position + 1
                if not isinstance(item, dict):
                    rejected.append(
                        {"page": page, "position": position, "reason": "not_object"}
                    )
                    continue
                if (
                    item.get("legislation_type", cursor["legislation_type"])
                    != cursor["legislation_type"]
                ):
                    raise ValueError("source did not honor legislation_type")
                work_id = str(item.get("work_id", "")).strip()
                if not WORK_ID.fullmatch(work_id):
                    rejected.append(
                        {
                            "page": page,
                            "position": position,
                            "reason": "malformed_work_id",
                        }
                    )
                    continue
                page_ids.append(work_id)
                version = item.get("latest_matching_version") or {}
                if not isinstance(version, dict):
                    raise ValueError("partial or malformed discovery version")
                normalized = {
                    "work_id": work_id,
                    "canonical_uri": item.get("canonical_uri"),
                    "legislation_type": item.get("legislation_type"),
                    "title": version.get("title") or item.get("title"),
                }
                if work_id in candidates:
                    duplicates.append({"work_id": work_id, "page": page})
                else:
                    candidates[work_id] = normalized
                if len(candidates) >= scope.max_candidates:
                    break
            pages.append(
                {
                    "term": cursor["term"],
                    "legislation_type": cursor["legislation_type"],
                    "page": page,
                    "start_offset": offset,
                    "result_count": len(results),
                    "response_sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
                    "result_sha256": hashlib.sha256(_canonical(page_ids)).hexdigest(),
                }
            )
            if cursor["offset"] == len(results):
                cursor.update(
                    page=page + 1, offset=0, exhausted=len(results) < scope.page_size
                )
            if cursor["exhausted"] or len(candidates) >= scope.max_candidates:
                break
    ordered = [candidates[key] for key in sorted(candidates)]
    return {
        "schema_version": SCHEMA,
        "query": query,
        "query_sha256": query_sha,
        "pages": pages,
        "candidates": ordered,
        "candidate_count": len(ordered),
        "candidate_inventory_sha256": hashlib.sha256(
            _canonical([item["work_id"] for item in ordered])
        ).hexdigest(),
        "duplicates": duplicates,
        "rejected": rejected,
        "continuations": cursors,
        "next_page": cursors[0]["page"]
        if len(cursors) == 1 and not cursors[0]["exhausted"]
        else None,
        "queries_exhausted": all(cursor["exhausted"] for cursor in cursors),
        "bounded": True,
        "authoritative_completeness": False,
        "custody_or_acquisition_proven": False,
    }


def assert_same_query(previous: dict[str, Any], current: dict[str, Any]) -> None:
    """Fail closed when a resumed scope silently changes semantics."""
    if previous.get("query_sha256") != current.get("query_sha256"):
        raise ValueError("discovery query drift requires a new scope version")


def acquisition_receipts(
    candidate_receipt: dict[str, Any], harvest_receipt: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Separate attempt outcomes from pending canonical admission."""
    if candidate_receipt.get("schema_version") not in {
        SCHEMA,
        "archive-govt-nz.legislation-discovery-query/v1",
    }:
        raise ValueError("invalid candidate receipt")
    if (
        harvest_receipt.get("schema_version")
        != "archive-govt-nz.legislation-harvest-receipt/v3"
    ):
        raise ValueError("acquisition requires a v3 harvest receipt")
    try:
        accounting = HarvestAccounting.from_receipt(harvest_receipt).to_receipt()
    except (TypeError, ValueError) as exc:
        raise ValueError("harvest accounting is incomplete") from exc
    allowed = {
        "newly_preserved",
        "changed_preserved",
        "unchanged_revalidated",
        "already_processed_skipped",
        "unavailable",
        "partial",
        "failed",
    }
    groups: dict[str, list[dict[str, Any]]] = {key: [] for key in allowed}
    for row in accounting["works"]:
        groups[row["disposition"]].append(row)
    accepted = groups["newly_preserved"] + groups["changed_preserved"]
    rejected = groups["unavailable"] + groups["partial"] + groups["failed"]
    duplicate = groups["already_processed_skipped"]
    base = {
        "scope_id": candidate_receipt["query"]["scope_id"],
        "candidate_receipt_sha256": hashlib.sha256(
            _canonical(candidate_receipt)
        ).hexdigest(),
        "canonical_state_changed": False,
    }
    return {
        "acquisition-attempts": {**base, "works": accounting["works"]},
        "accepted-pending-merge": {
            **base,
            "works": accepted,
            "admission_status": "pending_verified_state_merge",
            "merge_tool": "tools/merge_legislation_states.py",
        },
        "rejected-duplicate-unavailable-partial-failed": {
            **base,
            "rejected": rejected,
            "duplicates": duplicate,
            "unchanged": groups["unchanged_revalidated"],
        },
    }
