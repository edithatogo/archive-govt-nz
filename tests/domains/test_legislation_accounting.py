"""Tests for fail-closed legislation harvest accounting."""
# ruff: noqa: D103

from __future__ import annotations

from dataclasses import replace

import pytest

from archive_govt_nz.domains.legislation.accounting import (
    V2_SCHEMA,
    HarvestAccounting,
    StateCommitStatus,
    WorkAccounting,
    WorkDisposition,
    read_harvest_receipt,
)

HASH = "a" * 64
COMMIT = "b" * 40


def work(name: str, disposition: WorkDisposition, retries: int = 0) -> WorkAccounting:
    classifications = (
        ()
        if disposition is WorkDisposition.ALREADY_PROCESSED_SKIPPED
        else ("http_200",)
    )
    return WorkAccounting(name, disposition, classifications, retries)


def accounting() -> HarvestAccounting:
    works = (
        work("new", WorkDisposition.NEWLY_PRESERVED),
        work("changed", WorkDisposition.CHANGED_PRESERVED, 1),
        work("same", WorkDisposition.UNCHANGED_REVALIDATED),
        work("skip", WorkDisposition.ALREADY_PROCESSED_SKIPPED),
        work("missing", WorkDisposition.UNAVAILABLE, 2),
        work("partial", WorkDisposition.PARTIAL),
        work("failed", WorkDisposition.FAILED),
    )
    return HarvestAccounting(
        candidate_works_discovered=9,
        works_in_scope=7,
        works_attempted=6,
        newly_preserved=1,
        changed_preserved=1,
        unchanged_revalidated=1,
        already_processed_skipped=1,
        unavailable=1,
        partial=1,
        failed=1,
        total_state_records_before=10,
        total_state_records_after=11,
        total_cas_objects_before=12,
        total_cas_objects_after=14,
        scope_digests={"seed": HASH, "resolved": "c" * 64},
        parent_manifest_root=HASH,
        parent_checkpoint_root=HASH,
        output_manifest_root=HASH,
        output_checkpoint_root=HASH,
        software_commit=COMMIT,
        workflow_identity="manual",
        run_identity="run-1",
        state_commit_status=StateCommitStatus.COMMITTED,
        state_commit=COMMIT,
        works=works,
    )


def test_v3_round_trip_and_computed_deltas() -> None:
    original = accounting()
    receipt = original.to_receipt()
    parsed = read_harvest_receipt(receipt)
    assert parsed.evidence_strength == "strong"
    assert parsed.accounting == original
    assert receipt["total_retry_count"] == 3
    assert receipt["state_record_delta"] == 1
    assert receipt["cas_object_delta"] == 2
    assert list(receipt["scope_digests"]) == ["resolved", "seed"]


