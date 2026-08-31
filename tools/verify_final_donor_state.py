"""Authenticate one bounded donor ZIP and verify state without canonical writes.

The caller must obtain metadata through GitHub and independently pin expectations.
This offline tool never downloads, publishes, or selects a supposedly latest run.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import stat
import zipfile
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, NoReturn, cast
from urllib.parse import urlsplit

import blake3

from archive_govt_nz.domains.legislation.models import validate_legislation_record

if TYPE_CHECKING:
    from collections.abc import Sequence
ROOT = Path(__file__).resolve().parents[1]
STATE = "target/build/legislation-state/"
SEED = "seeds/reviewed/historical-work-ids-0001.txt"
CAS = STATE + "cas/sha256/"
RECEIPTS = (
    "harvest",
    "reconciliation",
    "canary-harvest",
    "canary-reconciliation",
    "weekly-harvest",
    "weekly-reconciliation",
    "weekly-state-lineage",
    "incoming-cas-verification",
)
DOCUMENTS = {STATE + x + ".json" for x in ("manifest", "checkpoint")}
DOCUMENTS |= {STATE + "receipts/" + x + ".json" for x in RECEIPTS}
MAX_ZIP = 64 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_MEMBER = 64 * 1024 * 1024
MAX_FILES = 4096
MANIFESTATION_PARTS = 6


class VerificationError(ValueError):
    """A stable mismatch code, never untrusted payload text."""


def require(*, condition: bool, code: str) -> None:
    """Fail closed on one violated invariant."""
    if not condition:
        raise VerificationError(code)


def equal(actual: object, expected: object, code: str) -> None:
    """Reject type confusion as well as unequal values."""
    require(condition=type(actual) is type(expected) and actual == expected, code=code)


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys before they can hide conflicting evidence."""
    result: dict[str, Any] = {}
    for key, value in items:
        require(condition=key not in result, code="json_duplicate_key")
        result[key] = value
    return result


def reject_constant(_value: str) -> NoReturn:
    """Reject non-finite JSON numbers without rejecting ordinary string values."""
    message = "json_nonfinite"
    raise VerificationError(message)


def load(data: bytes) -> dict[str, Any]:
    """Load a JSON object with no non-finite numbers or duplicate keys."""
    obj = json.loads(data, object_pairs_hook=pairs, parse_constant=reject_constant)
    require(condition=isinstance(obj, dict), code="json_object_required")
    return obj


def sha(data: bytes) -> str:
    """Return the byte-level SHA-256, not a semantic document root."""
    return hashlib.sha256(data).hexdigest()


def check_metadata(meta: dict[str, Any], expected: dict[str, Any]) -> None:
    """Bind live run/artifact identities to separately audited expectations."""
    artifact, run = (meta["artifact"], meta["run"])
    for key in ("id", "name", "digest"):
        equal(artifact[key], expected["artifact"][key], "artifact_" + key)
    equal(artifact["expired"], expected=False, code="artifact_expired")
    for key in ("id", "name", "path", "head_sha"):
        equal(run[key], expected["run"][key], "run_" + key)
    equal(run["status"], "completed", "run_status")
    equal(run["conclusion"], "success", "run_conclusion")
    equal(artifact["workflow_run"]["id"], run["id"], "artifact_run")
    equal(artifact["workflow_run"]["head_sha"], run["head_sha"], "artifact_head")
    equal(
        artifact["workflow_run"]["repository_id"],
        expected["repository_id"],
        "artifact_repository",
    )
    require(
        condition=type(run["run_attempt"]) is int and run["run_attempt"] > 0,
        code="run_attempt",
    )


