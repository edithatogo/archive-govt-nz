"""Generate paired Hugging Face card and Zenodo metadata previews."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
TRACK_MANIFEST = (
    ROOT
    / "conductor/tracks/treasury_archive_mvp_20260731"
    / "evidence/phase-10-source-resolution-manifest.json"
)
EVIDENCE_ROOT = ROOT / "evidence"


def _read_json(path: Path) -> dict[str, Any]:
    """Read one bounded JSON file and return an empty object on miss."""
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        try:
            payload = json.load(handle)
        except json.JSONDecodeError:
            return {}
    if not isinstance(payload, dict):
        return {}
    return cast(dict[str, Any], payload)


def _read_dict_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Return a list of dictionaries for a known evidence key."""
    raw = payload.get(key)
    if not isinstance(raw, list):
        return []
    items: list[dict[str, Any]] = []
    for item in cast(list[Any], raw):
        if isinstance(item, dict):
            items.append(cast(dict[str, Any], item))
    return items


def _as_str(value: Any) -> str:
    """Return a strict string for metadata serialization."""
    return value if isinstance(value, str) else ""


def _as_dict(value: Any) -> dict[str, Any]:
    """Return a strict dict for metadata inspection."""
    if not isinstance(value, dict):
        return {}
    return cast(dict[str, Any], value)


def _build_resource_snapshot() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Combine resolution request and authoritative manifest per-resource stages."""
    request = _read_json(EVIDENCE_ROOT / "phase-10-publisher-resolution-request.json")
    track_manifest = _read_json(TRACK_MANIFEST)

    manifest_map: dict[str, dict[str, Any]] = {}
    for item in _read_dict_list(track_manifest, "resources"):
        resource_id = item.get("resource_id")
        if isinstance(resource_id, str):
            manifest_map[resource_id] = item

    resources: list[dict[str, Any]] = []
    stage_counts: dict[str, int] = {}
    for item in _read_dict_list(request, "resources"):
        resource_id = item.get("resource_id")
        if not isinstance(resource_id, str):
            continue

        request_state = item.get("state")
        request_state_str = request_state if isinstance(request_state, str) else None
        capture_state = ""
        dataset_id = ""
        source_url = ""
        restriction = None

        manifest_item = manifest_map.get(resource_id)
        if manifest_item is not None:
            dataset_id = _as_str(manifest_item.get("dataset_id"))
            source_url = _as_str(manifest_item.get("source_url"))
            capture_state = _as_str(manifest_item.get("capture_state"))
            policy = _as_dict(manifest_item.get("policy_decision"))
            restriction = _as_str(policy.get("disposition"))

        resources.append(
            {
                "resource_id": resource_id,
                "dataset_id": dataset_id,
                "source_url": source_url,
                "state": request_state_str,
                "capture_state": capture_state,
                "disposition": restriction,
                "reason": item.get("reason"),
                "candidate_count": item.get("candidate_count"),
                "http_statuses": item.get("http_statuses"),
            }
        )
        if request_state_str is not None:
            stage_counts[request_state_str] = stage_counts.get(request_state_str, 0) + 1

    return resources, stage_counts


def _load_publication_receipts() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any]
]:
    """Load Hugging Face, Zenodo, and reconciliation evidence if available."""
    hf = _read_json(EVIDENCE_ROOT / "phase-8-hf-publication-verification.json")
    zenodo = _read_json(EVIDENCE_ROOT / "phase-9-zenodo-publication.json")
    final_recon = _read_json(EVIDENCE_ROOT / "phase-10-final-reconciliation.json")
    return hf, zenodo, final_recon


def _load_counts() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load capture and rights snapshots used by the metadata summary."""
    return (
        _read_json(EVIDENCE_ROOT / "phase-6-capture-summary.json"),
        _read_json(EVIDENCE_ROOT / "phase-6-rights-classification.json"),
    )


