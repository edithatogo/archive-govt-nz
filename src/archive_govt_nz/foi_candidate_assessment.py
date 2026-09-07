"""Assess discovery evidence without conflating factual review with admission."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from archive_govt_nz.foi_catalogue import _origin
from archive_govt_nz.foi_reconciliation import reconcile_rollout

DISCOVERY_SCHEMA = "archive-govt-nz.source-discovery/v1"
MAX_BODY_BYTES = 2_000_000
MAX_METADATA_LENGTH = 200
MAX_REDIRECT_CHAIN = 3
MAX_SELECTED_LINKS = 20
MAX_ROBOTS_BYTES = 65_536
MIN_HTTP_STATUS, MAX_HTTP_STATUS = 100, 599
PAGE_ROLES = {"homepage", "catalogue"}


def _require(condition: object, reason: str = "observation_contract_mismatch") -> None:
    if not condition:
        raise ValueError(reason)


def _site(url: str) -> str:
    _origin(url)
    parsed = urlsplit(url)
    _require(parsed.port in {None, 443}, "unsafe_observation_port")
    return str(parsed.hostname).removeprefix("www.")


def _dated(value: str) -> None:
    _require(datetime.fromisoformat(value).utcoffset() is not None)


def _page(page: dict[str, Any], source_id: str, site: str) -> None:
    _require(page["source_id"] == source_id)
    _dated(page["observed_at"])
    _require(page["method"] == "GET" and page["authentication"] == "none")
    _require(
        type(page["status"]) is int
        and MIN_HTTP_STATUS <= page["status"] <= MAX_HTTP_STATUS
    )
    _require(
        type(page["body_bytes"]) is int and 0 <= page["body_bytes"] <= MAX_BODY_BYTES
    )
    _require(re.fullmatch(r"[0-9a-f]{64}", page["body_sha256"]))
    _require(page["body_retained"] is False)
    _require(
        isinstance(page["title"], str) and len(page["title"]) <= MAX_METADATA_LENGTH
    )
    chain = page["redirect_chain"]
    _require(1 <= len(chain) <= MAX_REDIRECT_CHAIN)
    _require(chain[0]["url"] == page["requested_url"])
    _require(chain[-1] == {"url": page["final_url"], "status": page["status"]})
    _require(all(step["status"] in {301, 302, 303, 307, 308} for step in chain[:-1]))
    _require(all(_site(step["url"]) == site for step in chain))
    _require(len(page["selected_links"]) <= MAX_SELECTED_LINKS)
    for link in page["selected_links"]:
        _require(_site(link["url"]) == site)
        _require(
            isinstance(link["label"], str) and len(link["label"]) <= MAX_METADATA_LENGTH
        )


def _robots(observation: dict[str, Any], pages: dict[str, Any]) -> dict[str, Any]:
    record = observation["robots"]
    homepage = pages["homepage"]
    _require(_site(record["url"]) == _site(homepage["requested_url"]))
    _require(urlsplit(record["url"]).path == "/robots.txt")
    _dated(record["observed_at"])
    payload = record["text"].encode()
    _require(len(payload) <= MAX_ROBOTS_BYTES)
    _require(hashlib.sha256(payload).hexdigest() == record["body_sha256"])
    _require(
        type(record["status"]) is int
        and MIN_HTTP_STATUS <= record["status"] <= MAX_HTTP_STATUS
    )
    parser = RobotFileParser(record["url"])
    parser.parse(record["text"].splitlines())
    api_urls = sorted(
        {link["url"] for link in homepage["selected_links"] if "/api/" in link["url"]}
    )
    # Older supported Python patch releases lack wildcard/end-anchor matching.
    # Conservatively deny complex rule sets, even on newer parsers; evaluate
    # the default agent, never a privileged crawler exception.
    complex_rules = any(
        re.match(r"\s*(?:allow|disallow)\s*:.*[*$]", line, re.IGNORECASE)
        for line in record["text"].splitlines()
    )
    api_allowed = None
    if record["status"] == HTTPStatus.OK and api_urls:
        api_allowed = not complex_rules and all(
            parser.can_fetch("*", url) for url in api_urls
        )
    return {
        "status": "observed" if record["status"] == HTTPStatus.OK else "unverified",
        "body_sha256": record["body_sha256"],
        "linked_api_urls": api_urls,
        "linked_api_allowed": api_allowed,
        "crawl_delay_seconds": parser.crawl_delay("*")
        if record["status"] == HTTPStatus.OK
        else None,
        "rate_limit_verified": False,
    }


def _observed_facts(
    observation: dict[str, Any], retained: dict[str, Any]
) -> dict[str, Any]:
    pages = {page["role"]: page for page in observation["pages"]}
    _require(len(observation["pages"]) == len(PAGE_ROLES) and set(pages) == PAGE_ROLES)
    site = _site(retained["source_url"])
    for page in pages.values():
        _page(page, retained["source_id"], site)
    home, catalogue = pages["homepage"], pages["catalogue"]
    _require(home["requested_url"] == retained["source_url"])
    _require(
        catalogue["requested_url"].rstrip("/")
        in {link["url"].rstrip("/") for link in home["selected_links"]}
    )
    accessible = (
        home["status"] == HTTPStatus.OK
        and home["media_type"] == "text/html"
        and home["body_bytes"] > 0
        and bool(home["title"].strip())
    )
    catalogue_accessible = (
        catalogue["status"] == HTTPStatus.OK
        and catalogue["media_type"] == "text/html"
        and catalogue["body_bytes"] > 0
    )
    title = (
        unicodedata.normalize("NFKD", catalogue["title"])
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )
    register_title = all(word in title for word in ("kerkesave", "pergjigjeve")) or all(
        word in title for word in ("request", "response")
    )
    register = (
        accessible
        and catalogue_accessible
        and register_title
        and any(
            link["url"].rstrip("/") != catalogue["final_url"].rstrip("/")
            and re.search(r"\b(?:19|20)\d{2}\b", link["label"])
            for link in catalogue["selected_links"]
        )
    )
    general = accessible and catalogue_accessible and "open data" in title
    return {
        "factual_review": "bounded_observations_assessed",
        "source_existence": "http_endpoint_observed",
        "source_access": "anonymous_html_observed"
        if accessible
        else "access_not_established",
        "interface": (
            "register_landing_page_observed"
            if register
            else "general_data_catalogue_observed"
            if general
            else "not_established"
        ),
        "foi_scope": "request_response_register_landing_page_observed"
        if register
        else "not_established",
        "robots": _robots(observation, pages),
        "observation_times": sorted(page["observed_at"] for page in pages.values()),
        "observed_urls": sorted(
            {step["url"] for page in pages.values() for step in page["redirect_chain"]}
        ),
        "observation_limit": "selected_metadata_only_original_html_not_retained",
    }


def _retained(row: dict[str, Any], folder: Path) -> dict[str, Any]:
    _require(row["receipt"] is not None, "candidate_discovery_receipt_missing")
    payload = (folder / row["receipt"]).read_bytes()
    _require(
        hashlib.sha256(payload).hexdigest() == row["receipt_sha256"],
        "candidate_receipt_changed",
    )
    receipt = json.loads(payload)
    _require(
        receipt.get("evidence_schema", receipt.get("schema_version"))
        == DISCOVERY_SCHEMA,
        "candidate_discovery_schema_mismatch",
    )
    url = receipt.get("source_url", receipt.get("url"))
    _site(url)
    return {
        "source_id": row["source_id"],
        "entity_id": row["entity_id"],
        "source_url": url,
        "retained_receipt": row["receipt"],
        "retained_receipt_sha256": row["receipt_sha256"],
        "declared_source_kind": receipt.get(
            "discovery_kind", receipt.get("source_type")
        ),
        "factual_review": "retained_evidence_assessed",
        "retained_evidence_support": (
            "discovery_lead_assertions_without_retained_transport"
        ),
        "declared_disposition": receipt.get("disposition", "candidate_only"),
        "source_existence": "reported_not_independently_verified",
        "source_access": "not_observed",
        "foi_scope": "not_established",
        "interface": "not_established",
        "robots": {"status": "not_observed", "rate_limit_verified": False},
        "capture_adapter_verified": False,
        "publisher_attribution": "reported_not_independently_verified",
        "access_rights": receipt.get("access_decision", "not_assessed"),
        "capture_rights": receipt.get("capture_decision", "not_assessed"),
        "retention": receipt.get("retention_decision", "not_assessed"),
        "redistribution": receipt.get("rights_decision", "not_assessed"),
        "privacy": receipt.get("privacy_decision", "not_assessed"),
        "publication_approved": False,
        "schedule_active": False,
        "hf_target": None,
        "request_denominator": None,
        "country_complete": False,
    }


def assess_candidates(
    seeds: Path, rollout_path: Path, evidence_dir: Path, observations_path: Path
) -> dict[str, Any]:
    """Assess all retained candidates and exactly the supplied factual cohort.

    Observations are local metadata receipts, not preserved original HTML or
    legal decisions. A completed factual assessment never admits a source to
    capture, public payload export or exhaustive country coverage.
    """
    lineage = reconcile_rollout(seeds, rollout_path, evidence_dir)
    candidates = [
        r
        for r in lineage["sources"]
        if r["lineage"] == "additional_candidate_not_catalogue_reviewed"
    ]
    rows = {r["source_id"]: _retained(r, evidence_dir) for r in candidates}
    _require(not observations_path.is_symlink(), "unsafe_observation_path")
    payload = observations_path.read_bytes()
    observations = json.loads(payload)
    _require(
        observations["schema_version"] == "archive-govt-nz.foi-factual-observations/v1"
    )
    _require(observations["rollout_sha256"] == lineage["rollout_sha256"])
    sources = {r["source_id"]: r for r in observations["sources"]}
    cohort = observations["cohort_source_ids"]
    _require(
        len(sources) == len(observations["sources"]) == len(cohort) == len(set(cohort))
    )
    _require(set(sources) == set(cohort) and set(sources) <= set(rows))
    for source_id, observation in sources.items():
        retained = rows[source_id]
        _require(observation["entity_id"] == retained["entity_id"])
        _require(
            observation["retained_receipt_sha256"]
            == retained["retained_receipt_sha256"]
        )
        retained.update(_observed_facts(observation, retained))
    result = sorted(rows.values(), key=lambda row: row["source_id"])
    for row in result:
        if row["declared_disposition"] == "restricted" or row["privacy"] in {
            "restricted",
            "disallowed",
        }:
            # Preserve factual findings while exporting only safe gap metadata.
            row["source_url"] = None
            row.pop("observed_urls", None)
            row["robots"].pop("linked_api_urls", None)
    return {
        "schema_version": "archive-govt-nz.foi-candidate-assessment/v1",
        "scope": "factual_source_review_not_rights_or_publication_admission",
        "catalogue_sha256": lineage["catalogue_sha256"],
        "rollout_sha256": lineage["rollout_sha256"],
        "observations_sha256": hashlib.sha256(payload).hexdigest(),
        "cohort_source_ids": sorted(sources),
        "sources": result,
        "summary": {
            "candidates": len(rows),
            "retained_receipts_assessed": len(rows),
            "bounded_factual_reviews": len(sources),
            "anonymous_html_endpoints_observed": sum(
                r["source_access"] == "anonymous_html_observed" for r in result
            ),
            "request_response_register_landings_observed": sum(
                r["foi_scope"] == "request_response_register_landing_page_observed"
                for r in result
            ),
            "general_data_catalogues_observed": sum(
                r["interface"] == "general_data_catalogue_observed" for r in result
            ),
            "candidates_without_transport_observations": len(rows) - len(sources),
            "capture_adapters_verified": 0,
            "publication_credit_granted": 0,
        },
        "remaining_catalogue_work": [
            "evidence_backed_source_scope_adapter_and_pacing_dispositions",
            "country_level_broader_discovery_dispositions",
            "import_candidate_dispositions_without_changing_pinned_seed_identity",
            "publish_and_verify_catalogue_metadata_under_separate_authority",
        ],
        "separate_execution_evidence": [
            "institutional_explicit_licence_and_nonpersonal_schema",
            "mixed_correspondence_metadata_only_until_applicable_raw_decision",
            "capture_retention_redistribution_privacy_and_HF_delivery",
            "enumerated_denominators_for_capture_completeness_claims_only",
        ],
    }


def assessment_files(report: dict[str, Any]) -> dict[str, bytes]:
    """Render factual outcomes and independent unresolved criteria together."""
    lines = [
        "# FOI candidate factual assessment",
        "",
        "Automated factual assessment is separate from rights and publication.",
        "Receipt assertions establish leads, not transport access.",
        "Selected HTML metadata does not preserve or verify original payloads.",
        "Request denominators stay null. No country completion credit is granted.",
        "",
        "| Measure | Count |",
        "| --- | ---: |",
        *(f"| {key} | {value} |" for key, value in report["summary"].items()),
        "",
        "## Remaining catalogue work",
        "",
        *(f"- {criterion}" for criterion in report["remaining_catalogue_work"]),
        "",
        "## Separate capture/publication evidence",
        "",
        "These are not prerequisites for automated factual source review.",
        *(f"- {criterion}" for criterion in report["separate_execution_evidence"]),
        "",
        "## Source assessments",
        "",
        "| Source | Factual review | Access | FOI scope | Redistribution |",
        "| --- | --- | --- | --- | --- |",
        *(
            f"| {r['source_id']} | {r['factual_review']} | {r['source_access']} | "
            f"{r['foi_scope']} | {r['redistribution']} |"
            for r in report["sources"]
        ),
    ]
    return {
        "candidate-assessment.json": (
            json.dumps(report, sort_keys=True, indent=2) + "\n"
        ).encode(),
        "candidate-assessment.md": ("\n".join(lines) + "\n").encode(),
    }


def main(argv: list[str] | None = None) -> int:
    """Emit a deterministic assessment using retained inputs only, never network."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("seeds", "rollout", "evidence-dir", "observations"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "md"), default="json")
    args = parser.parse_args(argv)
    try:
        report = assess_candidates(
            args.seeds, args.rollout, args.evidence_dir, args.observations
        )
    except OSError, ValueError, KeyError, TypeError:
        sys.stderr.write(
            "FOI factual assessment rejected invalid or unavailable inputs.\n"
        )
        return 2
    sys.stdout.write(
        assessment_files(report)[f"candidate-assessment.{args.format}"].decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
