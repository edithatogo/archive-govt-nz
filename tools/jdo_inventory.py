"""Inventory the Ministry's Supreme Court judgment links for one calendar year."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def inventory(client: httpx.Client, year: int) -> list[str]:
    """Reject incomplete, overlapping and changing result sets."""
    start = f"{year:04d}-01-01T00:00:00Z"
    end = f"{year:04d}-12-31T23:59:59Z"
    links: set[str] = set()
    count = None
    page = 1
    while True:
        response = client.get(
            "https://www.justice.govt.nz/jdo-search-api/",
            params={
                "court": "Supreme Court",
                "judgmentDate": f"['{start}','{end}']",
                "page": page,
            },
        )
        response.raise_for_status()
        data = response.json()
        if count is None:
            count = data["count"]
        if count != data["count"] or not data["results"]:
            raise ValueError("Unconfirmed or changing JDO inventory")
        for row in data["results"]:
            path = row["url"]
            if not path.startswith("/jdo_documents/") or path in links:
                raise ValueError("Unexpected or duplicate judgment link")
            links.add(path)
        if len(links) >= count:
            if len(links) != count:
                raise ValueError("JDO count mismatch")
            return sorted(links)
        page += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with httpx.Client(timeout=30) as session:
        result = inventory(session, args.year)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
