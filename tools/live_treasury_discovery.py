"""Run a bounded read-only CKAN capability and Treasury scope observation."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from archive_govt_nz.ckan.client import BoundedCkanClient, CkanClientConfig
from archive_govt_nz.ckan.discovery import TreasuryDiscovery
from archive_govt_nz.ckan.live_evidence import write_live_evidence

_DEFAULT_BASE_URL = "https://catalogue.data.govt.nz"
_USER_AGENT = "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"


def _canonical_json(document: object) -> bytes:
    """Serialize one deterministic JSON receipt."""
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()


async def _observe(
    output_dir: Path,
    *,
    base_url: str,
    page_size: int,
) -> dict[str, object]:
    """Complete both live observations through one bounded client."""
    config = CkanClientConfig(
        base_url=base_url,
        user_agent=_USER_AGENT,
        timeout_seconds=20.0,
        max_attempts=3,
        base_backoff_seconds=1.0,
        jitter_seconds=0.25,
        max_response_bytes=8 * 1024 * 1024,
    )
    async with BoundedCkanClient(config) as client:
        capability = await client.observe_capability()
        scope = await TreasuryDiscovery(client, page_size=page_size).discover()
    return write_live_evidence(output_dir, capability, scope)


def _parse_args() -> argparse.Namespace:
    """Parse non-interactive bounded live-check arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--base-url", default=_DEFAULT_BASE_URL)
    parser.add_argument("--page-size", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    """Run the observation and emit one compact machine-readable summary."""
    args = _parse_args()
    result = asyncio.run(
        _observe(
            args.output_dir,
            base_url=args.base_url,
            page_size=args.page_size,
        )
    )
    print(_canonical_json(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