def unpack(archive: Path, meta: dict[str, Any], quarantine: Path) -> dict[str, bytes]:
    """Check outer hash, ZIP bounds and all paths before creating quarantine."""
    require(condition=not archive.is_symlink(), code="archive_symlink")
    with archive.open("rb") as source:
        raw = source.read(MAX_ZIP + 1)
    require(condition=len(raw) <= MAX_ZIP, code="zip_size_limit")
    equal(len(raw), meta["artifact"]["size_in_bytes"], "zip_size")
    equal("sha256:" + sha(raw), meta["artifact"]["digest"], "zip_digest")
    require(
        condition=not quarantine.resolve().is_relative_to(ROOT),
        code="canonical_workspace_forbidden",
    )
    require(
        condition=not quarantine.exists() and (not quarantine.is_symlink()),
        code="quarantine_exists",
    )
    files: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        entries = bundle.infolist()
        require(condition=0 < len(entries) <= MAX_FILES, code="zip_member_count")
        require(
            condition=sum(x.file_size for x in entries) <= MAX_EXPANDED,
            code="zip_expansion_limit",
        )
        names: set[str] = set()
        for entry in entries:
            name = entry.filename
            path = PurePosixPath(name)
            require(
                condition=not path.is_absolute() and path.as_posix() == name,
                code="zip_path",
            )
            require(
                condition=not any(x in {"", ".", ".."} for x in name.split("/")),
                code="zip_path",
            )
            require(
                condition=not any(x in name for x in ("\\", ":", "\x00")),
                code="zip_path",
            )
            require(condition=name.casefold() not in names, code="zip_duplicate")
            names.add(name.casefold())
            require(
                condition=stat.S_IFMT(entry.external_attr >> 16) in {0, stat.S_IFREG},
                code="zip_member_type",
            )
            require(condition=not entry.flag_bits & 1, code="zip_encrypted")
            require(
                condition=0 <= entry.file_size <= MAX_MEMBER, code="zip_member_limit"
            )
            require(
                condition=name == SEED or name in DOCUMENTS or name.startswith(CAS),
                code="zip_unexpected_member",
            )
        for entry in entries:
            files[entry.filename] = bundle.read(entry)
    require(
        condition=set(DOCUMENTS) | {SEED} <= files.keys(), code="critical_file_missing"
    )
    quarantine.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = quarantine / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        equal(sha(path.read_bytes()), sha(data), "extraction_readback")
        path.chmod(292)
    return files


def identifiers(value: object, code: str) -> list[str]:
    """Require a nonempty canonical set encoded as a sorted string list."""
    require(condition=isinstance(value, list) and bool(value), code=code)
    values = cast("list[str]", value)
    require(
        condition=all(isinstance(x, str) and x and x == x.strip() for x in values),
        code=code,
    )
    require(condition=values == sorted(set(values)), code=code)
    return values


def check_roots(
    docs: dict[str, Any], seed: list[str], expected: dict[str, Any]
) -> list[dict[str, Any]]:
    """Recompute manifest/inventory roots and all checkpoint accounting."""
    manifest, checkpoint = (docs["manifest"], docs["checkpoint"])
    equal(
        manifest["schema_version"],
        "archive-govt-nz.legislation-manifest/v1",
        "manifest_schema",
    )
    equal(
        checkpoint["schema_version"],
        "archive-govt-nz.legislation-checkpoint/v1",
        "checkpoint_schema",
    )
    records = manifest["records"]
    require(
        condition=isinstance(records, list) and bool(records), code="manifest_records"
    )
    require(
        condition=all(isinstance(x, dict) for x in records),
        code="manifest_record_type",
    )
    root = hashlib.sha256()
    for record in sorted(records, key=lambda x: x["manifestation_id"]):
        root.update(json.dumps(record, sort_keys=True).encode())
    equal(root.hexdigest(), manifest["manifest_sha256"], "manifest_root")
    equal(root.hexdigest(), expected["manifest_sha256"], "audited_manifest_root")
    inventory = identifiers(manifest["discovered_work_ids"], "discovered_ids")
    equal(inventory, seed, "seed_manifest_ids")
    inventory_root = sha(json.dumps(inventory, separators=(",", ":")).encode())
    equal(manifest["discovered_inventory_sha256"], inventory_root, "inventory_root")
    equal(manifest["discovered_works_count"], len(inventory), "inventory_count")
    equal(manifest["total_records"], len(records), "manifest_count")
    equal(
        identifiers(checkpoint["processed_work_ids"], "processed_ids"),
        seed,
        "checkpoint_ids",
    )
    equal(checkpoint["last_processed_index"], len(seed), "checkpoint_index")
    equal(checkpoint["total_records_preserved"], len(records), "checkpoint_count")
    for field in ("manifest_sha256", "discovered_inventory_sha256"):
        equal(checkpoint["metadata"][field], manifest[field], "checkpoint_" + field)
    require(
        condition=isinstance(checkpoint["metadata"]["conditional_requests"], dict),
        code="checkpoint_conditionals",
    )
    require(
        condition=datetime.fromisoformat(checkpoint["last_updated"]).tzinfo is not None,
        code="checkpoint_timestamp",
    )
    batches = checkpoint["completed_batches"]
    require(
        condition=isinstance(batches, list)
        and all(isinstance(x, str) and x.strip() == x and x for x in batches)
        and len(set(batches)) == len(batches),
        code="checkpoint_batches",
    )
    equal(manifest["run_id"], expected["batch_id"], "manifest_run")
    require(condition=expected["batch_id"] in batches, code="checkpoint_batch_missing")
    return records


