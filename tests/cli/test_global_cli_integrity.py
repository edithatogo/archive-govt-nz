"""Adversarial contracts for the service-backed global CLI foundation."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.cli import (
    archive,
    doctor,
    provenance,
    publish,
    replay,
    search,
    verify,
)
from archive_govt_nz.cli_integrity import (
    _verify_wacz_path,
    _verify_warc_stream,
    discover_archive_files,
    load_and_validate_provenance,
    load_publication_package,
    search_scope_manifest,
    validate_schema_directory,
    verify_archive_directory,
    verify_cas,
)
from archive_govt_nz.compactor import ArchiveCompactor
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def _write_fixity_manifest(root: Path, filename: str, content: bytes) -> Path:
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.archive-fixity/v1",
                "files": [
                    {
                        "path": filename,
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "size_bytes": len(content),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest


def _write_evidence_ledger(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.evidence-ledger/v1",
                "generated_at": "2026-08-20T00:00:00Z",
                "stages": [
                    {
                        "stage": "captured",
                        "state": "observed",
                        "evidence": ["receipt.json"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_replay_verifies_production_sharded_cas(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Replay must traverse and stream-verify the real object-store layout."""
    store = ContentAddressedStore(tmp_path / "cas")
    store.put_bytes(b"production-shaped object")

    code = replay(cas_dir=str(store.root), format="json")
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["status"] == "verified"
    assert payload["records_replayed"] == 1


