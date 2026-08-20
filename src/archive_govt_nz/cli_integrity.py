"""Fail-closed local evidence backends for the global command-line interface."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, BinaryIO, NoReturn, cast

from jsonschema.validators import validator_for

from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError
from archive_govt_nz.provenance import ProvenanceError, build_manifest
from archive_govt_nz.semantic_search import (
    SemanticKnowledgeSearchIndex,
    extract_semantic_documents,
)

if TYPE_CHECKING:
    from archive_govt_nz.semantic_search import SemanticSearchResult

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_HEX_PREFIX = re.compile(r"^[0-9a-f]{2}$")
_ARCHIVE_SUFFIXES = (".warc", ".warc.gz", ".wacz")
_READ_SIZE = 1024 * 1024


@dataclass(frozen=True, slots=True)
class IntegritySummary:
    """Bounded result of an integrity inspection."""

    observed: int
    verified: int
    failures: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProvenanceSummary:
    """Validated provenance document summary."""

    schema_version: str
    entities: int


@dataclass(frozen=True, slots=True)
class PublicationPackage:
    """Locally fixed publication package with an explicit rights decision."""

    target: str
    repository: str
    files: tuple[Path, ...]
    rights_status: str
    redistribution_allowed: bool


def _fail(error_class: str) -> NoReturn:
    """Raise one stable local evidence validation error."""
    raise ValueError(error_class)


def _missing(error_class: str) -> NoReturn:
    """Raise one stable missing-state error."""
    raise FileNotFoundError(error_class)


def verify_cas(cas_root: Path) -> IntegritySummary:
    """Traverse the production CAS layout and stream-verify every object."""
    objects_root = cas_root / "sha256"
    if objects_root.is_symlink():
        return IntegritySummary(1, 0, ("invalid_layout:sha256",))
    if not objects_root.is_dir():
        return IntegritySummary(0, 0, ())

    object_ids: list[str] = []
    failures: list[str] = []
    for prefix_path in sorted(objects_root.iterdir()):
        if (
            prefix_path.is_symlink()
            or not prefix_path.is_dir()
            or not _HEX_PREFIX.fullmatch(prefix_path.name)
        ):
            failures.append(f"invalid_layout:{prefix_path.name}")
            continue
        for object_path in sorted(prefix_path.iterdir()):
            digest = object_path.name
            if (
                object_path.is_symlink()
                or not object_path.is_file()
                or not _SHA256.fullmatch(digest)
                or not digest.startswith(prefix_path.name)
            ):
                failures.append(f"invalid_layout:{prefix_path.name}/{digest}")
                continue
            object_ids.append(f"sha256:{digest}")

    observed = len(object_ids) + len(failures)
    store = ContentAddressedStore(cas_root, create=False)
    verified = 0
    for object_id in object_ids:
        try:
            store.verify(object_id)
        except ObjectStoreError as exc:
            failures.append(f"{object_id}:{exc.error_class}")
        else:
            verified += 1
    return IntegritySummary(observed, verified, tuple(failures))


def discover_archive_files(root: Path) -> list[Path]:
    """Return supported archive files beneath a bounded output directory."""
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.name.endswith(_ARCHIVE_SUFFIXES)
    )


def _read_exact(stream: BinaryIO, byte_count: int) -> bool:
    """Consume exactly the declared number of bytes from a binary stream."""
    remaining = byte_count
    while remaining:
        chunk = stream.read(min(_READ_SIZE, remaining))
        if not chunk:
            return False
        remaining -= len(chunk)
    return True


def _read_warc_headers(stream: BinaryIO) -> dict[str, str]:
    """Read one WARC header block from the current stream position."""
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            _fail("truncated_warc_headers")
        if line in {b"\r\n", b"\n"}:
            return headers
        try:
            name, value = line.decode("utf-8").rstrip("\r\n").split(":", 1)
        except UnicodeDecodeError, ValueError:
            _fail("invalid_warc_header")
        headers[name.lower()] = value.strip()


def _declared_content_length(headers: dict[str, str]) -> int:
    """Return one non-negative declared WARC content length."""
    if not headers.get("warc-type"):
        _fail("missing_warc_type")
    try:
        content_length = int(headers["content-length"])
    except KeyError, ValueError:
        _fail("invalid_warc_content_length")
    if content_length < 0:
        _fail("invalid_warc_content_length")
    return content_length


def _verify_warc_stream(stream: BinaryIO) -> int:
    """Validate bounded WARC headers and declared content lengths."""
    records = 0
    while True:
        first = stream.readline()
        while first in {b"\r\n", b"\n"}:
            first = stream.readline()
        if not first:
            break
        if first.rstrip(b"\r\n") not in {b"WARC/1.0", b"WARC/1.1"}:
            _fail("invalid_warc_version")
        content_length = _declared_content_length(_read_warc_headers(stream))
        if not _read_exact(stream, content_length):
            _fail("truncated_warc_record")
        records += 1
    if records == 0:
        _fail("empty_warc")
    return records


def _verify_warc_path(path: Path) -> int:
    """Open and validate one WARC or compressed WARC path."""
    if path.name.endswith(".warc.gz"):
        with gzip.open(path, "rb") as stream:
            return _verify_warc_stream(cast("BinaryIO", stream))
    with path.open("rb") as stream:
        return _verify_warc_stream(stream)


def _verify_wacz_path(path: Path) -> int:
    """Validate one WACZ container and every embedded WARC member."""
    records = 0
    with zipfile.ZipFile(path, "r") as archive:
        if archive.testzip() is not None:
            _fail("wacz_crc_mismatch")
        names = archive.namelist()
        if "datapackage.json" not in names:
            _fail("wacz_datapackage_missing")
        package = json.loads(archive.read("datapackage.json"))
        if not isinstance(package, dict):
            _fail("wacz_datapackage_invalid")
        warc_names = [
            name
            for name in names
            if name.startswith("archive/") and name.endswith((".warc", ".warc.gz"))
        ]
        if not warc_names:
            _fail("wacz_warc_missing")
        for name in warc_names:
            with archive.open(name, "r") as member:
                if name.endswith(".gz"):
                    with gzip.GzipFile(fileobj=member, mode="rb") as stream:
                        records += _verify_warc_stream(cast("BinaryIO", stream))
                else:
                    records += _verify_warc_stream(cast("BinaryIO", member))
    return records


def _hash_path(path: Path) -> tuple[str, int]:
    """Stream-hash a local path and return SHA-256 plus byte count."""
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(_READ_SIZE), b""):
            digest.update(chunk)
            byte_count += len(chunk)
    return digest.hexdigest(), byte_count


def _load_file_entries(
    manifest_path: Path, expected_schema: str
) -> list[dict[str, Any]]:
    """Load a strict local fixity manifest."""
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != expected_schema
    ):
        _fail("unsupported_fixity_manifest")
    entries = payload.get("files")
    if (
        not isinstance(entries, list)
        or not entries
        or not all(isinstance(entry, dict) for entry in entries)
    ):
        _fail("invalid_fixity_entries")
    return cast("list[dict[str, Any]]", entries)


def _resolve_manifest_entry(root: Path, entry: dict[str, Any]) -> Path:
    """Resolve one manifest entry without allowing path escape or ambiguity."""
    relative = entry.get("path")
    if not isinstance(relative, str) or not relative:
        _fail("invalid_fixity_path")
    pure_path = PurePosixPath(relative)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        _fail("unsafe_fixity_path")
    path = root.joinpath(*pure_path.parts)
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        _fail("missing_fixity_file")
    return path


def _require_archive_path(path: Path) -> None:
    """Reject fixity entries that do not name a supported archive container."""
    if not path.name.endswith(_ARCHIVE_SUFFIXES):
        _fail("unsupported_archive_type")


def verify_archive_directory(root: Path, manifest_path: Path) -> IntegritySummary:
    """Verify archive structure and declared file fixity as one closed set."""
    archive_files = discover_archive_files(root)
    try:
        entries = _load_file_entries(manifest_path, "archive-govt-nz.archive-fixity/v1")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return IntegritySummary(len(archive_files), 0, (str(exc),))

    verified = 0
    failures: list[str] = []
    declared_paths: set[Path] = set()
    for entry in entries:
        try:
            path = _resolve_manifest_entry(root, entry)
            _require_archive_path(path)
            if path in declared_paths:
                _fail("duplicate_fixity_path")
            declared_paths.add(path)
            expected_hash = entry.get("sha256")
            expected_size = entry.get("size_bytes")
            if not isinstance(expected_hash, str) or not _SHA256.fullmatch(
                expected_hash
            ):
                _fail("invalid_fixity_sha256")
            if isinstance(expected_size, bool) or not isinstance(expected_size, int):
                _fail("invalid_fixity_size")
            actual_hash, actual_size = _hash_path(path)
            if actual_hash != expected_hash or actual_size != expected_size:
                _fail("archive_fixity_mismatch")
            if path.name.endswith(".wacz"):
                _verify_wacz_path(path)
            else:
                _verify_warc_path(path)
        except (
            OSError,
            EOFError,
            gzip.BadGzipFile,
            zipfile.BadZipFile,
            ValueError,
        ) as exc:
            failures.append(f"{entry.get('path', '<invalid>')}:{exc}")
        else:
            verified += 1

    undeclared = set(archive_files) - declared_paths
    failures.extend(
        f"{path.relative_to(root).as_posix()}:undeclared_archive"
        for path in sorted(undeclared)
    )
    return IntegritySummary(len(archive_files), verified, tuple(failures))


def load_and_validate_provenance(path: Path) -> ProvenanceSummary:
    """Load one supported provenance document and validate its closure."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _fail("provenance_document_must_be_object")
    schema_version = payload.get("schema_version")
    if schema_version == "archive-govt-nz.evidence-ledger/v1":
        stages = payload.get("stages")
        if not isinstance(stages, list) or not stages:
            _fail("invalid_evidence_stages")
        names: set[str] = set()
        for stage in stages:
            if not isinstance(stage, dict):
                _fail("invalid_evidence_stage")
            name = stage.get("stage")
            state = stage.get("state")
            evidence = stage.get("evidence")
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(state, str)
                or not state
                or not isinstance(evidence, list)
                or not all(isinstance(item, str) and item for item in evidence)
            ):
                _fail("invalid_evidence_stage")
            if name in names:
                _fail("duplicate_evidence_stage")
            names.add(name)
        return ProvenanceSummary(schema_version, len(stages))

    if schema_version == "archive-govt-nz.manifest/v1":
        try:
            receipt = build_manifest(
                archive_id=str(payload.get("archive_id") or ""),
                observations=cast("list[dict[str, Any]]", payload.get("observations")),
                objects=cast("list[dict[str, Any]]", payload.get("objects")),
                versions=cast("list[dict[str, Any]]", payload.get("versions")),
                derivatives=cast(
                    "list[dict[str, Any]] | None", payload.get("derivatives")
                ),
                warc_records=cast(
                    "list[dict[str, Any]] | None", payload.get("warc_records")
                ),
                receipts=cast(
                    "dict[str, list[dict[str, Any]]] | None", payload.get("receipts")
                ),
                context=cast("dict[str, Any] | None", payload.get("context")),
            )
        except (ProvenanceError, TypeError) as exc:
            _fail(f"invalid_closed_manifest:{exc}")
        entity_count = sum(
            len(cast("list[object]", receipt.document[name]))
            for name in ("observations", "objects", "versions", "derivatives")
        )
        return ProvenanceSummary(schema_version, entity_count)
    _fail("unsupported_provenance_schema")