def manifestation_identity(value: str) -> tuple[str, str, str]:
    """Parse explicit files or the donor's dated HTML fallback page."""
    uri = urlsplit(value)
    require(
        condition=uri.scheme == "https" and uri.netloc == "www.legislation.govt.nz",
        code="manifestation_origin",
    )
    require(condition=not uri.query and not uri.fragment, code="manifestation_query")
    parts = uri.path.removeprefix("/").split("/")
    if len(parts) == MANIFESTATION_PARTS + 1 and parts[-1] == "":
        parts = parts[:-1]
        version, extension = parts[-1], "html"
    else:
        version, _, extension = parts[-1].rpartition(".")
    require(
        condition=len(parts) == MANIFESTATION_PARTS and parts[-2] == "en",
        code="manifestation_path",
    )
    equal(date.fromisoformat(version).isoformat(), version, "expression_date")
    require(condition=extension in {"xml", "html", "pdf"}, code="manifestation_format")
    return "_".join(parts[:4]), version, extension


def check_identity(record: dict[str, Any]) -> str:
    """Validate W/E/M linkage while preserving preferred and retrieved formats."""
    require(condition=not validate_legislation_record(record), code="record_schema")
    work, version, extension = manifestation_identity(record["manifestation_id"])
    equal(record["work_id"], work, "work_identity")
    equal(record["expression_id"], work + "_en_" + version, "expression_identity")
    canonical_work, canonical_version, _ = manifestation_identity(
        record["canonical_uri"]
    )
    equal((canonical_work, canonical_version), (work, version), "canonical_uri")
    require(condition=bool(record["document_id"]), code="document_id")
    return extension


def check_objects(
    files: dict[str, bytes], records: list[dict[str, Any]], seed: list[str]
) -> dict[str, Any]:
    """Verify every referenced object, aliases, size and optional media claims."""
    for field in ("work_id", "expression_id", "manifestation_id", "document_id"):
        values = [x[field] for x in records]
        equal(len(set(values)), len(values), "duplicate_" + field)
    equal(sorted(x["work_id"] for x in records), seed, "record_work_ids")
    objects: dict[str, Any] = {}
    for record in records:
        extension = check_identity(record)
        digest = record["raw_cas_hash_sha256"]
        path = CAS + digest[:2] + "/" + digest
        require(condition=path in files, code="cas_missing")
        data = files[path]
        equal(sha(data), digest, "cas_sha256")
        b3 = blake3.blake3(data).hexdigest()
        equal(record["raw_cas_hash_blake3"], b3, "cas_blake3")
        equal(record["byte_size"], len(data), "cas_size")
        equal(record.get("raw_sha256", digest), digest, "sha256_alias")
        equal(record.get("raw_blake3", b3), b3, "blake3_alias")
        if "media_type" in record:
            signatures = {
                "application/xml": b"<",
                "text/xml": b"<",
                "text/html": b"<",
                "application/pdf": b"%PDF-",
            }
            media = record["media_type"]
            formats = {
                "xml": {"application/xml", "text/xml"},
                "html": {"text/html"},
                "pdf": {"application/pdf"},
            }
            require(condition=media in formats[extension], code="media_type_extension")
            require(
                condition=data.removeprefix(b"\xef\xbb\xbf")
                .lstrip()
                .startswith(signatures[media]),
                code="media_type_mismatch",
            )
        require(condition=digest not in objects, code="cas_shared_object")
        objects[digest] = {"sha256": digest, "blake3": b3, "size_bytes": len(data)}
    equal(
        {x for x in files if x.startswith(CAS)},
        {CAS + x[:2] + "/" + x for x in objects},
        "cas_unreferenced",
    )
    return objects


