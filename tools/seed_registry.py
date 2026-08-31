"""Resolve an immutable reviewed seed ID using offline, fail-closed validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

WORK_ID = re.compile(
    r"(?:act|bill|secondary_legislation|amendment_paper)_[a-z]+_[0-9]{4}_[0-9]+"
)


def _require(condition: bool, message: str) -> None:  # noqa: FBT001 - assertion predicate
    if not condition:
        raise ValueError(message)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(value)


def read_json(path: Path) -> Any:  # noqa: ANN401
    """Reject ambiguous JSON before evaluating its schema."""
    return json.loads(
        path.read_bytes(), object_pairs_hook=_pairs, parse_constant=_constant
    )


def validate_bytes(data: bytes, content: dict[str, Any]) -> tuple[str, ...]:
    """Check syntax and order without normalizing or repairing original bytes."""
    _require(data.endswith(b"\n"), "missing terminal LF")
    _require(b"\r" not in data, "CR line ending")
    ids = tuple(data.decode("ascii").split("\n")[:-1])
    _require(
        all(WORK_ID.fullmatch(work) is not None for work in ids),
        "malformed or blank work ID",
    )
    _require(len(ids) == len(set(ids)), "duplicate work ID")
    _require(
        ids == tuple(sorted(ids)),
        "noncanonical order; do not reorder an existing version",
    )
    _require(len(ids) == content["line_count"], "line count mismatch")
    _require(len(data) == content["byte_size"], "byte size mismatch")
    _require(
        hashlib.sha256(data).hexdigest() == content["sha256"], "seed hash mismatch"
    )
    return ids


def resolve_seed(root: Path, seed_id: str) -> dict[str, Any]:
    """Return verified IDs and provenance; never accept a user-provided seed path."""
    root = root.resolve()
    schema = read_json(root / "schemas/seed-registry-v1.schema.json")
    registry = read_json(root / "seeds/registry.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(registry)
    entries = {entry["seed_id"]: entry for entry in registry["entries"]}
    _require(seed_id in entries, "unknown seed ID")
    entry = entries[seed_id]
    path = root.joinpath(*entry["path_parts"])
    _require(
        not any(part.is_symlink() for part in (path, *path.parents)),
        "symlink seed path",
    )
    ids = validate_bytes(path.read_bytes(), entry["content"])
    return {
        "seed_id": seed_id,
        "path_parts": entry["path_parts"],
        "sha256": entry["content"]["sha256"],
        "work_ids": ids,
    }


def main(argv: list[str] | None = None) -> int:
    """Print a verified selection as JSON, or fail without partial output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seed_id")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args(argv)
    print(json.dumps(resolve_seed(args.root, args.seed_id), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
