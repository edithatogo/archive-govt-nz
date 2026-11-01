"""Bounded, resumable legislation candidate discovery receipts."""

# ruff: noqa: C901, D102, EM101, PLR0912, PLR2004, TRY003, TRY004

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

SCHEMA = "archive-govt-nz.legislation-discovery-query/v1"
OFFICIAL_ENDPOINT = "https://api.legislation.govt.nz/v0/works/"
GENERIC_TERMS = {"act", "bill", "regulation"}
WORK_ID = re.compile(r"^[a-z][a-z0-9_./-]{2,199}$")


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
    sort: str = "work_id"

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
        if not 1 <= self.page_size <= 100:
            raise ValueError("page_size must be within 1..100")
        if not 1 <= self.max_pages <= 100:
            raise ValueError("max_pages must be within 1..100")
        if not 1 <= self.max_candidates <= self.page_size * self.max_pages:
            raise ValueError("max_candidates exceeds the page bound")
        if self.start_page < 1 or self.sort != "work_id":
            raise ValueError("pagination must use positive pages sorted by work_id")


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def discover(scope: DiscoveryScope, fetch: PageFetcher) -> dict[str, Any]:
    """Fetch deterministic pages and retain malformed/duplicate evidence."""
    scope.validate()
    candidates: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    exhausted = False
    for term in scope.terms:
        for legislation_type in scope.legislation_types:
            for page in range(scope.start_page, scope.start_page + scope.max_pages):
                params = {
                    "search_term": term,
                    "search_field": "title",
                    "legislation_type": legislation_type,
                    "page": page,
                    "per_page": scope.page_size,
                    "sort": scope.sort,
                }
                payload = fetch(params)
                if not isinstance(payload, dict) or not isinstance(
                    payload.get("results"), list
                ):
                    raise ValueError("partial or malformed discovery page")
                results = payload["results"]
                page_ids: list[str] = []
                for position, item in enumerate(results):
                    if not isinstance(item, dict):
                        rejected.append(
                            {"page": page, "position": position, "reason": "not_object"}
                        )
                        continue
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
                    normalized = {
                        "work_id": work_id,
                        "canonical_uri": item.get("canonical_uri"),
                        "legislation_type": item.get("legislation_type"),
                        "title": item.get("title"),
                    }
                    if work_id in candidates:
                        duplicates.append({"work_id": work_id, "page": page})
                    else:
                        candidates[work_id] = normalized
                    if len(candidates) >= scope.max_candidates:
                        break
                pages.append(
                    {
                        "term": term,
                        "legislation_type": legislation_type,
                        "page": page,
                        "result_count": len(results),
                        "result_sha256": hashlib.sha256(
                            _canonical(page_ids)
                        ).hexdigest(),
                    }
                )
                if len(candidates) >= scope.max_candidates:
                    break
                if len(results) < scope.page_size:
                    exhausted = True
                    break
            if len(candidates) >= scope.max_candidates:
                break
        if len(candidates) >= scope.max_candidates:
            break
    ordered = [candidates[key] for key in sorted(candidates)]
    query = {
        "scope_id": scope.scope_id,
        "endpoint": scope.endpoint,
        "terms": list(scope.terms),
        "legislation_types": list(scope.legislation_types),
        "sort": scope.sort,
        "page_size": scope.page_size,
        "max_pages": scope.max_pages,
        "max_candidates": scope.max_candidates,
        "start_page": scope.start_page,
    }
    query_sha = hashlib.sha256(_canonical(query)).hexdigest()
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
        "next_page": None if exhausted else scope.start_page + scope.max_pages,
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
    if candidate_receipt.get("schema_version") != SCHEMA:
        raise ValueError("invalid candidate receipt")
    if (
        harvest_receipt.get("schema_version")
        != "archive-govt-nz.legislation-harvest-receipt/v3"
    ):
        raise ValueError("acquisition requires a v3 harvest receipt")
    accounting = harvest_receipt.get("accounting")
    if not isinstance(accounting, dict) or not isinstance(
        accounting.get("works"), list
    ):
        raise ValueError("harvest accounting is incomplete")
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
        if not isinstance(row, dict) or row.get("disposition") not in allowed:
            raise ValueError("harvest work disposition is malformed")
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
