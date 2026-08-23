"""Build the cross-domain identifier interlink manifest (fail-closed)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

INTERLINK_SCHEMA = "archive-govt-nz.identifier-interlink/v1"

_UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_HF_SLUG_REGEX = re.compile(r"^[a-z0-9-]+/[a-z0-9.-]+$")
_ZENODO_DOI_REGEX = re.compile(r"^10\.5281/zenodo\.\d+$")


def _load_json(path: Path) -> dict[str, Any]:
    """Load one UTF-8 JSON object."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_legislation_ids(path: Path) -> list[str]:
    """Load processed legislation work IDs from a durable checkpoint."""
    data = _load_json(path)
    ids = data.get("processed_work_ids", [])
    if not isinstance(ids, list):
        msg = "legislation checkpoint processed_work_ids must be an array"
        raise TypeError(msg)
    return [str(i) for i in ids]


def load_health_pairs(path: Path) -> list[dict[str, str]]:
    """Load health dataset/resource identifier pairs from a metadata snapshot."""
    data = _load_json(path)
    resources = data.get("resources", [])
    if not isinstance(resources, list):
        msg = "health snapshot must contain a 'resources' array"
        raise TypeError(msg)
    return [
        {
            "dataset_id": str(r["dataset_id"]),
            "resource_id": str(r["resource_id"]),
        }
        for r in resources
        if isinstance(r, dict) and r.get("dataset_id") and r.get("resource_id")
    ]


def load_publication_identities(path: Path) -> dict[str, list[str]]:
    """Load registered HF slugs and Zenodo DOIs from a readback receipt."""
    data = _load_json(path)
    hf_slugs = [str(slug) for slug in data.get("huggingface", {})]
    zenodo = data.get("zenodo", {})
    dois = [str(zenodo["doi"])] if zenodo.get("doi") else []
    return {"hf_slugs": hf_slugs, "zenodo_dois": dois}


def validate_domain_ids(domain: str, ids: list[str]) -> list[str]:
    """Validate per-domain identifier shape; returns human findings."""
    findings: list[str] = []
    for value in ids:
        if not value.strip():
            findings.append(f"{domain}: empty identifier")
        elif domain in {"health-resource", "health-dataset"} and not _UUID_REGEX.match(
            value
        ):
            findings.append(f"{domain}: malformed UUID: {value}")
        elif domain == "publication-hf" and not _HF_SLUG_REGEX.match(value):
            findings.append(f"publication-hf: malformed slug: {value}")
        elif domain == "publication-zenodo" and not _ZENODO_DOI_REGEX.match(value):
            findings.append(f"publication-zenodo: malformed DOI: {value}")
    return findings


def find_collisions(domains: dict[str, list[str]]) -> list[str]:
    """Detect identical raw identifiers appearing in multiple domains."""
    seen: dict[str, str] = {}
    collisions: list[str] = []
    for domain in sorted(domains):
        for value in domains[domain]:
            if not value:
                continue
            if value in seen and seen[value] != domain:
                collisions.append(
                    f"cross-domain collision: '{value}' in {seen[value]} and {domain}"
                )
            elif value not in seen:
                seen[value] = domain
    return collisions


def build_interlink(
    legislation_ids: list[str],
    health_pairs: list[dict[str, str]],
    publications: dict[str, list[str]],
) -> dict[str, Any]:
    """Assemble the interlink receipt with validation and cross-references."""
    domains: dict[str, list[str]] = {
        "legislation": sorted(set(legislation_ids)),
        "health-dataset": sorted({p["dataset_id"] for p in health_pairs}),
        "health-resource": sorted({p["resource_id"] for p in health_pairs}),
        "publication-hf": sorted(publications.get("hf_slugs", [])),
        "publication-zenodo": sorted(publications.get("zenodo_dois", [])),
    }
    findings: list[str] = []
    for domain, ids in domains.items():
        findings.extend(validate_domain_ids(domain, ids))
    findings.extend(find_collisions(domains))

    resource_to_dataset = {p["resource_id"]: p["dataset_id"] for p in health_pairs}

    return {
        "schema_version": INTERLINK_SCHEMA,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "domains": {k: {"count": len(v), "identifiers": v} for k, v in domains.items()},
        "relationships": {"health_resource_to_dataset": resource_to_dataset},
        "findings_count": len(findings),
        "findings": findings,
        "status": "passed" if not findings else "findings-present",
    }


def main() -> int:
    """CLI entrypoint for the identifier interlink builder."""
    parser = argparse.ArgumentParser(
        description="Build cross-domain identifier interlink manifest"
    )
    parser.add_argument(
        "--legislation-checkpoint",
        type=Path,
        default=Path("evidence/checkpoints/legislation.json"),
    )
    parser.add_argument(
        "--health-snapshot",
        type=Path,
        default=Path(
            "conductor/tracks/health_payload_capture_20260802/evidence/"
            "moh-resource-metadata.json"
        ),
    )
    parser.add_argument(
        "--publication-readback",
        type=Path,
        default=Path(
            "evidence/migrations/corpus-legislation-nz/"
            "remote-publication-readback-receipt.json"
        ),
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=Path("evidence/identifier-interlink.json"),
    )
    args = parser.parse_args()

    try:
        legislation_ids = load_legislation_ids(args.legislation_checkpoint)
        health_pairs = load_health_pairs(args.health_snapshot)
        publications = load_publication_identities(args.publication_readback)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    receipt = build_interlink(legislation_ids, health_pairs, publications)
    args.receipt_path.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        "[INTERLINK] "
        + " ".join(f"{k}={v['count']}" for k, v in receipt["domains"].items())
        + f" findings={receipt['findings_count']} receipt={args.receipt_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