def validate_schema_directory(path: Path) -> IntegritySummary:
    """Validate every declared JSON Schema in a bounded directory."""
    if not path.is_dir():
        return IntegritySummary(0, 0, ())
    schema_paths = sorted(path.rglob("*.schema.json"))
    failures: list[str] = []
    verified = 0
    for schema_path in schema_paths:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            if not isinstance(schema, dict):
                _fail("schema_must_be_object")
            validator_for(schema).check_schema(schema)
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            failures.append(f"{schema_path.name}:{exc}")
        else:
            verified += 1
    return IntegritySummary(len(schema_paths), verified, tuple(failures))


def search_scope_manifest(index_path: Path, query: str) -> list[SemanticSearchResult]:
    """Load a real scope manifest and query the existing semantic index."""
    manifest_path = index_path
    if index_path.is_dir():
        manifest_path = index_path / "scope-manifest.json"
    if not manifest_path.is_file():
        _missing("scope_manifest_missing")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("datasets"), list):
        _fail("scope_manifest_invalid")
    datasets = cast("list[object]", payload["datasets"])
    identifiers = [
        dataset.get("id") if isinstance(dataset, dict) else None for dataset in datasets
    ]
    if any(
        not isinstance(identifier, str) or not identifier for identifier in identifiers
    ):
        _fail("scope_dataset_identity_invalid")
    if len(set(cast("list[str]", identifiers))) != len(identifiers):
        _fail("scope_dataset_identity_duplicate")
    documents = extract_semantic_documents(payload)
    return SemanticKnowledgeSearchIndex(documents).search(query)


