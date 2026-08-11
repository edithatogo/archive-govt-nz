"""Create the final, fail-closed Treasury source-resolution receipt."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

AUTHORITATIVE_HOST = "www.treasury.govt.nz"


def _unresolved(plan: dict[str, Any], recovery: dict[str, Any]) -> list[dict[str, Any]]:
    recovered = {
        str(item["resource_id"])
        for item in recovery.get("resources", [])
        if item.get("resource_id")
    }
    return sorted(
        (
            item
            for item in plan.get("outcomes", [])
            if item.get("resource_id") and str(item["resource_id"]) not in recovered
        ),
        key=lambda item: str(item["resource_id"]),
    )


def _validate_official_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != AUTHORITATIVE_HOST:
        message = f"replacement is not on the authoritative host: {url}"
        raise ValueError(message)


def resolve(
    plan: dict[str, Any],
    recovery: dict[str, Any],
    config: dict[str, Any],
    *,
    observed_at: str,
    auxiliary: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve each non-DataStore resource to evidence or a tombstone."""
    replacements = config.get("official_replacements", {})
    rights = config.get("rights_evidence", {})
    resources: list[dict[str, Any]] = []
    redundancy = (auxiliary or {}).get("redundancy")
    archivebox = (auxiliary or {}).get("archivebox")
    redundancy_by_id = {
        str(item["resource_id"]): item for item in (redundancy or {}).get("records", [])
    }
    counts = {
        "resources": 0,
        "authoritative_replacement": 0,
        "rights_evidenced": 0,
        "tombstone": 0,
    }

    for item in _unresolved(plan, recovery):
        source_url = str(item["source_url"])
        decision = item.get("decision", {})
        reason = str(decision.get("reason", "unknown"))
        dataset_id = str(item["dataset_id"])
        row: dict[str, Any] = {
            "dataset_id": dataset_id,
            "resource_id": str(item["resource_id"]),
            "title": str(decision.get("sanitized_filename", "")),
            "source_url": source_url,
            "source_host": urlparse(source_url).netloc,
            "observed_at": observed_at,
        }

        replacement = replacements.get(source_url)
        evidence = rights.get(dataset_id)
        if reason == "unsafe_scheme" and replacement:
            replacement_url = str(replacement)
            _validate_official_url(replacement_url)
            row.update(
                state="authoritative_replacement",
                reason="publisher_migrated_legacy_path",
                replacement_url=replacement_url,
                identity_scope="authoritative publication or collection page",
                payload_equivalence="not_claimed",
            )
        elif reason == "rights_unknown" and evidence:
            evidence_url = str(evidence["url"])
            _validate_official_url(evidence_url)
            row.update(
                state="rights_evidenced",
                reason="resource_rights_supported_by_official_publisher_page",
                rights_evidence_url=evidence_url,
                licence=str(evidence["licence"]),
                rights_basis=str(evidence["basis"]),
                payload_state="source_endpoint_not_recaptured",
            )
        else:
            tombstone_reason = (
                "rights_evidence_unavailable"
                if reason == "rights_unknown"
                else "no_verified_secure_replacement"
            )
            row.update(
                state="tombstone",
                reason=tombstone_reason,
                retry_state="scheduled_verification",
                limitation=(
                    "No eligible source was promoted without authoritative evidence."
                ),
            )
        mirror = redundancy_by_id.get(str(item["resource_id"]))
        if mirror:
            row["internet_archive"] = {
                "classification": mirror.get("classification"),
                "snapshot_state": mirror.get("snapshot_state"),
                "snapshot_url": mirror.get("snapshot_url"),
                "sha256": mirror.get("sha256"),
                "bytes": mirror.get("bytes"),
            }
        counts[str(row["state"])] += 1
        counts["resources"] += 1
        resources.append(row)

    document: dict[str, Any] = {
        "schema_version": "treasury-source-resolution/v1",
        "observed_at": observed_at,
        "policy": {
            "authoritative_hosts": [AUTHORITATIVE_HOST],
            "payload_equivalence_required_for_payload_claim": True,
            "unknown_rights_fail_closed": True,
            "tombstones_are_resolution_outcomes_not_payload_captures": True,
        },
        "counts": counts,
        "resources": resources,
    }
    if redundancy is not None:
        document["internet_archive"] = {
            "record_count": redundancy.get("record_count"),
            "canonical_report_sha256": redundancy.get("canonical_report_sha256"),
            "verified_snapshots": sum(
                item.get("snapshot_state") == "verified"
                for item in redundancy.get("records", [])
            ),
        }
    if archivebox is not None:
        document["archivebox"] = {
            "admission_state": archivebox.get("admission_state"),
            "decision": archivebox.get("decision"),
            "candidate_count": archivebox.get("candidate_count"),
            "original_payloads_verified": sum(
                bool(item.get("original_payload_verified"))
                for item in archivebox.get("candidate_outcomes", [])
            ),
        }
    return document


def _markdown(receipt: dict[str, Any]) -> str:
    counts = receipt["counts"]
    lines = [
        "# Treasury source resolution",
        "",
        f"Observed: `{receipt['observed_at']}`",
        "",
        "| State | Resources |",
        "| --- | ---: |",
        f"| Authoritative replacement | {counts['authoritative_replacement']} |",
        f"| Rights evidenced | {counts['rights_evidenced']} |",
        f"| Explicit tombstone | {counts['tombstone']} |",
        f"| Total | {counts['resources']} |",
        "",
        (
            "Replacement pages establish authoritative identity/context; byte-for-byte "
            "payload equivalence is not claimed. Rights evidence changes eligibility "
            "only; it does not claim that the source payload was recaptured."
        ),
        "",
        "| Resource | State | Evidence or reason |",
        "| --- | --- | --- |",
    ]
    for row in receipt["resources"]:
        evidence = row.get("replacement_url") or row.get("rights_evidence_url")
        detail = str(evidence or row["reason"])
        lines.append(f"| `{row['resource_id']}` | {row['state']} | {detail} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    """Write paired source-resolution evidence from governed inputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--redundancy", type=Path)
    parser.add_argument("--archivebox-evaluation", type=Path)
    parser.add_argument("--observed-at")
    args = parser.parse_args()
    observed_at = args.observed_at or (
        datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )
    receipt = resolve(
        json.loads(args.plan.read_text(encoding="utf-8")),
        json.loads(args.recovery.read_text(encoding="utf-8")),
        json.loads(args.config.read_text(encoding="utf-8")),
        observed_at=observed_at,
        auxiliary={
            key: value
            for key, value in {
                "redundancy": (
                    json.loads(args.redundancy.read_text(encoding="utf-8"))
                    if args.redundancy
                    else None
                ),
                "archivebox": (
                    json.loads(args.archivebox_evaluation.read_text(encoding="utf-8"))
                    if args.archivebox_evaluation
                    else None
                ),
            }.items()
            if value is not None
        },
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(_markdown(receipt), encoding="utf-8")
    print(json.dumps(receipt["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
