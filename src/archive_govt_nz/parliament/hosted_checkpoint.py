"""Durable public checkpoints and cross-process fenced ownership."""

from __future__ import annotations

import gzip
import json
import os
import re
import shutil
import time
import zlib
from typing import Any
lazy from pathlib import Path

from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreReceipt
from archive_govt_nz.parliament.hosted_cooldown import is_write_rate_limit
from archive_govt_nz.parliament.hosted_state import (
    canonical,
    digest,
    export_state,
    import_state,
    validate_state,
)
from archive_govt_nz.parliament.hosted_transport import (
    POINTER,
    HostedError,
    NativeTransport,
    abort,
    validate_pointer,
)
lazy from archive_govt_nz.parliament.pipeline import ParliamentArchive

SPOOL = 8589934592
HEADROOM = 1048576000


def read_pinned_snapshot(
    transport: NativeTransport, revision: str, sha: str
) -> dict[str, Any]:
    """Read a bounded immutable snapshot without claiming an owner or writing."""
    if not re.fullmatch(r"[0-9a-f]{40}", revision) or not re.fullmatch(
        r"[0-9a-f]{64}", sha
    ):
        abort("checkpoint_reference")
    compressed = transport.read(
        "parliament/checkpoints/" + sha[:2] + "/" + sha + ".json.gz",
        revision,
    )
    if digest(compressed) != sha:
        abort("checkpoint_snapshot_integrity")
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    raw = decoder.decompress(compressed, 64 * 1024 * 1024 + 1)
    if len(raw) > 64 * 1024 * 1024 or not decoder.eof or decoder.unused_data:
        abort("checkpoint_snapshot_bound")
    state = json.loads(raw)
    validate_state(state)
    return state


class RestorableStore(ContentAddressedStore):
    """Hydrate only requested working copies from immutable verified references."""

    def __init__(self, root: Path, manager: Checkpoints) -> None:
        """Retain the shared qualified object index."""
        super().__init__(root)
        self.manager = manager

    def verify(self, object_id: str) -> ObjectStoreReceipt:
        """Require pinned remote integrity before restoring an absent local object."""
        sha = object_id.removeprefix("sha256:")
        path = self.objects / sha[:2] / sha
        if not path.exists() and sha in self.manager.refs:
            ref = self.manager.refs[sha]
            self.manager.space(2 * ref["size"])
            data = self.manager.transport.read(ref["path"], ref["revision"])
            if digest(data) != sha or len(data) != ref["size"]:
                abort("remote_object_integrity")
            self.put_bytes(data)
        return super().verify(object_id)


