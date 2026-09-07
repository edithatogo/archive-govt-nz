"""Immutable public snapshots are restored before the current pointer moves."""

import hashlib
import json
import runpy
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

import pytest
from jsonschema import Draft202012Validator

import archive_govt_nz.foi_delivery as module
import archive_govt_nz.foi_publication as publication
from archive_govt_nz.foi_canonical import build_source_index
from archive_govt_nz.foi_catalogue import catalogue_files
from archive_govt_nz.foi_child_manifests import (
    bind_child_manifests,
    reconcile_child_manifests,
)
from archive_govt_nz.foi_delivery import publish_snapshot
from archive_govt_nz.foi_discovery import build_reviewed_catalogue

TRACK = Path("conductor/tracks/global_foi_public_archive_20260830")
SEEDS = Path("config/foi")
CHILD_HUB = runpy.run_path(
    str(Path(__file__).with_name("test_foi_child_manifests.py"))
)["ChildHub"]


class MemoryHub:
    """Exercise public identity, revision and atomic commit boundaries."""

    def __init__(self) -> None:
        """Start with a public empty repository."""
        self.revision = "a" * 40
        self.files: dict[str, bytes] = {}
        self.history = {self.revision: {}}
        self.private = False
        self.gated = False
        self.identity = "owner/catalogue"
        self.expected_repo = "owner/catalogue"
        self.corrupt = False
        self.calls = 0

    def info(self, repo: str) -> dict:
        """Return configurable identity evidence."""
        assert repo == self.expected_repo
        return {
            "id": self.identity,
            "sha": self.revision,
            "private": self.private,
            "gated": self.gated,
        }

    def sizes(self, repo: str, revision: str, names: list[str]) -> dict[str, int]:
        """Return sizes from one immutable in-memory revision."""
        assert repo == self.expected_repo
        return {
            name: len(self.history[revision][name])
            for name in names
            if name in self.history[revision]
        }

    def download(
        self, repo: str, revision: str, name: str, output: Path, size: int
    ) -> None:
        """Write remote bytes while allowing integrity fault injection."""
        assert repo == self.expected_repo
        assert size >= 0
        output.parent.mkdir(parents=True, exist_ok=True)
        data = self.history[revision][name]
        output.write_bytes(b"bad" if self.corrupt else data)

    def commit(self, repo: str, parent: str, files: dict[str, Path]) -> str:
        """Apply an atomic compare-and-swap update."""
        assert repo == self.expected_repo
        assert parent == self.revision
        self.calls += 1
        self.files.update({name: path.read_bytes() for name, path in files.items()})
        self.revision = f"{self.calls:040x}"
        self.history[self.revision] = dict(self.files)
        return self.revision


def candidate(tmp_path: Path) -> dict[str, Path]:
    """Create synthetic metadata with no source payload."""
    path = tmp_path / "manifest.json"
    path.write_bytes(b'{"synthetic":true}\n')
    return {"manifest.json": path}


def test_verify_before_promote_and_idempotent_retry(tmp_path: Path) -> None:
    """Restore before pointer promotion and verify again without rewriting."""
    hub = MemoryHub()
    files = candidate(tmp_path)
    observed = []

    def restore(root: Path) -> None:
        assert "current.json" not in hub.files
        observed.append((root / "manifest.json").read_bytes())

    result = publish_snapshot(hub, "owner/catalogue", files, restore)
    assert result["status"] == "verified"
    assert hub.calls == 2
    assert observed == [files["manifest.json"].read_bytes()]
    again = publish_snapshot(hub, "owner/catalogue", files, lambda _root: None)
    assert again["manifest_sha256"] == result["manifest_sha256"]
    assert hub.calls == 2


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("private", True),
        ("gated", True),
        ("identity", "wrong/repo"),
        ("revision", "bad"),
    ],
)
def test_wrong_target_never_uploads(tmp_path: Path, field: str, value: object) -> None:
    """Reject private, gated, misidentified or unpinned repositories."""
    hub = MemoryHub()
    setattr(hub, field, value)
    with pytest.raises(
        ValueError, match=r"repository_identity|invalid_remote_revision"
    ):
        publish_snapshot(
            hub, "owner/catalogue", candidate(tmp_path), lambda _root: None
        )
    assert hub.calls == 0


