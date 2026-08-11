"""Discover bounded, lawful replacement and Internet Archive snapshot URLs."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


def _timemap(url: str, timeout: float) -> list[dict[str, str]]:
    endpoint = "https://web.archive.org/web/timemap/json?url=" + quote(url, safe="")
    request = Request(endpoint, headers={"User-Agent": "archive-govt-nz/1.0"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS host
        payload = cast("list[list[Any]]", json.load(response))
    if len(payload) < 2:  # noqa: PLR2004
        return []
    headers = [str(item) for item in payload[0]]
    return [
        {key: str(value) for key, value in zip(headers, item, strict=False)}
        for item in payload[1:]
        if item
    ]


def _snapshot(row: dict[str, str]) -> str | None:
    timestamp = row.get("timestamp")
    original = row.get("original")
    if not timestamp or not original:
        return None
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def main() -> int:
    """Discover official URL upgrades and Internet Archive snapshots."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--delay", type=float, default=0.25)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    recovery = json.loads(args.recovery.read_text(encoding="utf-8"))
    recovered = {str(item["resource_id"]) for item in recovery.get("resources", [])}
    unresolved = [
        item
        for item in plan.get("outcomes", [])
        if item.get("resource_id") not in recovered
    ]
    urls = list(
        dict.fromkeys(
            str(item["source_url"])
            for item in unresolved
            if item.get("source_url")
        )
    )
    records: list[dict[str, object]] = []
    for index, source_url in enumerate(urls):
        record: dict[str, object] = {
            "source_url": source_url,
            "official_https_candidate": source_url.replace("http://", "https://", 1),
            "source_host": urlparse(source_url).netloc,
            "internet_archive": {"status": "unavailable", "snapshots": []},
        }
        try:
            rows = _timemap(source_url, args.timeout)
            snapshots = [
                {
                    "timestamp": row.get("timestamp"),
                    "statuscode": row.get("statuscode"),
                    "mimetype": row.get("mimetype"),
                    "digest": row.get("digest"),
                    "url": _snapshot(row),
                }
                for row in rows
                if row.get("statuscode") == "200" and _snapshot(row)
            ]
            record["internet_archive"] = {
                "status": "available" if snapshots else "no-success-capture",
                "snapshots": snapshots[-10:],
            }
        except Exception as error:  # noqa: BLE001 - bounded evidence; continue batch
            record["internet_archive"] = {
                "status": "query-error",
                "error_class": type(error).__name__,
            }
        records.append(record)
        if index + 1 < len(urls):
            time.sleep(args.delay)

    output = {
        "schema_version": "replacement-discovery/v1",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "policy": {
            "lawful_sources_only": True,
            "internet_archive": (
                "timemap metadata only; no snapshot promoted without content "
                "verification"
            ),
            "prohibited_sources": [
                "Anna's Archive",
                "known illicit distribution sources",
            ],
        },
        "input_counts": {
            "unresolved_resources": len(unresolved),
            "unique_source_urls": len(urls),
        },
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "unresolved_resources": len(unresolved),
                "unique_urls": len(urls),
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
