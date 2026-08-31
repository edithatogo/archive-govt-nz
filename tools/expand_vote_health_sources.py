"""Expand Vote Health edition pages into authoritative Treasury PDFs."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

import httpx

from archive_govt_nz.domains.health_appropriations.census import (
    extract_official_links,
)


async def _fetch(
    client: httpx.AsyncClient, row: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]], str | None]:
    source = cast("str", row["url"])
    transport = f"https://r.jina.ai/http://{source.removeprefix('https://')}"
    try:
        response = await client.get(transport)
        response.raise_for_status()
    except httpx.HTTPError as error:
        return row, [], type(error).__name__
    links = extract_official_links(
        response.text,
        hosts={"www.treasury.govt.nz"},
    )
    pdfs = [
        link for link in links if urlsplit(link["url"]).path.lower().endswith(".pdf")
    ]
    return row, pdfs, None


async def _expand(census: dict[str, Any]) -> dict[str, Any]:
    rows = cast("list[dict[str, Any]]", census["records"])
    vote_rows = [row for row in rows if row["family"] == "treasury_vote_health"]
    async with httpx.AsyncClient(
        timeout=90, limits=httpx.Limits(max_connections=8)
    ) as client:
        observations = await asyncio.gather(*(_fetch(client, row) for row in vote_rows))
    expanded: list[dict[str, Any]] = [
        row for row in rows if row["family"] != "treasury_vote_health"
    ]
    resources: dict[str, dict[str, Any]] = {}
    for observed_landing, pdfs, error in observations:
        landing = dict(observed_landing)
        if error:
            landing["disposition"] = "retryable"
            landing["reason"] = f"edition expansion failed: {error}"
        else:
            landing["disposition"] = "out_of_scope"
            landing["reason"] = (
                "discovery landing page represented by authoritative linked resources"
            )
        expanded.append(landing)
        for link in pdfs:
            url = link["url"]
            resources.setdefault(
                url,
                {
                    "source_id": (
                        "treasury-vote-health-pdf-"
                        f"{hashlib.sha256(url.encode()).hexdigest()[:16]}"
                    ),
                    "family": "treasury_vote_health_document",
                    "title": link["title"],
                    "url": url,
                    "media_type": "application/pdf",
                    "observed_at": census["observed_at"],
                    "cutoff": census["cutoff"],
                    "disposition": "discovered",
                    "reason": (
                        "authoritative PDF linked by official Vote Health edition page"
                    ),
                    "rights_uri": "https://www.treasury.govt.nz/copyright-and-licensing",
                },
            )
    expanded.extend(resources[url] for url in sorted(resources))
    expanded.sort(key=lambda row: cast("str", row["source_id"]))
    return {
        **census,
        "record_count": len(expanded),
        "records": expanded,
        "vote_expansion": {
            "landing_pages": len(vote_rows),
            "pdf_resources": len(resources),
            "failed_landings": sum(error is not None for _, _, error in observations),
        },
    }


def main() -> int:
    """Expand the census and replace its metadata file deterministically."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    census = json.loads(args.census.read_text(encoding="utf-8"))
    expanded = asyncio.run(_expand(census))
    args.output.write_text(
        json.dumps(expanded, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps({"status": "passed", **expanded["vote_expansion"]}, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