def check_receipts(
    docs: dict[str, Any],
    seed: list[str],
    objects: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    """Cross-check weekly receipts and incoming object inventory against bytes."""
    count = len(seed)
    manifest = docs["manifest"]
    harvest, reconciliation, lineage = (
        docs[x]
        for x in ("weekly-harvest", "weekly-reconciliation", "weekly-state-lineage")
    )
    equal(
        harvest["schema_version"],
        "archive-govt-nz.legislation-harvest-receipt/v2",
        "harvest_schema",
    )
    equal(harvest["batch_id"], expected["batch_id"], "harvest_batch")
    equal(harvest["work_ids"], seed, "harvest_ids")
    for field in (
        "max_works",
        "works_attempted",
        "records_preserved",
        "discovered_works_count",
    ):
        equal(harvest[field], count, "harvest_" + field)
    for field in ("force_resync", "state_committed"):
        equal(harvest[field], expected=True, code="harvest_" + field)
    require(
        condition=harvest["outcome"] in {"changed", "no_change"}, code="harvest_outcome"
    )
    equal(harvest["errors"], [], "harvest_errors")
    equal(harvest["manifest_sha256"], manifest["manifest_sha256"], "harvest_root")
    equal(
        reconciliation["schema_version"],
        "archive-govt-nz.legislation-one-batch-reconciliation/v1",
        "reconciliation_schema",
    )
    for field, value in {
        "batch_id": expected["batch_id"],
        "batch_sha256": expected["seed_sha256"],
        "batch_file": "historical-work-ids-0001.txt",
        "status": "passed",
        "mismatch_count": 0,
        "mismatches": [],
    }.items():
        equal(reconciliation[field], value, "reconciliation_" + field)
    for field in (
        "batch_work_ids_count",
        "cas_objects_verified",
        "checkpoint_processed_ids_count",
        "discovered_works_count",
        "manifest_total_records",
        "reconciled_work_ids_count",
        "selected_records_count",
    ):
        equal(reconciliation[field], count, "reconciliation_" + field)
    for field in ("manifest_sha256", "discovered_inventory_sha256"):
        equal(reconciliation[field], manifest[field], "reconciliation_" + field)
    equal(
        lineage["schema_version"],
        "corpus-legislation-nz.weekly-state-lineage/v1",
        "lineage_schema",
    )
    for field in ("prior_run_id", "prior_artifact"):
        equal(lineage[field], expected[field], "lineage_" + field)
    equal(lineage["manifest_sha256"], manifest["manifest_sha256"], "lineage_root")
    equal(lineage["discovered_works_count"], count, "lineage_count")
    incoming = docs["incoming-cas-verification"]
    equal(
        incoming["schema_version"],
        "archive-govt-nz.object-integrity/v1",
        "incoming_schema",
    )
    for field, value in {
        "object_count": len(objects),
        "verified": len(objects),
        "failed": 0,
    }.items():
        equal(incoming[field], value, "incoming_" + field)
    equal(len(incoming["results"]), len(objects), "incoming_results_count")
    seen: set[str] = set()
    for entry in incoming["results"]:
        digest = entry["object_id"].removeprefix("sha256:")
        equal(entry["object_id"], "sha256:" + digest, "incoming_algorithm")
        require(
            condition=digest in objects and digest not in seen, code="incoming_identity"
        )
        seen.add(digest)
        equal(entry["status"], "verified", "incoming_status")
        equal(entry["bytes"], objects[digest]["size_bytes"], "incoming_size")
        equal(entry["blake3"], objects[digest]["blake3"], "incoming_blake3")


def check_retained_receipts(docs: dict[str, Any], seed: list[str]) -> None:
    """Check retained bootstrap/canary receipts without claiming parent recovery."""
    for prefix in ("", "canary-"):
        harvest = docs[prefix + "harvest"]
        reconciliation = docs[prefix + "reconciliation"]
        ids = identifiers(harvest["work_ids"], "retained_work_ids")
        require(condition=set(ids) <= set(seed), code="retained_inventory_subset")
        equal(
            harvest["schema_version"],
            "archive-govt-nz.legislation-harvest-receipt/v2",
            "retained_harvest_schema",
        )
        equal(
            reconciliation["schema_version"],
            "archive-govt-nz.legislation-one-batch-reconciliation/v1",
            "retained_reconciliation_schema",
        )
        equal(
            harvest["state_committed"], expected=True, code="retained_state_committed"
        )
        equal(harvest["errors"], [], "retained_errors")
        equal(reconciliation["batch_id"], harvest["batch_id"], "retained_batch_id")
        equal(
            reconciliation["batch_sha256"],
            sha(("\n".join(ids) + "\n").encode()),
            "retained_seed_digest",
        )
        for field in ("works_attempted", "records_preserved"):
            equal(harvest[field], len(ids), "retained_" + field)
        for field in (
            "batch_work_ids_count",
            "reconciled_work_ids_count",
            "selected_records_count",
            "cas_objects_verified",
        ):
            equal(reconciliation[field], len(ids), "retained_" + field)
        for field, value in {
            "status": "passed",
            "mismatch_count": 0,
            "mismatches": [],
        }.items():
            equal(reconciliation[field], value, "retained_" + field)
        equal(
            harvest["manifest_sha256"],
            docs["manifest"]["manifest_sha256"],
            "retained_harvest_root",
        )
        equal(
            reconciliation["manifest_sha256"],
            docs["manifest"]["manifest_sha256"],
            "retained_reconciliation_root",
        )


def verify_archive(
    archive: Path, metadata: dict[str, Any], expected: dict[str, Any], quarantine: Path
) -> dict[str, Any]:
    """Return a bounded failure ledger or a verified immutable input inventory."""
    result: dict[str, Any] = {
        "schema_version": "archive-govt-nz.final-donor-state-verification/v1",
        "status": "failed",
        "mismatches": [],
        "files": [],
        "observed": {},
    }
    try:
        check_metadata(metadata, expected)
        files = unpack(archive, metadata, quarantine)
        result.update(
            artifact_sha256=metadata["artifact"]["digest"].removeprefix("sha256:"),
            donor_commit=metadata["run"]["head_sha"],
            run_id=metadata["run"]["id"],
            artifact_id=metadata["artifact"]["id"],
        )
        result["files"] = [
            {
                "path_parts": list(PurePosixPath(name).parts),
                "size_bytes": len(data),
                "sha256": sha(data),
            }
            for name, data in sorted(files.items())
        ]
        equal(sha(files[SEED]), expected["seed_sha256"], "seed_digest")
        seed = identifiers(files[SEED].decode().splitlines(), "seed_ids")
        docs = {
            PurePosixPath(name).stem: load(files[name]) for name in sorted(DOCUMENTS)
        }
        result["observed"] = {
            "seed_ids": len(seed),
            "manifest_records": len(docs["manifest"]["records"]),
            "processed_ids": len(docs["checkpoint"]["processed_work_ids"]),
            "cas_objects": sum(x.startswith(CAS) for x in files),
        }
        records = check_roots(docs, seed, expected)
        objects = check_objects(files, records, seed)
        check_receipts(docs, seed, objects, expected)
        check_retained_receipts(docs, seed)
        result.update(
            status="passed",
            objects=list(objects.values()),
            work_ids=seed,
            manifest_sha256=docs["manifest"]["manifest_sha256"],
            inventory_sha256=docs["manifest"]["discovered_inventory_sha256"],
            media_type_fields_checked=sum("media_type" in record for record in records),
        )
    except VerificationError as exc:
        result["mismatches"].append(str(exc))
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        zipfile.BadZipFile,
        RuntimeError,
    ):
        result["mismatches"].append("invalid_or_unreadable_package")
    result["mismatch_count"] = len(result["mismatches"])
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Write new reports only; a failed package never becomes eligible input."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "metadata", "expectations", "quarantine", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    input_hashes: dict[str, str] = {}
    try:
        expected_bytes = args.expectations.read_bytes()
        input_hashes["expectations_sha256"] = sha(expected_bytes)
        metadata_bytes = args.metadata.read_bytes()
        input_hashes["metadata_sha256"] = sha(metadata_bytes)
        result = verify_archive(
            args.archive, load(metadata_bytes), load(expected_bytes), args.quarantine
        )
    except OSError, ValueError:
        result = {
            "status": "failed",
            "mismatches": ["invalid_verification_inputs"],
            "mismatch_count": 1,
            "observed": {},
            "files": [],
        }
    result["schema_version"] = "archive-govt-nz.final-donor-state-verification/v1"
    result["verifier_sha256"] = sha(Path(__file__).read_bytes())
    result["input_hashes"] = input_hashes
    inventory = {
        "eligible_for_prompt04": result["status"] == "passed",
        "artifact_sha256": result.get("artifact_sha256"),
        "files": result.pop("files"),
    }
    outputs = {
        "final-donor-state-verification.json": result,
        "prompt04-inventory.json": inventory,
    }
    for name, value in outputs.items():
        (args.output / name).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )
    (args.output / "report.md").write_text(
        "# Final donor state verification\n\nStatus: "
        + result["status"]
        + "\n\nObserved: "
        + json.dumps(result["observed"])
        + "\n\nMismatches: "
        + json.dumps(result["mismatches"])
        + "\n\nQuarantine only. No canonical import, publication, "
        "rights clearance or parent payload recovery.\n",
        encoding="utf-8",
    )
    names = [*outputs, "report.md"]
    (args.output / "SHA256SUMS").write_text(
        "".join(
            sha((args.output / name).read_bytes()) + "  " + name + "\n"
            for name in names
        ),
        encoding="utf-8",
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
