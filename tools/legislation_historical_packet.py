"""Capture a bounded historical child and publish only its explicitly pinned bytes."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import io
import json
import logging
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import defusedxml.ElementTree as DefusedET
import httpx
from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

from archive_govt_nz.domains.legislation.api import HTTP_OK, NZLegislationApiClient
from archive_govt_nz.domains.legislation.corpus import LegislationArchiveService
from archive_govt_nz.domains.legislation.historical_packet import (
    Bounds,
    encoded,
    missing_targets,
    official_url,
)
from archive_govt_nz.domains.legislation.normalise import normalise_legislation_payload
from archive_govt_nz.object_store import ContentAddressedStore
from tools import legislation_parent_state as parent

REPOSITORY = "edithatogo/corpus-legislation-nz"
AUTHORITY = "user-20261031-historical-legislation-publication"
MAX_FILE = 16 * 1024 * 1024
MAX_ADDITIONS = 128 * 1024 * 1024


def write(path: Path, value: object) -> None:
    """Persist one locally owned evidence file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def digest(data: bytes) -> str:
    """Return exact-byte publication fixity."""
    return hashlib.sha256(data).hexdigest()


def package_bytes(files: dict[str, bytes]) -> bytes:
    """Use deterministic compressed canonical ZIPs within the recovery byte cap."""
    stream = io.BytesIO()
    with zipfile.ZipFile(
        stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100444 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data, compresslevel=9)
    return stream.getvalue()


