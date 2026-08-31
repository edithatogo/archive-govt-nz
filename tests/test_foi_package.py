"""Original-byte FOI packages survive cold restoration and reject false inputs."""
# ruff: noqa: SLF001 -- exercise bounded parser primitives without allocating gigabytes

import gzip
import hashlib
import importlib.util
import io
import json
import sys
import tarfile
from dataclasses import replace
from pathlib import Path
from typing import IO, TYPE_CHECKING
from unittest.mock import MagicMock

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from jsonschema import Draft202012Validator
from warcio.statusandheaders import StatusAndHeaders
from warcio.warcwriter import WARCWriter

import archive_govt_nz.foi_package as module
import archive_govt_nz.foi_publication as publication
from archive_govt_nz.foi_package import (
    CaptureContext,
    FOIPackageError,
    prepare_package,
    restore_package,
    verify_package,
)
from archive_govt_nz.foi_publication import publish_raw_package

if TYPE_CHECKING:
    from collections.abc import Callable


def capture(
    root: Path, *, events: list | None = None, html: bytes = b"<html>fixture</html>"
) -> str:
    """Reproduce the adapter's single gzip container without real source data."""
    request = root / "data/raw/requests/authority/1"
    request.mkdir(parents=True)
    document = {
        "id": 1,
        "info_request_events": [
            {"id": 2, "event_type": "response", "created_at": "2026-08-30T00:00:00Z"}
        ],
    }
    if events is not None:
        document["info_request_events"] = events
    raw_json = json.dumps(document, indent=3).encode()
    (request / "request.json").write_text(json.dumps(document))
    (request / "page.html").write_bytes(html)
    attachment = root / "data/attachments/fixture.gz"
    attachment.parent.mkdir(parents=True)
    attachment.write_bytes(gzip.compress(b"fixture attachment", mtime=0))
    warc = root / "data/warc/capture.warc.gz"
    warc.parent.mkdir(parents=True)
    resources = []
    with gzip.open(warc, "wb") as stream:
        writer = WARCWriter(stream, gzip=False)
        for kind, payload, path in [
            ("json", raw_json, None),
            ("html", html, None),
            ("attachment", attachment.read_bytes(), "data/attachments/fixture.gz"),
        ]:
            record = writer.create_warc_record(
                "https://example.org/" + kind,
                "response",
                payload=io.BytesIO(payload),
                http_headers=StatusAndHeaders(
                    "200 OK",
                    [("Content-Type", "application/octet-stream")]
                    + ([("Content-Encoding", "gzip")] if kind == "attachment" else []),
                    protocol="HTTP/1.1",
                ),
            )
            writer.write_record(record)
            resources.append(
                {
                    "kind": kind,
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "path": path,
                    "warc_record_id": record.rec_headers.get_header("WARC-Record-ID"),
                    "url": "https://example.org/" + kind,
                    "content_type": "application/octet-stream",
                }
            )
    (request / "snapshot_meta.json").write_text(json.dumps({"resources": resources}))
    files = [
        {
            "path": p.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "size": p.stat().st_size,
        }
        for p in sorted(root.rglob("*"))
        if p.is_file()
    ]
    inventory = {
        "schema": "fyi-archive.raw-batch-inventory.v1",
        "request_count": 1,
        "warc_resource_count": 3,
        "total_bytes": sum(p["size"] for p in files),
        "public_publication_verified": False,
        "storage_scope": (
            "temporary GitHub artifact; durable publication still required"
        ),
        "files": files,
    }
    payload = json.dumps(inventory).encode()
    (root / "raw-package-manifest.json").write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def prepare(root: Path, output: Path, digest: str) -> dict:
    """Use an explicit synthetic capture receipt context."""
    return prepare_package(
        root,
        output,
        context=CaptureContext(
            "nz-fyi", "NZ", "2026-08-30T00:00:00Z", "a" * 40, "123", "1.2.1"
        ),
        inventory_sha256=digest,
    )


