"""Project an observation-preserving inventory from explicit retained cohorts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.capture_inventory import (
    CaptureSnapshot,
    InventorySnapshot,
    build_capture_inventory,
)


def _snapshot(path: Path) -> InventorySnapshot:
    return InventorySnapshot(path.name, path.read_bytes())


def main() -> int:
    """Pin supplied evidence, verify request bindings and exclusively write output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", action="append", type=Path, required=True)
    parser.add_argument("--capture-manifest", action="append", type=Path, default=[])
    parser.add_argument("--request", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    censuses = tuple(_snapshot(path) for path in args.census)
    supplied_requests = tuple(_snapshot(path) for path in args.request)
    requests: dict[str, list[InventorySnapshot]] = {}
    for item in (*censuses, *supplied_requests):
        candidates = requests.setdefault(hashlib.sha256(item.data).hexdigest(), [])
        if item not in candidates:
            candidates.append(item)
    consumed: set[InventorySnapshot] = set()
    captures = []
    for path in args.capture_manifest:
        manifest = _snapshot(path)
        context = json.loads(manifest.data).get("capture_context", {})
        request_hash = (
            context.get("census_sha256") if isinstance(context, dict) else None
        )
        matches = (
            requests.get(request_hash, []) if isinstance(request_hash, str) else []
        )
        if len(matches) > 1:
            error = "capture_request_hash_ambiguous"
            raise ValueError(error)
        request = matches[0] if matches else None
        if request is not None:
            consumed.add(request)
        captures.append(CaptureSnapshot(manifest, request))
    if any(item not in consumed for item in supplied_requests):
        error = "capture_request_unconsumed"
        raise ValueError(error)
    inventory = build_capture_inventory(censuses, tuple(captures))
    with args.output.open("x", encoding="utf-8") as output:
        output.write(
            json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
    print(json.dumps(inventory["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
