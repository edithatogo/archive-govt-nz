"""Verify the legislation donor Git bundle without trusting extracted content."""

# ruff: noqa: C901, E501, PLC0415, PLR0912, PLR2004, S603

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any, NoReturn, cast

from jsonschema import Draft202012Validator, FormatChecker

RELEASE_ID = 377118888
ASSET_ID = 530775782
ASSET_NAME = "corpus-legislation-nz-full-20260826.bundle"
ASSET_SHA256 = "f125f91b06264a97e59f65fac47878a74d646c915f12c0b05841c1550ec741c2"
ASSET_SIZE = 2_365_303
DONOR = "edithatogo/corpus-legislation-nz"
FINAL_HEAD = "b40587f1b1aec7356a0f623916fcc8212397d283"
MAX_BUNDLE_BYTES = 100 * 1024 * 1024
REQUIRED_PATHS = (
    "LICENSE",
    "NOTICE.md",
    "CITATION.cff",
    "README.md",
    "DATASET_CARD.md",
)
SCHEMA = Path("schemas/legislation-donor-bundle-verification-v1.schema.json")


class BundleVerificationError(ValueError):
    """The bundle or its claimed authority fails closed verification."""


def _fail(code: str, cause: BaseException | None = None) -> NoReturn:
    if cause is None:
        raise BundleVerificationError(code)
    raise BundleVerificationError(code) from cause


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"unreadable_json:{path.name}", exc)
    if not isinstance(value, dict):
        _fail(f"expected_object:{path.name}")
    return cast("dict[str, Any]", value)


def _run(arguments: list[str], cwd: Path, *, stdin: str | None = None) -> str:
    try:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _fail(
            f"command_failed:{arguments[1] if len(arguments) > 1 else arguments[0]}",
            exc,
        )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        suffix = detail[-1] if detail else "no_output"
        _fail(f"command_failed:{arguments[1]}:{suffix}")
    return result.stdout


def _check_inputs(
    bundle: Path, metadata: dict[str, Any], expected: dict[str, Any], workspace: Path
) -> bytes:
    try:
        mode = bundle.lstat().st_mode
    except OSError as exc:
        _fail("bundle_unreadable", exc)
    if not stat.S_ISREG(mode) or bundle.is_symlink():
        _fail("bundle_not_regular")
    if workspace.exists() or workspace.is_symlink():
        _fail("workspace_exists")
    if not workspace.is_absolute():
        _fail("workspace_not_absolute")
    raw = bundle.read_bytes()
    if not raw or len(raw) > MAX_BUNDLE_BYTES:
        _fail("bundle_size_limit")
    release = metadata.get("release")
    asset = metadata.get("asset")
    if not isinstance(release, dict) or not isinstance(asset, dict):
        _fail("metadata_shape")
    if release.get("id") != RELEASE_ID or release.get("draft") is not True:
        _fail("release_identity")
    required_asset = {
        "id": ASSET_ID,
        "name": ASSET_NAME,
        "size": ASSET_SIZE,
        "state": "uploaded",
        "digest": "sha256:" + ASSET_SHA256,
    }
    if any(asset.get(key) != value for key, value in required_asset.items()):
        _fail("asset_identity")
    if len(raw) != ASSET_SIZE or _sha(raw) != ASSET_SHA256:
        _fail("asset_fixity")
    if expected.get("donor") != DONOR or expected.get("final_head") != FINAL_HEAD:
        _fail("authority_identity")
    refs = expected.get("refs")
    if not isinstance(refs, dict) or not refs:
        _fail("authority_refs")
    for name, value in refs.items():
        if not isinstance(name, str) or not name.startswith(
            ("refs/heads/", "refs/tags/")
        ):
            _fail("authority_ref_name")
        if not isinstance(value, str) or len(value) != 40:
            _fail("authority_ref_object")
    return raw


def _refs(repository: Path) -> dict[str, dict[str, str | None]]:
    output = _run(
        [
            "git",
            "for-each-ref",
            "--format=%(refname)\t%(objecttype)\t%(objectname)",
            "refs",
        ],
        repository,
    )
    result: dict[str, dict[str, str | None]] = {}
    for line in output.splitlines():
        name, kind, object_id = line.split("\t")
        peeled = None
        if kind == "tag":
            peeled = _run(["git", "rev-parse", f"{name}^{{}}"], repository).strip()
        result[name] = {"object": object_id, "type": kind, "peeled": peeled}
    return dict(sorted(result.items()))


def _inventory(
    repository: Path, final_head: str
) -> tuple[dict[str, str], list[str], list[str], str, int]:
    governed: dict[str, str] = {}
    for path in REQUIRED_PATHS:
        try:
            value = _run(
                ["git", "rev-parse", f"{final_head}:{path}"], repository
            ).strip()
        except BundleVerificationError as exc:
            _fail(f"required_path_missing:{path}", exc)
        governed[path] = value
    names = _run(
        ["git", "ls-tree", "-r", "--name-only", final_head], repository
    ).splitlines()
    workflows = sorted(
        path
        for path in names
        if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
    )
    conductor = sorted(path for path in names if path.startswith("conductor/"))
    if not workflows:
        _fail("workflow_history_missing")
    if not conductor:
        _fail("conductor_history_missing")
    objects = sorted(
        {
            line.split(" ", 1)[0]
            for line in _run(
                ["git", "rev-list", "--objects", "--all", "--missing=print"], repository
            ).splitlines()
        }
    )
    if any(value.startswith("?") for value in objects):
        _fail("reachable_object_missing")
    object_root = _sha(("\n".join(objects) + "\n").encode())
    return governed, workflows, conductor, object_root, len(objects)


