"""Streamlined, bounded whole-catalogue CKAN discovery tool."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from archive_govt_nz.ckan.client import BoundedCkanClient, CkanClientConfig
from archive_govt_nz.ckan.global_discovery import (
    GlobalCkanDiscovery,
    GlobalCkanScope,
    canonical_global_scope_manifest,
    global_scope_report_markdown,
)

DEFAULT_BASE_URL = "https://catalogue.data.govt.nz"
USER_AGENT = "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
MAX_PAGE_SIZE = 1000


async def _discover_scope(
    base_url: str,
    page_size: int,
) -> GlobalCkanScope:
    config = CkanClientConfig(
        base_url=base_url,
        user_agent=USER_AGENT,
        timeout_seconds=30,
        max_attempts=3,
        base_backoff_seconds=1,
        jitter_seconds=0,
        max_response_bytes=16 * 1024 * 1024,
    )
    async with BoundedCkanClient(config) as client:
        discovery = GlobalCkanDiscovery(client, page_size=page_size)
        return await discovery.discover()


def main() -> int:
    """Run global discovery across all datasets and emit manifest receipts."""
    parser = argparse.ArgumentParser(
        description="Discover the complete CKAN catalogue."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/global-ckan-scope.json"),
        help="Path for canonical scope manifest JSON",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("evidence/global-ckan-scope.md"),
        help="Path for scope summary Markdown report",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("evidence/global_discovery/raw"),
        help="Directory to store raw page responses",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()

    if args.page_size < 1 or args.page_size > MAX_PAGE_SIZE:
        raise SystemExit(2)

    scope = asyncio.run(_discover_scope(args.base_url, args.page_size))

    if args.raw_dir is not None:
        args.raw_dir.mkdir(parents=True, exist_ok=True)
        for page in scope.pages:
            page_path = args.raw_dir / f"package_search-{page.start:08d}.json"
            page_path.write_bytes(page.raw_body)

    manifest_bytes = canonical_global_scope_manifest(scope)
    markdown_bytes = global_scope_report_markdown(scope)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(manifest_bytes)

    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_bytes(markdown_bytes)

    datasets = scope.discovered_dataset_count
    resources = scope.discovered_resource_count
    print(f"Discovered {datasets} datasets, {resources} resources -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
