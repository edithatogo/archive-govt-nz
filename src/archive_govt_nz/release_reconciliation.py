"""Cross-target release and recovery reconciliation contracts."""

from __future__ import annotations

import hashlib
import tarfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class ReconciliationCheck:
    """One explicit cross-target comparison."""

    name: str
    state: str
    detail: str


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Bounded report suitable for JSON or Markdown evidence."""

    state: str
    checks: tuple[ReconciliationCheck, ...]


def verify_release_archive(
    archive: Path,
    expected_sha256: str,
    required_prefixes: tuple[str, ...],
) -> ReconciliationCheck:
    """Verify package checksum, safe member names, and preservation-layer closure."""
    if not archive.is_file():
        return ReconciliationCheck("recovery_archive", "unavailable", "archive missing")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != expected_sha256:
        return ReconciliationCheck(
            "recovery_archive", "drifted", "archive checksum differs"
        )
    try:
        with tarfile.open(archive, mode="r:") as handle:
            names = {member.name for member in handle.getmembers()}
    except tarfile.TarError, OSError:
        return ReconciliationCheck(
            "recovery_archive", "invalid", "archive cannot be read"
        )
    unsafe = [
        name for name in names if name.startswith("/") or ".." in Path(name).parts
    ]
    if unsafe:
        return ReconciliationCheck(
            "recovery_archive", "invalid", "unsafe archive member path"
        )
    missing = [
        prefix
        for prefix in required_prefixes
        if not any(name.startswith(prefix) for name in names)
    ]
    if missing:
        return ReconciliationCheck(
            "recovery_archive", "incomplete", "required preservation layer missing"
        )
    return ReconciliationCheck(
        "recovery_archive", "verified", "checksum and preservation layers verified"
    )


def reconcile_release_records(
    local: Mapping[str, object],
    huggingface: Mapping[str, object],
    zenodo: Mapping[str, object],
) -> ReconciliationReport:
    """Compare identity, publication, and checksum evidence without network calls."""
    checks: list[ReconciliationCheck] = []
    local_package = _mapping(local.get("package"))
    local_sha = str(local_package.get("sha256", ""))
    zenodo_sha = str(zenodo.get("package_sha256", ""))
    if local_sha and zenodo_sha:
        checks.append(
            ReconciliationCheck(
                "package_sha256",
                "matched" if local_sha == zenodo_sha else "drifted",
                "local candidate and Zenodo receipt share the package hash"
                if local_sha == zenodo_sha
                else "package hashes differ",
            )
        )
    else:
        checks.append(
            ReconciliationCheck(
                "package_sha256", "unavailable", "one or both package hashes are absent"
            )
        )
    checks.append(
        ReconciliationCheck(
            "huggingface_revision",
            "verified" if _has_text(huggingface.get("revision")) else "unavailable",
            str(huggingface.get("revision", "no revision receipt")),
        )
    )
    checks.append(
        ReconciliationCheck(
            "zenodo_release",
            "verified"
            if zenodo.get("state") == "published" and _has_text(zenodo.get("doi"))
            else "unavailable",
            str(zenodo.get("doi", "no published DOI")),
        )
    )
    checks.append(
        ReconciliationCheck(
            "recovery_receipt",
            "verified"
            if _positive_int(zenodo.get("file_size"))
            and _has_text(zenodo.get("zenodo_checksum"))
            else "unavailable",
            "remote file size and checksum recorded"
            if zenodo.get("file_size") and zenodo.get("zenodo_checksum")
            else "remote file receipt incomplete",
        )
    )
    state = (
        "reconciled"
        if all(check.state in {"matched", "verified"} for check in checks)
        else "incomplete"
    )
    return ReconciliationReport(state, tuple(checks))


def _mapping(value: object) -> Mapping[str, object]:
    """Return a typed mapping or an empty mapping for bounded receipts."""
    return cast("Mapping[str, object]", value) if isinstance(value, Mapping) else {}


def _has_text(value: object) -> bool:
    """Accept only bounded, non-empty textual receipt fields."""
    return isinstance(value, str) and bool(value.strip())


def _positive_int(value: object) -> bool:
    """Require a genuine positive byte count, not a truthy string or float."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