def test_byte_exact_metadata_resources_events_and_cold_restore(tmp_path: Path) -> None:
    """Verify the named archive-integrity contract."""
    source = tmp_path / "capture"
    digest = capture(source)
    package = tmp_path / "package"
    manifest = prepare(source, package, digest)
    assert manifest["publication_status"] == "not_published"
    assert manifest["counts"]["requests"] == 1
    assert manifest["counts"]["responses"] == 3
    assert manifest["counts"]["events"] == 1
    resources = pq.read_table(package / "indexes/resources.parquet").to_pylist()
    assert {r["kind"] for r in resources} == {"json", "html", "attachment"}
    assert all(r["object_id"] == "sha256:" + r["sha256"] for r in resources)
    verify_package(package)
    restored = tmp_path / "restored"
    restore_package(package, restored)
    for path in source.rglob("*"):
        if path.is_file():
            assert (
                restored / path.relative_to(source)
            ).read_bytes() == path.read_bytes()
    assert prepare(source, package, digest) == manifest
    assert prepare(source, tmp_path / "second", digest) == manifest


@pytest.mark.parametrize(
    "fault",
    ["digest", "missing", "corrupt", "extra", "symlink", "traversal", "wrong_count"],
)
def test_reject_untrusted_or_incomplete_capture(tmp_path: Path, fault: str) -> None:
    """Verify the named archive-integrity contract."""
    source = tmp_path / "capture"
    digest = capture(source)
    if fault == "digest":
        digest = "0" * 64
    if fault == "missing":
        (source / "data/warc/capture.warc.gz").unlink()
    if fault == "corrupt":
        (source / "data/raw/requests/authority/1/page.html").write_bytes(b"bad")
    if fault == "extra":
        (source / "data/unlisted").write_bytes(b"hidden")
    if fault == "symlink":
        (source / "data/link").symlink_to(source / "data/warc")
    if fault in {"traversal", "wrong_count"}:
        path = source / "raw-package-manifest.json"
        document = json.loads(path.read_text())
        if fault == "traversal":
            document["files"][0]["path"] = "../outside"
        else:
            document["request_count"] = 2
        path.write_text(json.dumps(document))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(FOIPackageError):
        prepare(source, tmp_path / "package", digest)
    assert not (tmp_path / "package").exists()


def test_reject_corrupt_package_and_nonempty_restore(tmp_path: Path) -> None:
    """Verify the named archive-integrity contract."""
    source = tmp_path / "capture"
    digest = capture(source)
    package = tmp_path / "package"
    prepare(source, package, digest)
    target = tmp_path / "restored"
    target.mkdir()
    (target / "keep").write_bytes(b"user data")
    with pytest.raises(FOIPackageError):
        restore_package(package, target)
    (package / "raw.tar").write_bytes(b"corrupt")
    with pytest.raises(FOIPackageError):
        verify_package(package)
    assert (target / "keep").read_bytes() == b"user data"


def repin_inventory(root: Path) -> str:
    """Model a newly trusted observation so deeper consistency checks are tested."""
    path = root / "raw-package-manifest.json"
    document = json.loads(path.read_text())
    for row in document["files"]:
        target = root / row["path"]
        row.update(
            size=target.stat().st_size,
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        )
    document["total_bytes"] = sum(row["size"] for row in document["files"])
    path.write_text(json.dumps(document))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repin_package(root: Path) -> None:
    """Update envelope hashes to test semantic integrity, not just fixity."""
    path = root / "manifest.json"
    document = json.loads(path.read_text())
    for row in document["files"]:
        target = root / row["path"]
        row.update(
            bytes=target.stat().st_size,
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        )
    path.write_text(json.dumps(document))


