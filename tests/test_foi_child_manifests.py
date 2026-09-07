"""Child metadata readback must not become raw or rights verification."""

import hashlib
from pathlib import Path

import pytest

import archive_govt_nz.foi_child_manifests as module
from archive_govt_nz.foi_child_manifests import reconcile_child_manifests
from archive_govt_nz.foi_package import canonical

SOURCE = {
    "id": "nz-fyi",
    "entity_id": "NZ",
    "hf_repo_id": "owner/nz",
    "hf_revision": "a" * 40,
}


class ChildHub:
    """Two immutable revisions; any write or unplanned read is an error."""

    def __init__(self, source: dict | None = None) -> None:
        """Prepare inert manifest bytes for a catalogue identity."""
        self.source = SOURCE if source is None else source
        self.manifest = {
            "schema_version": "archive-govt-nz.foi-package/v2",
            "source_id": self.source["id"],
            "country": self.source["entity_id"],
            "captured_at": "2026-08-30T00:00:00Z",
            "source_revision": "c" * 40,
            "source_run_id": "123",
            "adapter_version": "1.0.0",
            "capture_inventory_sha256": "d" * 64,
            "publication_status": "not_published",
            "rights_status": "unreviewed",
            "privacy_status": "unreviewed",
            "counts": {"requests": 1, "responses": 2, "events": 0, "original_files": 1},
            "files": [
                {"path": name, "bytes": 10, "sha256": "e" * 64}
                for name in [
                    "raw.tar",
                    "README.md",
                    *[
                        f"indexes/{name}.{ext}"
                        for name in (
                            "objects",
                            "resources",
                            "requests",
                            "events",
                            "attachments",
                        )
                        for ext in ("jsonl", "parquet")
                    ],
                ]
            ],
        }
        self.reads: list[tuple[str, str, str]] = []
        self.files: dict[tuple[str, str], bytes] = {}
        self.refresh()

    def refresh(self) -> None:
        """Rehash the synthetic child after a deliberate mutation."""
        payload = canonical(self.manifest)
        digest = hashlib.sha256(payload).hexdigest()
        self.pointer = {
            "schema_version": "archive-govt-nz.foi-current/v1",
            "repo_id": self.source["hf_repo_id"],
            "manifest_sha256": digest,
            "snapshot_revision": "b" * 40,
            "tables": {
                name: f"indexes/{name}.parquet"
                for name in (
                    "objects",
                    "resources",
                    "requests",
                    "events",
                    "attachments",
                )
            },
        }
        self.files = {
            (self.source["hf_revision"], "current.json"): canonical(self.pointer),
            ("b" * 40, f"snapshots/{digest}/manifest.json"): payload,
        }

    def info(self, repo: str) -> dict:
        """Observe identity without making latest head the pointer pin."""
        assert repo == self.source["hf_repo_id"]
        return {"id": repo, "private": False, "gated": False, "sha": "f" * 40}

    def sizes(self, repo: str, revision: str, names: list[str]) -> dict:
        """Resolve metadata only at exact synthetic revisions."""
        assert repo == self.source["hf_repo_id"]
        return {
            name: len(self.files[revision, name])
            for name in names
            if (revision, name) in self.files
        }

    def download(
        self, repo: str, revision: str, name: str, output: Path, size: int
    ) -> None:
        """Copy only the exact requested metadata bytes."""
        self.reads.append((repo, revision, name))
        payload = self.files[revision, name]
        assert len(payload) == size
        output.write_bytes(payload)

    def commit(self, repo: str, parent: str, files: dict[str, Path]) -> str:
        """Reject writes through this read-only fixture."""
        del repo, parent, files
        pytest.fail("child reconciliation must not write")


