"""Fail-closed legislation completion evaluation from the canonical evidence index."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.legislation_evidence_index import (
    DEFAULT_INDEX,
    EvidenceIndexError,
    validate_evidence_index,
)

OUTPUT_EVIDENCE_PATH = Path(
    "evidence/migrations/corpus-legislation-nz/completion-evaluation-current.json"
)
DIMENSIONS = (
    "code_capability_migration",
    "operational_state_migration",
    "corpus_custody_recoverability",
    "publication_identity_migration",
)


def evaluate_completion(
    root: Path | None = None, *, index_path: Path = DEFAULT_INDEX
) -> tuple[bool, dict[str, Any]]:
    """Evaluate only schema-valid, fixity-bound evidence selected by the index."""
    base = (root or Path()).resolve()
    result: dict[str, Any] = {
        "schema_version": "archive-govt-nz.completion-evaluator/v2",
        "evaluated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence_index": index_path.as_posix(),
        "evidence_index_valid": False,
        "dimensions": {},
        "status": "incomplete",
        "blockers": [],
        "errors": [],
    }
    try:
        index = validate_evidence_index(base, index_path=index_path)
    except EvidenceIndexError as exc:
        result["errors"].append(f"evidence_index_invalid:{exc}")
        return False, result

    result["evidence_index_valid"] = True
    index_bytes = (base / index_path).read_bytes()
    result["evidence_index_sha256"] = hashlib.sha256(index_bytes).hexdigest()
    result["index_id"] = index["index_id"]
    result["target_commit"] = index["target_commit"]
    result["donor_commit"] = index["donor_commit"]
    entries = {
        cast("str", row["evidence_id"]): row
        for row in cast("list[dict[str, Any]]", index["entries"])
    }
    inputs = cast("dict[str, list[str]]", index["evaluator_inputs"])
    indexed_dimensions = cast("dict[str, dict[str, Any]]", index["dimensions"])

    for dimension in DIMENSIONS:
        source = indexed_dimensions[dimension]
        status = cast("str", source["status"])
        proof_ids = cast("list[str]", source["proof_ids"])
        selected = set(inputs.get(dimension, []))
        if status == "complete":
            eligible = bool(proof_ids) and all(
                proof_id in selected
                and proof_id in entries
                and entries[proof_id].get("classification") == "active"
                and dimension in entries[proof_id].get("claim_dimensions", [])
                and entries[proof_id].get("artefact_type") != "public_claim"
                for proof_id in proof_ids
            )
        else:
            eligible = bool(proof_ids) and all(
                proof_id in entries
                and entries[proof_id].get("classification") == status
                and dimension in entries[proof_id].get("claim_dimensions", [])
                for proof_id in proof_ids
            )
        result["dimensions"][dimension] = {
            "status": status,
            "proof_ids": proof_ids,
            "proof_eligible": eligible,
            "rationale": source["rationale"],
        }
        if status != "complete":
            result["blockers"].append(f"dimension_incomplete:{dimension}:{status}")
        if not eligible:
            result["blockers"].append(f"dimension_proof_ineligible:{dimension}")

    is_complete = (
        not result["errors"]
        and not result["blockers"]
        and set(result["dimensions"]) == set(DIMENSIONS)
    )
    result["status"] = "complete" if is_complete else "incomplete"
    return is_complete, result


def main() -> int:
    """Write the current evaluation without modifying historical evaluator output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path())
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output", type=Path, default=OUTPUT_EVIDENCE_PATH)
    args = parser.parse_args()

    is_complete, result = evaluate_completion(args.root, index_path=args.index)
    output = args.output if args.output.is_absolute() else args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "Legislation consolidation completion evaluation: "
        + ("COMPLETE" if is_complete else "INCOMPLETE")
    )
    for blocker in result["blockers"]:
        print(f"  [BLOCKER] {blocker}")
    for error in result["errors"]:
        print(f"  [ERROR] {error}")
    return 0 if is_complete else 1


if __name__ == "__main__":  # pragma: no cover - exercised as a script
    sys.exit(main())