@pytest.mark.parametrize(
    "fault",
    [
        "schema",
        "claimed_public",
        "empty",
        "duplicate",
        "outside_scope",
        "negative_size",
        "bool_size",
        "wrong_total",
    ],
)
def test_inventory_policy_invariants(tmp_path: Path, fault: str) -> None:
    """A trusted hash cannot make an internally invalid inventory acceptable."""
    source = tmp_path / "capture"
    capture(source)
    path = source / "raw-package-manifest.json"
    doc = json.loads(path.read_text())
    if fault == "schema":
        doc["schema"] = "CDX-discovery-only"
    elif fault == "claimed_public":
        doc["public_publication_verified"] = True
    elif fault == "empty":
        doc["files"] = []
    elif fault == "duplicate":
        doc["files"].append(doc["files"][0])
    elif fault == "outside_scope":
        doc["files"][0]["path"] = "README.md"
    elif fault == "negative_size":
        doc["files"][0]["size"] = -1
    elif fault == "bool_size":
        doc["files"][0]["size"] = True
    else:
        doc["total_bytes"] += 1
    path.write_text(json.dumps(doc))
    with pytest.raises(FOIPackageError):
        prepare(
            source, tmp_path / "package", hashlib.sha256(path.read_bytes()).hexdigest()
        )


@pytest.mark.parametrize(
    "fault",
    [
        "no_json",
        "double_json",
        "missing_record",
        "duplicate_record",
        "bad_kind",
        "attachment_path",
        "changed_html",
        "normalized_json",
        "request_id",
    ],
)
def test_original_response_relationships(tmp_path: Path, fault: str) -> None:
    """Raw responses must substantiate every request and attachment reference."""
    source = tmp_path / "capture"
    capture(source)
    metadata = source / "data/raw/requests/authority/1/snapshot_meta.json"
    request = source / "data/raw/requests/authority/1/request.json"
    doc = json.loads(metadata.read_text())
    if fault == "no_json":
        doc["resources"] = doc["resources"][1:]
    elif fault == "double_json":
        doc["resources"].append(doc["resources"][0])
    elif fault == "missing_record":
        doc["resources"][0]["warc_record_id"] = "missing"
    elif fault == "duplicate_record":
        doc["resources"].append(doc["resources"][-1])
    elif fault == "bad_kind":
        doc["resources"][-1]["kind"] = "extracted_summary"
    elif fault == "attachment_path":
        doc["resources"][-1]["path"] = "data/no-such-file"
    elif fault == "changed_html":
        (source / "data/raw/requests/authority/1/page.html").write_bytes(b"different")
    else:
        raw = json.loads(request.read_text())
        if fault == "request_id":
            raw["id"] = "not-a-request"
        else:
            raw["invented"] = True
        request.write_text(json.dumps(raw))
    metadata.write_text(json.dumps(doc))
    with pytest.raises(FOIPackageError):
        prepare(source, tmp_path / "package", repin_inventory(source))


@pytest.mark.parametrize(
    "name",
    ["", "/absolute", "../parent", "./same", "a//b", "C:drive", "a\\b", "a/../b"],
)
def test_path_ambiguity_is_rejected(tmp_path: Path, name: str) -> None:
    """Portable restore names cannot exploit platform path differences."""
    with pytest.raises(FOIPackageError):
        module.safe_path(tmp_path, name)


