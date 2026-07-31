"""Complete, drift-aware Treasury discovery contracts."""

import asyncio
import hashlib
import json
from datetime import UTC, datetime

import pytest

from archive_govt_nz.ckan.client import ActionObservation, TransportAttempt
from archive_govt_nz.ckan.discovery import (
    TreasuryDiscovery,
    TreasuryDiscoveryError,
    TreasuryScope,
    canonical_scope_manifest,
    scope_report_markdown,
)
from archive_govt_nz.ckan.envelope import ActionResponse

OBSERVED_AT = datetime(2026, 7, 31, 5, 20, tzinfo=UTC)


def make_observation(result: dict[str, object]) -> ActionObservation:
    """Build exact deterministic Action evidence for a fixture result."""
    document: dict[str, object] = {"success": True, "result": result}
    raw_body = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return ActionObservation(
        response=ActionResponse(
            status_code=200,
            result=result,
            response_document=document,
        ),
        raw_body=raw_body,
        raw_sha256=hashlib.sha256(raw_body).hexdigest(),
        observed_at=OBSERVED_AT,
        attempts=(
            TransportAttempt(
                attempt=1,
                status_code=200,
                error_class=None,
                observed_at=OBSERVED_AT,
            ),
        ),
        response_headers={"content-type": "application/json"},
    )


class FakeActionClient:
    """Ordered deterministic Action client fixture."""

    def __init__(self, *responses: ActionObservation) -> None:
        """Retain expected observations."""
        self._responses = iter(responses)
        self.requests: list[tuple[str, dict[str, object]]] = []

    async def action(
        self,
        action: str,
        params: dict[str, object] | None = None,
    ) -> ActionObservation:
        """Record the request and return its fixture observation."""
        self.requests.append((action, params or {}))
        return next(self._responses)


def discover(client: FakeActionClient, *, page_size: int = 2) -> TreasuryScope:
    """Run one deterministic Treasury discovery."""
    return asyncio.run(TreasuryDiscovery(client, page_size=page_size).discover())


def organisation() -> ActionObservation:
    """Return a stable Treasury organisation observation."""
    return make_observation(
        {
            "id": "8f3e87ca-c7b8-44ed-8c6b-241448e3b75f",
            "name": "the-treasury",
            "title": "The Treasury",
        }
    )


def dataset(identifier: str) -> dict[str, object]:
    """Return a minimal identified CKAN dataset."""
    return {
        "id": identifier,
        "name": f"dataset-{identifier}",
        "metadata_modified": "2026-07-31T00:00:00.000000",
    }


def page(count: int, *identifiers: str) -> ActionObservation:
    """Return one package-search page observation."""
    return make_observation(
        {
            "count": count,
            "results": [dataset(identifier) for identifier in identifiers],
        }
    )


def test_resolves_treasury_and_uses_stable_organisation_filter() -> None:
    """The human slug is resolved before its verified identity scopes search."""
    client = FakeActionClient(organisation(), page(1, "dataset-a"))

    scope = discover(client)

    assert scope.organization.id == "8f3e87ca-c7b8-44ed-8c6b-241448e3b75f"
    assert scope.organization.name == "the-treasury"
    assert scope.organization.title == "The Treasury"
    assert client.requests == [
        ("organization_show", {"id": "the-treasury"}),
        (
            "package_search",
            {
                "fq": "organization:the-treasury",
                "rows": 2,
                "sort": "id asc",
                "start": 0,
            },
        ),
    ]


def test_paginates_from_live_counts_and_records_count_drift() -> None:
    """A rising live count extends discovery without a dated fixed-count gate."""
    client = FakeActionClient(
        organisation(),
        page(3, "dataset-a", "dataset-b"),
        page(4, "dataset-c", "dataset-d"),
    )

    scope = discover(client)

    assert scope.dataset_ids == (
        "dataset-a",
        "dataset-b",
        "dataset-c",
        "dataset-d",
    )
    assert scope.reported_counts == (3, 4)
    assert scope.discovered_count == 4
    assert client.requests[-1][1]["start"] == 2
    assert 54 not in scope.reported_counts


def test_preserves_raw_pages_and_builds_deterministic_scope_manifest() -> None:
    """Raw discovery responses remain hash-addressable beside stable JSON."""
    organization_response = organisation()
    first_page = page(2, "dataset-a", "dataset-b")

    scope = discover(FakeActionClient(organization_response, first_page))
    first = canonical_scope_manifest(scope)
    second = canonical_scope_manifest(scope)
    manifest = json.loads(first)
    markdown = scope_report_markdown(scope)

    assert first == second
    assert first.endswith(b"\n")
    assert markdown.startswith(b"# Treasury discovery scope\n")
    assert markdown.endswith(b"\n")
    assert first_page.raw_sha256.encode() in markdown
    assert b"does not claim resource capture or publication" in markdown
    assert scope.organization.raw_body == organization_response.raw_body
    assert scope.pages[0].raw_body == first_page.raw_body
    assert scope.pages[0].raw_sha256 == first_page.raw_sha256
    assert manifest["schema_version"] == "archive-govt-nz.treasury-scope/v1"
    assert manifest["observed_at"] == "2026-07-31T05:20:00Z"
    assert manifest["discovered_count"] == 2
    assert manifest["dataset_ids"] == ["dataset-a", "dataset-b"]
    assert manifest["pages"][0]["raw_sha256"] == first_page.raw_sha256


