"""Fail-closed contracts for the isolated ArchiveBox preservation pilot."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

if TYPE_CHECKING:
    from pathlib import Path

_ALLOWED_HOSTS = frozenset(
    {
        "treasury.govt.nz",
        "www.treasury.govt.nz",
        "nzdmo.govt.nz",
        "www.nzdmo.govt.nz",
    }
)
_IMAGE_PATTERN = re.compile(r"^archivebox/archivebox@sha256:[0-9a-f]{64}$")
_MAX_CANDIDATES = 5


class ArchiveBoxPilotError(ValueError):
    """A bounded ArchiveBox pilot invariant failed."""

    def __init__(self, error_class: str) -> None:
        """Expose a stable error class without echoing unsafe input."""
        self.error_class = error_class
        super().__init__(error_class)


@dataclass(frozen=True, slots=True)
class PilotDocument:
    """Canonical pilot document and its content identity."""

    document: dict[str, object]
    canonical_json: bytes
    sha256: str


def _error(error_class: str) -> ArchiveBoxPilotError:
    return ArchiveBoxPilotError(error_class)


def _canonical_document(document: dict[str, object]) -> PilotDocument:
    canonical = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return PilotDocument(
        document=document,
        canonical_json=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )


def _validate_candidate_url(url: str) -> None:
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError as error:
        raise _error("unsafe_candidate_url") from error
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or not parsed.path.startswith("/")
        or parsed.fragment
    ):
        raise _error("unsafe_candidate_url")
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise _error("candidate_host_not_allowed")


def build_input_manifest(
    urls: list[str], *, image: str, prepared_at: str
) -> PilotDocument:
    """Validate and identify a bounded, order-independent pilot input set."""
    if not urls:
        raise _error("empty_candidate_set")
    if len(urls) > _MAX_CANDIDATES:
        raise _error("too_many_candidates")
    if len(set(urls)) != len(urls):
        raise _error("duplicate_candidate_url")
    if not _IMAGE_PATTERN.fullmatch(image):
        raise _error("image_not_digest_pinned")
    for url in urls:
        _validate_candidate_url(url)
    ordered = sorted(urls)
    return _canonical_document(
        {
            "schema_version": "archive-govt-nz.archivebox-pilot-input/v1",
            "prepared_at": prepared_at,
            "image": image,
            "candidate_count": len(ordered),
            "candidates": ordered,
            "authority": "secondary-web-preservation-pilot",
            "promotion_policy": "existing-admission-gates-required",
        }
    )


def load_input_manifest(payload: dict[str, object]) -> PilotDocument:
    """Rebuild and verify a serialized input manifest."""
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise _error("invalid_input_manifest")
    candidate_values = cast("list[object]", candidates)
    if not all(isinstance(item, str) for item in candidate_values):
        raise _error("invalid_input_manifest")
    image = payload.get("image")
    prepared_at = payload.get("prepared_at")
    expected = payload.get("canonical_sha256")
    if not isinstance(image, str) or not isinstance(prepared_at, str):
        raise _error("invalid_input_manifest")
    rebuilt = build_input_manifest(
        cast("list[str]", candidate_values), image=image, prepared_at=prepared_at
    )
    if expected is not None and expected != rebuilt.sha256:
        raise _error("input_manifest_hash_mismatch")
    return rebuilt


def _output_role(relative_path: str) -> str:
    lowered = relative_path.lower()
    if ".warc" in lowered:
        return "secondary-warc"
    if lowered.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "secondary-screenshot"
    if lowered.endswith((".html", ".htm")):
        return "secondary-html"
    if lowered.endswith((".json", ".sqlite3", ".sqlite")):
        return "secondary-metadata"
    return "secondary-other"


def inventory_archivebox_output(
    root: Path,
    *,
    manifest: PilotDocument,
    observed_at: str,
    max_total_bytes: int,
    max_files: int,
) -> PilotDocument:
    """Hash a bounded output tree without treating any file as an original."""
    if max_total_bytes < 1 or max_files < 1:
        raise _error("invalid_inventory_bound")
    if not root.is_dir() or root.is_symlink():
        raise _error("archivebox_output_missing")
    files: list[dict[str, object]] = []
    total_bytes = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise _error("archivebox_output_symlink")
        if not path.is_file():
            continue
        if len(files) >= max_files:
            raise _error("output_files_exceeded")
        size = path.stat().st_size
        total_bytes += size
        if total_bytes > max_total_bytes:
            raise _error("output_bytes_exceeded")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        relative = path.relative_to(root).as_posix()
        files.append(
            {
                "path": relative,
                "bytes": size,
                "sha256": digest.hexdigest(),
                "role": _output_role(relative),
                "authoritative_original": False,
            }
        )
    if not files:
        raise _error("empty_archivebox_output")
    amplification = round(total_bytes / len(manifest.canonical_json), 6)
    return _canonical_document(
        {
            "schema_version": "archive-govt-nz.archivebox-pilot-receipt/v1",
            "observed_at": observed_at,
            "state": "outputs-inventoried-and-hashed",
            "input_manifest_sha256": manifest.sha256,
            "image": manifest.document["image"],
            "file_count": len(files),
            "total_bytes": total_bytes,
            "storage_amplification_vs_input_manifest": amplification,
            "files": files,
            "authority": "secondary-web-preservation-pilot",
            "admission_state": "not-admitted",
            "limitations": [
                "process-success-does-not-prove-source-identity",
                "captured-page-assets-may-include-third-party-hosts",
                "github-actions-artifacts-are-operational-not-durable",
            ],
        }
    )


def render_inventory_markdown(receipt: PilotDocument) -> str:
    """Render a concise paired human-readable receipt."""
    document = receipt.document
    return "\n".join(
        [
            "# ArchiveBox pilot receipt",
            "",
            f"- State: `{document['state']}`",
            f"- Observed: `{document['observed_at']}`",
            f"- Input manifest: `{document['input_manifest_sha256']}`",
            f"- Container: `{document['image']}`",
            f"- Files inventoried: `{document['file_count']}`",
            f"- Total bytes: `{document['total_bytes']}`",
            "- Authority: `secondary-web-preservation-pilot`",
            "- Durable admission: `not-admitted`",
            "",
            "A successful container process is not evidence of source identity, ",
            "completeness, or durable publication. See the JSON receipt for hashes.",
            "",
        ]
    )