def test_pinned_manifest_only() -> None:
    """Latest head cannot override pinned child metadata."""
    hub = ChildHub()
    result = reconcile_child_manifests(hub, [SOURCE])
    row = result["children"][0]
    assert row["source_id"] == "nz-fyi"
    assert row["pointer_revision"] == "a" * 40
    assert row["snapshot_revision"] == "b" * 40
    assert row["manifest_sha256"] == hub.pointer["manifest_sha256"]
    assert result["raw_objects_verified"] is False
    assert result["rights_approval"] is False
    assert len(hub.reads) == 2
    assert all(
        name == "current.json" or name.endswith("/manifest.json")
        for _, _, name in hub.reads
    )
    assert result == reconcile_child_manifests(ChildHub(), [SOURCE])


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "hash",
        "source",
        "country",
        "schema",
        "duplicate_file",
        "traversal",
        "tables",
        "pointer_repo",
        "pointer_revision",
        "oversize",
        "bool_size",
        "private",
        "wrong_repo",
        "duplicate_source",
    ],
)
def test_invalid_child_fails_closed(
    fault: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject mutated child identity, bytes and manifest structure."""
    hub = ChildHub()
    sources = [SOURCE]
    if fault == "missing":
        hub.files.pop(next(key for key in hub.files if key[1] != "current.json"))
    elif fault == "hash":
        key = next(key for key in hub.files if key[1] != "current.json")
        hub.files[key] += b" "
    elif fault in {"source", "country", "schema", "duplicate_file", "traversal"}:
        mutate_manifest(hub, fault)
    elif fault in {"tables", "pointer_repo", "pointer_revision"}:
        if fault == "tables":
            hub.pointer["tables"] = {}
        elif fault == "pointer_repo":
            hub.pointer["repo_id"] = "other/repo"
        else:
            hub.pointer["snapshot_revision"] = "main"
        hub.files["a" * 40, "current.json"] = canonical(hub.pointer)
    elif fault in {"oversize", "bool_size"}:
        monkeypatch.setattr(
            hub,
            "sizes",
            lambda _r, _v, names: {names[0]: True if fault == "bool_size" else 10**9},
        )
    elif fault in {"private", "wrong_repo"}:
        monkeypatch.setattr(
            hub,
            "info",
            lambda repo: {
                "id": "wrong/repo" if fault == "wrong_repo" else repo,
                "private": fault == "private",
                "gated": False,
                "sha": "f" * 40,
            },
        )
    else:
        sources = [SOURCE, SOURCE]
    with pytest.raises(ValueError, match="child_manifest"):
        reconcile_child_manifests(hub, sources)


def mutate_manifest(hub: ChildHub, fault: str) -> None:
    """Rehash structurally or semantically invalid manifest bytes."""
    fields = {
        "source": ("source_id", "other-source"),
        "country": ("country", "GB"),
        "schema": ("schema_version", "unknown"),
    }
    if fault in fields:
        field, value = fields[fault]
        hub.manifest[field] = value
    elif fault == "duplicate_file":
        hub.manifest["files"][0] = dict(hub.manifest["files"][1], bytes=11)
    else:
        hub.manifest["files"][0]["path"] = "../raw.tar"
    hub.refresh()


@pytest.mark.parametrize("revision", [None, "main", "a" * 39])
def test_bad_reference_before_reads(revision: str | None) -> None:
    """Only immutable catalogue revision references are admitted."""
    hub = ChildHub()
    with pytest.raises(ValueError, match="child_manifest"):
        reconcile_child_manifests(hub, [{**SOURCE, "hf_revision": revision}])
    assert not hub.reads


@pytest.mark.parametrize("fault", ["duplicate_json", "read_size"])
def test_hostile_readback(fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Duplicate JSON members and download-size disagreement are rejected."""
    hub = ChildHub()
    if fault == "duplicate_json":
        hub.files["a" * 40, "current.json"] = (
            b'{"repo_id":"owner/nz","repo_id":"owner/nz"}'
        )
    else:
        monkeypatch.setattr(
            hub, "download", lambda _r, _v, _n, output, _s: output.write_bytes(b"bad")
        )
    with pytest.raises(ValueError, match="child_manifest"):
        reconcile_child_manifests(hub, [SOURCE])


@pytest.mark.parametrize(
    "name", ["foi-package-v2.schema.json", "foi-current-v1.schema.json"]
)
def test_runtime_schema_parity(name: str) -> None:
    """Installed runtime copies exactly match existing release contracts."""
    assert (Path("src/archive_govt_nz/schemas") / name).read_bytes() == (
        Path("schemas") / name
    ).read_bytes()


def test_no_payload_repositories() -> None:
    """Sources without a child target need no remote observation."""
    assert (
        reconcile_child_manifests(ChildHub(), [{**SOURCE, "hf_repo_id": None}])[
            "children"
        ]
        == []
    )


@pytest.mark.parametrize(
    "fault", ["too_many", "duplicate_repo", "unsafe_repo", "manifest_limit"]
)
def test_explicit_resource_bounds(fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Metadata byte and child-set limits precede unbounded work."""
    hub = ChildHub()
    sources = [SOURCE]
    if fault == "too_many":
        sources = [
            {**SOURCE, "id": f"source-{i}", "hf_repo_id": f"owner/source-{i}"}
            for i in range(24)
        ]
    elif fault == "duplicate_repo":
        sources = [SOURCE, {**SOURCE, "id": "other-source"}]
    elif fault == "unsafe_repo":
        sources = [{**SOURCE, "hf_repo_id": "https://private.invalid/source"}]
    else:
        monkeypatch.setattr(module, "MAX_MANIFEST_BYTES", 1)
    with pytest.raises(ValueError, match="child_manifest"):
        reconcile_child_manifests(hub, sources)
    assert len(hub.reads) == (1 if fault == "manifest_limit" else 0)