@pytest.mark.parametrize("disposition", list(WorkDisposition))
def test_each_terminal_disposition_can_account_for_one_work(
    disposition: WorkDisposition,
) -> None:
    attempted = disposition is not WorkDisposition.ALREADY_PROCESSED_SKIPPED
    mutations = disposition in {
        WorkDisposition.NEWLY_PRESERVED,
        WorkDisposition.CHANGED_PRESERVED,
    }
    item = work("id", disposition)
    counts = {member.value: 0 for member in WorkDisposition}
    counts[disposition.value] = 1
    value = HarvestAccounting(
        candidate_works_discovered=1,
        works_in_scope=1,
        works_attempted=int(attempted),
        **counts,
        total_state_records_before=0,
        total_state_records_after=int(mutations),
        total_cas_objects_before=0,
        total_cas_objects_after=int(mutations),
        scope_digests={"resolved": HASH},
        parent_manifest_root=None,
        parent_checkpoint_root=None,
        output_manifest_root=HASH,
        output_checkpoint_root=HASH,
        software_commit=COMMIT,
        workflow_identity="test",
        run_identity="generated-case",
        state_commit_status=(
            StateCommitStatus.COMMITTED if mutations else StateCommitStatus.NO_CHANGE
        ),
        state_commit=COMMIT,
        works=(item,),
    )
    assert value.works_attempted == int(attempted)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("candidate_works_discovered", 6, "candidate works"),
        ("works_attempted", 5, "works_attempted"),
        ("newly_preserved", 0, "newly_preserved"),
        ("total_state_records_after", 9, "cannot decrease"),
        ("total_cas_objects_after", 11, "cannot decrease"),
        ("scope_digests", {"seed": "BAD"}, "scope digests"),
        ("software_commit", "b" * 39, "software_commit"),
        ("workflow_identity", "", "workflow_identity"),
    ],
)
def test_invalid_aggregate_or_identity_is_rejected(
    field: str, value: object, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        replace(accounting(), **{field: value})


def test_duplicate_work_ids_are_rejected() -> None:
    value = accounting()
    with pytest.raises(ValueError, match="duplicate"):
        replace(
            value, works=(*value.works[:-1], replace(value.works[-1], work_id="new"))
        )


def test_no_change_cannot_hide_state_mutation() -> None:
    same = work("same", WorkDisposition.UNCHANGED_REVALIDATED)
    base = replace(
        accounting(),
        candidate_works_discovered=1,
        works_in_scope=1,
        works_attempted=1,
        newly_preserved=0,
        changed_preserved=0,
        unchanged_revalidated=1,
        already_processed_skipped=0,
        unavailable=0,
        partial=0,
        failed=0,
        total_state_records_before=10,
        total_state_records_after=10,
        total_cas_objects_before=12,
        total_cas_objects_after=12,
        works=(same,),
    )
    with pytest.raises(ValueError, match="state-record deltas"):
        replace(base, total_state_records_after=11)


def test_failed_uncommitted_attempt_may_leave_orphan_cas_object() -> None:
    """Immutable CAS writes may precede a failed state commit."""
    failed = work("failed", WorkDisposition.FAILED)
    value = replace(
        accounting(),
        candidate_works_discovered=1,
        works_in_scope=1,
        works_attempted=1,
        newly_preserved=0,
        changed_preserved=0,
        unchanged_revalidated=0,
        already_processed_skipped=0,
        unavailable=0,
        partial=0,
        failed=1,
        total_state_records_before=10,
        total_state_records_after=10,
        total_cas_objects_before=12,
        total_cas_objects_after=13,
        output_manifest_root=None,
        output_checkpoint_root=None,
        state_commit_status=StateCommitStatus.NOT_COMMITTED,
        state_commit=None,
        works=(failed,),
    )
    assert value.cas_object_delta == 1


def test_preserved_disposition_requires_observable_delta() -> None:
    with pytest.raises(ValueError, match="require a state or CAS delta"):
        replace(
            accounting(),
            total_state_records_after=10,
            total_cas_objects_after=12,
        )


@pytest.mark.parametrize("retry", [-1, -10])
def test_negative_retry_is_rejected(retry: int) -> None:
    with pytest.raises(ValueError, match="retry_count"):
        work("id", WorkDisposition.FAILED, retry)


def test_attempt_requires_source_classification() -> None:
    with pytest.raises(ValueError, match="source response"):
        WorkAccounting("id", WorkDisposition.FAILED)


def test_skipped_work_cannot_claim_retries() -> None:
    with pytest.raises(ValueError, match="skipped work"):
        WorkAccounting("id", WorkDisposition.ALREADY_PROCESSED_SKIPPED, (), 1)


def test_v3_rejects_tampered_computed_counter() -> None:
    receipt = accounting().to_receipt()
    receipt["total_retry_count"] = 4
    with pytest.raises(ValueError, match="total_retry_count"):
        read_harvest_receipt(receipt)


def test_v2_is_retained_as_weak_evidence_without_synthesised_categories() -> None:
    receipt = {
        "schema_version": V2_SCHEMA,
        "works_attempted": 500,
        "works_synced": 0,
        "records_preserved": 500,
        "outcome": "success",
    }
    parsed = read_harvest_receipt(receipt)
    assert parsed.evidence_strength == "weak_legacy_accounting"
    assert parsed.accounting is None
    assert parsed.historical_counters == {
        "works_attempted": 500,
        "works_synced": 0,
        "records_preserved": 500,
    }


@pytest.mark.parametrize("schema", [None, "v1", "archive-govt-nz.other/v3"])
def test_unknown_receipt_schema_fails_closed(schema: str | None) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        read_harvest_receipt({"schema_version": schema})


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"work_id": " "}, "work_id"),
        ({"source_response_classifications": (" ",)}, "classifications"),
    ],
)
def test_work_accounting_rejects_noncanonical_text(
    kwargs: dict[str, object], match: str
) -> None:
    values: dict[str, object] = {
        "work_id": "id",
        "disposition": WorkDisposition.FAILED,
        "source_response_classifications": ("http_500",),
    }
    values.update(kwargs)
    with pytest.raises(ValueError, match=match):
        WorkAccounting(**values)  # type: ignore[arg-type]


def test_work_accounting_reader_rejects_non_string_classifications() -> None:
    with pytest.raises(TypeError, match="string array"):
        WorkAccounting.from_dict(
            {
                "work_id": "id",
                "disposition": "failed",
                "source_response_classifications": [500],
                "retry_count": 0,
            }
        )


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        ({"works_in_scope": True}, "non-negative integer"),
        ({"works_in_scope": 8}, "work accounting count"),
        ({"scope_digests": {}}, "scope digest"),
        ({"parent_manifest_root": "BAD"}, "parent_manifest_root"),
        ({"state_commit": "BAD"}, "state_commit"),
        ({"state_commit": None}, "committed state"),
        ({"state_commit_status": StateCommitStatus.NO_CHANGE}, "no_change"),
        (
            {"state_commit_status": StateCommitStatus.NOT_COMMITTED},
            "cannot claim a commit",
        ),
        (
            {
                "state_commit_status": StateCommitStatus.NOT_COMMITTED,
                "state_commit": None,
            },
            "cannot claim output roots",
        ),
    ],
)
def test_accounting_rejects_remaining_lineage_contradictions(
    changes: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        replace(accounting(), **changes)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ({"schema_version": "wrong"}, "not a v3"),
        ({"works": "wrong"}, "array of objects"),
        ({"scope_digests": []}, "string mapping"),
        ({"software_commit": 1}, "must be a string"),
        ({"parent_manifest_root": 1}, "string or null"),
        ({"works_attempted": True}, "must be an integer"),
    ],
)
def test_v3_reader_rejects_remaining_type_boundaries(
    mutation: dict[str, object], match: str
) -> None:
    receipt = accounting().to_receipt()
    receipt.update(mutation)
    with pytest.raises((TypeError, ValueError), match=match):
        HarvestAccounting.from_receipt(receipt)