def test_json_and_resource_budgets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stored-byte, file-count and parser budgets fail before publication."""
    source = tmp_path / "capture"
    digest = capture(source)
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_FILES", 1)
        with pytest.raises(FOIPackageError):
            prepare(source, tmp_path / "p1", digest)
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_JSON", 1)
        with pytest.raises(FOIPackageError):
            prepare(source, tmp_path / "p2", digest)
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_BYTES", 1)
        with pytest.raises(FOIPackageError):
            prepare(source, tmp_path / "p3", digest)
    non_object = tmp_path / "not-object.json"
    non_object.write_text("[]")
    with pytest.raises(FOIPackageError):
        module.load_json(non_object)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_id", "../bad"),
        ("country", "NZL"),
        ("captured_at", "yesterday"),
        ("source_revision", "main"),
        ("source_run_id", "unknown"),
        ("adapter_version", "latest"),
    ],
)
def test_capture_context_is_revision_bound(
    tmp_path: Path, field: str, value: str
) -> None:
    """Labels cannot substitute for a pinned capture revision and run identity."""
    source = tmp_path / "capture"
    digest = capture(source)
    context = CaptureContext(
        "nz-fyi", "NZ", "2026-08-30T00:00:00Z", "a" * 40, "123", "1.2.1"
    )
    with pytest.raises(FOIPackageError):
        prepare_package(
            source,
            tmp_path / "package",
            context=replace(context, **{field: value}),
            inventory_sha256=digest,
        )


@pytest.mark.parametrize(
    "fault",
    [
        "schema",
        "status",
        "duplicate_file",
        "extra_file",
        "missing_file",
        "wrong_count",
        "bad_object",
        "cross_source",
        "orphan_response",
        "orphan_event",
        "original_reference",
        "duplicate_request",
        "parquet",
    ],
)
def test_package_manifest_and_relationship_tampering(  # noqa: C901, PLR0912
    tmp_path: Path, fault: str
) -> None:
    """Rehashed transport metadata cannot conceal inconsistent indexes."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    manifest_path = package / "manifest.json"
    doc = json.loads(manifest_path.read_text())
    table = None
    if fault == "schema":
        doc["schema_version"] = "unknown"
    elif fault == "status":
        doc["publication_status"] = "published"
    elif fault == "duplicate_file":
        doc["files"].append(doc["files"][0])
    elif fault == "extra_file":
        (package / "extra").write_bytes(b"unlisted")
    elif fault == "missing_file":
        doc["files"] = doc["files"][1:]
    elif fault == "wrong_count":
        doc["counts"]["requests"] += 1
    else:
        table = {
            "bad_object": "objects",
            "cross_source": "objects",
            "orphan_response": "resources",
            "orphan_event": "events",
            "original_reference": "requests",
            "duplicate_request": "requests",
            "parquet": "objects",
        }[fault]
        path = package / f"indexes/{table}.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if fault == "bad_object":
            rows[0]["object_id"] = "sha256:" + "0" * 64
        elif fault == "cross_source":
            rows[0]["source_id"] = "other-instance"
        elif fault in {"orphan_response", "orphan_event"}:
            rows[0]["request_id"] = "other-instance:99"
        elif fault == "original_reference":
            rows[0]["original_json_sha256"] = "0" * 64
        elif fault == "duplicate_request":
            rows.append(rows[0])
        else:
            rows[0]["role"] = "changed"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        if fault != "parquet":
            pq.write_table(
                pa.Table.from_pylist(rows), package / f"indexes/{table}.parquet"
            )
    manifest_path.write_text(json.dumps(doc))
    if table is not None:
        repin_package(package)
    with pytest.raises(FOIPackageError):
        verify_package(package)


