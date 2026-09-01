"""Build fixity-bound historical legislation coverage evidence."""

# ruff: noqa: C901, EM101, EM102, ISC004, PLR0912, TRY003, TRY004

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

EXPECTED_BATCHES = 68
EXPECTED_CANDIDATES = 33_693
EXPECTED_CANDIDATE_SHA256 = (
    "6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b"
)
_BATCH_RE = re.compile(r"historical-work-ids-(\d{4})\.txt")
_CLAIM_RE = re.compile(r"33,?693|33693")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _evidence_base(root: Path) -> Path:
    nested = root / "evidence/migrations/corpus-legislation-nz"
    return nested if nested.is_dir() else root


def audit_batches(donor_root: Path) -> dict[str, Any]:
    """Verify the exact candidate partition."""
    if donor_root.is_symlink():
        raise ValueError("donor root must not be a symlink")
    batch_dir = donor_root / "seeds/reviewed"
    paths = sorted(batch_dir.glob("historical-work-ids-*.txt"))
    expected_names = [f"historical-work-ids-{index:04d}.txt" for index in range(1, 69)]
    if [path.name for path in paths] != expected_names:
        raise ValueError("historical batch set is not exactly 0001 through 0068")

    all_ids: list[str] = []
    batches: list[dict[str, Any]] = []
    raw_parts: list[bytes] = []
    for index, path in enumerate(paths, start=1):
        if path.is_symlink() or not path.resolve().is_relative_to(donor_root.resolve()):
            raise ValueError("batch escapes trusted donor root")
        match = _BATCH_RE.fullmatch(path.name)
        if match is None or int(match.group(1)) != index:
            raise ValueError(f"noncanonical batch name: {path.name}")
        raw = path.read_bytes()
        if b"\r" in raw or not raw.endswith(b"\n"):
            raise ValueError(f"batch must use LF with terminal newline: {path.name}")
        try:
            text = raw.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError(f"batch is not ASCII: {path.name}") from exc
        ids = text.splitlines()
        expected_count = 193 if index == EXPECTED_BATCHES else 500
        if len(ids) != expected_count:
            raise ValueError(f"unexpected line count in {path.name}")
        if any(not item or item.startswith("#") for item in ids):
            raise ValueError(f"blank or comment line in {path.name}")
        if ids != sorted(set(ids)):
            raise ValueError(f"batch is not sorted and unique: {path.name}")
        raw_parts.append(raw)
        all_ids.extend(ids)
        batches.append(
            {
                "batch_id": f"{index:04d}",
                "path": str(path.relative_to(donor_root)),
                "candidate_ids": len(ids),
                "byte_size": len(raw),
                "sha256": _sha256(raw),
                "first_id": ids[0],
                "last_id": ids[-1],
            }
        )
    if len(all_ids) != EXPECTED_CANDIDATES or len(set(all_ids)) != len(all_ids):
        raise ValueError("aggregate candidate count or uniqueness mismatch")
    if all_ids != sorted(all_ids):
        raise ValueError("aggregate candidate ordering mismatch")
    concatenated = b"".join(raw_parts)
    if _sha256(concatenated) != EXPECTED_CANDIDATE_SHA256:
        raise ValueError("canonical candidate concatenation hash mismatch")

    inventory = donor_root / "seeds/work_ids.txt"
    inventory_raw = inventory.read_bytes()
    candidate_lines = [
        line
        for line in inventory_raw.decode("utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    if candidate_lines != all_ids:
        raise ValueError("comment-filtered inventory differs from reviewed batches")
    return {
        "batch_count": len(paths),
        "candidate_ids": len(all_ids),
        "candidate_sha256": _sha256(concatenated),
        "candidate_bytes": len(concatenated),
        "inventory_file_sha256": _sha256(inventory_raw),
        "inventory_physical_lines": len(inventory_raw.splitlines()),
        "inventory_comment_or_blank_lines": len(inventory_raw.splitlines())
        - len(candidate_lines),
        "batches": batches,
        "ids": all_ids,
    }


def audit_target_state(target_evidence_root: Path) -> dict[str, Any]:
    """Read the independently verified canonical merge receipt without inference."""
    if target_evidence_root.is_symlink():
        raise ValueError("target evidence root must not be a symlink")
    base = _evidence_base(target_evidence_root)
    receipt_path = (
        base / "final-state-merge/execution-02/final-state-merge-receipt.json"
    )
    readback_path = base / "final-state-merge/execution-02/independent-readback.json"
    receipt = _load_object(receipt_path)
    readback = _load_object(readback_path)
    if receipt.get("status") != "passed" or readback.get("status") != "passed":
        raise ValueError("canonical target state lacks passed receipt and readback")
    output = receipt.get("output")
    if not isinstance(output, dict) or output != readback.get("output"):
        raise ValueError("canonical receipt and readback output mismatch")
    required = ("records", "work_ids", "objects")
    if any(
        isinstance(output.get(key), bool) or not isinstance(output.get(key), int)
        for key in required
    ):
        raise ValueError("canonical target counts are missing or malformed")
    if len({output[key] for key in required}) != 1:
        raise ValueError("canonical work, record, and object counts differ")
    parents = receipt.get("parents")
    if (
        not isinstance(parents, list)
        or sum(int(parent["records"]) for parent in parents) != output["records"]
    ):
        raise ValueError("canonical parent record accounting mismatch")
    return {
        "works": output["work_ids"],
        "state_records": output["records"],
        "cas_objects": output["objects"],
        "receipt_sha256": _sha256(receipt_path.read_bytes()),
        "readback_sha256": _sha256(readback_path.read_bytes()),
        "manifest_sha256": output.get("manifest_sha256"),
        "inventory_sha256": output.get("inventory_sha256"),
    }


def find_claim_inputs(claim_root: Path) -> list[dict[str, Any]]:
    """Enumerate claim-bearing inputs for later correction without editing them."""
    rows: list[dict[str, Any]] = []
    for path in sorted(item for item in claim_root.rglob("*") if item.is_file()):
        if {".git", ".venv", "build"}.intersection(
            path.parts
        ) or path.suffix.lower() not in {
            ".json",
            ".md",
            ".yml",
            ".yaml",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        matches = list(_CLAIM_RE.finditer(text))
        if matches:
            relative = str(path.relative_to(claim_root))
            rows.append(
                {
                    "path": relative,
                    "sha256": _sha256(path.read_bytes()),
                    "occurrences": len(matches),
                    "historical_or_imported": relative.startswith("conductor/archive/")
                    or "invalidated" in text.lower()
                    or relative.endswith("parity/historical-batch-parity.json"),
                }
            )
    return rows


def audit_public_observations(claim_root: Path) -> dict[str, Any]:
    """Validate the retained, surface-specific public observation receipt."""
    path = (
        claim_root
        / "evidence/migrations/corpus-legislation-nz/historical-coverage"
        / "public-surface-observations.json"
    )
    document = _load_object(path)
    if document.get("schema_version") != (
        "archive-govt-nz.prompt14-public-surface-observations/v1"
    ):
        raise ValueError("unexpected public observation schema")
    surfaces = document.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ValueError("public observation surfaces missing")
    identifiers: set[str] = set()
    for surface in surfaces:
        if not isinstance(surface, dict) or not isinstance(
            surface.get("surface_id"), str
        ):
            raise ValueError("malformed public observation surface")
        identifier = surface["surface_id"]
        if identifier in identifiers:
            raise ValueError("duplicate public observation surface")
        identifiers.add(identifier)
        digest = surface.get("api_response_sha256")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("invalid public observation response hash")
        rows = surface.get("published_row_count")
        if rows is not None and (
            isinstance(rows, bool) or not isinstance(rows, int) or rows < 0
        ):
            raise ValueError("invalid public row count")
        inventory = surface.get("file_inventory")
        if not isinstance(inventory, dict):
            raise ValueError("public file inventory missing")
        files = inventory.get("total_files")
        if isinstance(files, bool) or not isinstance(files, int) or files < 0:
            raise ValueError("invalid public file count")
    return {
        "receipt_sha256": _sha256(path.read_bytes()),
        "surfaces": surfaces,
        "aggregate_rule": "surface_specific_do_not_sum",
    }


def build_report(
    donor_root: Path, target_evidence_root: Path, claim_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a report that never converts unknown outcomes into zeroes."""
    candidates = audit_batches(donor_root)
    target = audit_target_state(target_evidence_root)
    public_observations = audit_public_observations(claim_root)
    registry_path = claim_root / "seeds/registry.json"
    registry_evidence: dict[str, Any] | None = None
    governed_reviewed: int | None = None
    reviewed_is_candidate_subset = False
    if registry_path.is_file():
        registry = _load_object(registry_path)
        entries = registry.get("entries")
        if isinstance(entries, list) and len(entries) == 1:
            entry = entries[0]
            count = entry.get("candidate_count")
            if isinstance(count, int) and not isinstance(count, bool):
                path_parts = entry.get("path_parts")
                content = entry.get("content")
                if isinstance(path_parts, list) and isinstance(content, dict):
                    seed_path = claim_root.joinpath(*path_parts)
                    expected = content.get("sha256")
                    seed_raw = seed_path.read_bytes() if seed_path.is_file() else b""
                    seed_ids = seed_raw.decode("ascii").splitlines() if seed_raw else []
                    if (
                        entry.get("seed_id") == "historical-work-ids-0001"
                        and seed_path.is_file()
                        and _sha256(seed_raw) == expected
                        and content.get("line_count") == count == len(seed_ids)
                        and content.get("unique") is True
                        and seed_ids == sorted(set(seed_ids))
                        and set(seed_ids).issubset(candidates["ids"])
                    ):
                        governed_reviewed = count
                        reviewed_is_candidate_subset = True
                        registry_evidence = {
                            "kind": "target_seed_registry_and_bytes",
                            "registry_sha256": _sha256(registry_path.read_bytes()),
                            "seed_sha256": expected,
                            "status": "verified",
                        }
    state_works = target["works"]
    candidate_evidence = {
        "kind": "primary_bytes",
        "sha256": candidates["candidate_sha256"],
        "status": "verified",
    }
    state_evidence = {
        "kind": "canonical_state_receipt_and_readback",
        "receipt_sha256": target["receipt_sha256"],
        "readback_sha256": target["readback_sha256"],
        "status": "verified",
    }
    report = {
        "schema_version": "archive-govt-nz.legislation-historical-coverage/v1",
        "status": "verified_with_unknown_outcomes",
        "populations": {
            "candidate_ids": {
                "value": candidates["candidate_ids"],
                "evidence": candidate_evidence,
            },
            "target_governed_reviewed_ids": {
                "value": governed_reviewed,
                "evidence": registry_evidence,
            },
            "attempted_works": {"value": None, "evidence": None},
            "successfully_retrieved_works": {"value": None, "evidence": None},
            "canonical_state_works": {"value": state_works, "evidence": state_evidence},
            "canonical_state_records": {
                "value": target["state_records"],
                "evidence": state_evidence,
            },
            "expressions": {"value": None, "evidence": None},
            "manifestations": {"value": None, "evidence": None},
            "normalised_records": {"value": None, "evidence": None},
            "cas_objects": {"value": target["cas_objects"], "evidence": state_evidence},
            "published_rows": {"value": None, "evidence": None},
            "published_files": {"value": None, "evidence": None},
            "metadata_only_entries": {"value": None, "evidence": None},
            "failed": {"value": None, "evidence": None},
            "unavailable": {"value": None, "evidence": None},
            "deferred": {"value": None, "evidence": None},
            "rights_blocked": {"value": None, "evidence": None},
            "not_attempted": {"value": None, "evidence": None},
        },
        "candidate_inventory": {
            key: value for key, value in candidates.items() if key != "ids"
        },
        "target_state": target,
        "publication_surfaces": public_observations,
        "reconciliation": {
            "canonical_state_candidate_overlap": None,
            "canonical_state_outside_candidate_inventory": None,
            "candidate_disposition_unknown": (
                candidates["candidate_ids"] - governed_reviewed
                if governed_reviewed is not None and reviewed_is_candidate_subset
                else None
            ),
            "candidate_disposition_unknown_basis": (
                "Only the governed 500-ID subset is bound to acquired donor state; "
                "the remaining candidates have no campaign disposition evidence."
            ),
            "candidate_completeness_proven": False,
            "publication_completeness_proven": False,
            "mismatch_ledger": [],
        },
        "limitations": [
            "Candidate membership does not prove attempt, acquisition, publication, "
            "or legislative completeness.",
            "Absence from verified target state is not classified as unavailable "
            "or not attempted.",
            "Historical generated parity receipts are invalidated and are not "
            "coverage evidence.",
        ],
    }
    corrections = {
        "schema_version": "archive-govt-nz.legislation-coverage-correction-inputs/v1",
        "candidate_claim": 33_693,
        "replacement_acquired_count": None,
        "canonical_state_works": state_works,
        "inputs": find_claim_inputs(claim_root),
    }
    return report, corrections


def render_markdown(report: dict[str, Any]) -> str:
    """Render population counts without collapsing unknowns to zero."""
    populations = report["populations"]
    rows = [
        "# Historical legislation coverage",
        "",
        "| Population | Verified count |",
        "|---|---:|",
    ]
    rows.extend(
        f"| {name.replace('_', ' ')} | "
        f"{'unknown' if item['value'] is None else format(item['value'], ',')} |"
        for name, item in populations.items()
    )
    rows.extend(
        [
            "",
            "The 33,693 IDs are search-derived candidates. They are not a "
            "completeness denominator.",
            "",
        ]
    )
    rows.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(rows) + "\n"


def main() -> None:
    """Run the explicit-input historical coverage analysis."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--donor-root", type=Path, required=True)
    parser.add_argument("--target-evidence-root", type=Path, required=True)
    parser.add_argument("--claim-root", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--correction-output", type=Path, required=True)
    args = parser.parse_args()
    report, corrections = build_report(
        args.donor_root, args.target_evidence_root, args.claim_root
    )
    for path in (args.json_output, args.markdown_output, args.correction_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    args.correction_output.write_text(
        json.dumps(corrections, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
