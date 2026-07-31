"""Versioned archive record schema and canonicalization contracts."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from archive_govt_nz.records import (
    ArchiveRecordError,
    RecordHeader,
    archive_schema_documents,
    canonical_record_bytes,
    load_archive_schema,
    validate_archive_record,
)

SHA256 = "0" * 64
BLAKE3 = "1" * 64
OBSERVED_AT = "2026-07-31T05:22:16Z"


def common(kind: str, *, state: str) -> dict[str, object]:
    """Build fields shared by every v1 record."""
    return {
        "schema_version": f"archive-govt-nz.{kind}/v1",
        "record_id": f"{kind}-record",
        "observed_at": OBSERVED_AT,
        "state": state,
        "evidence": [],
    }


def minimal_records() -> dict[str, dict[str, object]]:
    """Return one valid representative for every archive record schema."""
    return {
        "capability": {
            **common("capability", state="observed"),
            "catalogue_url": "https://catalogue.data.govt.nz",
            "action_api_version": "3",
            "ckan_version": "2.10.9",
            "site_url": "https://catalogue.data.govt.nz",
            "raw_sha256": SHA256,
            "attempt_ids": ["attempt-capability-1"],
        },
        "scope": {
            **common("scope", state="reconciled"),
            "catalogue_url": "https://catalogue.data.govt.nz",
            "organization_id": "organization-id",
            "organization_name": "the-treasury",
            "dataset_ids": ["dataset-a"],
            "page_sha256": [SHA256],
            "reported_counts": [1],
            "observation_started_at": OBSERVED_AT,
            "observation_ended_at": OBSERVED_AT,
        },
        "dataset": {
            **common("dataset", state="observed"),
            "dataset_id": "dataset-a",
            "name": "dataset-a",
            "organization_id": "organization-id",
            "raw_metadata_object_id": f"sha256:{SHA256}",
            "resource_ids": ["resource-a"],
            "tombstone": False,
        },
        "resource": {
            **common("resource", state="eligible"),
            "resource_id": "resource-a",
            "dataset_id": "dataset-a",
            "source_url": "https://example.govt.nz/resource.csv",
            "source_filename": "resource.csv",
            "declared_format": "CSV",
            "declared_media_type": "text/csv",
            "policy_version": "resource-policy/v1",
            "disposition": "eligible",
        },
        "attempt": {
            **common("attempt", state="succeeded"),
            "target_record_id": "resource-record",
            "ordinal": 1,
            "error_class": None,
            "started_at": OBSERVED_AT,
            "ended_at": OBSERVED_AT,
            "status_code": 200,
            "safe_request": {},
            "safe_response": {"content-type": "text/csv"},
            "byte_count": 12,
            "retry_disposition": "not_required",
            "object_id": f"sha256:{SHA256}",
        },
        "object": {
            **common("object", state="verified"),
            "object_id": f"sha256:{SHA256}",
            "sha256": SHA256,
            "blake3": BLAKE3,
            "byte_count": 12,
            "media_type": "text/csv",
            "role": "source_resource",
            "verified_at": OBSERVED_AT,
            "source_record_id": "resource-record",
        },
        "version": {
            **common("version", state="material"),
            "dataset_id": "dataset-a",
            "version_id": "dataset-a:v1",
            "comparison_sha256": SHA256,
            "predecessor_version_id": None,
            "change_reasons": ["first_observation"],
            "metadata_object_ids": [f"sha256:{SHA256}"],
            "resource_object_ids": [f"sha256:{SHA256}"],
            "policy_version": "version-policy/v1",
            "created_at": OBSERVED_AT,
            "tombstone": False,
        },
        "transformation": {
            **common("transformation", state="succeeded"),
            "name": "normalize-ckan",
            "version": "1",
            "implementation_revision": "revision",
            "input_object_ids": [f"sha256:{SHA256}"],
            "output_object_ids": [f"sha256:{'2' * 64}"],
            "parameters": {},
            "environment_sbom_id": "sbom-id",
            "started_at": OBSERVED_AT,
            "ended_at": OBSERVED_AT,
            "information_loss": "Nested CKAN fields are retained in raw metadata.",
            "deterministic": True,
        },
        "validation": {
            **common("validation", state="passed"),
            "validator_name": "manifest-closure",
            "validator_version": "1",
            "subject_ids": ["dataset-a:v1"],
            "checks": ["all_objects_present"],
            "findings": [],
            "started_at": OBSERVED_AT,
            "ended_at": OBSERVED_AT,
        },
        "publication": {
            **common("publication", state="prepared"),
            "target": "hugging_face",
            "local_version_id": "dataset-a:v1",
            "manifest_sha256": SHA256,
            "requested_at": OBSERVED_AT,
            "remote_identifier": None,
            "remote_revision": None,
            "verified_at": None,
            "doi": None,
        },
    }


@pytest.mark.parametrize(("kind", "record"), minimal_records().items())
def test_every_v1_schema_accepts_its_minimal_record(
    kind: str,
    record: dict[str, object],
) -> None:
    """Every catalogue entry has an executable strict v1 schema."""
    schema = load_archive_schema(kind)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    validate_archive_record(record)


@pytest.mark.parametrize("kind", minimal_records())
def test_committed_schema_matches_the_typed_catalogue(kind: str) -> None:
    """Generated schema files cannot drift from the validation authority."""
    path = Path("schemas/archive/v1") / f"{kind}.schema.json"

    assert json.loads(path.read_bytes()) == load_archive_schema(kind)


@pytest.mark.parametrize("kind", minimal_records())
def test_missing_id_unknown_field_and_non_utc_time_fail_closed(kind: str) -> None:
    """Common provenance fields have identical strict behavior in every schema."""
    record = minimal_records()[kind]

    missing_id = deepcopy(record)
    del missing_id["record_id"]
    with pytest.raises(ArchiveRecordError):
        validate_archive_record(missing_id)

    unknown = deepcopy(record)
    unknown["undeclared"] = True
    with pytest.raises(ArchiveRecordError):
        validate_archive_record(unknown)

    non_utc = deepcopy(record)
    non_utc["observed_at"] = "2026-07-31T15:22:16+10:00"
    with pytest.raises(ArchiveRecordError):
        validate_archive_record(non_utc)


def test_source_and_derivative_object_roles_remain_explicit() -> None:
    """Objects cannot use an invented role that obscures source provenance."""
    record = minimal_records()["object"]
    record["role"] = "source_and_derivative"

    with pytest.raises(ArchiveRecordError):
        validate_archive_record(record)


@pytest.mark.parametrize("state", ["prepared", "uploaded"])
def test_publication_cannot_claim_a_doi_before_release(state: str) -> None:
    """A DOI cannot appear merely because a package or upload exists."""
    record = minimal_records()["publication"]
    record["state"] = state
    record["doi"] = "10.5281/zenodo.123"

    with pytest.raises(ArchiveRecordError):
        validate_archive_record(record)


def test_remote_verification_requires_remote_identity_revision_and_time() -> None:
    """Remote verification is a complete evidence state, not a status label."""
    record = minimal_records()["publication"]
    record["state"] = "remotely_verified"
    record["remote_identifier"] = "dataset-repository"

    with pytest.raises(ArchiveRecordError):
        validate_archive_record(record)

    record["remote_revision"] = "remote-revision"
    record["verified_at"] = OBSERVED_AT
    validate_archive_record(record)


def test_canonical_bytes_are_stable_and_reject_non_finite_numbers() -> None:
    """Canonical hashes cannot depend on insertion order or non-standard JSON."""
    record = minimal_records()["capability"]
    reversed_record = dict(reversed(tuple(record.items())))

    assert canonical_record_bytes(record) == canonical_record_bytes(reversed_record)
    assert canonical_record_bytes(record).endswith(b"\n")

    invalid = deepcopy(record)
    invalid["evidence"] = [{"score": float("nan")}]
    with pytest.raises(ArchiveRecordError):
        canonical_record_bytes(invalid)


def test_schema_documents_are_defensive_and_header_is_typed() -> None:
    """Callers cannot mutate the catalogue shared by later validations."""
    documents = archive_schema_documents()
    documents["capability"]["title"] = "mutated"

    assert load_archive_schema("capability")["title"] != "mutated"
    header = RecordHeader(
        schema_version="archive-govt-nz.capability/v1",
        record_id="capability-record",
        observed_at=OBSERVED_AT,
        state="observed",
    )
    assert header.evidence == ()


@pytest.mark.parametrize(
    "record",
    [
        {},
        {"schema_version": "other.capability/v1"},
        {"schema_version": "archive-govt-nz.capability/v2"},
        {"schema_version": "archive-govt-nz.unknown/v1"},
    ],
)
def test_unknown_or_missing_schema_versions_fail_closed(
    record: dict[str, object],
) -> None:
    """Readers reject missing, foreign, newer, and unknown schema identifiers."""
    with pytest.raises(ArchiveRecordError):
        validate_archive_record(record)


def test_unknown_schema_catalogue_key_fails_closed() -> None:
    """A caller cannot infer a schema from an undeclared kind."""
    with pytest.raises(ArchiveRecordError):
        load_archive_schema("unknown")
