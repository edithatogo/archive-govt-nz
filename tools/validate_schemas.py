"""Validate committed JSON Schemas and their representative fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from jsonschema import Draft202012Validator

from archive_govt_nz.records import archive_schema_documents

if TYPE_CHECKING:
    from collections.abc import Callable

type JsonValue = (
    bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None
)

REPOSITORY_ROOT = Path(__file__).parents[1]
VALIDATION_PAIRS = (
    (
        REPOSITORY_ROOT / "schemas" / "health-raw-gold-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "health-raw-gold-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "foi-package-v2.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "foi-package-sample-v2.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "foi-package-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "foi-package-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "health-raw-compatibility-v1.schema.json",
        REPOSITORY_ROOT
        / "tests"
        / "fixtures"
        / "health-raw-compatibility-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "foi-source-catalogue-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "foi-source-catalogue-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "health-workbook-inspection-v1.schema.json",
        REPOSITORY_ROOT
        / "tests"
        / "fixtures"
        / "health-workbook-inspection-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "health-raw-rebuild-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "health-raw-rebuild-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "health-historical-reconciliation-v1.schema.json",
        REPOSITORY_ROOT
        / "tests"
        / "fixtures"
        / "health-historical-reconciliation-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "cli-envelope-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "cli-version-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "conductor-autonomy-policy-v1.schema.json",
        REPOSITORY_ROOT / "conductor" / "autonomy-policy.json",
    ),
    (
        REPOSITORY_ROOT
        / "schemas"
        / "archive"
        / "v1"
        / "migration-baseline.schema.json",
        REPOSITORY_ROOT / "conductor" / "migrations" / "sm-govt-nz.json",
    ),
    (
        REPOSITORY_ROOT
        / "schemas"
        / "archive"
        / "v1"
        / "migration-baseline-evidence.schema.json",
        REPOSITORY_ROOT / "evidence" / "migrations" / "sm-govt-nz" / "baseline.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "migrations" / "capability-matrix-v1.schema.json",
        REPOSITORY_ROOT
        / "docs"
        / "migrations"
        / "sm-govt-nz"
        / "capability-matrix.json",
    ),
    (
        REPOSITORY_ROOT
        / "schemas"
        / "archive"
        / "v1"
        / "donor-track-lineage.schema.json",
        REPOSITORY_ROOT
        / "evidence"
        / "migrations"
        / "sm-govt-nz"
        / "donor-track-lineage.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "archive" / "v1" / "source-manifest.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "source-manifest-sample.json",
    ),
    (
        REPOSITORY_ROOT
        / "schemas"
        / "archive"
        / "v1"
        / "preservation-manifest.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "preservation-manifest-sample.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "archive" / "v1" / "capture-event.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "capture-event-sample.json",
    ),
    (
        REPOSITORY_ROOT
        / "schemas"
        / "archive"
        / "v1"
        / "publication-receipt.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "publication-receipt-sample.json",
    ),
    (
        REPOSITORY_ROOT
        / "schemas"
        / "legislation"
        / "v1"
        / "legislation-record.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "legislation-record-sample.json",
    ),
    (
        REPOSITORY_ROOT
        / "schemas"
        / "legislation"
        / "v1"
        / "one-batch-reconciliation.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "legislation-one-batch-failure.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "bronze-ingestion-manifest-v1.schema.json",
        REPOSITORY_ROOT
        / "tests"
        / "fixtures"
        / "bronze-ingestion-manifest-sample.json",
    ),
    (
        REPOSITORY_ROOT
        / "schemas"
        / "migrations"
        / "shadow-operation-cutover-attestation-v1.schema.json",
        REPOSITORY_ROOT
        / "evidence"
        / "migrations"
        / "corpus-legislation-nz"
        / "shadow-operation-cutover-attestation.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "hansard-debate-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "hansard-debate-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "hathi-volume-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "hathi-volume-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "medilegal-case-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "medilegal-case-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "publication-manifest-v2.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "publication-manifest-v2-sample.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "claim-drift-receipt-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "claim-drift-receipt-sample-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "donor-retirement-attestation-v1.schema.json",
        REPOSITORY_ROOT
        / "tests"
        / "fixtures"
        / "donor-retirement-attestation-sample-v1.json",
    ),
)
ARCHIVE_SCHEMA_DIRECTORY = REPOSITORY_ROOT / "schemas" / "archive" / "v1"


def load_json_object(path: Path) -> dict[str, JsonValue]:
    """Load one UTF-8 JSON object."""
    with path.open(encoding="utf-8") as stream:
        document = cast("JsonValue", json.load(stream))
    if not isinstance(document, dict):
        message = f"expected a JSON object in {path}"
        raise TypeError(message)
    return document


def validate() -> None:
    """Validate each schema itself and its representative document."""
    for schema_path, document_path in VALIDATION_PAIRS:
        schema = load_json_object(schema_path)
        document = load_json_object(document_path)
        Draft202012Validator.check_schema(schema)
        validate_document = cast(
            "Callable[[object], None]",
            Draft202012Validator(schema).validate,  # pyright: ignore[reportUnknownMemberType]
        )
        validate_document(document)
    for kind, expected_schema in archive_schema_documents().items():
        schema = load_json_object(ARCHIVE_SCHEMA_DIRECTORY / f"{kind}.schema.json")
        Draft202012Validator.check_schema(schema)
        if schema != expected_schema:
            message = f"generated archive schema drift: {kind}"
            raise ValueError(message)


def main() -> int:
    """Run schema validation as a process-safe gate."""
    validate()
    archive_count = len(archive_schema_documents())
    print(
        f"validated {len(VALIDATION_PAIRS) + archive_count} schemas "
        f"and {len(VALIDATION_PAIRS)} representative documents"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
