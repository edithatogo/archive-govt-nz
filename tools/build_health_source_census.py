"""Build the cutoff-bound health-appropriations source census."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import httpx

from archive_govt_nz.domains.health_appropriations.census import (
    build_census,
    extract_official_links,
)

_VOTE_INDEX = "https://www.treasury.govt.nz/publications/budgets/vote-information?vote=1640&year=All"
_DISCOVERY_TRANSPORT = (
    f"https://r.jina.ai/http://{_VOTE_INDEX.removeprefix('https://')}"
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix="census-")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """Fetch the official index through a read-only text transport and census it."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cutoff", required=True)
    arguments = parser.parse_args()
    observed_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    response = httpx.get(_DISCOVERY_TRANSPORT, timeout=90, follow_redirects=True)
    response.raise_for_status()
    links = extract_official_links(
        response.text,
        hosts={"www.treasury.govt.nz"},
        title_pattern=r"Vote Health",
    )
    census = build_census(
        vote_links=links,
        observed_at=observed_at,
        cutoff=arguments.cutoff,
    )
    census["discovery_evidence"] = {
        "canonical_index": _VOTE_INDEX,
        "transport": "read-only text proxy",
        "transport_status": response.status_code,
        "vote_link_count": len(links),
    }
    _write(arguments.output, census)
    print(
        json.dumps(
            {"status": "passed", "records": census["record_count"]}, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
