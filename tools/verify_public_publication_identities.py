"""Verify public publication identities (Hugging Face datasets and Zenodo DOIs)."""

from __future__ import annotations

import argparse
import hashlib
import json
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

    data = json.loads(body.decode("utf-8"))
    revision_sha = data.get("sha")
    card_data = data.get("cardData", {})
    siblings = [s.get("rfilename") for s in data.get("siblings", [])]

    # Check datasets-server viewer validity
    is_valid_url = (
        f"https://datasets-server.huggingface.co/is-valid?dataset={dataset_slug}"
    )
    v_status, v_body, _, _ = fetch_fn(is_valid_url)
    viewer_state: dict[str, Any] = {}
    if v_status == HTTP_OK:
        try:
            viewer_state = json.loads(v_body.decode("utf-8"))
        except Exception:  # noqa: BLE001
            viewer_state = {"raw": v_body.decode("utf-8", errors="replace")}
    else:
        viewer_state = {
            "http_status": v_status,
            "message": v_body.decode("utf-8", errors="replace")[:200],
        }

    # Check datasets-server info
    info_url = f"https://datasets-server.huggingface.co/info?dataset={dataset_slug}"
    i_status, i_body, _, _ = fetch_fn(info_url)
    configs: list[str] = []
    direct_row_counts: dict[str, int] = {}
    if i_status == HTTP_OK:
        try:
            info_data = json.loads(i_body.decode("utf-8"))
            dataset_info = info_data.get("dataset_info", {})
            configs = list(dataset_info.keys())
            for cfg_name, cfg_val in dataset_info.items():
                if isinstance(cfg_val, dict) and "splits" in cfg_val:
                    for split_name, split_val in cfg_val["splits"].items():
                        if isinstance(split_val, dict) and "num_examples" in split_val:
                            direct_row_counts[f"{cfg_name}.{split_name}"] = split_val[
                                "num_examples"
                            ]
        except Exception:  # noqa: BLE001
            direct_row_counts = {}

    # Check rights statement raw file
    rights_url = f"https://huggingface.co/datasets/{dataset_slug}/raw/main/RIGHTS.md"
    r_status, r_body, r_sha256, _ = fetch_fn(rights_url)
    rights_text = (
        r_body.decode("utf-8", errors="replace") if r_status == HTTP_OK else None
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
        "has_rights_statement": rights_text is not None,
        "rights_preview": rights_text[:200] if rights_text else None,
        "rights_sha256": r_sha256 if rights_text else None,
        "status": "verified",
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