@pytest.mark.parametrize(
    "fault",
    ["removed", "changed", "duplicate", "symlink", "wrong_size", "foreign_member"],
)
def test_raw_tar_is_not_a_trusted_extractor(tmp_path: Path, fault: str) -> None:
    """Only exact regular members can resolve content-addressed object references."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    raw = package / "raw.tar"
    with tarfile.open(raw) as archive:
        entries = []
        for entry in archive:
            stream = archive.extractfile(entry)
            assert stream is not None
            entries.append((entry, stream.read()))
    if fault == "removed":
        entries.pop()
    elif fault == "duplicate":
        entries.append(entries[0])
    elif fault == "changed":
        entries[0] = (entries[0][0], b"x" * len(entries[0][1]))
    elif fault == "wrong_size":
        entries[0][0].size += 1
        entries[0] = (entries[0][0], entries[0][1] + b"x")
    elif fault == "foreign_member":
        entries[0][0].name = "../outside"
    else:
        entries[0][0].type = tarfile.SYMTYPE
        entries[0][0].linkname = "../../outside"
        entries[0][0].size = 0
    with tarfile.open(raw, "w") as archive:
        for entry, data in entries:
            archive.addfile(entry, io.BytesIO(data))
    repin_package(package)
    with pytest.raises(FOIPackageError):
        restore_package(package, tmp_path / "restore")
    assert not (tmp_path / "restore").exists()


def test_symlink_internal_path_and_output_collisions(tmp_path: Path) -> None:
    """Existing packages and source paths cannot be silently replaced."""
    source = tmp_path / "capture"
    digest = capture(source)
    with pytest.raises(FOIPackageError):
        prepare(source, source / "output", digest)
    (tmp_path / "link").symlink_to(source, target_is_directory=True)
    with pytest.raises(FOIPackageError):
        module.safe_path(tmp_path, "link/file")
    with pytest.raises(FOIPackageError):
        prepare(tmp_path / "link", tmp_path / "output", digest)
    with pytest.raises(FOIPackageError):
        prepare(source, tmp_path / "link", digest)
    package = tmp_path / "package"
    prepare(source, package, digest)
    context = CaptureContext(
        "nz-fyi", "NZ", "2026-08-31T00:00:00Z", "a" * 40, "123", "1.2.1"
    )
    with pytest.raises(FOIPackageError):
        prepare_package(source, package, context=context, inventory_sha256=digest)


def test_file_index_and_package_budget_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Independent file and decoded-index limits constrain malformed inputs."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_FILES", 1)
        with pytest.raises(FOIPackageError):
            module._files(package)
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_BYTES", 1)
        with pytest.raises(FOIPackageError):
            verify_package(package)
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_JSON", 1)
        with pytest.raises(FOIPackageError):
            module._read_rows(package, "objects")
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_FILES", 0)
        with pytest.raises(FOIPackageError):
            module._read_rows(package, "objects")
    (package / "indexes/events.jsonl").write_text("[]\n")
    with pytest.raises(FOIPackageError):
        module._read_rows(package, "events")


def test_whole_warc_expansion_budget_and_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A WARC container is bounded independently of its stored compressed size."""
    source = tmp_path / "capture"
    capture(source)
    warc = source / "data/warc/capture.warc.gz"
    store = module.ContentAddressedStore(tmp_path / "cas")
    with monkeypatch.context() as patch:
        patch.setattr(module, "MAX_BYTES", 1)
        with pytest.raises(FOIPackageError):
            module._responses(source, store)
    content = gzip.decompress(warc.read_bytes())
    warc.write_bytes(gzip.compress(content.replace(b"200 OK", b"404 NO")))
    with pytest.raises(FOIPackageError):
        module._responses(source, store)
    with io.BytesIO() as stream:
        writer = WARCWriter(stream, gzip=False)
        writer.write_record(
            writer.create_warc_record(
                "https://example.org",
                "warcinfo",
                payload=io.BytesIO(b"format: fixture\r\n"),
            )
        )
        warc.write_bytes(gzip.compress(stream.getvalue() + content))
    assert len(module._responses(source, store)) == 3


@pytest.mark.parametrize(
    "events",
    [
        [],
        [{"id": 2, "event_type": "response"}, {"id": 2, "event_type": "response"}],
        [{"id": "bad", "event_type": "response"}],
    ],
)
def test_event_identity_and_empty_event_indexes(tmp_path: Path, events: list) -> None:
    """Empty correspondence is valid; duplicate or invalid event identities are not."""
    source = tmp_path / "capture"
    digest = capture(source, events=events)
    if events:
        with pytest.raises(FOIPackageError):
            prepare(source, tmp_path / "package", digest)
    else:
        result = prepare(source, tmp_path / "package", digest)
        assert result["counts"]["events"] == 0


@pytest.mark.parametrize("target", ["raw_file", "inventory"])
def test_input_replacement_during_packaging_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    """Rechecking copied bytes detects changes after the initial inventory pass."""
    source = tmp_path / "capture"
    digest = capture(source)
    original = module._inventory

    def replace_after_check(root: Path, expected: str) -> dict:
        result = original(root, expected)
        path = root / (
            "data/attachments/fixture.gz"
            if target == "raw_file"
            else "raw-package-manifest.json"
        )
        path.write_bytes(b"replaced after inspection")
        return result

    monkeypatch.setattr(module, "_inventory", replace_after_check)
    with pytest.raises(FOIPackageError):
        prepare(source, tmp_path / "package", digest)
    assert not (tmp_path / "package").exists()


