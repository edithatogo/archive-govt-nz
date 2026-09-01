"""Build fixity-bound historical legislation coverage evidence."""

# ruff: noqa: C901, EM101, EM102, ISC004, PLR0912, PLR0915, TRY003, TRY004

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

EXPECTED_BATCHES = 68
EXPECTED_CANDIDATES = 33_693
HTTP_OK = 200
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


def _load_array(path: Path) -> list[Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"expected JSON array: {path}")
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
    inventory_path = base / "final-state-merge/execution-02/package-inventory.json"
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
    inventory_document = _load_object(inventory_path)
    inventory = inventory_document.get("files")
    if not isinstance(inventory, list):
        raise ValueError("package inventory files missing")
    cas_entries = [
        entry
        for entry in inventory
        if isinstance(entry, dict)
        and isinstance(entry.get("path_parts"), list)
        and entry["path_parts"][:2] == ["cas", "sha256"]
    ]
    if len(cas_entries) != output["objects"]:
        raise ValueError("package inventory CAS count mismatch")
    for entry in cas_entries:
        parts = entry["path_parts"]
        digest = entry.get("sha256")
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or parts[-1] != digest
            or parts[-2] != digest[:2]
        ):
            raise ValueError("malformed package inventory CAS identity")
    return {
        "works": output["work_ids"],
        "state_records": output["records"],
        "cas_objects": output["objects"],
        "receipt_sha256": _sha256(receipt_path.read_bytes()),
        "readback_sha256": _sha256(readback_path.read_bytes()),
        "package_inventory_sha256": _sha256(inventory_path.read_bytes()),
        "package_inventory_files": len(inventory),
        "package_inventory_root_sha256": inventory_document.get("inventory_sha256"),
        "manifest_sha256": output.get("manifest_sha256"),
        "inventory_sha256": output.get("inventory_sha256"),
    }


def find_claim_inputs(claim_root: Path) -> list[dict[str, Any]]:
    """Enumerate claim-bearing inputs for later correction without editing them."""
    rows: list[dict[str, Any]] = []
    for path in sorted(item for item in claim_root.rglob("*") if item.is_file()):
        relative_path = path.relative_to(claim_root)
        if relative_path.is_relative_to(
            Path("evidence/migrations/corpus-legislation-nz/historical-coverage")
        ) or relative_path.is_relative_to(
            Path("conductor/tracks/legislation_historical_coverage_20260901")
        ):
            continue
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
            relative = str(relative_path)
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