def verify_bundle(
    bundle: Path, metadata: dict[str, Any], expected: dict[str, Any], workspace: Path
) -> dict[str, Any]:
    """Verify bytes, Git closure, refs and required final-head governance content."""
    raw = _check_inputs(bundle, metadata, expected, workspace)
    workspace.mkdir(parents=True, exist_ok=False)
    verifier = workspace / "verifier.git"
    restored = workspace / "restored.git"
    _run(["git", "init", "--bare", str(verifier)], workspace)
    _run(["git", "bundle", "verify", str(bundle.resolve())], verifier)
    _run(["git", "clone", "--mirror", str(bundle.resolve()), str(restored)], workspace)
    _run(["git", "fsck", "--full", "--strict", "--no-dangling"], restored)
    restored_refs = _refs(restored)
    authoritative = cast("dict[str, str]", expected["refs"])
    missing = sorted(name for name in authoritative if name not in restored_refs)
    mismatched = sorted(
        name
        for name, oid in authoritative.items()
        if name in restored_refs and restored_refs[name]["object"] != oid
    )
    if missing:
        _fail("required_refs_missing:" + ",".join(missing))
    if mismatched:
        _fail("required_refs_mismatched:" + ",".join(mismatched))
    if FINAL_HEAD not in {
        cast("str", value["object"]) for value in restored_refs.values()
    }:
        _fail("final_head_missing")
    _run(
        ["git", "merge-base", "--is-ancestor", FINAL_HEAD, "refs/heads/main"], restored
    )
    governed, workflows, conductor, object_root, object_count = _inventory(
        restored, FINAL_HEAD
    )
    commit_lines = sorted(
        _run(
            [
                "git",
                "log",
                "--all",
                "--format=%H%x00%P%x00%T%x00%an%x00%ae%x00%aI%x00%cn%x00%ce%x00%cI",
            ],
            restored,
        ).splitlines()
    )
    commit_ids = set(_run(["git", "rev-list", "--all"], restored).splitlines())
    tag_ids = {
        cast("str", value["object"])
        for value in restored_refs.values()
        if value["type"] == "tag"
    }
    signature_objects = 0
    for object_id in sorted(commit_ids | tag_ids):
        content = _run(["git", "cat-file", "-p", object_id], restored)
        if "\ngpgsig " in "\n" + content or (
            content.startswith("object ") and "\n-----BEGIN" in content
        ):
            signature_objects += 1
    bundle_only = sorted(set(restored_refs) - set(authoritative))
    receipt = {
        "schema_version": "archive-govt-nz.legislation-donor-bundle-verification/v1",
        "status": "passed",
        "preservation_classification": "complete_reachable_git_copy",
        "donor": DONOR,
        "final_head": FINAL_HEAD,
        "asset": {
            "release_id": RELEASE_ID,
            "asset_id": ASSET_ID,
            "name": ASSET_NAME,
            "size": len(raw),
            "sha256": _sha(raw),
        },
        "git": {
            "version": _run(["git", "--version"], workspace).strip(),
            "bundle_verify_passed": True,
            "fsck_passed": True,
            "restored_refs": restored_refs,
            "missing_refs": missing,
            "mismatched_refs": mismatched,
            "bundle_only_refs": bundle_only,
            "reachable_object_count": object_count,
            "reachable_object_inventory_sha256": object_root,
            "commit_metadata_count": len(commit_lines),
            "commit_metadata_sha256": _sha(("\n".join(commit_lines) + "\n").encode()),
            "signature_objects_preserved": signature_objects,
        },
        "governed_content": {
            "required_blobs": governed,
            "workflow_paths": workflows,
            "conductor_paths": conductor,
        },
        "limitations": [
            "Completeness covers Git objects reachable from public heads and tags observed in the authority snapshot.",
            "GitHub issues, pull requests, Actions, releases, settings, hidden refs, reflogs, unreachable objects, and external LFS or submodule bytes are outside this bundle claim.",
            "Object identity preserves embedded signatures; cryptographic trust requires an independently governed keyring.",
        ],
        "external_action": {
            "release_published": False,
            "donor_modified": False,
            "donor_unarchived": False,
        },
    }
    schema_path = Path(__file__).resolve().parents[1] / SCHEMA
    Draft202012Validator(_load(schema_path), format_checker=FormatChecker()).validate(
        receipt
    )
    return receipt


def main() -> int:
    """Verify one downloaded bundle and write a deterministic receipt."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = verify_bundle(
            args.bundle, _load(args.metadata), _load(args.expected), args.workspace
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (BundleVerificationError, OSError, ValueError) as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
