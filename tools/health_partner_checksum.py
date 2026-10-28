# SPDX-License-Identifier: Apache-2.0
"""One approved, parent-bound publisher correction; hosted execution only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

REPO = "edithatogo/global-medicines-atlas-catalogue"
PARENT = "117caee3e1cf31d476c6a66a9860963cc35ed0cb"
OLD = "c09ce43753629afa979988bd30b9c099847310c17117672d3435b5f06843078f"
NEW = "b0ca284d64824f14e8ddb4a618917dba87114ddac9ea3cf99c4e9b0d3336e00d"
README = "02825cc9f6dd66acf7346711dede1cde366a0ce5ba5b21462f57ff151c0c1736"
STALE = "f62c8c5b18011100b1fcd55cb85d4349a6b9a688849d45489fde4321f0538200"
TREE_MEMBERS = 62
MAX_METADATA_BYTES = 65536
REQUIRED = {
    "Assurance (ubuntu-latest)",
    "Assurance (macos-latest)",
    "Assurance (windows-latest)",
    "analyze",
    "lint",
}


def digest(body: bytes) -> str:
    """Return an exact byte identity."""
    return hashlib.sha256(body).hexdigest()


def correction(body: bytes, readme: bytes) -> bytes:
    """Accept only the pre-reviewed one-line change."""
    if digest(body) != OLD or digest(readme) != README:
        msg = "checksum_correction_source_identity"
        raise ValueError(msg)
    before = f"{STALE}  README.md".encode()
    after = f"{README}  README.md".encode()
    changed = body.replace(before, after)
    if body.count(before) != 1 or digest(changed) != NEW:
        msg = "checksum_correction_payload_identity"
        raise ValueError(msg)
    return changed


def hosted_guard(approved: str) -> None:
    """Require explicit approval, hosted ownership and an unreplayed dispatch."""
    expected = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REPOSITORY": "edithatogo/archive-govt-nz",
        "GITHUB_ACTOR": "edithatogo",
        "GITHUB_RUN_ATTEMPT": "1",
    }
    if approved != NEW or any(os.environ.get(k) != v for k, v in expected.items()):
        msg = "checksum_correction_hosted_approval_required"
        raise ValueError(msg)


def checks_guard(checks: list[dict[str, Any]], head: str) -> None:
    """Require all protected contexts on the executing source revision."""
    for name in REQUIRED:
        latest = next((c for c in checks if c.get("name") == name), {})
        if (
            latest.get("head_sha") != head
            or latest.get("conclusion") != "success"
            or latest.get("app", {}).get("slug") != "github-actions"
        ):
            msg = "checksum_correction_required_checks"
            raise ValueError(msg)


def snapshot(revision: str) -> tuple[str, dict[str, tuple[str, int]]]:
    """Read the anonymous public tree, without retrieving data payloads."""
    info = HfApi(token=False).dataset_info(REPO, revision=revision, files_metadata=True)
    if info.private is not False or info.gated is not False or not info.sha:
        msg = "checksum_correction_public_target_required"
        raise ValueError(msg)
    tree = {}
    for item in info.siblings or []:
        if not item.blob_id or item.size is None:
            msg = "checksum_correction_incomplete_tree"
            raise ValueError(msg)
        tree[item.rfilename] = (item.blob_id, item.size)
    if len(tree) != TREE_MEMBERS:
        msg = "checksum_correction_tree_size"
        raise ValueError(msg)
    return info.sha, tree


def read(revision: str, name: str) -> bytes:
    """Read only the two approved public metadata members."""
    if name not in {"README.md", "SHA256SUMS"}:
        msg = "checksum_correction_metadata_only"
        raise ValueError(msg)
    path = hf_hub_download(
        REPO, name, repo_type="dataset", revision=revision, token=False
    )
    if Path(path).stat().st_size > MAX_METADATA_BYTES:
        msg = "checksum_correction_member_bound"
        raise ValueError(msg)
    return Path(path).read_bytes()


def verify(revision: str) -> dict[str, Any]:
    """Prove the approved correction and unchanged remaining tree anonymously."""
    _, before = snapshot(PARENT)
    pinned, after = snapshot(revision)
    changed = sorted(k for k in before if before[k] != after.get(k))
    if (
        set(before) != set(after)
        or changed != ["SHA256SUMS"]
        or digest(read(pinned, "SHA256SUMS")) != NEW
        or digest(read(pinned, "README.md")) != README
    ):
        msg = "checksum_correction_readback_mismatch"
        raise ValueError(msg)
    return {
        "target": REPO,
        "parent_revision": PARENT,
        "verified_revision": pinned,
        "changed_paths": changed,
        "unchanged_members": len(before) - 1,
        "payload_sha256": NEW,
        "readme_sha256": README,
        "verification": "anonymous_immutable_readback",
    }


def permission_summary(identity: dict[str, Any]) -> dict[str, Any]:
    """Expose target-relevant permission metadata without token or private targets."""
    auth = identity.get("auth", {})
    token = auth.get("accessToken", {})
    fine = token.get("fineGrained", {})
    scoped = []
    for grant in fine.get("scoped", []):
        entity = grant.get("entity", {})
        if entity.get("name") in {REPO, "edithatogo"}:
            scoped.append(
                {
                    "entity": entity.get("name"),
                    "type": entity.get("type"),
                    "permissions": [
                        p
                        for p in grant.get("permissions", [])
                        if p in {"repo.write", "repo.content.read", "repo.access.read"}
                    ],
                }
            )
    return {
        "account_matches": identity.get("name") == "edithatogo",
        "token_role": token.get("role"),
        "global_permissions": [
            p
            for p in fine.get("global", [])
            if p in {"repo.write", "repo.content.read", "repo.access.read"}
        ],
        "target_scopes": scoped,
        "publication": "not_performed",
    }


def write_guard(identity: dict[str, Any]) -> None:
    """Qualify the observed owner-scoped fine-grained repo.write grant."""
    summary = permission_summary(identity)
    role = summary["token_role"]
    owner_grant = any(
        g["entity"] == "edithatogo"
        and g["type"] == "user"
        and "repo.write" in g["permissions"]
        for g in summary["target_scopes"]
    )
    if not summary["account_matches"] or not (
        role == "write" or (role == "fineGrained" and owner_grant)
    ):
        msg = "checksum_correction_write_permission_unqualified"
        raise ValueError(msg)


def main() -> None:
    """Prepare, apply once, or verify; never run the harvest pipeline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=("prepare", "publish", "verify", "qualify")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--approved-sha256", default="")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.operation == "qualify":
        receipt = permission_summary(
            HfApi(token=os.environ["HF_TOKEN"]).whoami(cache=False)
        )
    elif args.operation == "verify":
        receipt = verify("main")
    else:
        head, _ = snapshot("main")
        if head != PARENT:
            # An already-applied correction is read-only; unrelated drift fails closed.
            receipt = verify(head)
        else:
            payload = correction(read(PARENT, "SHA256SUMS"), read(PARENT, "README.md"))
            intent = {
                "target": REPO,
                "parent_revision": PARENT,
                "path": "SHA256SUMS",
                "sha256": NEW,
            }
            if args.operation == "prepare":
                (args.output / "SHA256SUMS.corrected").write_bytes(payload)
                receipt = {**intent, "publication": "not_performed"}
            else:
                hosted_guard(args.approved_sha256)
                source = os.environ["GITHUB_SHA"]
                response = subprocess.run(  # noqa: S603
                    [
                        shutil.which("gh") or "/usr/bin/gh",
                        "api",
                        f"repos/edithatogo/archive-govt-nz/commits/{source}/check-runs?per_page=100",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                checks_guard(json.loads(response.stdout)["check_runs"], source)
                retained = json.loads((args.output / "receipt.json").read_bytes())
                if retained != {**intent, "publication": "not_performed"}:
                    msg = "checksum_correction_retained_intent"
                    raise ValueError(msg)
                token = os.environ["HF_TOKEN"]
                api = HfApi(token=token)
                identity = api.whoami(cache=False)
                write_guard(identity)
                # One commit invocation; inspect uncertain responses without resending.
                try:
                    commit = api.create_commit(
                        REPO,
                        repo_type="dataset",
                        revision="main",
                        parent_commit=PARENT,
                        operations=[
                            CommitOperationAdd(
                                path_in_repo="SHA256SUMS", path_or_fileobj=payload
                            )
                        ],
                        commit_message=(
                            "Correct README checksum; preserve dataset payloads"
                        ),
                    )
                except Exception:  # noqa: BLE001
                    receipt = verify("main")
                    receipt["commit_response"] = "uncertain_verified_without_resend"
                else:
                    receipt = verify(commit.oid)
                    receipt["commit_response"] = "received"
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