def validate_claim_correction_manifest(
    manifest_path: Path, analyzer_inputs_path: Path, claim_root: Path
) -> dict[str, Any]:
    """Bind every correction entry to scanned inputs and exact current lines."""
    manifest = _load_object(manifest_path)
    analyzer = _load_object(analyzer_inputs_path)
    if manifest.get("schema_version") != (
        "archive-govt-nz.prompt14-claim-correction-manifest/v1"
    ):
        raise ValueError("unexpected claim correction manifest schema")
    inputs_digest = _sha256(analyzer_inputs_path.read_bytes())
    if manifest.get("analyzer_claim_inputs_sha256") != inputs_digest:
        raise ValueError("claim correction analyzer input hash mismatch")
    inputs = analyzer.get("inputs")
    claims = manifest.get("claims")
    if not isinstance(inputs, list) or not isinstance(claims, list):
        raise ValueError("claim correction inputs or claims missing")
    indexed: dict[str, dict[str, Any]] = {}
    for item in inputs:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("malformed analyzer claim input")
        if item["path"] in indexed:
            raise ValueError("duplicate analyzer claim input")
        indexed[item["path"]] = item
    claim_ids: set[str] = set()
    claim_locations: set[tuple[str, int]] = set()
    observed: dict[str, int] = dict.fromkeys(indexed, 0)
    trusted_root = claim_root.resolve()
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("malformed claim correction entry")
        claim_id = claim.get("claim_id")
        relative = claim.get("file")
        line_number = claim.get("line")
        if not isinstance(claim_id, str) or claim_id in claim_ids:
            raise ValueError("duplicate or malformed claim correction id")
        claim_ids.add(claim_id)
        if not isinstance(relative, str) or relative not in indexed:
            raise ValueError("claim correction file absent from analyzer inputs")
        if isinstance(line_number, bool) or not isinstance(line_number, int):
            raise ValueError("claim correction line is malformed")
        location = (relative, line_number)
        if location in claim_locations:
            raise ValueError("duplicate claim correction source line")
        claim_locations.add(location)
        source = claim_root / relative
        if source.is_symlink() or not source.resolve().is_relative_to(trusted_root):
            raise ValueError("claim correction source escapes trusted root")
        raw = source.read_bytes()
        expected_sha256 = indexed[relative].get("sha256")
        if (
            _sha256(raw) != expected_sha256
            or claim.get("source_sha256") != expected_sha256
        ):
            raise ValueError("claim correction source hash mismatch")
        try:
            lines = raw.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise ValueError("claim correction source is not UTF-8") from exc
        if line_number < 1 or line_number > len(lines):
            raise ValueError("claim correction line is out of range")
        text = lines[line_number - 1]
        if (
            claim.get("text") != text.strip()
            or claim.get("source_line_sha256") != _sha256(text.encode("utf-8"))
            or _CLAIM_RE.search(text) is None
        ):
            raise ValueError("claim correction text does not match source line")
        observed[relative] += len(_CLAIM_RE.findall(text))
    if any(
        observed[path] > int(item.get("occurrences", -1))
        for path, item in indexed.items()
    ):
        raise ValueError("claim correction occurrence coverage mismatch")
    scan = manifest.get("scan_contract")
    if not isinstance(scan, dict) or scan.get("occurrence_count") != len(claims):
        raise ValueError("claim correction scan count mismatch")
    return {
        "status": "passed",
        "claims_verified": len(claims),
        "source_files_verified": len(indexed),
        "analyzer_claim_inputs_sha256": inputs_digest,
        "manifest_sha256": _sha256(manifest_path.read_bytes()),
    }


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
    observed_at = document.get("observed_at")
    if not isinstance(observed_at, str):
        raise ValueError("public observation timestamp missing")
    try:
        parsed_observed_at = datetime.fromisoformat(observed_at)
    except ValueError as exc:
        raise ValueError("invalid public observation timestamp") from exc
    if parsed_observed_at.tzinfo is None:
        raise ValueError("public observation timestamp must include a timezone")
    if not isinstance(document.get("method"), str) or not document["method"].strip():
        raise ValueError("public observation method missing")
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
        platform = surface.get("platform")
        api_url = surface.get("api_url")
        if platform not in {"huggingface", "zenodo"}:
            raise ValueError("unsupported public observation platform")
        if (
            not isinstance(api_url, str)
            or urlparse(api_url).scheme != "https"
            or surface.get("http_status") != HTTP_OK
        ):
            raise ValueError("public observation identity or status invalid")
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
        if platform == "huggingface":
            prefix = "https://huggingface.co/api/datasets/"
            repository = identifier.removeprefix("huggingface:")
            revision = surface.get("observed_revision")
            if (
                not identifier.startswith("huggingface:")
                or not repository
                or api_url != prefix + repository
                or surface.get("public") is not True
                or surface.get("disabled") is not False
                or not isinstance(revision, str)
                or re.fullmatch(r"[0-9a-f]{40}", revision) is None
            ):
                raise ValueError("invalid Hugging Face observation identity")
            classified = 0
            for key in ("parquet_files", "raw_xml_files", "records_jsonl_files"):
                count = inventory.get(key)
                if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                    raise ValueError("invalid Hugging Face file inventory")
                classified += count
            if classified > files:
                raise ValueError("Hugging Face file inventory exceeds total")
        else:
            record_id = surface.get("record_id")
            listed = inventory.get("files")
            if (
                not isinstance(record_id, str)
                or identifier != f"zenodo:{record_id}"
                or api_url != f"https://zenodo.org/api/records/{record_id}"
                or surface.get("access_right") != "open"
                or not isinstance(listed, list)
                or len(listed) != files
            ):
                raise ValueError("invalid Zenodo observation identity or inventory")
            for item in listed:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get("key"), str)
                    or re.fullmatch(r"md5:[0-9a-f]{32}", str(item.get("checksum")))
                    is None
                    or isinstance(item.get("size_bytes"), bool)
                    or not isinstance(item.get("size_bytes"), int)
                    or item["size_bytes"] < 0
                ):
                    raise ValueError("invalid Zenodo file inventory item")
            manifest = surface.get("manifest")
            if (
                not isinstance(manifest, dict)
                or manifest.get("http_status") != HTTP_OK
                or manifest.get("reported_record_count") != rows
            ):
                raise ValueError("invalid Zenodo manifest accounting")
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
                if (
                    isinstance(path_parts, list)
                    and path_parts
                    and all(
                        isinstance(part, str)
                        and part not in {"", ".", ".."}
                        and Path(part).name == part
                        for part in path_parts
                    )
                    and isinstance(content, dict)
                ):
                    seed_path = claim_root.joinpath(*path_parts)
                    expected = content.get("sha256")
                    trusted_root = claim_root.resolve()
                    seed_is_trusted = (
                        not seed_path.is_symlink()
                        and seed_path.is_file()
                        and seed_path.resolve().is_relative_to(trusted_root)
                    )
                    seed_raw = seed_path.read_bytes() if seed_is_trusted else b""
                    seed_ids = seed_raw.decode("ascii").splitlines() if seed_raw else []
                    if (
                        entry.get("seed_id") == "historical-work-ids-0001"
                        and seed_is_trusted
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
            "candidate_ids_outside_governed_subset": (
                candidates["candidate_ids"] - governed_reviewed
                if governed_reviewed is not None and reviewed_is_candidate_subset
                else None
            ),
            "candidate_ids_outside_governed_subset_basis": (
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
