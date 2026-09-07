"""Offline, source-bound factual assessment of the complete candidate cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from itertools import pairwise
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from archive_govt_nz.foi_candidate_probe import (
    CHUNK_BYTES,
    MAX_LABEL,
    MAX_LINKS,
    ROBOTS_BYTES,
    Bounds,
    classify_metadata,
    safe_url,
)


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _date(value: str) -> datetime:
    date = datetime.fromisoformat(value)
    _require(date.utcoffset() is not None, "undated_observation")
    return date


def _trace(trace: dict[str, Any], cap: int, start: datetime, end: datetime) -> None:
    _require(start <= _date(trace["observed_at"]) <= end, "observation_date_range")
    _require(trace["url"] is None or safe_url(trace["url"]), "unsafe_trace_url")
    count = trace["body_bytes"]
    _require(type(count) is int and 0 <= count <= cap, "body_byte_limit")
    received = trace.get("received_bytes", 0)
    _require(
        type(received) is int and count <= received <= cap + CHUNK_BYTES,
        "received_byte_limit",
    )
    digest = trace["body_sha256"]
    _require(
        digest is None or bool(re.fullmatch(r"[0-9a-f]{64}", digest)),
        "invalid_body_digest",
    )
    if trace["outcome"] == "observed":
        _require(
            trace["status"] == HTTPStatus.OK and digest is not None,
            "unbacked_observation",
        )


def _observation(row: dict[str, Any], bounds: Bounds) -> None:
    start, end = _date(row["observed_at"]), _date(row["finished_at"])
    _require(start <= end, "observation_date_range")
    for key, cap in (("robots", ROBOTS_BYTES), ("redirect_chain", bounds.max_bytes)):
        _require(len(row[key]) <= bounds.max_redirects + 1, "redirect_limit")
        for trace in row[key]:
            _trace(trace, cap, start, end)
        chain = row[key]
        if chain:
            source = urlsplit(row["source_url"])
            expected = (
                f"{source.scheme}://{source.netloc}/robots.txt"
                if key == "robots"
                else row["source_url"]
            )
            _require(chain[0]["url"] == expected, "trace_source_mismatch")
            for previous, current in pairwise(chain):
                _require(
                    previous["outcome"] == "redirect"
                    and previous.get("redirect_url") == current["url"],
                    "unbound_redirect_trace",
                )
    page = row["homepage"]
    if page is not None:
        _require(bool(row["robots"]), "missing_robots_observation")
        robots = row["robots"][-1]
        _require(
            robots["status"] in {HTTPStatus.NOT_FOUND, HTTPStatus.GONE}
            or (
                robots["outcome"] == "observed"
                and row.get("robots_policy", {}).get("allowed") is True
            ),
            "unverified_robots_admission",
        )
        _require(bool(row["redirect_chain"]), "missing_page_trace")
        terminal = row["redirect_chain"][-1]
        for key in (
            "url",
            "observed_at",
            "status",
            "body_bytes",
            "body_sha256",
            "media_type",
        ):
            _require(page[key] == terminal[key], "page_trace_mismatch")
        expected_outcome = terminal["outcome"]
        if expected_outcome == "observed":
            _require(terminal["status"] == HTTPStatus.OK, "unbacked_terminal_success")
            if terminal["media_type"] == "text/plain":
                expected_outcome = "non_html_metadata"
                _require(
                    not page["title"] and not page["links"],
                    "non_html_terminal_metadata",
                )
            else:
                _require(
                    terminal["media_type"] in {"text/html", "application/xhtml+xml"},
                    "non_html_terminal_success",
                )
        _require(page["outcome"] == expected_outcome, "page_terminal_outcome_mismatch")
        _require(row["outcome"] == page["outcome"], "page_outcome_mismatch")
        _require(
            len(page["title"]) <= MAX_LABEL and len(page["links"]) <= MAX_LINKS,
            "metadata_limit",
        )
        for link in page["links"]:
            _require(
                safe_url(link["url"])
                and len(link["label"]) <= MAX_LABEL
                and link["kind"] in {"foi", "catalogue"},
                "invalid_navigation",
            )
    else:
        _require(row["outcome"] != "observed", "missing_observed_page")


def disposition(page: dict[str, Any] | None) -> str:
    """Reject successful challenge pages as evidence of catalogue access."""
    if page is None:
        return "access_unverified"
    title = page["title"].casefold()
    if any(
        term in title
        for term in (
            "challenge validation",
            "just a moment",
            "access denied",
            "403 forbidden",
            "404 not found",
            "domain for sale",
        )
    ):
        return "access_unverified"
    return classify_metadata(page)


def assess_cohort(baseline_path: Path, observations_path: Path) -> dict[str, Any]:
    """Validate all remaining source identities; preserve prior policy and dates."""
    raw = baseline_path.read_bytes()
    baseline = json.loads(raw)
    observations_raw = observations_path.read_bytes()
    observations = json.loads(observations_raw)
    _require(
        observations["schema_version"] == "archive-govt-nz.foi-candidate-probes/v1",
        "probe_schema",
    )
    _require(
        observations["baseline_sha256"] == hashlib.sha256(raw).hexdigest(),
        "baseline_digest_mismatch",
    )
    bounds = Bounds(**observations["bounds"])
    remaining = {
        row["source_id"]: row
        for row in baseline["sources"]
        if row["factual_review"] == "retained_evidence_assessed"
    }
    probes = {row["source_id"]: row for row in observations["sources"]}
    _require(
        len(probes) == len(observations["sources"])
        and probes.keys() == remaining.keys(),
        "inexact_candidate_cohort",
    )
    output = []
    for original in sorted(baseline["sources"], key=lambda row: row["source_id"]):
        row = deepcopy(original)
        if row["source_id"] in probes:
            probe = probes[row["source_id"]]
            for key in ("entity_id", "source_url", "retained_receipt_sha256"):
                _require(probe[key] == row[key], "source_binding_mismatch")
            _observation(probe, bounds)
            row["factual_review"] = "bounded_observations_assessed"
            row["bounded_observation"] = deepcopy(probe)
            row["foi_capture_disposition"] = disposition(probe["homepage"])
            row["disposition_scope"] = (
                "observed_interface_only_not_country_or_entire_site"
            )
            row["source_access"] = probe["outcome"]
            row["source_existence"] = (
                "http_endpoint_observed"
                if any(t["status"] is not None for t in probe["redirect_chain"])
                else "not_established_by_this_probe"
            )
            row["foi_scope"] = row["foi_capture_disposition"]
            row["interface"] = "bounded_landing_metadata_only"
        output.append(row)
    return {
        "schema_version": "archive-govt-nz.foi-candidate-cohort-assessment/v1",
        "baseline_sha256": observations["baseline_sha256"],
        "observations_sha256": hashlib.sha256(observations_raw).hexdigest(),
        "bounds": observations["bounds"],
        "summary": {
            "candidate_count": len(output),
            "new_observation_count": len(probes),
            "prior_observations_preserved": len(output) - len(probes),
            "outcomes": dict(
                sorted(Counter(p["outcome"] for p in probes.values()).items())
            ),
            "dispositions": dict(
                sorted(
                    Counter(disposition(p["homepage"]) for p in probes.values()).items()
                )
            ),
        },
        "limitations": [
            "All candidates factually assessed; failures are not successful access.",
            "Out-of-scope applies only to the observed general catalogue interface.",
            (
                "No exhaustive country discovery, capture coverage, rights "
                "or publication credit."
            ),
            (
                "Title/navigation metadata and body digests are not retained "
                "original bodies."
            ),
            (
                "Publisher attribution, adapters, licence and nonpersonal schema "
                "remain separate."
            ),
            (
                "No human factual-review queue; unresolved facts require further "
                "public evidence."
            ),
        ],
        "sources": output,
    }


def report_files(report: dict[str, Any]) -> dict[str, str]:
    """Render deterministic JSON and a compact complete candidate outcome table."""
    lines = [
        "# Complete factual candidate assessment",
        "",
        json.dumps(report["summary"], sort_keys=True),
        "",
    ]
    lines.extend(report["limitations"])
    lines.extend(
        ["", "| Source | Outcome | FOI interface disposition |", "| --- | --- | --- |"]
    )
    lines.extend(
        f"| {row['source_id']} | {row['source_access']} | "
        f"{row.get('foi_capture_disposition', 'prior_assessment_preserved')} |"
        for row in report["sources"]
    )
    return {
        "candidate-assessment-complete.json": json.dumps(
            report, indent=2, sort_keys=True
        )
        + "\n",
        "candidate-assessment-complete.md": "\n".join(lines) + "\n",
    }


def main() -> None:
    """Emit the offline assessment to stdout; never perform network operations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("observations", type=Path)
    args = parser.parse_args()
    sys.stdout.write(
        json.dumps(
            assess_cohort(args.baseline, args.observations), indent=2, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
