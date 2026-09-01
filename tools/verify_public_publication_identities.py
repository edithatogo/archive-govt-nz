"""Verify public publication identities (Hugging Face datasets and Zenodo DOIs)."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HTTP_OK = 200

DEFAULT_HF_DATASETS = [
    "edithatogo/corpus-legislation-nz",
    "edithatogo/corpus-legislation-nz-historical",
    "edithatogo/nz-legislation-corpus",
]
DEFAULT_ZENODO_DOI = "10.5281/zenodo.20592540"
DEFAULT_RECEIPT_PATH = Path(
    "evidence/migrations/corpus-legislation-nz/remote-publication-readback-receipt.json"
)

FetchFnType = Callable[..., tuple[int, bytes, str, dict[str, str]]]
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _parse_huggingface_identity(body: bytes) -> tuple[dict[str, Any], str, list[str]]:
    """Parse the immutable identity and file inventory from an API response."""
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        msg = f"Hugging Face API response is not valid JSON: {exc}"
        raise ValueError(msg) from exc
    if not isinstance(data, dict):
        msg = "Hugging Face API response is not an object"
        raise TypeError(msg)
    revision_sha = data.get("sha")
    if not isinstance(revision_sha, str) or not GIT_SHA_PATTERN.fullmatch(revision_sha):
        msg = "Hugging Face API revision is not a 40-character Git SHA"
        raise ValueError(msg)
    raw_siblings = data.get("siblings")
    if not isinstance(raw_siblings, list) or not all(
        isinstance(sibling, dict)
        and isinstance(sibling.get("rfilename"), str)
        and sibling["rfilename"]
        for sibling in raw_siblings
    ):
        msg = "Hugging Face API siblings are not named file objects"
        raise ValueError(msg)
    return data, revision_sha, [sibling["rfilename"] for sibling in raw_siblings]


def _read_huggingface_viewer(
    dataset_slug: str, fetch_fn: FetchFnType
) -> dict[str, Any]:
    """Read the viewer state without changing identity verification semantics."""
    url = f"https://datasets-server.huggingface.co/is-valid?dataset={dataset_slug}"
    status, body, _, _ = fetch_fn(url)
    if status != HTTP_OK:
        return {
            "http_status": status,
            "message": body.decode("utf-8", errors="replace")[:200],
        }
    try:
        parsed = json.loads(body.decode("utf-8"))
        return parsed if isinstance(parsed, dict) else {"raw": parsed}
    except Exception:  # noqa: BLE001
        return {"raw": body.decode("utf-8", errors="replace")}


def _read_huggingface_info(
    dataset_slug: str, fetch_fn: FetchFnType
) -> tuple[list[str], dict[str, int]]:
    """Read configs and direct row counts from datasets-server."""
    url = f"https://datasets-server.huggingface.co/info?dataset={dataset_slug}"
    status, body, _, _ = fetch_fn(url)
    if status != HTTP_OK:
        return [], {}
    try:
        parsed = json.loads(body.decode("utf-8"))
        dataset_info = parsed.get("dataset_info", {})
        configs = list(dataset_info.keys())
        counts = {
            f"{config_name}.{split_name}": split["num_examples"]
            for config_name, config in dataset_info.items()
            if isinstance(config, dict) and isinstance(config.get("splits"), dict)
            for split_name, split in config["splits"].items()
            if isinstance(split, dict) and "num_examples" in split
        }
    except Exception:  # noqa: BLE001
        return [], {}
    else:
        return configs, counts


def fetch_url(
    url: str, timeout: float = 15.0
) -> tuple[int, bytes, str, dict[str, str]]:
    """Fetch URL and return HTTP status, body bytes, SHA-256, and headers."""
    req = urllib.request.Request(  # noqa: S310
        url, headers={"User-Agent": "archive-govt-nz-readback/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = resp.read()
            status = getattr(resp, "status", HTTP_OK)
            headers = dict(resp.headers)
            sha256 = hashlib.sha256(body).hexdigest()
            return status, body, sha256, headers
    except urllib.error.HTTPError as exc:
        body = exc.read()
        sha256 = hashlib.sha256(body).hexdigest()
        return exc.code, body, sha256, dict(exc.headers)
    except Exception as exc:  # noqa: BLE001
        err_bytes = str(exc).encode("utf-8")
        sha256 = hashlib.sha256(err_bytes).hexdigest()
        return 0, err_bytes, sha256, {}


def verify_huggingface_dataset(
    dataset_slug: str,
    fetch_fn: FetchFnType = fetch_url,
) -> dict[str, Any]:
    """Verify Hugging Face dataset public metadata, revision, and files."""
    api_url = f"https://huggingface.co/api/datasets/{dataset_slug}"
    status, body, sha256, _ = fetch_fn(api_url)

    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if status != HTTP_OK:
        return {
            "dataset_slug": dataset_slug,
            "request_url": api_url,
            "retrieval_timestamp": now_iso,
            "http_status": status,
            "response_sha256": sha256,
            "status": "unreachable",
            "error": body.decode("utf-8", errors="replace")[:300],
        }

    try:
        data, revision_sha, siblings = _parse_huggingface_identity(body)
    except (TypeError, ValueError) as exc:
        return {
            "dataset_slug": dataset_slug,
            "request_url": api_url,
            "retrieval_timestamp": now_iso,
            "http_status": status,
            "response_sha256": sha256,
            "status": "invalid_metadata",
            "error": str(exc),
        }
    card_data = data.get("cardData", {})

    viewer_state = _read_huggingface_viewer(dataset_slug, fetch_fn)
    configs, direct_row_counts = _read_huggingface_info(dataset_slug, fetch_fn)

    # Bind the rights inventory and readback to the same immutable revision.
    rights_listed = "RIGHTS.md" in siblings
    rights_url = (
        f"https://huggingface.co/datasets/{dataset_slug}/resolve/"
        f"{revision_sha}/RIGHTS.md"
    )
    r_status: int | None = None
    r_sha256: str | None = None
    rights_text: str | None = None
    rights_readback_verified = False
    rights_readback_status = "not_listed"
    result_status = "verified"
    if rights_listed:
        r_status, r_body, r_sha256, _ = fetch_fn(rights_url)
        if r_status == HTTP_OK and r_body:
            rights_text = r_body.decode("utf-8", errors="replace")
            rights_readback_verified = True
            rights_readback_status = "verified"
        else:
            result_status = "inconsistent_readback"
            rights_readback_status = (
                "listed_access_controlled"
                if r_status in {401, 403}
                else "listed_unreadable"
            )

    return {
        "dataset_slug": dataset_slug,
        "request_url": api_url,
        "retrieval_timestamp": now_iso,
        "http_status": status,
        "response_sha256": sha256,
        "revision_sha": revision_sha,
        "files_count": len(siblings),
        "files_sample": siblings[:25],
        "card_metadata": card_data,
        "viewer_state": viewer_state,
        "configs": configs,
        "direct_row_counts": direct_row_counts,
        "has_rights_statement": rights_listed,
        "rights_listed_at_revision": rights_listed,
        "rights_readback_verified": rights_readback_verified,
        "rights_readback_status": rights_readback_status,
        "rights_request_url": rights_url if rights_listed else None,
        "rights_http_status": r_status,
        "rights_preview": rights_text[:200] if rights_text else None,
        "rights_sha256": r_sha256 if rights_text else None,
        "status": result_status,
    }


def verify_zenodo_doi(
    doi: str = DEFAULT_ZENODO_DOI,
    fetch_fn: FetchFnType = fetch_url,
) -> dict[str, Any]:
    """Resolve and verify Zenodo DOI, concept DOI, and relations."""
    record_id = doi.rsplit(".", maxsplit=1)[-1]
    api_url = f"https://zenodo.org/api/records/{record_id}"
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    status, body, sha256, _ = fetch_fn(api_url)
    if status != HTTP_OK:
        return {
            "doi": doi,
            "request_url": api_url,
            "retrieval_timestamp": now_iso,
            "http_status": status,
            "response_sha256": sha256,
            "status": "unreachable",
            "error": body.decode("utf-8", errors="replace")[:300],
        }

    data = json.loads(body.decode("utf-8"))
    rec_id = data.get("id")
    resolved_doi = data.get("doi")
    concept_doi = data.get("conceptdoi")
    concept_rec_id = data.get("conceptrecid")
    metadata = data.get("metadata", {})
    relations = metadata.get("relations", {})
    related_identifiers = metadata.get("related_identifiers", [])

    is_version_doi = (
        resolved_doi == doi and concept_doi is not None and concept_doi != doi
    )

    # Extract all files and checksums
    raw_files = data.get("files", [])
    files = [
        {
            "key": f.get("key"),
            "size_bytes": f.get("size"),
            "checksum": f.get("checksum"),
        }
        for f in raw_files
    ]

    # Find linked Hugging Face dataset if asserted
    linked_hf_datasets = [
        r.get("identifier")
        for r in related_identifiers
        if "huggingface.co/datasets" in r.get("identifier", "")
    ]

    return {
        "doi": doi,
        "resolved_record_id": rec_id,
        "resolved_doi": resolved_doi,
        "is_version_doi": is_version_doi,
        "concept_doi": concept_doi,
        "concept_record_id": concept_rec_id,
        "title": metadata.get("title"),
        "publication_date": metadata.get("publication_date"),
        "license": metadata.get("license", {}).get("id"),
        "creators": metadata.get("creators", []),
        "version": metadata.get("version"),
        "relations": relations,
        "linked_hf_datasets": linked_hf_datasets,
        "files_count": len(files),
        "files": files,
        "request_url": api_url,
        "retrieval_timestamp": now_iso,
        "http_status": status,
        "response_sha256": sha256,
        "status": "verified",
    }


def run_publication_verification(
    receipt_path: Path = DEFAULT_RECEIPT_PATH,
    hf_datasets: list[str] | None = None,
    zenodo_doi: str = DEFAULT_ZENODO_DOI,
    fetch_fn: FetchFnType = fetch_url,
) -> int:
    """Execute public publication identity verification without remote writes."""
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    target_datasets = hf_datasets or DEFAULT_HF_DATASETS

    print(f"[PUB-VERIFY] Verifying HF datasets: {target_datasets}...")
    hf_results: dict[str, Any] = {}
    for ds in target_datasets:
        res = verify_huggingface_dataset(ds, fetch_fn=fetch_fn)
        hf_results[ds] = res
        print(f"  - {ds}: status={res['status']} revision={res.get('revision_sha')}")

    print(f"[PUB-VERIFY] Verifying Zenodo DOI: {zenodo_doi}...")
    zenodo_result = verify_zenodo_doi(zenodo_doi, fetch_fn=fetch_fn)
    print(
        f"  - Zenodo: status={zenodo_result['status']} "
        f"concept={zenodo_result.get('concept_doi')} "
        f"files={zenodo_result.get('files_count')}"
    )

    # Audit mismatches and unresolved claims
    mismatches: list[str] = []
    unresolved_claims: list[str] = []

    # Zenodo assertions
    if zenodo_result["status"] != "verified":
        mismatches.append(f"Zenodo DOI {zenodo_doi} could not be resolved.")
    else:
        if not zenodo_result.get("linked_hf_datasets"):
            unresolved_claims.append(
                "Zenodo record does not contain related_identifiers linking to HF."
            )
        unresolved_claims.append(
            "Linked GitHub commit is not explicitly embedded in Zenodo metadata."
        )

    # Hugging Face assertions
    for ds, hf_res in hf_results.items():
        if hf_res["status"] != "verified":
            mismatches.append(f"Hugging Face dataset {ds} is unreachable.")
        elif not hf_res.get("has_rights_statement"):
            unresolved_claims.append(
                f"Hugging Face dataset {ds} is missing a public RIGHTS.md."
            )

    overall_status = "passed" if not mismatches else "BLOCKED_REMOTE_READBACK"

    receipt = {
        "schema_version": "archive-govt-nz.remote-publication-readback/v1",
        "evaluated_at": now_iso,
        "huggingface": hf_results,
        "zenodo": zenodo_result,
        "mismatches_count": len(mismatches),
        "mismatches": mismatches,
        "unresolved_claims_count": len(unresolved_claims),
        "unresolved_claims": unresolved_claims,
        "status": overall_status,
    }

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(
        f"[PUB-VERIFY] Verification complete. Receipt: {receipt_path} "
        f"(status={overall_status})"
    )

    return 0 if overall_status == "passed" else 1


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Public Publication Identities Verifier"
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=DEFAULT_RECEIPT_PATH,
        help="Path for verification receipt output",
    )
    parser.add_argument(
        "--zenodo-doi",
        type=str,
        default=DEFAULT_ZENODO_DOI,
        help="Zenodo DOI to resolve",
    )
    parser.add_argument(
        "--hf-dataset",
        action="append",
        dest="hf_datasets",
        help="Hugging Face dataset slug(s) to verify",
    )
    args = parser.parse_args()
    code = run_publication_verification(
        receipt_path=args.receipt_path,
        hf_datasets=args.hf_datasets,
        zenodo_doi=args.zenodo_doi,
    )
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
