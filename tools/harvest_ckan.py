"""Unified end-to-end CKAN preservation harvest orchestrator."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from archive_govt_nz.ckan.client import BoundedCkanClient, CkanClientConfig
from archive_govt_nz.ckan.global_discovery import (
    GlobalCkanDiscovery,
    canonical_global_scope_manifest,
    global_scope_report_markdown,
)
from archive_govt_nz.global_capture import (
    GlobalBatchCaptureConfig,
    run_global_batch_capture,
)
from archive_govt_nz.global_policy import classify_global_manifest
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.preservation import (
    build_bagit_package,
    build_ro_crate_metadata,
)

DEFAULT_BASE_URL = "https://catalogue.data.govt.nz"
DEFAULT_USER_AGENT = (
    "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
)


@dataclass(frozen=True, slots=True)
class HarvestConfig:
    """Configuration options for the full preservation harvest pipeline."""

    base_url: str = DEFAULT_BASE_URL
    objects_dir: Path = Path("objects")
    evidence_dir: Path = Path("evidence")
    page_size: int = 100
    max_workers: int = 8
    concurrency_per_host: int = 2
    timeout_seconds: float = 45.0
    user_agent: str = DEFAULT_USER_AGENT
    max_datasets: int | None = None


async def _execute_harvest_network_phases(
    config: HarvestConfig,
) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:
    client_config = CkanClientConfig(
        base_url=config.base_url,
        user_agent=config.user_agent,
        timeout_seconds=30,
        max_attempts=3,
        base_backoff_seconds=1,
        jitter_seconds=0,
        max_response_bytes=16 * 1024 * 1024,
    )
    async with BoundedCkanClient(client_config) as client:
        discovery = GlobalCkanDiscovery(
            client,
            page_size=config.page_size,
            max_datasets=config.max_datasets,
        )
        scope = await discovery.discover()

    scope_manifest_bytes = canonical_global_scope_manifest(scope)
    scope_report_bytes = global_scope_report_markdown(scope)
    scope_dict = json.loads(scope_manifest_bytes.decode("utf-8"))

    classification_receipt = classify_global_manifest(scope_dict)

    store = ContentAddressedStore(config.objects_dir)
    batch_config = GlobalBatchCaptureConfig(
        max_workers=config.max_workers,
        max_concurrency_per_host=config.concurrency_per_host,
        timeout_seconds=config.timeout_seconds,
    )
    candidates = classification_receipt.get("records", [])
    capture_receipt = await run_global_batch_capture(candidates, store, batch_config)

    return (
        scope_manifest_bytes,
        scope_report_bytes,
        classification_receipt,
        capture_receipt,
    )


def execute_unified_harvest(config: HarvestConfig | None = None) -> dict[str, Any]:
    """Execute the full 4-stage global preservation harvest synchronously."""
    if config is None:
        config = HarvestConfig()

    started_at = datetime.now(UTC).isoformat()
    config.evidence_dir.mkdir(parents=True, exist_ok=True)
    config.objects_dir.mkdir(parents=True, exist_ok=True)

    scope_mb, scope_rb, class_rcpt, cap_rcpt = asyncio.run(
        _execute_harvest_network_phases(config)
    )

    (config.evidence_dir / "global-ckan-scope.json").write_bytes(scope_mb)
    (config.evidence_dir / "global-ckan-scope.md").write_bytes(scope_rb)
    scope_dict = json.loads(scope_mb.decode("utf-8"))

    (config.evidence_dir / "global-rights-classification.json").write_text(
        json.dumps(class_rcpt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (config.evidence_dir / "global-capture-receipt.json").write_text(
        json.dumps(cap_rcpt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    broken_urls = cap_rcpt.get("broken_urls", [])
    broken_ledger = {
        "schema_version": "archive-govt-nz.broken-urls-ledger/v1",
        "generated_at": cap_rcpt.get("generated_at"),
        "total_broken_urls": len(broken_urls),
        "broken_urls": broken_urls,
    }
    (config.evidence_dir / "global-broken-urls.json").write_text(
        json.dumps(broken_ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    ro_crate_data = build_ro_crate_metadata(scope_dict, cap_rcpt)
    (config.evidence_dir / "ro-crate-metadata.jsonld").write_text(
        json.dumps(ro_crate_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    bag_dir = config.evidence_dir / "preservation-bag"
    payload_files = [
        config.evidence_dir / "global-ckan-scope.json",
        config.evidence_dir / "global-rights-classification.json",
        config.evidence_dir / "global-capture-receipt.json",
        config.evidence_dir / "global-broken-urls.json",
        config.evidence_dir / "ro-crate-metadata.jsonld",
    ]
    build_bagit_package(bag_dir, payload_files)

    completed_at = datetime.now(UTC).isoformat()
    summary: dict[str, Any] = {
        "schema_version": "archive-govt-nz.global-harvest-summary/v1",
        "started_at": started_at,
        "completed_at": completed_at,
        "catalog_base_url": config.base_url,
        "discovered_datasets": len(scope_dict.get("datasets", [])),
        "discovered_resources": scope_dict.get("discovered_resource_count", 0),
        "eligible_resources": class_rcpt.get("counts", {}).get("eligible", 0),
        "tombstoned_resources": class_rcpt.get("counts", {}).get(
            "rights_restricted", 0
        ),
        "successful_captures": cap_rcpt.get("successful_count", 0),
        "broken_urls_count": len(broken_urls),
        "preservation_ro_crate": str(config.evidence_dir / "ro-crate-metadata.jsonld"),
        "preservation_bagit": str(bag_dir),
    }

    (config.evidence_dir / "global-harvest-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    """Run global harvester orchestrator CLI."""
    parser = argparse.ArgumentParser(
        description="Unified end-to-end CKAN preservation harvest orchestrator."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--objects-dir", type=Path, default=Path("objects"))
    parser.add_argument("--evidence-dir", type=Path, default=Path("evidence"))
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--concurrency-per-host", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument(
        "--max-datasets",
        type=int,
        default=None,
        help="Optional maximum number of datasets to discover and archive",
    )
    args = parser.parse_args()
    config = HarvestConfig(
        base_url=args.base_url,
        objects_dir=args.objects_dir,
        evidence_dir=args.evidence_dir,
        page_size=args.page_size,
        max_workers=args.workers,
        concurrency_per_host=args.concurrency_per_host,
        timeout_seconds=args.timeout,
        max_datasets=args.max_datasets,
    )
    summary = execute_unified_harvest(config)

    print("=" * 60)
    print("GLOBAL CKAN HARVEST COMPLETE")
    print(f"Datasets Discovered : {summary['discovered_datasets']}")
    print(f"Resources Evaluated : {summary['discovered_resources']}")
    print(f"Captured into CAS   : {summary['successful_captures']}")
    print(f"Broken URLs Logged  : {summary['broken_urls_count']}")
    print(f"Summary Receipt     : {args.evidence_dir / 'global-harvest-summary.json'}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
