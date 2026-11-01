"""Inventory the Ministry's court judgment links for one calendar year."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import httpx


def inventory(
    client: httpx.Client, year: int, court: str = "Supreme Court"
) -> list[str]:
    """Reject incomplete, overlapping and changing result sets."""
    if court != "Supreme Court":
        taxonomy = client.get("https://www.justice.govt.nz/jdo-taxonomy-api/courts/")
        taxonomy.raise_for_status()
        names = {row["Name"].strip().casefold(): row["Name"] for row in taxonomy.json()}
        if court.strip().casefold() not in names:
            message = "Court absent from JDO taxonomy"
            raise ValueError(message)
        court = names[court.strip().casefold()]
    start = f"{year:04d}-01-01T00:00:00Z"
    end = f"{year:04d}-12-31T23:59:59Z"
    links: set[str] = set()
    count = None
    page = 1
    while True:
        response = client.get(
            "https://www.justice.govt.nz/jdo-search-api/",
            params={
                "court": court,
                "judgmentDate": f"['{start}','{end}']",
                "page": page,
            },
        )
        response.raise_for_status()
        data = response.json()
        if count is None:
            count = data["count"]
        if count != data["count"] or not data["results"]:
            message = "Unconfirmed or changing JDO inventory"
            raise ValueError(message)
        for row in data["results"]:
            path = row["url"]
            if (
                not re.fullmatch(r"/jdo_documents/[A-Za-z0-9_-]+\.pdf", path)
                or path in links
            ):
                message = "Unexpected or duplicate judgment link"
                raise ValueError(message)
            links.add(path)
        if len(links) >= count:
            if len(links) != count:
                message = "JDO count mismatch"
                raise ValueError(message)
            return sorted(links)
        page += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int)
    parser.add_argument("--court", default="Supreme Court")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with httpx.Client(timeout=30) as session:
        result = inventory(session, args.year, args.court)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
