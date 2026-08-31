"""Deterministic offline custody packages and plans; never uploads or grants rights."""

from __future__ import annotations

import argparse
import importlib.util
import io
import re
import stat
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import blake3

if TYPE_CHECKING:
    from collections.abc import Sequence
    from importlib.abc import Loader
    from importlib.machinery import ModuleSpec

_spec = cast(
    "ModuleSpec",
    importlib.util.spec_from_file_location(
        "parent_state", Path(__file__).with_name("legislation_parent_state.py")
    ),
)
P = importlib.util.module_from_spec(_spec)
cast("Loader", _spec.loader).exec_module(P)
M, v = P.M, P.v
ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "archive-govt-nz.legislation-durable-package/v1"
MAX_PACKAGE = 256 * 1024 * 1024
MERGED_DOCS = {
    "manifest.json",
    "checkpoint.json",
    "versions_by_work.json",
    "final-state-merge-receipt.json",
    "COMPLETE.json",
}
INSTRUCTIONS = (
    b"Verify the externally pinned SHA-256 with legislation_durable_state.py "
    b"verify before restore. Use a fresh private workspace. No network or Actions "
    b"state is required. Restoring a merged package does not authorize harvest, "
    b"adoption, publication or Prompt 10 recovery acceptance.\n"
)


def inventory(files: dict[str, bytes]) -> list[dict[str, Any]]:
    """Every original file has an exact spelling, size and two digests."""
    return [
        {
            "path_parts": name.split("/"),
            "size_bytes": len(data),
            "sha256": v.sha(data),
            "blake3": blake3.blake3(data).hexdigest(),
        }
        for name, data in sorted(files.items())
    ]


def allowed(name: str) -> bool:
    """Strict portable original state and retained parent names only."""
    return (
        name in MERGED_DOCS
        or P.allowed_name(name)
        or re.fullmatch(
            r"parents/[0-9a-f]{64}/(?:artifact\.zip|descriptor\.json)", name
        )
        is not None
    )


def state(files: dict[str, bytes], pin: dict[str, Any]) -> dict[str, Any]:
    """Authenticate explicit pins, original lineage and complete inner state."""
    P.schema(pin, "legislation-durable-input")
    v.equal(
        pin["source"],
        P.source_identity(pin["source"]["seed_id"] or ""),
        "source_identity",
    )
    v.require(condition=all(allowed(n) for n in files), code="state_member")
    manifest = v.load(files["manifest.json"])
    v.equal(manifest["manifest_sha256"], pin["manifest_sha256"], "pinned_manifest")
    if pin["kind"] == "continuation":
        reference = pin["parent_reference"]
        P.schema(reference, "legislation-parent-reference")
        v.equal(reference["source"], pin["source"], "pinned_source")
        v.equal(reference["lineage_sha256"], pin["marker_sha256"], "pinned_seal")
        v.equal(
            v.sha(files["receipts/harvest.json"]),
            pin["receipt_sha256"],
            "pinned_receipt",
        )
        P.verify_parent(files, reference)
    else:
        v.equal(pin["parent_reference"], None, "merged_reference")
        v.equal(pin["source"], P.source_identity(""), "merged_source")
        v.equal(
            v.sha(files["COMPLETE.json"]), pin["marker_sha256"], "pinned_completion"
        )
        v.equal(
            v.sha(files["final-state-merge-receipt.json"]),
            pin["receipt_sha256"],
            "pinned_receipt",
        )
        entries = [
            {k: value for k, value in e.items() if k != "blake3"}
            for e in inventory({n: b for n, b in files.items() if n != "COMPLETE.json"})
        ]
        v.equal(
            v.load(files["COMPLETE.json"]),
            {"files": entries, "inventory_sha256": v.sha(M.encoded(entries))},
            "completion_inventory",
        )
        receipt = v.load(files["final-state-merge-receipt.json"])
        P.schema(receipt, "legislation-state-merge")
        v.equal(receipt["status"], "passed", "merge_status")
        v.equal(receipt["conflicts"], [], "merge_conflicts")
        v.equal(receipt["mismatches"], [], "merge_mismatches")
        v.equal(len(receipt["parents"]), M.PARENT_COUNT, "merge_parent_count")
        parent_names = set()
        for parent in receipt["parents"]:
            prefix = "parents/" + parent["artifact_sha256"] + "/"
            parent_names.update({prefix + "artifact.zip", prefix + "descriptor.json"})
            v.equal(
                v.sha(files[prefix + "artifact.zip"]),
                parent["artifact_sha256"],
                "parent_archive",
            )
            v.equal(
                v.sha(files[prefix + "descriptor.json"]),
                parent["descriptor_sha256"],
                "parent_descriptor",
            )
            descriptor = v.load(files[prefix + "descriptor.json"])
            v.check_metadata(descriptor["metadata"], descriptor["expected"])
            v.equal(
                descriptor["metadata"]["run"]["head_sha"],
                parent["repository_commit"],
                "parent_commit",
            )
        v.equal(
            {n for n in files if n.startswith("parents/")},
            parent_names,
            "parent_members",
        )
        checkpoint = v.load(files["checkpoint.json"])
        P.LegislationArchiveService.validate_checkpoint(checkpoint)
        records = v.check_roots(
            {"manifest": manifest, "checkpoint": checkpoint},
            manifest["discovered_work_ids"],
            {"manifest_sha256": pin["manifest_sha256"], "batch_id": manifest["run_id"]},
        )
        objects = M.objects_for(records, files)
        v.equal(
            sorted({r["work_id"] for r in records}),
            manifest["discovered_work_ids"],
            "merged_membership",
        )
        v.equal(
            v.load(files["versions_by_work.json"]),
            {
                w: sorted(r["manifestation_id"] for r in records if r["work_id"] == w)
                for w in manifest["discovered_work_ids"]
            },
            "versions",
        )
        v.equal(
            receipt["output"],
            {
                "records": len(records),
                "work_ids": len(manifest["discovered_work_ids"]),
                "objects": len(objects),
                "manifest_sha256": pin["manifest_sha256"],
                "inventory_sha256": manifest["discovered_inventory_sha256"],
                "checkpoint_sha256": v.sha(files["checkpoint.json"]),
            },
            "merge_output",
        )
        v.require(
            condition=all(
                n in MERGED_DOCS or n.startswith((M.CAS, "parents/")) for n in files
            ),
            code="merged_member",
        )
    return {
        "manifest_sha256": pin["manifest_sha256"],
        "inventory_sha256": manifest["discovered_inventory_sha256"],
        "records": len(manifest["records"]),
        "work_ids": len(manifest["discovered_work_ids"]),
    }


