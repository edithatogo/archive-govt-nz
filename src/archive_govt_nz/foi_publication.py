"""Eligibility boundaries for public source catalogues and raw FOI packages."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn
from urllib.parse import urlsplit

from archive_govt_nz.foi_catalogue import catalogue_files
from archive_govt_nz.foi_delivery import publish_snapshot
from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_package import restore_package, sha256, verify_package

if TYPE_CHECKING:
    from archive_govt_nz.foi_delivery import Hub

CATALOGUE_REPO = "edithatogo/foi-source-catalogue"


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _review_evidence(decision: dict[str, Any]) -> bool:
    references = decision.get("evidence_references")
    if not isinstance(references, list) or not references:
        return False
    for reference in references:
        if not isinstance(reference, str):
            return False
        parsed = urlsplit(reference)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            return False
    return True


def publish_catalogue(hub: Hub, seeds: Path) -> dict[str, Any]:
    """Publish only deterministic metadata from the approved pinned seed importer."""
    catalogue = build_reviewed_catalogue(seeds)
    for source in catalogue["sources"]:
        if source["hf_repo_id"] is None:
            continue
        info = hub.info(source["hf_repo_id"])
        if (
            info["id"] != source["hf_repo_id"]
            or info["private"] is not False
            or info["gated"] is not False
        ):
            _fail("child_repository_not_public")
    content = catalogue_files(catalogue)
    with tempfile.TemporaryDirectory(prefix="foi-catalogue-candidate-") as temporary:
        root = Path(temporary)
        files = {}
        for name, data in content.items():
            path = root / name
            path.write_bytes(data)
            files[name] = path

        def restore(restored: Path) -> None:
            actual = {path.name: path.read_bytes() for path in restored.iterdir()}
            if actual != content:
                _fail("catalogue_restore_mismatch")

        result = publish_snapshot(hub, CATALOGUE_REPO, files, restore)
    return {
        **result,
        "scope": "source_catalogue_only",
        "payload_publication": False,
        "viewer_status": "not_checked",
        "coverage": catalogue["coverage"],
    }


def publish_raw_package(
    hub: Hub,
    package: Path,
    *,
    trusted_manifest_sha256: str,
    decision: dict[str, Any],
    seeds: Path,
) -> dict[str, Any]:
    """Require exact source, destination, rights and privacy approval before writes."""
    if sha256(package / "manifest.json") != trusted_manifest_sha256:
        _fail("untrusted_package_manifest")
    manifest = verify_package(package)
    catalogue = build_reviewed_catalogue(seeds)
    sources = {source["id"]: source for source in catalogue["sources"]}
    source = sources.get(manifest["source_id"])
    if (
        source is None
        or source["rights_status"] == "restricted"
        or source["entity_id"] != manifest["country"]
        or source["hf_repo_id"] is None
        or decision.get("manifest_sha256") != trusted_manifest_sha256
        or decision.get("source_id") != manifest["source_id"]
        or decision.get("repo_id") != source["hf_repo_id"]
        or decision.get("reviewer") != "edithatogo"
        or decision.get("rights_status") != "approved"
        or decision.get("privacy_status") != "approved"
        or decision.get("purpose") != "public_preservation"
        or not _review_evidence(decision)
    ):
        _fail("exact_publication_decision_required")
    if manifest["schema_version"] != "archive-govt-nz.foi-package/v2":
        _fail("attachment_census_required")
    attachments = [
        json.loads(line)
        for line in (package / "indexes/attachments.jsonl").read_bytes().splitlines()
    ]
    if any(row["status"] != "retained" for row in attachments):
        _fail("attachment_gaps_block_publication")
    with tempfile.TemporaryDirectory(prefix="foi-prepublication-restore-") as temporary:
        restore_package(package, Path(temporary) / "capture")
    files = {row["path"]: package / row["path"] for row in manifest["files"]}
    files["manifest.json"] = package / "manifest.json"

    def restore(restored: Path) -> None:
        with tempfile.TemporaryDirectory(
            prefix="foi-public-cold-restore-"
        ) as temporary:
            restore_package(restored, Path(temporary) / "capture")

    return publish_snapshot(hub, source["hf_repo_id"], files, restore)