def main() -> int:
    """Write publication metadata previews with explicit local-only boundaries."""
    ledger = _read_json(EVIDENCE_ROOT / "archive-evidence-ledger.json")
    states: dict[str, str] = {}
    for item in _read_dict_list(ledger, "stages"):
        stage = item.get("stage")
        state = item.get("state")
        if isinstance(stage, str) and isinstance(state, str):
            states[stage] = state

    capture, rights = _load_counts()
    hf_receipt, zenodo_receipt, final_reconciliation = _load_publication_receipts()
    resource_rows, stage_counts = _build_resource_snapshot()
    restrictions = _as_str(capture.get("publication")) == "not attempted"

    publication_payload = final_reconciliation.get("publication")
    release_state = None
    if isinstance(publication_payload, dict):
        release_state = cast(dict[str, Any], publication_payload).get("release_state")

    publication_receipts = {
        "hugging_face": {
            "repository": hf_receipt.get("repository"),
            "revision": hf_receipt.get("revision"),
            "publication_state": hf_receipt.get("publication_state"),
            "remote_url": hf_receipt.get("remote_url"),
            "verified_at": hf_receipt.get("verified_at"),
            "file_count": hf_receipt.get("file_count"),
            "viewer_status": hf_receipt.get("viewer_status"),
        },
        "zenodo": {
            "doi": zenodo_receipt.get("doi"),
            "record_id": zenodo_receipt.get("record_id"),
            "state": zenodo_receipt.get("state"),
            "package_sha256": zenodo_receipt.get("package_sha256"),
            "file": zenodo_receipt.get("file"),
            "file_size": zenodo_receipt.get("file_size"),
            "zenodo_checksum": zenodo_receipt.get("zenodo_checksum"),
            "viewer_state": zenodo_receipt.get("viewer_state"),
        },
        "reconciliation": {
            "status": final_reconciliation.get("status"),
            "release_state": release_state,
            "limit_remediation": final_reconciliation.get("limitations", []),
        },
    }
    card = f"""---
dataset_info:
  config_name: treasury-evidence
  features:
    - name: dataset_id
      dtype: string
  homepage: https://catalogue.data.govt.nz/organization/the-treasury
  license: cc-by-4.0
  language:
    - en
tags:
  - new-zealand
  - government-data
  - treasury
  - public-finance
  - ckan
---

# Archive Govt NZ — Treasury evidence preview

This is a prepared, evidence-first archive preview. It is not published yet.

## Scope

- Treasury discovery: `{states.get("discovered")}`
- Capture: `{capture.get("captured", "unknown")} out of {capture.get("attempted", "unknown")} resources locally validated`
- Validation: `{states.get("validated")}`
- Transformation: `{states.get("transformed")}`
- Publication: `{states.get("uploaded")}`
- Final reconciliation: `{final_reconciliation.get("status", "unknown")}`

## Publication receipts

- Hugging Face state: `{hf_receipt.get("publication_state", "not-verified")}`
- Hugging Face revision: `{hf_receipt.get("revision", "n/a")}`
- Zenodo DOI: `{zenodo_receipt.get("doi", "n/a")}`
- Zenodo state: `{zenodo_receipt.get("state", "n/a")}`
- Publication limit: `no remote publication claimed until explicit approval`

## Resource disposition snapshot

Original metadata and source files remain distinct from derivatives. Rights, restriction,
withdrawal, and transformation decisions are recorded with per-resource provenance and
stage snapshots.

## Per-resource provenance and restriction summary

- Restricted: {stage_counts.get("tombstone-required", 0)}
- Accessible: {stage_counts.get("secure-source-observed", 0)}
- Awaiting authoritative replacement: {stage_counts.get("await-authoritative-alternative", 0)}

`resource_summary` (JSON):

```json
{json.dumps(resource_rows, indent=2)}
```
"""

    rights_summary = {
        "source_license_observed": rights.get("publication_candidate"),
        "dataset_license_counts": rights.get("license_counts", {}),
        "dataset_rights_state": rights.get("rights_state"),
        "limitations": rights.get("limitations", []),
        "resource_access_gated": restrictions,
    }
    role_map = {
        "source_metadata": True,
        "source_resource": True,
        "derivative": (
            isinstance(hf_receipt.get("derivatives"), dict)
            and bool(hf_receipt.get("derivatives"))
        ),
        "warc_receipt": True,
        "manifest": True,
    }
    stage_records: list[str] = []
    for stage, state in states.items():
        stage_records.append(f"archive-evidence-ledger/stages/{stage}:{state}")

    zenodo = {
        "title": "Archive Govt NZ — Treasury evidence preview",
        "description": "Evidence-first, checksum-pinned Treasury archive preview with 12 locally captured resources; not yet published.",
        "upload_type": "dataset",
        "access_right": "open",
        "license": "cc-by-4.0",
        "version": "preview-0.1",
        "rights": rights_summary,
        "provenance": {
            "source_receipts": [
                "evidence/phase-8-hf-publication-verification.json",
                "evidence/phase-9-zenodo-publication.json",
                "evidence/phase-10-final-reconciliation.json",
                "evidence/phase-10-publisher-resolution-request.json",
            ],
            "stage_records": stage_records,
            "capture_summary": capture.get("capture_run"),
        },
        "roles": [role for role, active in role_map.items() if active],
        "resource_summary": {
            "stage_counts": stage_counts,
            "counts": final_reconciliation.get("counts", {}),
            "restricted_resources": rights.get("limitations", []),
            "publication_limit": "rights review and release authority required",
            "resources": resource_rows,
        },
        "publication_receipts": publication_receipts,
        "publication_state": "prepared-not-published",
        "doi_authorized": False,
        "limitations": [
            "payload_capture_scope_limited_to_12_preflight_approved_resources",
            "rights_review_incomplete",
            "no_remote_upload",
            "no_doi_confirmation_required",
        ],
    }
    output = ROOT / "evidence/publication-metadata"
    output.mkdir(parents=True, exist_ok=True)
    (output / "README.md").write_text(card, encoding="utf-8")
    (output / "zenodo.json").write_text(
        json.dumps(zenodo, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote publication metadata previews")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
