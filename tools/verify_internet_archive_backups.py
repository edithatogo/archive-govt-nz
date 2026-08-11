"""Verify captured Internet Archive objects and emit resource-level evidence."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.redundancy import (
    RedundancyError,
    RedundancyObservation,
    build_redundancy_report,
    verify_captured_object,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    return parser.parse_args()


def _load(path: Path) -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    """Verify all captured objects and classify every unresolved resource."""
    args = _arguments()
    plan = _load(args.plan)
    recovery = _load(args.recovery)
    backup = _load(args.backup)
    recovered = {str(item["resource_id"]) for item in recovery.get("resources", [])}
    backup_by_url = {
        str(item["source_url"]): item for item in backup.get("results", [])
    }
    observations: list[RedundancyObservation] = []
    verification_failures: list[dict[str, str]] = []
    for outcome in plan.get("outcomes", []):
        resource_id = str(outcome.get("resource_id", ""))
        if resource_id in recovered:
            continue
        source_url = str(outcome.get("source_url", ""))
        item = backup_by_url.get(source_url, {"status": "unavailable"})
        state = str(item.get("status", "unavailable"))
        if state == "captured":
            try:
                verify_captured_object(
                    Path(str(item["object"])),
                    str(item["sha256"]),
                    int(item["bytes"]),
                )
                state = "verified"
            except (KeyError, TypeError, ValueError, RedundancyError) as error:
                state = "failed"
                verification_failures.append(
                    {"resource_id": resource_id, "error_class": type(error).__name__}
                )
        observations.append(
            RedundancyObservation(
                resource_id=resource_id,
                source_url=source_url,
                official_available=None,
                snapshot_state=(
                    state if state in {"verified", "failed"} else "unavailable"
                ),
                snapshot_url=(
                    str(item["snapshot_url"]) if item.get("snapshot_url") else None
                ),
                sha256=str(item["sha256"]) if item.get("sha256") else None,
                bytes=int(item["bytes"]) if item.get("bytes") is not None else None,
            )
        )
    observed_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = build_redundancy_report(observations, observed_at=observed_at)
    document = {
        **report.document,
        "canonical_report_sha256": report.sha256,
        "verification_failures": verification_failures,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    counts: dict[str, int] = {}
    for record in cast("list[dict[str, Any]]", report.document["records"]):
        classification = str(record["classification"])
        counts[classification] = counts.get(classification, 0) + 1
    lines = [
        "# Internet Archive redundancy verification",
        "",
        f"Observed: `{observed_at}`",
        f"Resources: **{len(observations)}**",
        f"Canonical report SHA-256: `{report.sha256}`",
        "",
        "## Classifications",
        "",
        *[f"- `{key}`: {counts[key]}" for key in sorted(counts)],
        "",
        "Mirror evidence remains distinct from original-source capture.",
    ]
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"resources": len(observations), "counts": counts}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