@pytest.mark.parametrize("stage", ["verification", "restoration", "changed_stream"])
def test_archive_reader_failures_do_not_promote_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    """An unreadable or replaced stream cannot produce a successful restore."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    with tarfile.open(package / "raw.tar") as archive:
        members = len(archive.getmembers())
    original = tarfile.TarFile.extractfile
    calls = 0

    def broken_reader(
        self: tarfile.TarFile, member: str | tarfile.TarInfo
    ) -> IO[bytes] | None:
        nonlocal calls
        calls += 1
        if calls == (1 if stage == "verification" else members + 1):
            return io.BytesIO(b"replacement") if stage == "changed_stream" else None
        return original(self, member)

    monkeypatch.setattr(tarfile.TarFile, "extractfile", broken_reader)
    with pytest.raises(FOIPackageError):
        restore_package(package, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()


def test_duplicate_restore_paths_fail_without_output(tmp_path: Path) -> None:
    """Conflicting original paths cannot overwrite a previously restored object."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    path = package / "indexes/objects.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]["source_path"] = rows[0]["source_path"]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    pq.write_table(pa.Table.from_pylist(rows), package / "indexes/objects.parquet")
    repin_package(package)
    with pytest.raises(FOIPackageError):
        restore_package(package, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()


def test_cold_restore_rebuilds_relationships_from_originals(tmp_path: Path) -> None:
    """A rehashed event index must still agree with the preserved original JSON."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    path = package / "indexes/events.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["json_pointer"] = "/invented_event"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    pq.write_table(pa.Table.from_pylist(rows), package / "indexes/events.parquet")
    repin_package(package)
    with pytest.raises(FOIPackageError, match="restored_index_semantics_mismatch"):
        restore_package(package, tmp_path / "restored")


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "foi_package_tool", ROOT / "tools/foi_package.py"
)
assert SPEC is not None
assert SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


def test_cli_prepare_verify_restore_and_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A pinned manifest permits local restore but never creates a publication."""
    source = tmp_path / "capture"
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "source_id": "nz-fyi",
                "country": "NZ",
                "captured_at": "2026-08-30T00:00:00Z",
                "source_revision": "a" * 40,
                "source_run_id": "123",
                "adapter_version": "1.2.1",
                "inventory_sha256": capture(source),
            }
        )
    )
    package = tmp_path / "package"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "foi_package",
            "prepare",
            "--root",
            str(source),
            "--output",
            str(package),
            "--capture-receipt",
            str(receipt),
        ],
    )
    assert TOOL.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["public_upload"] is False
    manifest_hash = module.sha256(package / "manifest.json")
    schema = json.loads((ROOT / "schemas/foi-package-v2.schema.json").read_text())
    Draft202012Validator(schema).validate(
        json.loads((package / "manifest.json").read_text())
    )
    for action in ["verify", "restore"]:
        arguments = [
            "foi_package",
            action,
            "--root",
            str(package),
            "--manifest-sha256",
            manifest_hash,
        ]
        if action == "restore":
            arguments.extend(["--output", str(tmp_path / "restored")])
        monkeypatch.setattr(sys, "argv", arguments)
        assert TOOL.main() == 0
    assert (tmp_path / "restored/raw-package-manifest.json").read_bytes() == (
        source / "raw-package-manifest.json"
    ).read_bytes()


@pytest.mark.parametrize("action", ["prepare", "verify", "restore"])
def test_cli_requires_explicit_trusted_parameters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    """No implicit default receipt or restore destination bypasses the contract."""
    (tmp_path / "manifest.json").write_text("{}")
    args = ["foi_package", action, "--root", str(tmp_path)]
    if action == "restore":
        args.extend(["--manifest-sha256", module.sha256(tmp_path / "manifest.json")])
    monkeypatch.setattr(sys, "argv", args)
    if action == "restore":
        # Invalid package is rejected even before checking the missing destination.
        assert TOOL.main() == 1
    else:
        with pytest.raises(SystemExit):
            TOOL.main()