class Checkpoints:
    """One control generation, immutable snapshots and independent readback."""

    def __init__(self, transport: NativeTransport, root: Path) -> None:
        """Bind a transport and fresh hosted working root without native writes."""
        self.transport = transport
        self.root = root
        self.parent = ""
        self.pointer: dict[str, Any] = {}
        self.state: dict[str, Any] = {}
        self.state_revision = ""
        self.state_digest = ""
        self.refs: dict[str, Any] = {}
        self.owner: str | None = None
        self.archive: ParliamentArchive | None = None
        self.work: dict[str, Any] | None = None
        self.cycle = 0
        self.last_tick = time.monotonic()
        self.saving = False
        self.failed = False
        self.write_limited = False
        self.restored_working_copy = False
        self.hold_seconds = 0
        self.held = False

    def current(self) -> dict[str, Any]:
        """Read current ownership rather than trusting an old local lease."""
        self.parent = self.transport.head()
        if not self.transport.exists(POINTER, self.parent):
            abort("checkpoint_not_bootstrapped")
        pointer = json.loads(self.transport.read(POINTER, self.parent))
        validate_pointer(pointer)
        return pointer

    def guard(self) -> None:
        """Fence stale source and publication writers, including paused owners."""
        if self.write_limited:
            abort("hub_write_cooldown_active")
        p = self.current()
        if (
            not self.owner
            or p["owner"] != self.owner
            or p["lease_until"] <= time.time()
        ):
            abort("parliament_writer_fenced")
        self.pointer = p

    def source_guard(self) -> None:
        """Stop new requests on pause while allowing an in-flight durable flush."""
        self.guard()
        if self.pointer["paused"] is not None:
            abort("parliament_source_paused")
        if (
            not self.pointer["checkpoint"]
            or self.pointer["checkpoint"]["status"] != "verified"
        ):
            abort("unverified_checkpoint")

    def write_pointer(self) -> None:
        """Perform a single parent-bound transition and anonymously verify it."""
        if self.write_limited:
            abort("hub_write_cooldown_active")
        self.pointer["generation"] += 1
        validate_pointer(self.pointer)
        content = canonical(self.pointer)
        try:
            self.parent = self.transport.commit({POINTER: content}, self.parent)
        except HostedError as error:
            self.write_limited = self.write_limited or is_write_rate_limit(error)
            raise
        if self.transport.read(POINTER, self.parent) != content:
            abort("checkpoint_pointer_integrity")

    def load(self) -> None:
        """Read and validate the current immutable snapshot, without accepting it."""
        self.pointer = self.current()
        ref = self.pointer["checkpoint"]
        if ref is None:
            abort("checkpoint_missing")
        self.state_revision = ref["revision"] or self.parent
        self.state_digest = ref["sha256"]
        self.state = read_pinned_snapshot(
            self.transport, self.state_revision, ref["sha256"]
        )
        self.refs = {
            h: {**r, "revision": r["revision"] or self.state_revision}
            for h, r in self.state["objects"].items()
        }
        self.work = self.state["work"]
        self.cycle = self.state["cycle"]

    def claim(
        self,
        owner: str,
        *,
        previous_terminal_owner: str | None = None,
        expected_generation: int | None = None,
    ) -> None:
        """Claim a free/expired owner or one proved terminal by GitHub readback."""
        self.pointer = self.current()
        if (
            expected_generation is not None
            and self.pointer["generation"] != expected_generation
        ):
            abort("checkpoint_generation_changed")
        if (
            self.pointer["owner"]
            and self.pointer["owner"] != owner
            and self.pointer["lease_until"] > time.time()
            and self.pointer["owner"] != previous_terminal_owner
        ):
            abort("parliament_writer_busy")
        self.owner = owner
        self.pointer.update(owner=owner, lease_until=time.time() + 5 * 3600)
        self.write_pointer()
        os.environ["PARLIAMENT_WRITER_ID"] = owner

    def accept(self, *, all_objects: bool = False) -> None:
        """Verify staged object bytes before accepted checkpoint promotion."""
        self.guard()
        if self.pointer["checkpoint"]["sha256"] != self.state_digest:
            abort("checkpoint_generation_changed")
        staged = self.pointer["checkpoint"]["status"] == "uploaded"
        for sha, ref in self.refs.items():
            if all_objects or (
                staged and self.state["objects"][sha]["revision"] is None
            ):
                data = self.transport.read(ref["path"], ref["revision"])
                if digest(data) != sha or len(data) != ref["size"]:
                    abort("remote_object_integrity")
        self.guard()
        if self.pointer["checkpoint"]["sha256"] != self.state_digest:
            abort("checkpoint_generation_changed")
        if self.pointer["checkpoint"]["status"] != "verified":
            self.pointer["checkpoint"]["status"] = "verified"
            self.pointer["checkpoint"]["revision"] = self.state_revision
            self.write_pointer()

    def restore(self) -> ParliamentArchive:
        """Restore only accepted state, lazily hydrating exact referenced bytes."""
        self.guard()
        if self.pointer["checkpoint"]["status"] != "verified":
            abort("unverified_checkpoint")
        archive = import_state(self.state, self.root)
        archive.store = RestorableStore(self.root / "cas", self)
        archive.guard = self.guard
        archive.source_guard = self.source_guard
        archive.checkpoint = self.checkpoint
        (self.root / "hosted-authority.json").write_bytes(
            canonical({"authority": "hosted"})
        )
        self.archive = archive
        self.restored_working_copy = True
        for batch, manifest in self.state["batches"].items():
            target = self.root / "batches" / batch / "objects"
            target.mkdir(parents=True, exist_ok=True)
            for row in manifest["records"]:
                receipt = archive.store.verify("sha256:" + row["sha256"])
                if not (target / row["sha256"]).exists():
                    os.link(receipt.path, target / row["sha256"])
        # A stopped invocation has an unknown unacknowledged source interval.
        # Charge its remaining acquisition allowance in full; publish/recover its
        # accepted bytes, then drain pending queue under a NEW bounded attempt.
        if self.work is not None and self.work["phase"] != "publish":
            self.work.update(
                phase="publish",
                seconds=900,
                bytes=262144000,
                reserved=0,
                interrupted=True,
            )
        self.last_tick = time.monotonic()
        return archive

    def tick(self) -> None:
        """Charge source/local acquisition time, excluding checkpoint transport."""
        now = time.monotonic()
        if self.work and self.work["phase"] in {"discover", "capture"}:
            self.work["seconds"] = min(900, self.work["seconds"] + now - self.last_tick)
        self.last_tick = now

    def checkpoint(self, stage: str, detail: dict[str, object]) -> None:
        """Acknowledge source milestones only after immutable public durability."""
        if self.saving or self.failed:
            return
        if stage == "capture_received":
            self.qualify_capture(detail)
            return
        self.tick()
        if self.work:
            if stage == "reports":
                self.work["bytes"] += int(str(detail["bytes"]))
                self.work["observed"] += int(str(detail["discovered"]))
                self.work.update(phase="capture", reserved=0)
            elif stage == "capture_object":
                self.work["bytes"] += int(str(detail["bytes"]))
                self.work["reserved"] = 0
            elif stage == "capture_record":
                self.work["captured"] += 1
                # The preceding per-object checkpoint already preserves these
                # bytes. A conservative pending record is replayable on cold
                # restore; promote its status with the next durable boundary.
                return
        self.save()
        if stage == "reports" and self.hold_seconds and not self.held:
            self.held = True
            time.sleep(self.hold_seconds)
        self.last_tick = time.monotonic()

    def qualify_capture(self, detail: dict[str, object]) -> None:
        """Apply the existing PDF gate before any public checkpoint object write."""
        if self.archive is None:
            abort("checkpoint_archive_missing")
        sha = str(detail["sha256"])
        receipt = self.archive.store.verify("sha256:" + sha)
        with receipt.path.open("rb") as handle:
            if handle.read(5) == b"%PDF-":
                return
        # Retain an exact public hash receipt, never the unqualified body. The
        # ordinary capture error path holds this source without retrying it.
        with self.archive._connection() as connection:  # noqa: SLF001 - shared archive transaction
            connection.execute(
                "INSERT INTO events VALUES(?,?,?,?)",
                (detail["source_id"], "unqualified_payload", sha, time.time()),
            )
        message = "report_payload_not_pdf"
        raise ValueError(message)

    def save(self) -> None:
        """Stage objects/snapshot, verify them, then promote the accepted pointer."""
        if self.archive is None:
            abort("checkpoint_archive_missing")
        self.guard()
        self.space()
        self.saving = True
        try:
            state, local_files = export_state(
                self.archive,
                self.refs,
                work=self.work,
                cycle=self.cycle,
                previous_candidates=self.state.get("candidates", {}),
            )
            files: dict[str, bytes | Path] = dict(local_files)
            encoded = gzip.compress(canonical(state), mtime=0)
            sha = digest(encoded)
            files["parliament/checkpoints/" + sha[:2] + "/" + sha + ".json.gz"] = (
                encoded
            )
            # A null revision is a self-reference only in an UPLOADED pointer.
            # On read, pin it to that observed head; immutable hash paths make
            # an unknown commit outcome recoverable without repeating a write.
            self.pointer["checkpoint"] = {
                "sha256": sha,
                "revision": None,
                "status": "uploaded",
            }
            self.pointer["lease_until"] = time.time() + 5 * 3600
            self.pointer["generation"] += 1
            validate_pointer(self.pointer)
            files[POINTER] = canonical(self.pointer)
            self.parent = self.transport.commit(files, self.parent)
            self.load()
            self.accept()
        except KeyboardInterrupt, SystemExit:
            self.failed = True
            raise
        except HostedError as error:
            self.failed = True
            self.write_limited = self.write_limited or is_write_rate_limit(error)
            raise
        except Exception:  # noqa: BLE001 - durability failures must escape source retries
            self.failed = True
            abort("checkpoint_durability_failed")
        finally:
            self.saving = False
            self.last_tick = time.monotonic()

    def space(self, extra: int = 0) -> None:
        """Keep retained files plus conservative verification room below8GiB."""
        self.root.mkdir(parents=True, exist_ok=True)
        retained = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
        if (
            retained + HEADROOM + extra >= SPOOL
            or shutil.disk_usage(self.root).free < HEADROOM + extra
        ):
            abort("checkpoint_spool_bound")

    def retire(self) -> None:
        """Remove only verified hosted working copies; immutable remote bytes stay."""
        self.guard()
        if not self.restored_working_copy:
            abort("retirement_requires_restored_working_copy")
        if not self.archive or self.archive.pending_report_batch():
            abort("retirement_publication_pending")
        for path in list(self.archive.store.objects.glob("*/*")):
            ref = self.refs.get(path.name)
            if ref is None or digest(path.read_bytes()) != path.name:
                abort("retirement_object_unqualified")
        for path in (self.root / "candidates").glob("*.json"):
            shard = self.state["candidates"].get(path.stem)
            if shard is None or canonical(shard) != path.read_bytes():
                abort("retirement_candidate_unqualified")
        # Hardlink packages are no longer recovery authority once their exact
        # membership and verified publication are in an accepted checkpoint.
        shutil.rmtree(self.root / "batches", ignore_errors=True)
        for path in self.archive.store.objects.glob("*/*"):
            path.unlink()
        shutil.rmtree(self.root / "candidates", ignore_errors=True)

    def release(self) -> None:
        """Release only this still-current owner; never clear another lease."""
        if self.write_limited:
            os.environ.pop("PARLIAMENT_WRITER_ID", None)
            return
        pointer = self.current()
        if pointer["owner"] == self.owner:
            self.pointer = pointer
            self.pointer.update(owner=None, lease_until=0)
            self.write_pointer()
        os.environ.pop("PARLIAMENT_WRITER_ID", None)
