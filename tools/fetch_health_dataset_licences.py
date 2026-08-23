"""Read-only CKAN licence probe for MoH payload eligibility evidence.

Preserves raw package_show responses and emits a dataset_id -> licence_id map
consumable by tools/evaluate_health_payload_eligibility.py --licence-map.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from archive_govt_nz.ckan.client import BoundedCkanClient, CkanClientConfig

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.evaluate_health_payload_eligibility import (
    load_resource_snapshot,
)

PROBE_RECEIPT_SCHEMA = "archive-govt-nz.health-licence-probe/v1"
DEFAULT_CATALOGUE_URL = "https://catalogue.data.govt.nz"
USER_AGENT = (
    "archive-govt-nz/0.1.0 (Licence Evidence Probe; "
    "+https://github.com/edithatogo/archive-govt-nz)"
)


def load_dataset_ids(snapshot_path: Path) -> list[str]:
    """Load the distinct dataset identifiers in first-seen order."""
    resources = load_resource_snapshot(snapshot_path)
    seen: dict[str, None] = {}
    for resource in resources:
        dataset_id = str(resource.get("dataset_id", "")).strip()
        if dataset_id:
            seen.setdefault(dataset_id, None)
    return list(seen)


def _default_client_config() -> CkanClientConfig:
    """Return bounded client configuration for read-only probing."""
    return CkanClientConfig(
        base_url=DEFAULT_CATALOGUE_URL,
        user_agent=USER_AGENT,
        timeout_seconds=30.0,
        max_attempts=3,
        base_backoff_seconds=2.0,
        jitter_seconds=1.0,
        max_response_bytes=4 * 1024 * 1024,
    )


def extract_licence_id(raw_body: bytes) -> str:
    """Extract licence_id from a preserved package_show envelope body."""
    document = json.loads(raw_body.decode("utf-8"))
    result = document.get("result")
    if not isinstance(result, dict):
        msg = "package_show envelope lacks a result object"
        raise TypeError(msg)
    for field in ("license_id", "licence_id"):
        licence = result.get(field)
        if licence:
            return str(licence).strip()
    return ""


def preserve_raw_response(
    raw_dir: Path, dataset_id: str, raw_body: bytes, sha256: str
) -> Path:
    """Persist one raw package_show response with a checksum sidecar."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{dataset_id}.json"
    path.write_bytes(raw_body)
    sidecar = raw_dir / f"{dataset_id}.sha256"
    sidecar.write_text(f"{sha256}  {dataset_id}.json\n", encoding="utf-8")
    return path


def build_map_offline(
    dataset_ids: list[str], raw_dir: Path
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Rebuild the licence map from previously preserved responses."""
    licence_map: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    for dataset_id in dataset_ids:
        path = raw_dir / f"{dataset_id}.json"
        if not path.is_file():
            records.append(
                {
                    "dataset_id": dataset_id,
                    "status": "missing-raw-response",
                    "licence_id": "",
                }
            )
            continue
        raw_body = path.read_bytes()
        sha256 = hashlib.sha256(raw_body).hexdigest()
        try:
            licence_id = extract_licence_id(raw_body)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            records.append(
                {
                    "dataset_id": dataset_id,
                    "status": "unparseable-response",
                    "error": str(exc)[:200],
                    "licence_id": "",
                }
            )
            continue
        records.append(
            {
                "dataset_id": dataset_id,
                "status": "observed",
                "licence_id": licence_id,
                "response_sha256": sha256,
            }
        )
        if licence_id:
            licence_map[dataset_id] = licence_id
    return licence_map, records


def _probe_live(
    dataset_ids: list[str], raw_dir: Path
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Probe the live catalogue read-only and preserve every raw response."""

    async def _collect() -> tuple[dict[str, str], list[dict[str, Any]]]:
        async with BoundedCkanClient(_default_client_config()) as client:
            local_map: dict[str, str] = {}
            local_records: list[dict[str, Any]] = []
            for dataset_id in dataset_ids:
                try:
                    observation = await client.action_get(
                        "package_show", {"id": dataset_id}
                    )
                except Exception as exc:  # noqa: BLE001
                    local_records.append(
                        {
                            "dataset_id": dataset_id,
                            "status": "transport-error",
                            "error": str(exc)[:200],
                            "licence_id": "",
                        }
                    )
                    continue
                preserve_raw_response(
                    raw_dir, dataset_id, observation.raw_body, observation.raw_sha256
                )
                try:
                    licence_id = extract_licence_id(observation.raw_body)
                except (ValueError, json.JSONDecodeError) as exc:
                    local_records.append(
                        {
                            "dataset_id": dataset_id,
                            "status": "unparseable-response",
                            "error": str(exc)[:200],
                            "licence_id": "",
                        }
                    )
                    continue
                local_records.append(
                    {
                        "dataset_id": dataset_id,
                        "status": "observed",
                        "licence_id": licence_id,
                        "response_sha256": observation.raw_sha256,
                        "attempts": observation.attempt_count,
                    }
                )
                if licence_id:
                    local_map[dataset_id] = licence_id
            return local_map, local_records

    return asyncio.run(_collect())


def main() -> int:
    """CLI entrypoint for the licence evidence probe."""
    parser = argparse.ArgumentParser(
        description="Read-only CKAN licence probe (evidence-only)"
    )
    parser.add_argument(
        "--resource-snapshot",
        type=Path,
        default=Path(
            "conductor/tracks/health_payload_capture_20260802/evidence/"
            "moh-resource-metadata.json"
        ),
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("evidence/health/licence-probe-raw"),
    )
    parser.add_argument(
        "--map-path",
        type=Path,
        default=Path("evidence/health/licence-map.json"),
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=Path("evidence/health/licence-probe-receipt.json"),
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly enable live read-only CKAN queries",
    )
    args = parser.parse_args()

    if not args.live:
        print(
            "[PROBE] Offline replay mode (no network). "
            "Pass --live to query the catalogue.",
            file=sys.stderr,
        )

    dataset_ids = load_dataset_ids(args.resource_snapshot)
    print(f"[PROBE] Distinct datasets: {len(dataset_ids)}")

    if args.live:
        licence_map, records = _probe_live(dataset_ids, args.raw_dir)
    else:
        licence_map, records = build_map_offline(dataset_ids, args.raw_dir)

    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    args.map_path.parent.mkdir(parents=True, exist_ok=True)
    args.map_path.write_text(
        json.dumps(licence_map, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt = {
        "schema_version": PROBE_RECEIPT_SCHEMA,
        "probed_at": now_iso,
        "mode": "live" if args.live else "offline-replay",
        "catalogue_url": DEFAULT_CATALOGUE_URL,
        "datasets_total": len(dataset_ids),
        "licences_observed": len(licence_map),
        "raw_responses_dir": str(args.raw_dir),
        "records": records,
    }
    args.receipt_path.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"[PROBE] licences_observed={len(licence_map)} "
        f"map={args.map_path} receipt={args.receipt_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