def test_corrupt_readback_does_not_promote(tmp_path: Path) -> None:
    """A bad download cannot become the current snapshot."""
    hub = MemoryHub()
    hub.corrupt = True
    with pytest.raises(ValueError, match="remote_integrity"):
        publish_snapshot(
            hub, "owner/catalogue", candidate(tmp_path), lambda _root: None
        )
    assert "current.json" not in hub.files


def test_failed_restore_does_not_promote(tmp_path: Path) -> None:
    """A failed reconstruction leaves the pointer unchanged."""
    hub = MemoryHub()

    def fail(_root: Path) -> None:
        message = "restore_failed"
        raise ValueError(message)

    with pytest.raises(ValueError, match="restore_failed"):
        publish_snapshot(hub, "owner/catalogue", candidate(tmp_path), fail)
    assert "current.json" not in hub.files


@pytest.mark.parametrize(
    "value",
    [
        [],
        {"schema_version": "wrong"},
        {"schema_version": "archive-govt-nz.foi-current/v1", "repo_id": "wrong"},
        {
            "schema_version": "archive-govt-nz.foi-current/v1",
            "repo_id": "owner/catalogue",
            "manifest_sha256": "bad",
        },
    ],
)
def test_malformed_current_pointer_fails_before_upload(
    tmp_path: Path, value: object
) -> None:
    """Existing invalid publication state requires explicit reconciliation."""
    hub = MemoryHub()
    hub.history[hub.revision]["current.json"] = json.dumps(value).encode()
    with pytest.raises(ValueError, match="invalid_current_pointer"):
        publish_snapshot(
            hub, "owner/catalogue", candidate(tmp_path), lambda _root: None
        )
    assert hub.calls == 0


def test_budgets_and_missing_manifest_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bound local input and remote pointer size before publication."""
    hub = MemoryHub()
    with pytest.raises(ValueError, match="invalid_snapshot_file_set"):
        publish_snapshot(hub, "owner/catalogue", {}, lambda _root: None)
    files = candidate(tmp_path)
    monkeypatch.setattr(module, "MAX_BYTES", 0)
    with pytest.raises(ValueError, match="snapshot_byte_budget"):
        publish_snapshot(hub, "owner/catalogue", files, lambda _root: None)
    monkeypatch.setattr(module, "MAX_BYTES", 1000)
    hub.history[hub.revision]["current.json"] = b"x" * 4097
    with pytest.raises(ValueError, match="invalid_current_pointer"):
        publish_snapshot(hub, "owner/catalogue", files, lambda _root: None)


def test_immutable_conflict_and_failed_upload_retry(tmp_path: Path) -> None:
    """Existing snapshot objects are never silently overwritten."""
    hub = MemoryHub()
    files = candidate(tmp_path)
    digest = module.sha256(files["manifest.json"])
    key = f"snapshots/{digest}/manifest.json"
    hub.history[hub.revision][key] = b"conflict"
    with pytest.raises(ValueError, match="immutable_snapshot_conflict"):
        publish_snapshot(hub, "owner/catalogue", files, lambda _root: None)
    hub.history[hub.revision][key] = files["manifest.json"].read_bytes()
    result = publish_snapshot(hub, "owner/catalogue", files, lambda _root: None)
    assert result["uploaded"] is False
    assert hub.calls == 1


@pytest.mark.parametrize("call", [2, 3])
def test_concurrent_head_change_is_not_success(
    tmp_path: Path, call: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject changes before or after promotion instead of reporting stale state."""
    hub = MemoryHub()
    calls = 0
    original = hub.info

    def changed(repo: str) -> dict:
        nonlocal calls
        calls += 1
        value = original(repo)
        if calls == call:
            value["sha"] = "b" * 40
        return value

    monkeypatch.setattr(hub, "info", changed)
    with pytest.raises(ValueError, match="concurrent_publication"):
        publish_snapshot(
            hub, "owner/catalogue", candidate(tmp_path), lambda _root: None
        )


