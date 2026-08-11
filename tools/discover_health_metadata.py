"""Bounded metadata-only discovery for health-related CKAN datasets."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import anyio
from jsonschema import Draft202012Validator, FormatChecker

from archive_govt_nz.ckan.client import (
    ActionObservation,
    BoundedCkanClient,
    CkanClientConfig,
)
from archive_govt_nz.ckan.envelope import CkanTransportError
from archive_govt_nz.health_discovery import normalize_scoped_records, reconcile_rerun
from archive_govt_nz.health_scope import DEFAULT_SCOPES

DEFAULT_BASE_URL = "https://catalogue.data.govt.nz"
USER_AGENT = "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
MAX_PAGE_SIZE = 1000


def _fingerprint(record: dict[str, Any]) -> str:
    canonical = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


async def _page(
    client: BoundedCkanClient,
    params: dict[str, object],
) -> tuple[ActionObservation, str, dict[str, object] | None]:
    try:
        return await client.action("package_search", params), "POST", None
    except CkanTransportError as post_error:
        post_receipt: dict[str, object] = {
            "method": "POST",
            "status": "failed",
            "status_code": post_error.status_code,
            "error_class": post_error.error_class,
        }
        return await client.action_get("package_search", params), "GET", post_receipt


async def _discover(
    base_url: str,
    page_size: int,
    *,
    raw_dir: Path,
    previous: dict[str, object] | None = None,
) -> dict[str, object]:
    config = CkanClientConfig(
        base_url=base_url,
        user_agent=USER_AGENT,
        timeout_seconds=20,
        max_attempts=3,
        base_backoff_seconds=1,
        jitter_seconds=0,
        max_response_bytes=8 * 1024 * 1024,
    )
    await anyio.Path(raw_dir).mkdir(parents=True, exist_ok=True)
    async with BoundedCkanClient(config) as client:
        scoped_records: dict[str, list[dict[str, Any]]] = {}
        receipts: list[dict[str, object]] = []
        for scope in DEFAULT_SCOPES:
            scope_id = str(scope["id"])
            params = {key: value for key, value in scope.items() if key != "id"}
            start = 0
            records: list[dict[str, Any]] = []
            attempt_rows = tuple(dict.fromkeys((page_size, min(page_size, 25), 1)))
            while True:
                page: ActionObservation | None = None
                method = ""
                post_failure: dict[str, object] | None = None
                failures: list[dict[str, object]] = []
                rows_limit = page_size
                for candidate_rows in attempt_rows:
                    rows_limit = candidate_rows
                    request_params = {
                        **params,
                        "rows": candidate_rows,
                        "start": start,
                    }
                    try:
                        page, method, post_failure = await _page(client, request_params)
                        break
                    except CkanTransportError as error:
                        failures.append(
                            {
                                "method": "GET",
                                "rows": candidate_rows,
                                "status_code": error.status_code,
                                "error_class": error.error_class,
                            }
                        )
                if page is None:
                    return {
                        "schema_version": "archive-govt-nz.health-discovery/v1",
                        "observed_at": datetime.now(tz=UTC).isoformat(),
                        "catalogue_url": base_url,
                        "status": "unavailable",
                        "failed_scope": scope_id,
                        "failed_start": start,
                        "attempts": [*receipts, *failures],
                        "policy": _policy(page_size),
                    }

                result = cast("dict[str, Any]", page.response.result)
                rows = cast("list[dict[str, Any]]", result.get("results", []))
                count = int(result.get("count", 0))
                raw_path = raw_dir / f"{scope_id}-{start:08d}-{method.lower()}.json"
                raw_path.write_bytes(page.raw_body)
                receipts.append(
                    {
                        "scope": scope_id,
                        "start": start,
                        "requested_rows": rows_limit,
                        "count": count,
                        "returned": len(rows),
                        "method": method,
                        "fallback_from": post_failure,
                        "transport_reconciliation": (
                            "get-fallback" if method == "GET" else "post-primary"
                        ),
                        "raw_path": str(raw_path),
                        "raw_bytes": len(page.raw_body),
                        "sha256": page.raw_sha256,
                        "observed_at": page.observed_at.isoformat(),
                    }
                )
                records.extend(rows)
                if start + len(rows) >= count or not rows:
                    break
                start += len(rows)
            scoped_records[scope_id] = records

    normalized = normalize_scoped_records(scoped_records)
    fingerprints = {
        str(record["id"]): _fingerprint(record)
        for records in scoped_records.values()
        for record in records
    }
    previous_fingerprints = cast(
        "dict[str, str]", (previous or {}).get("metadata_fingerprints", {})
    )
    return {
        "schema_version": "archive-govt-nz.health-discovery/v1",
        "observed_at": datetime.now(tz=UTC).isoformat(),
        "catalogue_url": base_url,
        "status": "observed",
        "scopes": {
            scope: sorted({str(item["id"]) for item in records})
            for scope, records in scoped_records.items()
        },
        "dataset_count": len(normalized),
        "datasets": normalized,
        "metadata_fingerprints": dict(sorted(fingerprints.items())),
        "rerun": reconcile_rerun(
            [
                {"id": identifier, "fingerprint": fingerprint}
                for identifier, fingerprint in previous_fingerprints.items()
            ],
            [
                {"id": identifier, "fingerprint": fingerprint}
                for identifier, fingerprint in fingerprints.items()
            ],
        ),
        "pages": receipts,
        "policy": _policy(page_size),
    }


def _policy(page_size: int) -> dict[str, object]:
    return {
        "metadata_only": True,
        "payload_capture": False,
        "publication": False,
        "max_page_size": page_size,
        "post_primary_get_after_failure": True,
        "unknown_rights_fail_closed": True,
        "sensitivity_requires_decision": True,
    }


def main() -> int:
    """Run bounded discovery and write a JSON receipt plus exact raw pages."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()
    if args.page_size < 1 or args.page_size > MAX_PAGE_SIZE:
        raise SystemExit(2)
    previous = (
        json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    )
    raw_dir = args.raw_dir or args.output.parent / f"{args.output.stem}-raw"
    document = asyncio.run(
        _discover(
            args.base_url,
            args.page_size,
            raw_dir=raw_dir,
            previous=previous,
        )
    )
    schema = json.loads(
        (
            Path(__file__).parents[1] / "schemas" / "health-discovery-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(  # pyright: ignore[reportUnknownMemberType]
        schema, format_checker=FormatChecker()
    ).validate(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": document.get("status"),
                "dataset_count": document.get("dataset_count", 0),
            }
        )
    )
    return 0 if document.get("status") == "observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
