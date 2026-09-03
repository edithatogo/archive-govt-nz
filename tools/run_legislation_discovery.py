"""Run or classify one bounded legislation freshness attempt."""

# ruff: noqa: D103, EM101, TRY003, TRY004

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx

from archive_govt_nz.domains.legislation.discovery_lane import (
    DiscoveryScope,
    acquisition_receipts,
    discover,
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("document must be an object")
    return value


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def run(scope_path: Path, output: Path) -> None:
    value = load(scope_path)
    scope = DiscoveryScope(
        scope_id=value["scope_id"],
        terms=tuple(value["terms"]),
        legislation_types=tuple(value["legislation_types"]),
        page_size=value["page_size"],
        max_pages=value["max_pages"],
        max_candidates=value["max_candidates"],
        start_page=value["start_page"],
        endpoint=value["endpoint"],
        sort=value["sort"],
    )
    with httpx.Client(timeout=30.0, follow_redirects=False) as client:

        def fetch(params: dict[str, Any]) -> Any:  # noqa: ANN401
            response = client.get(
                scope.endpoint, params=params, headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()

        write(output, discover(scope, fetch))


def classify(candidate: Path, harvest: Path, output_dir: Path) -> None:
    for name, receipt in acquisition_receipts(load(candidate), load(harvest)).items():
        write(output_dir / f"{name}.json", receipt)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    query = sub.add_parser("query")
    query.add_argument("--scope", type=Path, required=True)
    query.add_argument("--output", type=Path, required=True)
    outcomes = sub.add_parser("classify")
    outcomes.add_argument("--candidate-receipt", type=Path, required=True)
    outcomes.add_argument("--harvest-receipt", type=Path, required=True)
    outcomes.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "query":
        run(args.scope, args.output)
    else:
        classify(args.candidate_receipt, args.harvest_receipt, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
