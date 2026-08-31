"""Offline, exclusive state merge. Caller pins authenticated parent descriptors.

No network, publication, source acquisition or in-place state modification.
Conflicting manifestation bytes or metadata produce a ledger, never a winner.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, cast

import blake3

if TYPE_CHECKING:
    from collections.abc import Sequence
    from importlib.abc import Loader
    from importlib.machinery import ModuleSpec

_spec = cast(
    "ModuleSpec",
    importlib.util.spec_from_file_location(
        "donor_state_verifier", Path(__file__).with_name("verify_final_donor_state.py")
    ),
)
v = importlib.util.module_from_spec(_spec)
cast("Loader", _spec.loader).exec_module(v)

CAS = "cas/sha256/"
DOCS = {"manifest.json", "checkpoint.json", "receipts/harvest.json"}
PARENT_COUNT = 2
SCHEMA = "archive-govt-nz.legislation-state-merge/v1"


def encoded(value: object) -> bytes:
    """Canonical JSON file bytes, including a final newline."""
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def root(records: list[dict[str, Any]]) -> str:
    """Use the existing native manifest semantic root contract."""
    return v.sha(b"".join(json.dumps(r, sort_keys=True).encode() for r in records))


def read_target(raw: bytes) -> dict[str, bytes]:
    """Read bounded ZIP members in memory, with no filesystem extraction."""
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        entries = bundle.infolist()
        v.require(condition=0 < len(entries) <= v.MAX_FILES, code="member_count")
        v.require(
            condition=sum(x.file_size for x in entries) <= v.MAX_EXPANDED,
            code="expanded_size",
        )
        seen: set[str] = set()
        for entry in entries:
            name = entry.filename
            parts = name.split("/")
            v.require(
                condition=not any(x in {"", ".", ".."} for x in parts)
                and not any(x in name for x in ("\\", ":", "\x00")),
                code="member_path",
            )
            v.require(condition=name.casefold() not in seen, code="duplicate_member")
            seen.add(name.casefold())
            v.require(
                condition=stat.S_IFMT(entry.external_attr >> 16) in {0, stat.S_IFREG}
                and not entry.flag_bits & 1,
                code="member_type",
            )
            v.require(condition=entry.file_size <= v.MAX_MEMBER, code="member_size")
            v.require(
                condition=name in DOCS
                or re.fullmatch(r"cas/sha256/[0-9a-f]{2}/[0-9a-f]{64}", name)
                is not None,
                code="unexpected_member",
            )
        files = {e.filename: bundle.read(e) for e in entries}
    v.require(condition=files.keys() >= DOCS, code="documents_missing")
    return files


def objects_for(
    records: list[dict[str, Any]], files: dict[str, bytes]
) -> dict[str, bytes]:
    """Verify identities and every CAS reference, including shared objects."""
    objects: dict[str, bytes] = {}
    identities: set[str] = set()
    for record in records:
        v.check_identity(record)
        identity = record["manifestation_id"]
        v.require(condition=identity not in identities, code="duplicate_identity")
        identities.add(identity)
        digest = record["raw_cas_hash_sha256"]
        path = CAS + digest[:2] + "/" + digest
        v.require(condition=path in files, code="missing_object")
        data = files[path]
        v.equal(v.sha(data), digest, "object_sha256")
        v.equal(
            blake3.blake3(data).hexdigest(),
            record["raw_cas_hash_blake3"],
            "object_blake3",
        )
        v.equal(len(data), record["byte_size"], "object_size")
        for alias, field in (
            ("raw_sha256", "raw_cas_hash_sha256"),
            ("raw_blake3", "raw_cas_hash_blake3"),
        ):
            v.equal(record.get(alias, record[field]), record[field], "hash_alias")
        if "media_type" in record:
            # Reuse the stricter verifier's optional declaration/signature check.
            v.check_objects({v.STATE + path: data}, [record], [record["work_id"]])
        objects[digest] = data
    v.equal(
        {name for name in files if name.startswith(CAS)},
        {CAS + digest[:2] + "/" + digest for digest in objects},
        "orphan_object",
    )
    return objects


def target_state(files: dict[str, bytes]) -> dict[str, Any]:
    """Independently reconcile target roots, cumulative membership and receipt."""
    docs = {Path(name).stem: v.load(files[name]) for name in sorted(DOCS)}
    manifest, checkpoint, receipt = (
        docs[k] for k in ("manifest", "checkpoint", "harvest")
    )
    expected = {
        "manifest_sha256": manifest["manifest_sha256"],
        "batch_id": manifest["run_id"],
    }
    records = v.check_roots(docs, manifest["discovered_work_ids"], expected)
    v.equal(
        sorted({r["work_id"] for r in records}),
        manifest["discovered_work_ids"],
        "work_membership",
    )
    objects = objects_for(records, files)
    v.equal(
        receipt["schema_version"],
        "archive-govt-nz.legislation-harvest-receipt/v2",
        "receipt_schema",
    )
    v.equal(receipt["batch_id"], manifest["run_id"], "receipt_batch")
    v.equal(receipt["manifest_sha256"], manifest["manifest_sha256"], "receipt_root")
    v.equal(
        receipt["discovered_works_count"],
        len(manifest["discovered_work_ids"]),
        "receipt_inventory",
    )
    v.equal(receipt["state_committed"], expected=True, code="receipt_commit")
    v.equal(receipt["errors"], [], "receipt_errors")
    v.require(
        condition=receipt["outcome"] in {"changed", "no_change"}, code="receipt_outcome"
    )
    counts = [
        receipt[k]
        for k in ("max_works", "works_attempted", "works_synced", "records_preserved")
    ]
    v.require(
        condition=all(type(n) is int and n >= 0 for n in counts), code="receipt_counts"
    )
    maximum, attempted, synced, preserved = counts
    v.require(
        condition=preserved <= attempted <= maximum and synced <= attempted,
        code="receipt_accounting",
    )
    return {"manifest": manifest, "checkpoint": checkpoint, "objects": objects}


def parent(archive: Path, descriptor: dict[str, Any]) -> dict[str, Any]:
    """Authenticate a pinned archive and independently verify its complete state."""
    v.require(condition=not archive.is_symlink(), code="archive_symlink")
    with archive.open("rb") as stream:
        raw = stream.read(v.MAX_ZIP + 1)
    v.require(condition=len(raw) <= v.MAX_ZIP, code="archive_size")
    metadata, expected = descriptor["metadata"], descriptor["expected"]
    v.check_metadata(metadata, expected)
    v.equal(len(raw), metadata["artifact"]["size_in_bytes"], "archive_size_metadata")
    v.equal("sha256:" + v.sha(raw), metadata["artifact"]["digest"], "archive_digest")
    role = descriptor["role"]
    v.require(condition=role in {"donor", "target"}, code="parent_role")
    if role == "donor":
        # Prompt 03 has already fixed every member's bytes; bind that inventory.
        inventory = descriptor["inventory"]
        v.equal(
            inventory["eligible_for_prompt04"], expected=True, code="donor_eligible"
        )
        v.equal(inventory["artifact_sha256"], v.sha(raw), "donor_inventory_archive")
        with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
            entries = bundle.infolist()
            v.require(
                condition=0 < len(entries) <= v.MAX_FILES, code="donor_member_count"
            )
            v.require(
                condition=sum(e.file_size for e in entries) <= v.MAX_EXPANDED,
                code="donor_expansion_limit",
            )
            v.require(
                condition=all(e.file_size <= v.MAX_MEMBER for e in entries),
                code="donor_member_limit",
            )
            names = bundle.namelist()
            v.equal(len(names), len(set(names)), "donor_duplicate")
            pinned = {"/".join(e["path_parts"]): e for e in inventory["files"]}
            v.equal(set(names), set(pinned), "donor_inventory_names")
            files = {name: bundle.read(name) for name in names}
        for name, data in files.items():
            v.equal(v.sha(data), pinned[name]["sha256"], "donor_inventory_digest")
            v.equal(len(data), pinned[name]["size_bytes"], "donor_inventory_size")
        seed = v.identifiers(files[v.SEED].decode().splitlines(), "donor_seed")
        v.equal(v.sha(files[v.SEED]), expected["seed_sha256"], "donor_seed_digest")
        docs = {PurePosixPath(n).stem: v.load(files[n]) for n in sorted(v.DOCUMENTS)}
        records = v.check_roots(docs, seed, expected)
        verified = v.check_objects(files, records, seed)
        v.check_receipts(docs, seed, verified, expected)
        v.check_retained_receipts(docs, seed)
        normalized = {
            n.removeprefix(v.STATE): b
            for n, b in files.items()
            if n.startswith(v.STATE)
        }
        state = {
            "manifest": docs["manifest"],
            "checkpoint": docs["checkpoint"],
            "objects": objects_for(records, normalized),
        }
    else:
        files = read_target(raw)
        state = target_state(files)
    prefix = v.STATE if role == "donor" else ""
    state.update(
        archive=raw,
        descriptor=descriptor,
        artifact_sha256=v.sha(raw),
        manifest_file_sha256=v.sha(files[prefix + "manifest.json"]),
        checkpoint_file_sha256=v.sha(files[prefix + "checkpoint.json"]),
    )
    return state


def canonical_merge(parents: list[dict[str, Any]]) -> dict[str, Any]:
    """Set union is commutative and idempotent; ambiguity is an explicit failure."""
    variants: dict[str, dict[str, dict[str, Any]]] = {}
    objects: dict[str, bytes] = {}
    for state in parents:
        for digest, data in state["objects"].items():
            v.equal(v.sha(data), digest, "input_object_changed")
            if digest in objects:
                v.equal(objects[digest], data, "content_collision")
            objects.setdefault(digest, data)
        for record in state["manifest"]["records"]:
            variants.setdefault(record["manifestation_id"], {})[
                v.sha(encoded(record))
            ] = record
    conflicts = []
    for identity, values in sorted(variants.items()):
        if len(values) > 1:
            records = list(values.values())
            classification = (
                "manifestation_bytes_changed"
                if len({r["raw_cas_hash_sha256"] for r in records}) > 1
                else "manifestation_metadata_conflict"
            )
            conflicts.append(
                {
                    "manifestation_id": identity,
                    "class": classification,
                    "record_sha256": sorted(values),
                    "resolution": "blocked_no_winner",
                }
            )
    if conflicts:
        return {"status": "failed", "conflicts": conflicts}
    records = [next(iter(values.values())) for _, values in sorted(variants.items())]
    objects_for(records, {CAS + d[:2] + "/" + d: data for d, data in objects.items()})
    ids = sorted({r["work_id"] for r in records})
    manifest_root = root(records)
    inventory_root = v.sha(json.dumps(ids, separators=(",", ":")).encode())
    timestamp = max(p["checkpoint"]["last_updated"] for p in parents)
    batch = "merged-" + manifest_root
    manifest = {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "generated_at": timestamp,
        "run_id": batch,
        "records": records,
        "total_records": len(records),
        "manifest_sha256": manifest_root,
        "discovered_work_ids": ids,
        "discovered_works_count": len(ids),
        "discovered_inventory_sha256": inventory_root,
    }
    checkpoint = {
        "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
        "last_updated": timestamp,
        "completed_batches": sorted(
            {b for p in parents for b in p["checkpoint"]["completed_batches"]} | {batch}
        ),
        "processed_work_ids": ids,
        "last_processed_index": len(ids),
        "total_records_preserved": len(records),
        "metadata": {
            "manifest_sha256": manifest_root,
            "discovered_inventory_sha256": inventory_root,
            "conditional_requests": {},
        },
    }
    links = {
        work: sorted(r["manifestation_id"] for r in records if r["work_id"] == work)
        for work in ids
    }
    return {
        "status": "passed",
        "conflicts": [],
        "manifest": manifest,
        "checkpoint": checkpoint,
        "objects": objects,
        "versions_by_work": links,
    }


def write_exclusive(path: Path, data: bytes) -> None:
    """No replacement; readback before declaring any output file complete."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    v.equal(path.read_bytes(), data, "output_readback")
    path.chmod(0o444)


