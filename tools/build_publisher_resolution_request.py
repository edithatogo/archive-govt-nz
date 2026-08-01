"""Build a safe, evidence-linked publisher resolution request packet."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_packet(probe: dict[str, Any], *, captured_at: str) -> dict[str, Any]:
    """Return a metadata-only publisher request from a probe receipt."""
    results = probe.get("results", [])
    counts: dict[str, int] = {}
    resources: list[dict[str, Any]] = []
    for row in results:
        state = str(row.get("state", "unknown"))
        counts[state] = counts.get(state, 0) + 1
        attempts = row.get("attempts", [])
        statuses = sorted(
            {a.get("status_code") for a in attempts if a.get("status_code") is not None}
        )
        resources.append(
            {
                "resource_id": row.get("resource_id"),
                "source_url": row.get("source_url"),
                "state": state,
                "http_statuses": statuses,
                "candidate_count": len(row.get("candidates", [])),
                "reason": row.get("reason"),
            }
        )
    return {
        "schema_version": "archive-govt-nz.publisher-resolution-request/v1",
        "captured_at": captured_at,
        "recipient": {"organisations": ["New Zealand Treasury", "data.govt.nz"]},
        "scope": {
            "catalogue": "https://catalogue.data.govt.nz",
            "organisation": "the-treasury",
            "purpose": "resolve secure authoritative payload sources for archival",
        },
        "safety": {
            "body_transfer": False,
            "credentials_included": False,
            "personal_information_included": False,
            "undocumented_mirrors_requested": False,
            "http_exception_requested": False,
        },
        "delivery": {
            "status": "draft-not-sent",
            "external_request_sent": False,
            "approval_required": True,
            "send_command": None,
        },
        "summary": {
            "resource_count": len(resources),
            "state_counts": counts,
            "requested_response": (
                "For each listed resource, provide an authoritative HTTPS replacement, "
                "confirm withdrawal, or explain access restrictions and intended "
                "access path."
            ),
        },
        "resources": resources,
        "evidence": [
            "evidence/phase-10-secure-source-probe.json",
            "evidence/phase-10-tombstone-reprobe.json",
            "conductor/tracks/treasury_archive_mvp_20260731/evidence/phase-10-ckan-api-probe.json",
        ],
    }


def render_markdown(packet: dict[str, Any]) -> str:
    """Render a human-readable version of a publisher request packet."""
    summary = packet["summary"]
    lines = [
        "# Treasury publisher-resolution request",
        "",
        (
            "This packet is a draft for an official Treasury/data.govt.nz request. It "
            "contains metadata-level identifiers and bounded HTTP status evidence "
            "only; "
            "no response bodies, credentials, signed URLs, or personal information are "
            "included."
        ),
        "",
        f"- Captured at: `{packet['captured_at']}`",
        (
            f"- Scope: `{packet['scope']['catalogue']}` organisation "
            f"`{packet['scope']['organisation']}`"
        ),
        f"- Resources: **{summary['resource_count']}**",
        f"- State counts: `{json.dumps(summary['state_counts'], sort_keys=True)}`",
        "",
        "## Requested response",
        "",
        summary["requested_response"],
        "For each resource, please provide one of:",
        "",
        "- an authoritative HTTPS replacement URL and effective date;",
        (
            "- confirmation that the resource was withdrawn or relocated, with "
            "successor "
            "identifier; or"
        ),
        "- the approved access procedure and rights/usage conditions.",
        "",
        "## Resource register",
        "",
        "| Resource ID | State | HTTP status evidence | Candidates | Source URL |",
        "|---|---|---:|---:|---|",
    ]
    for row in packet["resources"]:
        statuses = ", ".join(str(x) for x in row["http_statuses"]) or "none"
        lines.append(
            f"| `{row['resource_id']}` | `{row['state']}` | `{statuses}` | "
            f"{row['candidate_count']} | {row['source_url']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            *[f"- `{item}`" for item in packet["evidence"]],
            "",
            (
                "The archive will retain unresolved resources as tombstones and "
                "re-probe them on schedule. It will not bypass access controls, "
                "accept HTTP-only "
                "sources, or use undocumented mirrors."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Generate JSON and Markdown packets from a probe receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    probe = json.loads(args.probe.read_text(encoding="utf-8"))
    packet = build_packet(probe, captured_at=datetime.now(UTC).isoformat())
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(packet), encoding="utf-8")


if __name__ == "__main__":
    main()