def test_replay_detects_corrupt_sharded_object(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Replay cannot verify an object whose bytes disagree with its address."""
    store = ContentAddressedStore(tmp_path / "cas")
    receipt = store.put_bytes(b"original")
    receipt.path.write_bytes(b"corrupt")

    code = replay(cas_dir=str(store.root), format="json")
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert payload["status"] == "failed"
    assert payload["corrupted_records"] == 1


def test_cas_verifier_rejects_nonproduction_layout(tmp_path: Path) -> None:
    """Flat objects and malformed shard names are integrity failures."""
    objects = tmp_path / "cas" / "sha256"
    objects.mkdir(parents=True)
    (objects / "flat-object").write_bytes(b"flat")
    malformed_shard = objects / "zz"
    malformed_shard.mkdir()

    summary = verify_cas(tmp_path / "cas")

    assert summary.observed == 2
    assert summary.verified == 0
    assert len(summary.failures) == 2

    assert verify_cas(tmp_path / "missing").observed == 0
    assert discover_archive_files(tmp_path / "missing") == []


def test_cas_verifier_rejects_bad_object_inside_valid_shard(tmp_path: Path) -> None:
    """A valid shard directory cannot conceal a malformed object name."""
    shard = tmp_path / "cas" / "sha256" / "00"
    shard.mkdir(parents=True)
    (shard / "bad-name").write_bytes(b"bad")
    summary = verify_cas(tmp_path / "cas")
    assert summary.observed == 1
    assert summary.failures == ("invalid_layout:00/bad-name",)


def test_cas_verifier_rejects_symlinked_object(tmp_path: Path) -> None:
    """CAS identity cannot be satisfied by bytes outside the bounded store."""
    external = tmp_path / "external"
    external.write_bytes(b"external")
    digest = hashlib.sha256(external.read_bytes()).hexdigest()
    shard = tmp_path / "cas" / "sha256" / digest[:2]
    shard.mkdir(parents=True)
    (shard / digest).symlink_to(external)

    summary = verify_cas(tmp_path / "cas")

    assert summary.observed == 1
    assert summary.verified == 0
    assert summary.failures == (f"invalid_layout:{digest[:2]}/{digest}",)


def test_archive_verify_rejects_fixity_manifested_garbage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A matching filename and digest do not make arbitrary bytes a WARC."""
    garbage = b"WARC/1.0 header content"
    archive_path = tmp_path / "garbage.warc.gz"
    archive_path.write_bytes(garbage)
    manifest = _write_fixity_manifest(tmp_path, archive_path.name, garbage)

    code = archive(
        action="verify",
        output_dir=str(tmp_path),
        manifest_path=str(manifest),
        format="json",
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert payload["status"] == "failed"
    assert payload["verified_files_count"] == 0


def test_archive_verify_checks_structure_and_fixity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A real WARC with matching declared fixity can be reported verified."""
    archive_path = ArchiveCompactor.pack_records_to_warc_gz(
        [("https://example.test/data", b"payload", "application/octet-stream")],
        tmp_path / "archive.warc.gz",
    )
    content = archive_path.read_bytes()
    manifest = _write_fixity_manifest(tmp_path, archive_path.name, content)

    code = archive(
        action="verify",
        output_dir=str(tmp_path),
        manifest_path=str(manifest),
        format="json",
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["status"] == "verified"
    assert payload["verified_files_count"] == 1


def test_archive_verify_accepts_wacz_and_plain_warc(tmp_path: Path) -> None:
    """Both supported container paths receive structural and fixity checks."""
    plain = tmp_path / "plain.warc"
    plain.write_bytes(
        ArchiveCompactor.create_warc_record(
            "https://example.test/plain", "text/plain", b"plain"
        )
    )
    compressed = ArchiveCompactor.pack_records_to_warc_gz(
        [("https://example.test/zipped", b"zipped", "text/plain")],
        tmp_path / "embedded.warc.gz",
    )
    wacz = ArchiveCompactor.pack_to_wacz(
        compressed, {"profile": "data-package"}, tmp_path / "bundle.wacz"
    )
    files = [plain, compressed, wacz]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.archive-fixity/v1",
                "files": [
                    {
                        "path": path.name,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "size_bytes": path.stat().st_size,
                    }
                    for path in files
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = verify_archive_directory(tmp_path, manifest)

    assert summary.observed == 3
    assert summary.verified == 3
    assert summary.failures == ()


@pytest.mark.parametrize(
    ("content", "error"),
    [
        (b"", "empty_warc"),
        (b"NOT-WARC\r\n", "invalid_warc_version"),
        (b"WARC/1.0\r\n", "truncated_warc_headers"),
        (b"WARC/1.0\r\nbad-header\r\n\r\n", "invalid_warc_header"),
        (
            b"WARC/1.0\r\nContent-Length: 0\r\n\r\n",
            "missing_warc_type",
        ),
        (
            b"WARC/1.0\r\nWARC-Type: response\r\nContent-Length: bad\r\n\r\n",
            "invalid_warc_content_length",
        ),
        (
            b"WARC/1.0\r\nWARC-Type: response\r\nContent-Length: -1\r\n\r\n",
            "invalid_warc_content_length",
        ),
        (
            b"WARC/1.0\r\nWARC-Type: response\r\nContent-Length: 5\r\n\r\nabc",
            "truncated_warc_record",
        ),
    ],
)
def test_warc_validator_fails_closed(content: bytes, error: str) -> None:
    """Malformed WARC header and body states have stable failure classes."""
    with pytest.raises(ValueError, match=error):
        _verify_warc_stream(io.BytesIO(content))


def test_archive_manifest_requires_closed_safe_fixity_entries(tmp_path: Path) -> None:
    """Missing and escaping paths cannot enter an archive verification set."""
    archive_path = tmp_path / "archive.warc"
    archive_path.write_bytes(
        ArchiveCompactor.create_warc_record(
            "https://example.test/archive", "text/plain", b"body"
        )
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.archive-fixity/v1",
                "files": [
                    {"path": "../escape.warc", "sha256": "0" * 64, "size_bytes": 0}
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = verify_archive_directory(tmp_path, manifest)

    assert summary.verified == 0
    assert any("unsafe_fixity_path" in failure for failure in summary.failures)
    assert any("undeclared_archive" in failure for failure in summary.failures)


@pytest.mark.parametrize(
    ("package", "error"),
    [
        (None, "wacz_datapackage_missing"),
        ([], "wacz_datapackage_invalid"),
        ({}, "wacz_warc_missing"),
    ],
)
def test_wacz_validator_rejects_incomplete_containers(
    tmp_path: Path, package: object, error: str
) -> None:
    """WACZ requires a JSON object datapackage and an archive member."""
    path = tmp_path / "invalid.wacz"
    with zipfile.ZipFile(path, "w") as archive:
        if package is not None:
            archive.writestr("datapackage.json", json.dumps(package))
    with pytest.raises(ValueError, match=error):
        _verify_wacz_path(path)


def test_wacz_validator_accepts_uncompressed_warc_member(tmp_path: Path) -> None:
    """WACZ validation handles both compressed and plain WARC members."""
    path = tmp_path / "plain.wacz"
    record = ArchiveCompactor.create_warc_record(
        "https://example.test/plain-member", "text/plain", b"body"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("datapackage.json", "{}")
        archive.writestr("archive/data.warc", record)
    assert _verify_wacz_path(path) == 1


def test_wacz_validator_rejects_crc_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ZIP member CRC failure invalidates the complete WACZ container."""
    path = tmp_path / "crc.wacz"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("datapackage.json", "{}")
    monkeypatch.setattr(zipfile.ZipFile, "testzip", lambda _self: "bad-member")
    with pytest.raises(ValueError, match="wacz_crc_mismatch"):
        _verify_wacz_path(path)


def test_archive_fixity_manifest_rejects_invalid_entry_states(tmp_path: Path) -> None:
    """Every manifest field and declared byte identity is fail-closed."""
    archive_path = tmp_path / "archive.warc"
    content = ArchiveCompactor.create_warc_record(
        "https://example.test/archive", "text/plain", b"body"
    )
    archive_path.write_bytes(content)
    valid_entry = {
        "path": archive_path.name,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    }
    manifest = tmp_path / "manifest.json"
    payloads = [
        {"schema_version": "wrong", "files": [valid_entry]},
        {"schema_version": "archive-govt-nz.archive-fixity/v1", "files": []},
        {
            "schema_version": "archive-govt-nz.archive-fixity/v1",
            "files": [{**valid_entry, "path": None}],
        },
        {
            "schema_version": "archive-govt-nz.archive-fixity/v1",
            "files": [{**valid_entry, "path": "missing.warc"}],
        },
        {
            "schema_version": "archive-govt-nz.archive-fixity/v1",
            "files": [valid_entry, valid_entry],
        },
        {
            "schema_version": "archive-govt-nz.archive-fixity/v1",
            "files": [{**valid_entry, "sha256": "bad"}],
        },
        {
            "schema_version": "archive-govt-nz.archive-fixity/v1",
            "files": [{**valid_entry, "size_bytes": True}],
        },
        {
            "schema_version": "archive-govt-nz.archive-fixity/v1",
            "files": [{**valid_entry, "sha256": "0" * 64}],
        },
    ]
    for payload in payloads:
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        assert verify_archive_directory(tmp_path, manifest).failures

    manifest.write_text("{invalid", encoding="utf-8")
    assert verify_archive_directory(tmp_path, manifest).failures

    non_archive = tmp_path / "payload.bin"
    non_archive.write_bytes(content)
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.archive-fixity/v1",
                "files": [{**valid_entry, "path": non_archive.name}],
            }
        ),
        encoding="utf-8",
    )
    assert (
        "unsupported_archive_type"
        in verify_archive_directory(tmp_path, manifest).failures[0]
    )