def execute(
    inputs: list[tuple[Path, dict[str, Any]]], output: Path, revision: str
) -> dict[str, Any]:
    """Reserve fresh output; retain parents, failures and a completion marker."""
    v.require(
        condition=re.fullmatch(r"[0-9a-f]{40}", revision) is not None,
        code="software_revision",
    )
    v.require(condition=len(inputs) == PARENT_COUNT, code="two_parents_required")
    v.require(
        condition=not output.resolve().is_relative_to(v.ROOT),
        code="external_staging_required",
    )
    output.mkdir(parents=True, exist_ok=False)
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA,
        "status": "failed",
        "software_commit": revision,
        "merger_sha256": v.sha(Path(__file__).read_bytes()),
        "parents": [],
        "conflicts": [],
        "mismatches": [],
    }
    try:
        parents = []
        for archive, descriptor in inputs:
            state = parent(archive, descriptor)
            digest = state["artifact_sha256"]
            lineage = output / "parents" / digest
            if not lineage.exists():
                write_exclusive(lineage / "artifact.zip", state["archive"])
                write_exclusive(lineage / "descriptor.json", encoded(descriptor))
            parents.append(state)
        result = canonical_merge(parents)
        receipt.update(status=result["status"], conflicts=result["conflicts"])
        receipt["parents"] = sorted(
            [
                {
                    "artifact_sha256": p["artifact_sha256"],
                    "manifest_sha256": p["manifest"]["manifest_sha256"],
                    "checkpoint_file_sha256": p["checkpoint_file_sha256"],
                    "manifest_file_sha256": p["manifest_file_sha256"],
                    "descriptor_sha256": v.sha(encoded(p["descriptor"])),
                    "repository_commit": p["descriptor"]["metadata"]["run"]["head_sha"],
                    "records": len(p["manifest"]["records"]),
                    "objects": len(p["objects"]),
                }
                for p in parents
            ],
            key=lambda p: p["artifact_sha256"],
        )
        receipt["overlap"] = {
            field: len(
                {r[field] for r in parents[0]["manifest"]["records"]}
                & {r[field] for r in parents[1]["manifest"]["records"]}
            )
            for field in (
                "work_id",
                "expression_id",
                "manifestation_id",
                "canonical_uri",
                "raw_cas_hash_sha256",
                "raw_cas_hash_blake3",
            )
        }
        if result["status"] == "passed":
            for digest, data in sorted(result["objects"].items()):
                write_exclusive(output / CAS / digest[:2] / digest, data)
            for name in ("manifest", "checkpoint", "versions_by_work"):
                write_exclusive(output / (name + ".json"), encoded(result[name]))
            receipt["output"] = {
                "records": len(result["manifest"]["records"]),
                "work_ids": len(result["manifest"]["discovered_work_ids"]),
                "objects": len(result["objects"]),
                "manifest_sha256": result["manifest"]["manifest_sha256"],
                "inventory_sha256": result["manifest"]["discovered_inventory_sha256"],
                "checkpoint_sha256": v.sha(encoded(result["checkpoint"])),
            }
            receipt["conditional_requests_policy"] = (
                "reset_for_unconditional_revalidation; originals_retained_in_parents"
            )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        zipfile.BadZipFile,
    ) as exc:
        receipt["status"] = "failed"
        receipt["mismatches"] = [
            str(exc)
            if isinstance(exc, v.VerificationError)
            else "invalid_or_unreadable_input_output"
        ]
    write_exclusive(output / "final-state-merge-receipt.json", encoded(receipt))
    if receipt["status"] == "passed":
        inventory = [
            {
                "path_parts": list(p.relative_to(output).parts),
                "size_bytes": p.stat().st_size,
                "sha256": v.sha(p.read_bytes()),
            }
            for p in sorted(output.rglob("*"))
            if p.is_file()
        ]
        write_exclusive(
            output / "COMPLETE.json",
            encoded(
                {"files": inventory, "inventory_sha256": v.sha(encoded(inventory))}
            ),
        )
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    """Read explicit descriptors; no implicit latest-run selection or network."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parent",
        nargs=2,
        action="append",
        type=Path,
        required=True,
        metavar=("ZIP", "DESCRIPTOR"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--software-commit", required=True)
    args = parser.parse_args(argv)
    result = execute(
        [(p, v.load(d.read_bytes())) for p, d in args.parent],
        args.output,
        args.software_commit,
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