def test_cli_error_output_omits_private_details(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Private exception text and raw metadata never reach structured stdout."""
    monkeypatch.setattr(
        sys, "argv", ["foi_package", "verify", "--root", str(tmp_path / "private-path")]
    )
    assert TOOL.main() == 1
    output = capsys.readouterr().out
    assert "private-path" not in output
    assert json.loads(output)["error_class"] == "FileNotFoundError"


def test_package_contains_attachment_census(tmp_path: Path) -> None:
    """Every retained attachment appears in the relationship and gap index."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    rows = pq.read_table(package / "indexes/attachments.parquet").to_pylist()
    assert len(rows) == 1
    assert rows[0]["status"] == "retained"
    assert rows[0]["event_id"] is None
    restore_package(package, tmp_path / "restored")


def test_original_v1_package_remains_restorable(tmp_path: Path) -> None:
    """Adding a census does not invalidate the previous preservation contract."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    manifest = prepare(source, package, capture(source))
    manifest["schema_version"] = module.LEGACY_SCHEMA
    manifest["files"] = [
        r for r in manifest["files"] if not r["path"].startswith("indexes/attachments.")
    ]
    for extension in ("jsonl", "parquet"):
        (package / f"indexes/attachments.{extension}").unlink()
    (package / "manifest.json").write_bytes(module.canonical(manifest))
    restore_package(package, tmp_path / "restored")
    assert (tmp_path / "restored/raw-package-manifest.json").is_file()


def test_missing_attachment_survives_reconstruction(tmp_path: Path) -> None:
    """An omitted attachment remains a gap rather than fabricated retained bytes."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    digest = capture(
        source, html=b'<a href="/request/1/response/12/attach/1/missing.pdf">file</a>'
    )
    prepare(source, package, digest)
    rows = pq.read_table(package / "indexes/attachments.parquet").to_pylist()
    missing = [r for r in rows if r["status"] == "not_retained"]
    assert len(missing) == 1
    assert missing[0]["http_status"] is None
    assert missing[0]["sha256"] is None
    restore_package(package, tmp_path / "restored")


@pytest.mark.parametrize(
    "change", ["orphan", "hash", "status", "http", "duplicate", "parent", "missing"]
)
def test_attachment_index_tampering_is_rejected(tmp_path: Path, change: str) -> None:
    """Envelope hashes cannot legitimize fabricated attachment relationships."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    manifest = prepare(source, package, capture(source))
    path = package / "indexes/attachments.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if change == "orphan":
        rows[0]["request_id"] = "wrong:1"
    elif change == "hash":
        rows[0]["sha256"] = "b" * 64
    elif change == "status":
        rows[0]["status"] = "complete"
    elif change == "http":
        rows[0]["http_status"] = "404"
    elif change == "parent":
        rows[0]["event_id"] = "wrong:1:2"
    elif change == "missing":
        rows.clear()
    else:
        rows.append(rows[0].copy())
    path.write_bytes(b"".join(module.canonical(row) for row in rows))
    pq.write_table(pa.Table.from_pylist(rows), package / "indexes/attachments.parquet")
    for row in manifest["files"]:
        file = package / row["path"]
        row.update(bytes=file.stat().st_size, sha256=module.sha256(file))
    (package / "manifest.json").write_bytes(module.canonical(manifest))
    with pytest.raises(ValueError, match="attachment_index"):
        verify_package(package)


@pytest.mark.parametrize(
    "field",
    [
        "manifest_sha256",
        "source_id",
        "repo_id",
        "reviewer",
        "rights_status",
        "privacy_status",
        "purpose",
        "evidence_references",
    ],
)
def test_raw_publication_requires_exact_decision(tmp_path: Path, field: str) -> None:
    """Publication intent cannot replace exact source and privacy clearance."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    digest = module.sha256(package / "manifest.json")
    decision = {
        "manifest_sha256": digest,
        "source_id": "nz-fyi",
        "repo_id": "edithatogo/fyi-archive-nz",
        "reviewer": "edithatogo",
        "rights_status": "approved",
        "privacy_status": "approved",
        "purpose": "public_preservation",
        "evidence_references": ["https://example.org/fixture-review"],
    }
    decision[field] = None
    with pytest.raises(ValueError, match="exact_publication_decision_required"):
        publish_raw_package(
            MagicMock(),
            package,
            trusted_manifest_sha256=digest,
            decision=decision,
            seeds=ROOT / "config/foi",
        )