def test_provenance_rejects_scalar_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Syntactically valid unrelated JSON is not provenance evidence."""
    ledger = tmp_path / "scalar.json"
    ledger.write_text("12345", encoding="utf-8")

    code = provenance(ledger_path=str(ledger), format="json")
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert payload["status"] == "corrupt"


def test_provenance_validates_closed_manifest_and_rejects_dangling_state(
    tmp_path: Path,
) -> None:
    """Closed archive manifests use the domain provenance validator."""
    path = tmp_path / "manifest.json"
    payload = {
        "schema_version": "archive-govt-nz.manifest/v1",
        "archive_id": "archive-1",
        "observations": [{"observation_id": "observation-1"}],
        "objects": [{"object_id": "sha256:object"}],
        "versions": [{"version_id": "version-1", "observation_id": "observation-1"}],
        "derivatives": [
            {
                "derivative_id": "derivative-1",
                "source_object_id": "sha256:object",
                "version_id": "version-1",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    summary = load_and_validate_provenance(path)
    assert summary.entities == 4

    payload["derivatives"][0]["source_object_id"] = "missing"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid_closed_manifest"):
        load_and_validate_provenance(path)

    path.write_text(json.dumps({"schema_version": "unknown"}), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported_provenance_schema"):
        load_and_validate_provenance(path)


@pytest.mark.parametrize(
    "stages",
    [
        [],
        ["invalid"],
        [{"stage": "captured", "state": "", "evidence": []}],
        [
            {"stage": "captured", "state": "observed", "evidence": []},
            {"stage": "captured", "state": "observed", "evidence": []},
        ],
    ],
)
def test_provenance_rejects_invalid_evidence_stages(
    tmp_path: Path, stages: list[object]
) -> None:
    """Evidence-ledger stage structure is validated rather than counted."""
    path = tmp_path / "ledger.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.evidence-ledger/v1",
                "stages": stages,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"invalid|duplicate"):
        load_and_validate_provenance(path)


def test_search_queries_real_scope_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Search must construct and query the existing semantic backend."""
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    (index_dir / "scope-manifest.json").write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "id": "health-1",
                        "title": "Hospital admissions",
                        "notes": "Public hospital activity",
                        "organization": {"title": "Health New Zealand"},
                        "tags": [{"name": "health"}],
                        "resources": [{"format": "CSV"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    code = search("hospital health", index_dir=str(index_dir), format="json")
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["status"] == "observed"
    assert payload["total_matches"] == 1
    assert payload["results"][0]["dataset_id"] == "health-1"


def test_search_missing_index_is_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing search state uses the no-state exit rather than fabricated success."""
    code = search("health", index_dir=str(tmp_path / "missing"), format="json")
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert payload["status"] == "no_index"


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"datasets": ["not-an-object"]},
        {"datasets": [{"id": "duplicate"}, {"id": "duplicate"}]},
    ],
)
def test_search_rejects_corrupt_scope_manifests(
    tmp_path: Path, payload: object
) -> None:
    """Search refuses malformed or ambiguous dataset identity state."""
    manifest = tmp_path / "scope.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="scope_"):
        search_scope_manifest(manifest, "query")


def test_publish_token_only_and_empty_staging_are_not_ready(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A credential is capability, not package, fixity, or rights evidence."""
    staging = tmp_path / "staging"
    staging.mkdir()
    monkeypatch.setenv("HF_TOKEN", "not-publication-evidence")

    code = publish(
        target="huggingface",
        staging_dir=str(staging),
        repository="owner/archive",
        format="json",
    )
    payload = json.loads(capsys.readouterr().out)

    assert code != 0
    assert payload["status"] != "ready"


def test_publish_requires_rights_and_prepares_without_remote_claim(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A fixed package remains blocked until its explicit rights gate clears."""
    staging = tmp_path / "staging"
    staging.mkdir()
    artifact = staging / "data.json"
    artifact.write_text("{}", encoding="utf-8")
    manifest = staging / "publication-manifest.json"
    manifest_data = {
        "schema_version": "archive-govt-nz.publication-package/v1",
        "target": "huggingface",
        "repository": "owner/archive",
        "rights": {"status": "pending", "redistribution_allowed": False},
        "files": [
            {
                "path": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "size_bytes": artifact.stat().st_size,
            }
        ],
    }
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")

    blocked = publish(
        target="huggingface",
        staging_dir=str(staging),
        repository="owner/archive",
        format="json",
    )
    blocked_payload = json.loads(capsys.readouterr().out)
    assert blocked == 3
    assert blocked_payload["status"] == "blocked_by_rights"

    manifest_data["rights"] = {
        "status": "cleared",
        "redistribution_allowed": True,
    }
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    prepared = publish(
        target="huggingface",
        staging_dir=str(staging),
        repository="owner/archive",
        format="json",
    )
    prepared_payload = json.loads(capsys.readouterr().out)
    assert prepared == 0
    assert prepared_payload["status"] == "prepared-not-published"


def test_publication_package_rejects_destination_fixity_and_rights_drift(
    tmp_path: Path,
) -> None:
    """Destination, bytes, and rights must all match the signed local package."""
    staging = tmp_path / "staging"
    staging.mkdir()
    artifact = staging / "data.json"
    artifact.write_text("{}", encoding="utf-8")
    manifest = staging / "publication-manifest.json"
    base = {
        "schema_version": "archive-govt-nz.publication-package/v1",
        "target": "huggingface",
        "repository": "owner/archive",
        "rights": {"status": "cleared", "redistribution_allowed": True},
        "files": [
            {
                "path": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "size_bytes": artifact.stat().st_size,
            }
        ],
    }
    manifest.write_text(json.dumps(base), encoding="utf-8")
    assert load_publication_package(staging, "hf", "owner/archive").files == (artifact,)
    assert load_publication_package(staging, "dry-run", "").target == "huggingface"

    with pytest.raises(ValueError, match="repository_mismatch"):
        load_publication_package(staging, "huggingface", "owner/other")
    with pytest.raises(ValueError, match="target_mismatch"):
        load_publication_package(staging, "zenodo", "owner/archive")

    artifact.write_text('{"changed":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="fixity_mismatch"):
        load_publication_package(staging, "huggingface", "owner/archive")

    artifact.write_text("{}", encoding="utf-8")
    base.pop("rights")
    manifest.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="rights_missing"):
        load_publication_package(staging, "huggingface", "owner/archive")

    base["rights"] = {"status": 1, "redistribution_allowed": "yes"}
    manifest.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="rights_invalid"):
        load_publication_package(staging, "huggingface", "owner/archive")

    base["rights"] = {"status": "pending", "redistribution_allowed": True}
    manifest.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="rights_contradictory"):
        load_publication_package(staging, "huggingface", "owner/archive")


def test_schema_directory_reports_missing_and_invalid_schemas(tmp_path: Path) -> None:
    """Schema verification distinguishes no state from malformed schemas."""
    assert validate_schema_directory(tmp_path / "missing").observed == 0
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "invalid.schema.json").write_text("[]", encoding="utf-8")
    summary = validate_schema_directory(schemas)
    assert summary.observed == 1
    assert summary.verified == 0
    assert len(summary.failures) == 1


def test_verify_executes_real_cas_schema_and_provenance_checks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Global verification succeeds only on inspected integrity evidence."""
    store = ContentAddressedStore(tmp_path / "cas")
    store.put_bytes(b"verified")
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "example.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
            }
        ),
        encoding="utf-8",
    )
    ledger = tmp_path / "ledger.json"
    _write_evidence_ledger(ledger)

    code = verify(
        cas_dir=str(store.root),
        schemas_dir=str(schemas),
        provenance_path=str(ledger),
        format="json",
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["status"] == "passed"
    assert {check["name"] for check in payload["checks"]} == {
        "bitstream_fixity",
        "schema_validity",
        "provenance_integrity",
        "python_runtime",
    }


def test_doctor_enforces_python_314(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Doctor uses the declared project runtime rather than Python 3.11."""
    monkeypatch.setattr("archive_govt_nz.cli.sys.version_info", (3, 13, 9))

    code = doctor(format="json")
    payload = json.loads(capsys.readouterr().out)

    assert code == 1
    assert payload["python_min_satisfied"] is False
    assert payload["required_python"] == ">=3.14"