def zip_bytes(files: dict[str, bytes]) -> bytes:
    """Canonical uncompressed ZIP: fixed headers, sorted names, no host metadata."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o444) << 16
            archive.writestr(entry, data)
    raw = stream.getvalue()
    v.require(condition=len(raw) <= MAX_PACKAGE, code="package_limit")
    return raw


def build(
    files: dict[str, bytes], pin: dict[str, Any], rights: dict[str, Any], revision: str
) -> bytes:
    """Build verified state; caller must authenticate pin and rights authority."""
    roots = state(files, pin)
    document = {
        "schema_version": SCHEMA,
        "input": pin,
        "rights": rights,
        "software_commit": revision,
        "builder_sha256": v.sha(Path(__file__).read_bytes()),
        "roots": roots,
        "files": inventory(files),
    }
    P.schema(document, "legislation-durable-package")
    raw = zip_bytes(
        {"state/" + n: b for n, b in files.items()}
        | {"package.json": M.encoded(document), "RESTORE.txt": INSTRUCTIONS}
    )
    verify(raw, v.sha(raw))
    return raw


def verify(raw: bytes, expected: str) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Verify the external digest before parsing, then every inner byte and root."""
    v.require(
        condition=re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
        code="expected_digest",
    )
    v.equal(v.sha(raw), expected, "package_digest")
    v.require(condition=len(raw) <= MAX_PACKAGE, code="package_limit")
    files = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        v.require(condition=0 < len(entries) <= v.MAX_FILES + 2, code="package_count")
        v.require(
            condition=sum(e.file_size for e in entries) <= MAX_PACKAGE,
            code="package_expansion",
        )
        for entry in entries:
            name = entry.filename
            v.equal(entry.orig_filename, name, "package_spelling")
            v.require(
                condition=name in {"package.json", "RESTORE.txt"}
                or (name.startswith("state/") and allowed(name[6:])),
                code="package_path",
            )
            v.require(condition=name not in files, code="package_duplicate")
            v.require(
                condition=entry.compress_type == zipfile.ZIP_STORED
                and not entry.flag_bits & 1
                and stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFREG,
                code="package_member_type",
            )
            v.require(
                condition=entry.file_size <= v.MAX_MEMBER, code="package_member_size"
            )
            files[name] = archive.read(entry)
    v.equal(raw, zip_bytes(files), "package_encoding")
    v.equal(files.pop("RESTORE.txt"), INSTRUCTIONS, "restore_instructions")
    document_raw = files.pop("package.json")
    document = v.load(document_raw)
    P.schema(document, "legislation-durable-package")
    v.equal(document_raw, M.encoded(document), "package_json_encoding")
    originals = {n.removeprefix("state/"): b for n, b in files.items()}
    v.equal(document["files"], inventory(originals), "package_inventory")
    v.equal(document["roots"], state(originals, document["input"]), "package_roots")
    return document, originals