def load_publication_package(
    staging_dir: Path, requested_target: str, requested_repository: str
) -> PublicationPackage:
    """Validate local publication package fixity, destination, and rights."""
    manifest_path = staging_dir / "publication-manifest.json"
    entries = _load_file_entries(
        manifest_path, "archive-govt-nz.publication-package/v1"
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    target = str(payload.get("target") or "")
    repository = str(payload.get("repository") or "")
    normalized_target = "huggingface" if requested_target == "hf" else requested_target
    if normalized_target == "dry-run":
        normalized_target = target
    if target not in {"huggingface", "zenodo"} or target != normalized_target:
        _fail("publication_target_mismatch")
    if not repository or (requested_repository and repository != requested_repository):
        _fail("publication_repository_mismatch")

    files: list[Path] = []
    for entry in entries:
        path = _resolve_manifest_entry(staging_dir, entry)
        expected_hash = entry.get("sha256")
        expected_size = entry.get("size_bytes")
        actual_hash, actual_size = _hash_path(path)
        if (
            not isinstance(expected_hash, str)
            or not _SHA256.fullmatch(expected_hash)
            or isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_hash != actual_hash
            or expected_size != actual_size
        ):
            _fail("publication_fixity_mismatch")
        files.append(path)

    rights = payload.get("rights")
    if not isinstance(rights, dict):
        _fail("publication_rights_missing")
    rights_status = rights.get("status")
    redistribution_allowed = rights.get("redistribution_allowed")
    if not isinstance(rights_status, str) or not isinstance(
        redistribution_allowed, bool
    ):
        _fail("publication_rights_invalid")
    if redistribution_allowed and rights_status != "cleared":
        _fail("publication_rights_contradictory")
    return PublicationPackage(
        target,
        repository,
        tuple(files),
        rights_status,
        redistribution_allowed,
    )
