"""Parent-bound public checkpoint I/O with no raw SDK diagnostics in receipts."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, NoReturn

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

from archive_govt_nz.parliament.contracts import PUBLIC_REPOSITORY

POINTER = "parliament/control/continuation.json"
LIMIT = 64 * 1024 * 1024
MAX_COMMIT_FILES = 100


class HostedError(RuntimeError):
    """A fail-closed hosted operation; callers publish only this stable reason."""


def abort(reason: str) -> NoReturn:
    """Raise a stable reason without chaining potentially signed SDK URLs."""
    raise HostedError(reason) from None


class NativeTransport:
    """Bind every operation to the existing public, ungated repository."""

    def __init__(self) -> None:
        """Pace metadata beneath the documented anonymous shared-IP window."""
        self.last_metadata = 0.0

    def pace(self) -> None:
        """Leave retry handling for reads to the supported native SDK."""
        time.sleep(max(0.0, 2.0 - (time.monotonic() - self.last_metadata)))
        self.last_metadata = time.monotonic()

    def head(self) -> str:
        """Require a public target and current revision, never create a fallback."""
        try:
            self.pace()
            info = HfApi(token=False).dataset_info(PUBLIC_REPOSITORY)
        except Exception:  # noqa: BLE001 - suppress signed SDK diagnostics
            abort("public_checkpoint_unavailable")
        if info.private or info.gated or not info.sha:
            abort("public_target_not_qualified")
        return info.sha

    def exists(self, path: str, revision: str) -> bool:
        """Inspect one exact path without treating permission failures as absence."""
        try:
            self.pace()
            return bool(
                HfApi(token=False).get_paths_info(
                    PUBLIC_REPOSITORY,
                    paths=[path],
                    repo_type="dataset",
                    revision=revision,
                )
            )
        except Exception:  # noqa: BLE001 - suppress signed SDK diagnostics
            abort("checkpoint_path_unavailable")

    def read(self, path: str, revision: str) -> bytes:
        """Force a fresh anonymous pinned read and retire its temporary copy."""
        try:
            with TemporaryDirectory(prefix="parliament-pinned-") as cache:
                p = Path(
                    hf_hub_download(
                        PUBLIC_REPOSITORY,
                        path,
                        repo_type="dataset",
                        revision=revision,
                        token=False,
                        force_download=True,
                        cache_dir=cache,
                    )
                )
                if p.stat().st_size > LIMIT:
                    abort("checkpoint_read_bound")
                return p.read_bytes()
        except HostedError:
            raise
        except Exception:  # noqa: BLE001 - suppress signed SDK diagnostics
            abort("checkpoint_download_failed")

    def commit(self, files: dict[str, bytes | Path], parent: str) -> str:
        """Make one namespace-limited mutation; never retry writes blindly."""
        if len(files) >= MAX_COMMIT_FILES:
            abort("checkpoint_commit_bound")
        if not files or any(
            not (
                p == POINTER
                or re.fullmatch(
                    r"parliament/(?:checkpoints/[0-9a-f]{2}/[0-9a-f]{64}\.json\.gz|checkpoint-objects/[0-9a-f]{2}/[0-9a-f]{64})",
                    p,
                )
            )
            for p in files
        ):
            abort("checkpoint_namespace")
        operations = []
        for path, value in files.items():
            if path != POINTER:
                expected = path.rsplit("/", 1)[1].split(".")[0]
                if (
                    hashlib.sha256(
                        value.read_bytes() if isinstance(value, Path) else value
                    ).hexdigest()
                    != expected
                ):
                    abort("checkpoint_object_identity")
                if self.exists(path, parent):
                    actual = self.read(path, parent)
                    if hashlib.sha256(actual).hexdigest() != expected:
                        abort("immutable_checkpoint_conflict")
                    continue
            operations.append(
                CommitOperationAdd(
                    path_in_repo=path,
                    path_or_fileobj=str(value) if isinstance(value, Path) else value,
                )
            )
        if not operations:
            return parent
        try:
            self.pace()
            return (
                HfApi()
                .create_commit(
                    repo_id=PUBLIC_REPOSITORY,
                    repo_type="dataset",
                    parent_commit=parent,
                    operations=operations,
                    commit_message="Checkpoint qualified Parliament reports",
                )
                .oid
            )
        except Exception:  # noqa: BLE001 - suppress signed SDK diagnostics
            # The commit may have succeeded: its exact pointer/immutable paths
            # are inspected on resume. Suppress temporary signed URLs.
            abort("checkpoint_commit_outcome_unknown")


def validate_pointer(pointer: dict[str, Any]) -> None:
    """Reject ambiguous ownership or an unrecognised public control shape."""
    if (
        set(pointer)
        != {
            "schema",
            "generation",
            "owner",
            "lease_until",
            "authority",
            "enabled",
            "paused",
            "checkpoint",
            "card_sha256",
        }
        or pointer["schema"] != "parliament-continuation/v1"
    ):
        abort("checkpoint_pointer_schema")
    if (
        type(pointer["generation"]) is not int
        or pointer["generation"] < 0
        or pointer["authority"] not in {"local", "hosted"}
        or type(pointer["enabled"]) is not bool
    ):
        abort("checkpoint_pointer_schema")
    if pointer["owner"] is not None and not re.fullmatch(
        r"[a-zA-Z0-9_-]{1,100}", pointer["owner"]
    ):
        abort("checkpoint_pointer_owner")
    if (
        type(pointer["lease_until"]) not in {int, float}
        or not math.isfinite(pointer["lease_until"])
        or pointer["lease_until"] < 0
        or pointer["paused"] not in {None, "failure", "operator"}
        or not re.fullmatch(r"[0-9a-f]{64}", pointer["card_sha256"])
    ):
        abort("checkpoint_pointer_schema")
    checkpoint = pointer["checkpoint"]
    if checkpoint is not None and (
        set(checkpoint) != {"sha256", "revision", "status"}
        or not re.fullmatch(r"[0-9a-f]{64}", checkpoint["sha256"])
        or (checkpoint["revision"] is None and checkpoint["status"] != "uploaded")
        or (
            checkpoint["revision"] is not None
            and not re.fullmatch(r"[0-9a-f]{40}", checkpoint["revision"])
        )
        or checkpoint["status"] not in {"uploaded", "verified"}
    ):
        abort("checkpoint_pointer_reference")


def assert_publication_authority(repo: str, revision: str) -> None:
    """Fence legacy/manual publishers as well as the dedicated workflow."""
    if repo != PUBLIC_REPOSITORY:
        return
    transport = NativeTransport()
    if not transport.exists(POINTER, revision):
        return
    pointer = json.loads(transport.read(POINTER, revision))
    validate_pointer(pointer)
    owner = pointer["owner"]
    if pointer["checkpoint"] is None or pointer["checkpoint"]["status"] != "verified":
        abort("unverified_checkpoint")
    if owner is not None:
        if (
            os.environ.get("PARLIAMENT_WRITER_ID") != owner
            or pointer["lease_until"] <= time.time()
        ):
            abort("parliament_writer_fenced")
    elif pointer["authority"] == "hosted":
        abort("parliament_writer_lease_required")


def legacy_source_guard() -> None:
    """Stop legacy CLI acquisition once the shared handover pointer exists."""
    transport = NativeTransport()
    revision = transport.head()
    if transport.exists(POINTER, revision):
        # Only the checkpoint controller can advance report acquisition after
        # bootstrap. Even a valid environment owner is insufficient here.
        abort("source_requires_fenced_checkpoint_controller")