@pytest.mark.parametrize(
    ("results", "error_class"),
    [
        ([dataset("dataset-a"), dataset("dataset-a")], "duplicate_dataset_id"),
        ([{"name": "missing-stable-id"}], "missing_dataset_id"),
    ],
)
def test_duplicate_or_missing_dataset_identifiers_fail_closed(
    results: list[dict[str, object]],
    error_class: str,
) -> None:
    """Every dataset needs one unique stable identifier."""
    search = make_observation({"count": len(results), "results": results})

    with pytest.raises(TreasuryDiscoveryError) as raised:
        discover(FakeActionClient(organisation(), search))

    assert raised.value.error_class == error_class
    assert "dataset-a" not in str(raised.value)


def test_exhausted_page_before_reported_count_fails_reconciliation() -> None:
    """Premature empty pages cannot become a completeness claim."""
    client = FakeActionClient(
        organisation(),
        page(3, "dataset-a", "dataset-b"),
        page(3),
    )

    with pytest.raises(TreasuryDiscoveryError) as raised:
        discover(client)

    assert raised.value.error_class == "count_reconciliation"


def test_page_size_must_preserve_a_positive_progress_bound() -> None:
    """Zero-sized pagination cannot enter the discovery loop."""
    with pytest.raises(TreasuryDiscoveryError) as raised:
        TreasuryDiscovery(FakeActionClient(), page_size=0)

    assert raised.value.error_class == "page_size"


def test_out_of_order_ids_fail_before_a_scope_is_accepted() -> None:
    """The requested stable sort is verified rather than merely trusted."""
    client = FakeActionClient(organisation(), page(2, "dataset-b", "dataset-a"))

    with pytest.raises(TreasuryDiscoveryError) as raised:
        discover(client)

    assert raised.value.error_class == "dataset_order"


def test_count_falling_below_already_observed_results_fails_closed() -> None:
    """A downward drift cannot silently discard an already observed dataset."""
    client = FakeActionClient(
        organisation(),
        make_observation(
            {
                "count": 1,
                "results": [dataset("dataset-a"), dataset("dataset-b")],
            }
        ),
    )

    with pytest.raises(TreasuryDiscoveryError) as raised:
        discover(client)

    assert raised.value.error_class == "count_reconciliation"


@pytest.mark.parametrize(
    "result",
    [
        {"id": 7, "name": "the-treasury", "title": "The Treasury"},
        {"id": "", "name": "the-treasury", "title": "The Treasury"},
        {"id": "stable-id", "name": 7, "title": "The Treasury"},
        {"id": "stable-id", "name": "the-treasury", "title": 7},
    ],
)
def test_incomplete_organization_identity_is_terminal(
    result: dict[str, object],
) -> None:
    """Every stable organisation identity field is required."""
    with pytest.raises(TreasuryDiscoveryError) as raised:
        discover(FakeActionClient(make_observation(result)))

    assert raised.value.error_class == "organization_protocol"


def test_resolved_organization_name_must_match_requested_slug() -> None:
    """A valid but different organization cannot redefine Treasury scope."""
    wrong = make_observation(
        {"id": "stable-id", "name": "other-agency", "title": "Other Agency"}
    )

    with pytest.raises(TreasuryDiscoveryError) as raised:
        discover(FakeActionClient(wrong))

    assert raised.value.error_class == "organization_mismatch"


@pytest.mark.parametrize(
    "result",
    [
        {"count": "1", "results": []},
        {"count": True, "results": []},
        {"count": -1, "results": []},
        {"count": 1, "results": {}},
        {"count": 1, "results": ["not-a-dataset"]},
    ],
)
def test_malformed_search_pages_are_terminal(result: dict[str, object]) -> None:
    """Counts and results use exact CKAN-compatible structural types."""
    client = FakeActionClient(organisation(), make_observation(result))

    with pytest.raises(TreasuryDiscoveryError) as raised:
        discover(client)

    assert raised.value.error_class == "search_protocol"


def test_empty_scope_and_optional_dataset_labels_are_representable() -> None:
    """A genuine zero count and absent optional labels remain valid evidence."""
    empty_scope = discover(FakeActionClient(organisation(), page(0)))
    assert empty_scope.discovered_count == 0

    search = make_observation(
        {
            "count": 1,
            "results": [
                {
                    "id": "dataset-a",
                    "name": 7,
                    "metadata_modified": None,
                }
            ],
        }
    )
    labelled_scope = discover(FakeActionClient(organisation(), search))

    assert labelled_scope.datasets[0].name is None
    assert labelled_scope.datasets[0].metadata_modified is None