def read_package(path: Path) -> bytes:
    """Bounded input without symlink traversal."""
    P.no_symlinks(path)
    with path.open("rb") as stream:
        data = stream.read(MAX_PACKAGE + 1)
    v.require(condition=len(data) <= MAX_PACKAGE, code="package_limit")
    return data


def restore(raw: bytes, expected: str, output: Path) -> dict[str, Any]:
    """Verify completely, then reserve a private stage and promote once complete."""
    document, files = verify(raw, expected)
    P.no_symlinks(output)
    v.require(condition=not output.exists(), code="output_exists")
    stage = output.with_name(output.name + ".quarantine")
    P.no_symlinks(stage)
    stage.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, data in files.items():
        P.write_new(stage / name, data)
    v.equal(P.read_state(stage), files, "restore_readback")
    v.require(condition=not output.exists(), code="output_race")
    stage.rename(output)
    return {
        "status": "verified_local_restore",
        "package_sha256": expected,
        "roots": document["roots"],
        "prompt10_acceptance": False,
    }


def public_metadata(document: dict[str, Any], digest: str) -> dict[str, Any]:
    """Deliberately exclude originals, source URLs, paths and free-form rights text."""
    return {
        "schema_version": "archive-govt-nz.legislation-preservation-summary/v1",
        "package_sha256": digest,
        "roots": document["roots"],
        "payload_rights": document["rights"]["payload"],
        "full_coverage_claim": False,
        "remote_revision": None,
        "doi": None,
    }


def publication_plan(
    raw: bytes, expected: str, observed: dict[str, Any]
) -> dict[str, Any]:
    """Plan only; inventory claims never establish upload or cold-read success."""
    document, _ = verify(raw, expected)
    P.schema(observed, "legislation-publication-observation")
    policy = v.load((ROOT / "config/legislation/preservation.json").read_bytes())
    P.schema(policy, "legislation-preservation-policy")
    v.equal(observed["repository"], policy["repository"], "destination_identity")
    prefix = policy["prefix_parts"] + [expected]
    summary = M.encoded(public_metadata(document, expected))
    candidates = [("metadata.json", summary)]
    if document["rights"]["payload"] == "public_approved":
        candidates.append(("state.zip", raw))
    uploads = []
    for name, data in candidates:
        path = "/".join([*prefix, name])
        previous = observed["files"].get(path)
        digest = v.sha(data)
        if previous is not None:
            v.equal(
                previous, {"sha256": digest, "size_bytes": len(data)}, "remote_conflict"
            )
        uploads.append(
            {
                "path_parts": [*prefix, name],
                "sha256": digest,
                "size_bytes": len(data),
                "action": "verify_existing_bytes"
                if previous is not None
                else "upload_after_approval",
            }
        )
    return {
        "schema_version": "archive-govt-nz.legislation-publication-plan/v1",
        "status": "dry_run_only",
        "repository": policy["repository"],
        "base_revision": observed["revision"],
        "uploads": uploads,
        "metadata": public_metadata(document, expected),
        "payload_blocked": document["rights"]["payload"] != "public_approved",
        "requires_explicit_publication_approval": True,
        "published_revision": None,
        "doi": None,
        "readback_verified": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Offline CLI; output is exclusive, failures never imply an empty package."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "restore", "plan"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--digest", default="")
    parser.add_argument("--pin", type=Path)
    parser.add_argument("--rights", type=Path)
    parser.add_argument("--observation", type=Path)
    parser.add_argument("--software-commit", default="")
    args = parser.parse_args(argv)
    try:
        P.no_symlinks(args.output)
        if args.action == "build":
            v.require(
                condition=args.pin is not None and args.rights is not None,
                code="build_authority_required",
            )
            pin = v.load(read_package(cast("Path", args.pin)))
            rights = v.load(read_package(cast("Path", args.rights)))
            data = build(P.read_state(args.input), pin, rights, args.software_commit)
        else:
            raw = read_package(args.input)
            if args.action == "restore":
                restore(raw, args.digest, args.output)
                return 0
            if args.action == "verify":
                document, _ = verify(raw, args.digest)
                result = {
                    "status": "verified_local_package",
                    "package_sha256": args.digest,
                    "roots": document["roots"],
                }
            else:
                v.require(
                    condition=args.observation is not None, code="observation_required"
                )
                result = publication_plan(
                    raw, args.digest, v.load(read_package(args.observation))
                )
            data = M.encoded(result)
        P.write_new(args.output, data)
    except OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile:
        print("Durable state operation failed; no remote action was performed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