def test_publication_checks_source_hash_before_network(tmp_path: Path) -> None:
    """A valid package cannot substitute for the independently trusted hash."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    with pytest.raises(ValueError, match="untrusted_package_manifest"):
        publish_raw_package(
            MagicMock(),
            package,
            trusted_manifest_sha256="0" * 64,
            decision={},
            seeds=ROOT / "config/foi",
        )


def publication_decision(package: Path) -> dict:
    """Return approval-shaped synthetic data used only with a mocked transport."""
    return {
        "manifest_sha256": module.sha256(package / "manifest.json"),
        "source_id": "nz-fyi",
        "repo_id": "edithatogo/fyi-archive-nz",
        "reviewer": "edithatogo",
        "rights_status": "approved",
        "privacy_status": "approved",
        "purpose": "public_preservation",
        "evidence_references": ["https://example.org/fixture-review"],
        "reviewed_at": "2026-08-30T01:00:00Z",
    }


def test_eligible_synthetic_package_is_restored_before_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise raw delivery without network calls or real approval claims."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    decision = publication_decision(package)
    observed = []

    def transport(
        _hub: object,
        repo: str,
        files: dict[str, Path],
        restore: Callable[[Path], None],
    ) -> dict:
        assert repo == decision["repo_id"]
        assert "raw.tar" in files
        restore(package)
        observed.append(True)
        return {"status": "fixture_verified"}

    monkeypatch.setattr(publication, "publish_snapshot", transport)
    result = publication.publish_raw_package(
        MagicMock(),
        package,
        trusted_manifest_sha256=decision["manifest_sha256"],
        decision=decision,
        seeds=ROOT / "config/foi",
    )
    assert result["status"] == "fixture_verified"
    assert observed == [True]


@pytest.mark.parametrize("mode", ["legacy", "gap"])
def test_raw_publication_blocks_legacy_or_missing_census(
    tmp_path: Path, mode: str
) -> None:
    """Rights clearance cannot override an unaccounted attachment gap."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    manifest = prepare(
        source, package, capture(source, html=b'<a href="/attach/1/missing">file</a>')
    )
    if mode == "legacy":
        manifest["schema_version"] = module.LEGACY_SCHEMA
        manifest["files"] = [
            r
            for r in manifest["files"]
            if not r["path"].startswith("indexes/attachments.")
        ]
        for extension in ("jsonl", "parquet"):
            (package / f"indexes/attachments.{extension}").unlink()
        (package / "manifest.json").write_bytes(module.canonical(manifest))
    decision = publication_decision(package)
    with pytest.raises(
        ValueError,
        match=r"attachment_census_required|attachment_gaps_block_publication",
    ):
        publish_raw_package(
            MagicMock(),
            package,
            trusted_manifest_sha256=decision["manifest_sha256"],
            decision=decision,
            seeds=ROOT / "config/foi",
        )


@pytest.mark.parametrize(
    "value",
    [
        "not-a-list",
        [None],
        [],
        ["http://example.org/review"],
        ["https://example.org/review?token=synthetic"],
    ],
)
def test_raw_review_evidence_has_structured_public_references(
    tmp_path: Path, value: object
) -> None:
    """Approval metadata cannot carry ambiguous or credential-bearing references."""
    source = tmp_path / "capture"
    package = tmp_path / "package"
    prepare(source, package, capture(source))
    decision = publication_decision(package)
    decision["evidence_references"] = value
    with pytest.raises(ValueError, match="exact_publication_decision_required"):
        publish_raw_package(
            MagicMock(),
            package,
            trusted_manifest_sha256=decision["manifest_sha256"],
            decision=decision,
            seeds=ROOT / "config/foi",
        )