class PacketClient(NZLegislationApiClient):
    """Use the existing API login, with bounded anonymous original downloads."""

    def __init__(self) -> None:
        """Retain standard source pacing and a separate total byte budget."""
        super().__init__(min_interval_seconds=1.0, max_retries=0)
        self.downloaded = 0
        self.pages: list[dict[str, Any]] = []
        self.expected: dict[str, tuple[str, str]] = {}

    def get_catalogue_page(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """Retain public source metadata without request headers or credentials."""
        payload = super().get_catalogue_page(path, params)
        self.pages.append({"path": path, "query": params, "response": payload})
        return payload

    def check_representation(self, url: str, content: bytes) -> None:
        """Reject challenge/error pages before they can enter original custody."""
        inferred = (
            "application/pdf"
            if urlsplit(url).path.endswith(".pdf")
            else "application/xml"
        )
        mime, title = self.expected.get(url, (inferred, ""))
        if mime == "application/pdf" and not content.startswith(b"%PDF-"):
            message = "historical PDF signature mismatch"
            raise ValueError(message)
        if mime == "application/xml":
            root = DefusedET.fromstring(content)
            if root.tag.rsplit("}", 1)[-1].lower() not in {"act", "legislation"}:
                message = "historical XML is not an Act representation"
                raise ValueError(message)
        if mime == "text/html" and title:
            record = normalise_legislation_payload(
                content,
                "_".join(urlsplit(url).path.split("/")[1:5]),
                title,
                url,
                source_media_type=mime,
            )
            expected = "".join(c.casefold() for c in title if c.isalnum())
            actual = "".join(c.casefold() for c in record.plain_text if c.isalnum())
            if not expected or expected not in actual:
                message = "historical HTML does not identify the offered Act"
                raise ValueError(message)

    async def get_document_raw_async(
        self, target_url: str, etag: str | None = None, last_modified: str | None = None
    ) -> tuple[int, bytes, dict[str, str]]:
        """Stream originals without transferring the API key to web endpoints."""
        del etag, last_modified
        url = official_url(target_url)
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            for _ in range(5):
                self._pace()
                async with client.stream(
                    "GET",
                    url,
                    headers={
                        "Accept": "*/*",
                        "User-Agent": "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)",
                    },
                ) as response:
                    self._last_request_at = self._time_fn()
                    if response.status_code in {301, 302, 303, 307, 308}:
                        url = official_url(urljoin(url, response.headers["location"]))
                        continue
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        if (
                            len(data) + len(chunk) > MAX_FILE
                            or self.downloaded + len(chunk) > MAX_ADDITIONS
                        ):
                            message = "historical original exceeds byte budget"
                            raise ValueError(message)
                        data.extend(chunk)
                        self.downloaded += len(chunk)
                    if response.status_code == HTTP_OK:
                        self.check_representation(target_url, bytes(data))
                    return response.status_code, bytes(data), dict(response.headers)
        message = "historical original redirect bound exceeded"
        raise ValueError(message)


def capture(state: Path, output: Path, bounds: Bounds) -> dict[str, Any]:
    """Add only absent manifestations, keeping the parent's exact records intact."""
    output.mkdir(parents=True, exist_ok=False)
    client = PacketClient()
    service = LegislationArchiveService(
        ContentAddressedStore(state / "cas"), api_client=client
    )
    manifest_path = state / "manifest.json"
    before = service.load_manifest(manifest_path)
    if before is None:
        message = "verified nonempty historical parent required"
        raise ValueError(message)
    try:
        targets, inventory = missing_targets(client, before, bounds)
    finally:
        write(output / "source-pages.json", client.pages)
    write(output / "inventory.json", inventory)
    version_titles = {
        version["version_id"]: str(version.get("title") or "")
        for selected in inventory.get("selected", [])
        for version in selected.get("versions", [])
    }
    client.expected = {
        manifestation.target_url: (
            manifestation.media_type,
            version_titles.get(expression.expression_id) or target.title,
        )
        for target in targets
        for expression in target.expression_targets
        for manifestation in expression.manifestations
    }
    if not targets:
        message = "historical packet has no missing manifestations"
        raise ValueError(message)
    result = asyncio.run(
        service.sync_works(
            targets=targets,
            checkpoint_path=state / "checkpoint.json",
            manifest_path=manifest_path,
            batch_id="historical-" + os.environ["GITHUB_RUN_ID"],
            max_works=bounds.max_works,
            force_resync=True,
            fail_fast=True,
            software_commit=os.environ["GITHUB_SHA"],
            workflow_identity=os.environ["GITHUB_WORKFLOW"],
            run_identity=os.environ["GITHUB_RUN_ID"],
        )
    )
    if result.accounting is None:
        message = "historical accounting missing"
        raise ValueError(message)
    write(state / "receipts/harvest.json", result.accounting.to_receipt())
    if (
        result.status != "success"
        or result.accounting.failed
        or result.accounting.partial
    ):
        message = "historical capture incomplete; publication prohibited"
        raise ValueError(message)
    after = result.manifest
    retained = {row["manifestation_id"]: row for row in after["records"]}
    if not all(
        retained.get(row["manifestation_id"]) == row for row in before["records"]
    ):
        message = "historical parent record changed"
        raise ValueError(message)
    parent.seal(
        state,
        parent.context_from_environment(),
        Path("build/legislation-parent-quarantine"),
    )
    files = parent.read_state(state)
    roots = parent.state_roots(files)
    raw = package_bytes(files)
    # Validate the exact emitted ZIP through the existing recovery parser.
    if parent.state_roots(parent.unpack(raw)) != roots:
        message = "historical package recovery mismatch"
        raise ValueError(message)
    (output / "canonical-state.zip").write_bytes(raw)
    metadata = {
        "schema_version": "archive-govt-nz.historical-publication/v1",
        "repository": REPOSITORY,
        "capture_run": int(os.environ["GITHUB_RUN_ID"]),
        "software_commit": os.environ["GITHUB_SHA"],
        "package_sha256": digest(raw),
        "package_size": len(raw),
        "roots": roots,
        "records_before": len(before["records"]),
        "records_after": len(after["records"]),
        "works_before": len(before["discovered_work_ids"]),
        "works_after": len(after["discovered_work_ids"]),
        "new_records": len(after["records"]) - len(before["records"]),
        "inventory_sha256": digest((output / "inventory.json").read_bytes()),
        "source_pages_sha256": digest((output / "source-pages.json").read_bytes()),
        "authority": {
            "id": AUTHORITY,
            "kind": "delegated_scope_authorization",
            "scope": (
                "API-listed official PCO Acts only; "
                "existing records retain prior rights"
            ),
        },
        "rights": {
            "basis_url": "https://www.legislation.govt.nz/copyright/",
            "statutory_text": "No copyright under section 27, Copyright Act 1994",
            "presentation_and_api_metadata": "PCO Crown copyright, source CC-BY terms",
            "attribution": (
                "Source: Parliamentary Counsel Office, New Zealand Legislation"
            ),
            "third_party_incorporated_works": "not authorized by this decision",
            "agency_published_material": "excluded from this packet",
        },
        "default_parent_promoted": False,
        "source_completeness_claim": False,
    }
    write(output / "metadata.json", metadata)
    return metadata


def validate_package(directory: Path, expected: str) -> tuple[bytes, dict[str, Any]]:
    """Bind publication to the inspected package, scope inventory and sealed state."""
    raw = (directory / "canonical-state.zip").read_bytes()
    metadata = json.loads((directory / "metadata.json").read_bytes())
    if (
        not re.fullmatch(r"[0-9a-f]{64}", expected)
        or digest(raw) != expected
        or metadata["package_sha256"] != expected
        or metadata["repository"] != REPOSITORY
        or metadata["authority"]["id"] != AUTHORITY
    ):
        message = "historical publication approval/digest mismatch"
        raise ValueError(message)
    if (
        digest((directory / "inventory.json").read_bytes())
        != metadata["inventory_sha256"]
    ):
        message = "historical inventory digest mismatch"
        raise ValueError(message)
    if (
        digest((directory / "source-pages.json").read_bytes())
        != metadata["source_pages_sha256"]
    ):
        message = "historical source metadata digest mismatch"
        raise ValueError(message)
    files = parent.unpack(raw)
    roots = parent.state_roots(files)
    seal = json.loads(files[parent.SEAL])
    parent.schema(seal, "legislation-continuation")
    lineage = json.loads(files[parent.LINEAGE])
    parent.check_lineage(lineage)
    if (
        seal["parent_lineage_sha256"] != digest(files[parent.LINEAGE])
        or seal["context"] != lineage["context"]
        or seal["context"]["run_id"] != metadata["capture_run"]
        or seal["context"]["software_commit"] != metadata["software_commit"]
    ):
        message = "historical lineage provenance mismatch"
        raise ValueError(message)
    if (
        roots != metadata["roots"]
        or seal["roots"] != roots
        or seal["status"] != "complete"
    ):
        message = "historical sealed package mismatch"
        raise ValueError(message)
    return raw, metadata


def publish(directory: Path, expected: str, output: Path) -> dict[str, Any]:
    """One parent-bound additive commit; unknown outcomes are never replayed."""
    _raw, metadata = validate_package(directory, expected)
    output.mkdir(parents=True, exist_ok=False)
    prefix = "durable-state/v1/historical-" + str(metadata["capture_run"])
    api = HfApi(token=os.environ["HF_TOKEN"])
    info = api.dataset_info(REPOSITORY, expand=["sha", "private", "gated"])
    if info.private is not False or info.gated is not False:
        message = "historical publication requires the existing ungated public dataset"
        raise ValueError(message)
    api.auth_check(REPOSITORY, repo_type="dataset", write=True)
    package_path = prefix + "/canonical-state.zip"
    metadata_path = prefix + "/metadata.json"
    inventory_path = prefix + "/inventory.json"
    source_pages_path = prefix + "/source-pages.json"
    journal = {
        "status": "prepared",
        "repository": REPOSITORY,
        "parent_revision": info.sha,
        "package_sha256": expected,
        "paths": [package_path, metadata_path, inventory_path, source_pages_path],
        "mutation_attempts": 0,
    }
    write(output / "journal.json", journal)
    if api.get_paths_info(
        REPOSITORY, paths=[package_path], repo_type="dataset", revision=info.sha
    ):
        revision = info.sha
    else:
        journal.update(status="commit_outcome_unknown", mutation_attempts=1)
        write(output / "journal.json", journal)
        result = api.create_commit(
            repo_id=REPOSITORY,
            repo_type="dataset",
            parent_commit=info.sha,
            commit_message="Preserve verified historical legislation formats",
            operations=[
                CommitOperationAdd(
                    path_in_repo=package_path,
                    path_or_fileobj=str(directory / "canonical-state.zip"),
                ),
                CommitOperationAdd(
                    path_in_repo=metadata_path,
                    path_or_fileobj=str(directory / "metadata.json"),
                ),
                CommitOperationAdd(
                    path_in_repo=inventory_path,
                    path_or_fileobj=str(directory / "inventory.json"),
                ),
                CommitOperationAdd(
                    path_in_repo=source_pages_path,
                    path_or_fileobj=str(directory / "source-pages.json"),
                ),
            ],
        )
        revision = result.oid
    verified_files = []
    for filename, local in (
        (package_path, "canonical-state.zip"),
        (metadata_path, "metadata.json"),
        (inventory_path, "inventory.json"),
        (source_pages_path, "source-pages.json"),
    ):
        downloaded = hf_hub_download(
            REPOSITORY,
            filename,
            repo_type="dataset",
            revision=revision,
            token=False,
            local_dir=output / "readback",
        )
        expected_data = (directory / local).read_bytes()
        if Path(downloaded).read_bytes() != expected_data:
            message = "historical remote readback mismatch"
            raise ValueError(message)
        verified_files.append(
            {
                "path": filename,
                "sha256": digest(expected_data),
                "size": len(expected_data),
            }
        )
    receipt = {
        **metadata,
        "status": "published_verified",
        "revision": revision,
        "package_path": package_path,
        "anonymous_readback": True,
        "verified_files": verified_files,
        "mutation_attempts": journal["mutation_attempts"],
    }
    write(output / "receipt.json", receipt)
    journal.update(status="verified", revision=revision)
    write(output / "journal.json", journal)
    return receipt


def main() -> int:
    """Operate only on isolated state; never expose SDK URLs/credentials."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["capture", "publish"])
    parser.add_argument("--state", type=Path, default=Path("build/legislation-state"))
    parser.add_argument(
        "--directory", type=Path, default=Path("build/legislation-history")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("build/legislation-history-publication")
    )
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--expected-sha256", default="")
    args = parser.parse_args()
    previous_logging_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    private = Path("build/legislation-history-private.log")
    private.parent.mkdir(parents=True, exist_ok=True)
    try:
        with (
            private.open("w") as log,
            contextlib.redirect_stdout(log),
            contextlib.redirect_stderr(log),
        ):
            result = (
                capture(args.state, args.directory, Bounds(start_page=args.start_page))
                if args.operation == "capture"
                else publish(args.directory, args.expected_sha256, args.output)
            )
    except Exception as error:  # noqa: BLE001 - sanitize SDK errors, never retry writes
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "publication_retried": False,
                }
            )
        )
        return 1
    finally:
        logging.disable(previous_logging_disable)
    print(
        json.dumps(
            {
                "status": result.get("status", "captured_verified"),
                "records_after": result["records_after"],
                "package_sha256": result["package_sha256"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