def test_idempotent_read_detects_concurrent_pointer_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A matching snapshot cannot hide a concurrent current-pointer update."""
    hub = MemoryHub()
    files = candidate(tmp_path)
    publish_snapshot(hub, "owner/catalogue", files, lambda _root: None)
    original = hub.info
    calls = 0

    def changed(repo: str) -> dict:
        nonlocal calls
        calls += 1
        value = original(repo)
        if calls == 2:
            value["sha"] = "b" * 40
        return value

    monkeypatch.setattr(hub, "info", changed)
    with pytest.raises(ValueError, match="concurrent_publication"):
        publish_snapshot(hub, "owner/catalogue", files, lambda _root: None)


def test_dataset_card_matches_verified_snapshot(tmp_path: Path) -> None:
    """Public navigation must identify the exact verified snapshot."""
    hub = MemoryHub()
    result = publish_snapshot(
        hub, "owner/catalogue", candidate(tmp_path), lambda _root: None
    )
    card = hub.files["README.md"].decode()
    assert result["manifest_sha256"] in card
    assert result["snapshot_revision"] in card
    hub.history[hub.revision]["README.md"] = b"wrong"
    with pytest.raises(ValueError, match="remote_integrity"):
        publish_snapshot(
            hub, "owner/catalogue", candidate(tmp_path), lambda _root: None
        )


def test_live_catalogue_projection_has_no_raw_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Publish the pinned metadata projection, preserving unknown coverage."""
    hub = MemoryHub()
    hub.identity = hub.expected_repo = publication.CATALOGUE_REPO
    original = hub.info

    def public(repo: str) -> dict:
        return (
            original(repo)
            if repo == publication.CATALOGUE_REPO
            else {"id": repo, "private": False, "gated": False, "sha": "a" * 40}
        )

    monkeypatch.setattr(hub, "info", public)
    result = publication.publish_catalogue(hub, Path("config/foi"))
    schema = json.loads(Path("schemas/foi-current-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(json.loads(hub.files["current.json"]))
    assert '"config_name": "sources"' in hub.files["README.md"].decode()
    assert result["scope"] == "source_catalogue_only"
    assert result["coverage"]["verified_complete"] == 0
    assert result["coverage"]["geographic_entities"] == 250
    assert not any(name.endswith("raw.tar") for name in hub.files)
    repeated = publication.publish_catalogue(hub, Path("config/foi"))
    assert repeated["current_revision"] == result["current_revision"]
    assert hub.calls == 2


@pytest.mark.parametrize(
    ("field", "value"), [("private", True), ("gated", True), ("id", "wrong/repo")]
)
def test_catalogue_rejects_changed_child_access(
    field: str, value: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An old public observation cannot conceal a newly restricted child."""
    hub = MemoryHub()

    def private(repo: str) -> dict:
        return {"id": repo, "private": False, "gated": False, field: value}

    monkeypatch.setattr(hub, "info", private)
    with pytest.raises(ValueError, match="child_repository_not_public"):
        publication.publish_catalogue(hub, Path("config/foi"))
    assert hub.calls == 0


def test_catalogue_restore_rejects_a_different_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The catalogue restore callback compares the full pinned projection."""
    hub = MemoryHub()
    monkeypatch.setattr(
        hub, "info", lambda repo: {"id": repo, "private": False, "gated": False}
    )

    def changed(
        _hub: object,
        _repo: str,
        _files: dict[str, Path],
        restore: Callable[[Path], None],
    ) -> dict:
        restore(tmp_path)
        return {}

    monkeypatch.setattr(publication, "publish_snapshot", changed)
    with pytest.raises(ValueError, match="catalogue_restore_mismatch"):
        publication.publish_catalogue(hub, Path("config/foi"))


def catalogue_hub(monkeypatch: pytest.MonkeyPatch) -> MemoryHub:
    """Keep all catalogue and child repository operations in memory."""
    hub = MemoryHub()
    hub.identity = hub.expected_repo = publication.CATALOGUE_REPO
    original = hub.info
    children = {
        row["hf_repo_id"]: CHILD_HUB(row)
        for row in build_reviewed_catalogue(SEEDS)["sources"]
        if row["hf_repo_id"] is not None
    }
    original_sizes, original_download = hub.sizes, hub.download

    def sizes(repo: str, revision: str, names: list[str]) -> dict:
        return (
            children[repo].sizes(repo, revision, names)
            if repo in children
            else original_sizes(repo, revision, names)
        )

    def download(repo: str, revision: str, name: str, output: Path, size: int) -> None:
        if repo in children:
            children[repo].download(repo, revision, name, output, size)
        else:
            original_download(repo, revision, name, output, size)

    monkeypatch.setattr(hub, "sizes", sizes)
    monkeypatch.setattr(hub, "download", download)
    monkeypatch.setattr(
        hub,
        "info",
        lambda repo: (
            original(repo)
            if repo == publication.CATALOGUE_REPO
            else {"id": repo, "private": False, "gated": False}
        ),
    )
    return hub


@pytest.mark.parametrize("canonical", [False, True])
def test_publisher_exact_builder_bytes(
    monkeypatch: pytest.MonkeyPatch, *, canonical: bool
) -> None:
    """Default v1 and explicit v2 retain exact pinned metadata, never raw bytes."""
    hub = catalogue_hub(monkeypatch)
    options = {"canonical_track": TRACK} if canonical else {}
    expected = (
        build_source_index(SEEDS, TRACK)
        if canonical
        else catalogue_files(build_reviewed_catalogue(SEEDS))
    )
    if canonical:
        expected = bind_child_manifests(
            expected,
            reconcile_child_manifests(
                hub, json.loads(expected["registry.json"])["sources"]
            ),
        )
    result = publication.publish_catalogue(hub, SEEDS, **options)
    prefix = f"snapshots/{result['manifest_sha256']}/"
    assert {
        name.removeprefix(prefix): data
        for name, data in hub.files.items()
        if name.startswith(prefix)
    } == expected
    assert result["payload_publication"] is False
    assert result["coverage"] == json.loads(expected["coverage.json"])
    manifest = json.loads(expected["manifest.json"])
    assert manifest["schema_version"].endswith("/v2" if canonical else "/v1")
    assert manifest["payload_publication_authorized"] is False
    if canonical:
        registry = json.loads(expected["registry.json"])
        schema = json.loads(
            (TRACK / "canonical-source-catalogue-v2.schema.json").read_bytes()
        )
        Draft202012Validator(schema).validate(registry)
        assert len(registry["sources"]) == 255
        pins = json.loads((TRACK / "canonical-inputs-20260907.json").read_bytes())
        assert (
            manifest["provenance"]["canonical_join"]["inputs"]["files"] == pins["files"]
        )
        original = build_reviewed_catalogue(SEEDS)["sources"]
        by_id = {source["id"]: source for source in registry["sources"]}
        assert [by_id[source["id"]] for source in original] == original
    publication.publish_catalogue(hub, SEEDS, **options)
    assert hub.calls == 2


def test_canonical_publisher_bad_pin_before_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid canonical inputs cannot fall back to v1 or touch the Hub."""
    hub = MemoryHub()
    monkeypatch.setattr(hub, "info", lambda _repo: pytest.fail("transport reached"))
    pins = json.loads((TRACK / "canonical-inputs-20260907.json").read_bytes())
    pins["files"].pop(next(iter(pins["files"])))
    (tmp_path / "canonical-inputs-20260907.json").write_text(json.dumps(pins))
    with pytest.raises(ValueError, match="canonical_input_set"):
        publication.publish_catalogue(hub, SEEDS, canonical_track=tmp_path)
    assert hub.calls == 0


@pytest.mark.parametrize("failure", ["bytes", "files", "readback", "child"])
def test_canonical_publisher_failure_never_promotes(
    failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Canonical metadata inherits transport bounds and restore/identity guards."""
    hub = catalogue_hub(monkeypatch)
    if failure == "bytes":
        monkeypatch.setattr(module, "MAX_BYTES", 1)
    elif failure == "files":
        monkeypatch.setattr(module, "MAX_FILES", 1)
    elif failure == "readback":
        hub.corrupt = True
    else:
        monkeypatch.setattr(
            hub, "info", lambda repo: {"id": repo, "private": True, "gated": False}
        )
    reasons = {
        "bytes": "snapshot_byte_budget_exceeded",
        "files": "invalid_snapshot_file_set",
        "readback": "remote_integrity_failure",
        "child": "child_repository_not_public",
    }
    with pytest.raises(ValueError, match=reasons[failure]):
        publication.publish_catalogue(hub, SEEDS, canonical_track=TRACK)
    assert "current.json" not in hub.files
    assert "README.md" not in hub.files
    assert hub.calls == (1 if failure == "readback" else 0)


def test_failed_canonical_upgrade_preserves_v1_pointer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed v2 cold restore cannot move the previously verified v1 pointer."""
    hub = catalogue_hub(monkeypatch)
    publication.publish_catalogue(hub, SEEDS)
    pointer, card = hub.files["current.json"], hub.files["README.md"]
    original = hub.download

    def corrupt_registry(
        repo: str, revision: str, name: str, output: Path, size: int
    ) -> None:
        original(repo, revision, name, output, size)
        if name.endswith("/registry.json"):
            output.write_bytes(b"bad")

    monkeypatch.setattr(hub, "download", corrupt_registry)
    with pytest.raises(ValueError, match="remote_integrity_failure"):
        publication.publish_catalogue(hub, SEEDS, canonical_track=TRACK)
    assert hub.files["current.json"] == pointer
    assert hub.files["README.md"] == card
    assert hub.calls == 3  # Only immutable candidate bytes were staged.


@pytest.mark.parametrize("fault", ["missing", "forged", "newline_revision"])
def test_child_manifest_failure_preserves_existing_catalogue(
    fault: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No global snapshot upload or promotion precedes complete child checks."""
    hub = catalogue_hub(monkeypatch)
    publication.publish_catalogue(hub, SEEDS)
    before = dict(hub.files)
    original_sizes, original_download = hub.sizes, hub.download

    def sizes(repo: str, revision: str, names: list[str]) -> dict:
        if fault == "newline_revision" and repo != publication.CATALOGUE_REPO:
            assert names == ["current.json"], "invalid revision reached child manifest"
            return {
                "current.json": original_sizes(repo, revision, names)["current.json"]
                + 2
            }
        if (
            fault == "missing"
            and repo != publication.CATALOGUE_REPO
            and names[0].endswith("/manifest.json")
        ):
            return {}
        return original_sizes(repo, revision, names)

    def download(repo: str, revision: str, name: str, output: Path, size: int) -> None:
        if fault == "newline_revision" and repo != publication.CATALOGUE_REPO:
            assert name == "current.json"
            original_download(repo, revision, name, output, size - 2)
            payload = output.read_bytes()
            output.write_bytes(payload.replace(b"b" * 40, b"b" * 40 + b"\\n"))
        else:
            original_download(repo, revision, name, output, size)
        if (
            fault == "forged"
            and repo != publication.CATALOGUE_REPO
            and name.endswith("/manifest.json")
        ):
            payload = output.read_bytes()
            output.write_bytes(payload.replace(b'"unreviewed"', b'"unapprove"'))

    monkeypatch.setattr(hub, "sizes", sizes)
    monkeypatch.setattr(hub, "download", download)
    with pytest.raises(ValueError, match="child_manifest"):
        publication.publish_catalogue(hub, SEEDS, canonical_track=TRACK)
    assert hub.files == before
    assert hub.calls == 2


def test_canonical_child_refs_are_manifest_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All 23 child pins are covered by the immutable global manifest digest."""
    hub = catalogue_hub(monkeypatch)
    base = build_source_index(SEEDS, TRACK)
    result = publication.publish_catalogue(hub, SEEDS, canonical_track=TRACK)
    prefix = f"snapshots/{result['manifest_sha256']}/"
    payload = hub.files[prefix + "child-manifests.json"]
    receipt = json.loads(payload)
    refs = {row["source_id"]: row for row in receipt["children"]}
    children = [
        row
        for row in json.loads(base["registry.json"])["sources"]
        if row["hf_repo_id"] is not None
    ]
    assert len(refs) == len(children) == 23
    for source in children:
        row = refs[source["id"]]
        assert row["repo_id"] == source["hf_repo_id"]
        assert row["pointer_revision"] == source["hf_revision"]
        assert row["entity_id"] == source["entity_id"]
    manifest = json.loads(hub.files[prefix + "manifest.json"])
    binding = next(
        row for row in manifest["files"] if row["path"] == "child-manifests.json"
    )
    assert binding["sha256"] == hashlib.sha256(payload).hexdigest()
    assert binding["bytes"] == len(payload)
    for name, data in base.items():
        if name != "manifest.json":
            assert hub.files[prefix + name] == data
    assert receipt["raw_objects_verified"] is False
