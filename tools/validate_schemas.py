"""Validate committed JSON Schemas and their representative fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from jsonschema import Draft202012Validator

if TYPE_CHECKING:
    from collections.abc import Callable

type JsonValue = (
    bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None
)

REPOSITORY_ROOT = Path(__file__).parents[1]
VALIDATION_PAIRS = (
    (
        REPOSITORY_ROOT / "schemas" / "cli-envelope-v1.schema.json",
        REPOSITORY_ROOT / "tests" / "fixtures" / "cli-version-v1.json",
    ),
    (
        REPOSITORY_ROOT / "schemas" / "conductor-autonomy-policy-v1.schema.json",
        REPOSITORY_ROOT / "conductor" / "autonomy-policy.json",
    ),
)


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


def main() -> int:
    """Run schema validation as a process-safe gate."""
    validate()
    print(f"validated {len(VALIDATION_PAIRS)} schemas and documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
