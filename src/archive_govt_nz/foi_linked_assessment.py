"""Inspect a bounded, previously linked FOI cohort without retaining case text."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter
from dataclasses import asdict
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from archive_govt_nz.foi_candidate_cohort import _observation, disposition
from archive_govt_nz.foi_candidate_probe import (
    Bounds,
    collect_candidates,
    safe_get,
    safe_url,
)

BASELINE = "candidate-assessment-complete.json"
AL_INPUT = "factual-observations-al-bh-20260907.json"
COHORT_SIZE = 6
MIN_REGISTER_LABELS = 3
SCHEMA_LABELS = {
    "nr",
    "nr.",
    "data e kerkeses",
    "objekti i kerkeses",
    "data e pergjigjes",
    "pergjigje",
    "menyra e perfundimit te kerkeses",
    "tarifa",
    "request date",
    "response date",
    "request subject",
    "disposition",
}
NAVIGATION_LABELS = {
    "foia library",
    "foia libraries",
    "reading room",
    "electronic reading room",
    "disclosure log",
    "disclosure logs",
    "publication scheme",
    "publications",
    "make a request",
    "submit a request",
    "how to make a request",
    "access to information",
    "freedom of information",
    "foia",
    "annual reports",
}
ATTACHMENTS = {"pdf", "doc", "docx", "xls", "xlsx", "csv", "zip"}


def _normal(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .split()
    )


def _check(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


class Structure(HTMLParser):
    """Count HTML structure; never retain table cells or arbitrary link text."""

    def __init__(self) -> None:
        """Keep only finite vocabularies and integer counts."""
        super().__init__()
        self.tables = self.rows = 0
        self.context: str | None = None
        self.text = ""
        self.schema: set[str] = set()
        self.navigation: set[str] = set()
        self.attachments: Counter[str] = Counter()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Inspect tags and extension counts, not attachment URLs or names."""
        self.tables += tag == "table"
        self.rows += tag == "tr"
        if tag in {"td", "th", "a"}:
            self.context, self.text = tag, ""
        if tag == "a":
            href = dict(attrs).get("href") or ""
            # Pure string processing avoids parsing attacker-controlled authorities.
            extension = (
                href.split("?", 1)[0].split("#", 1)[0].rsplit(".", 1)[-1].lower()
            )
            if extension in ATTACHMENTS:
                self.attachments[extension] += 1

    def handle_data(self, data: str) -> None:
        """Cap transient label matching; nonmatching text is never exported."""
        if self.context is not None:
            self.text = (self.text + data)[:160]

    def handle_endtag(self, tag: str) -> None:
        """Select exact known labels, including headers rendered as data cells."""
        if tag == self.context:
            label = _normal(self.text)
            if tag in {"th", "td"} and label in SCHEMA_LABELS:
                self.schema.add(label)
            if tag == "a" and label in NAVIGATION_LABELS:
                self.navigation.add(label)
            self.context, self.text = None, ""

    def result(self) -> dict[str, Any]:
        """Return stable structural metadata, not request or capture counts."""
        return {
            "table_elements": self.tables,
            "table_row_elements": self.rows,
            "schema_labels": sorted(self.schema),
            "navigation_labels": sorted(self.navigation),
            "attachment_link_counts": dict(sorted(self.attachments.items())),
        }


def linked_targets(track: Path) -> list[dict[str, Any]]:
    """Derive precisely the four FOI leads and two retained AL year links."""
    baseline = json.loads((track / BASELINE).read_bytes())
    al_input = json.loads((track / AL_INPUT).read_bytes())
    targets = []
    for row in baseline["sources"]:
        if row.get("foi_capture_disposition") == "foi_metadata_lead":
            page = row["bounded_observation"]["homepage"]
            links = [link for link in page["links"] if link["kind"] == "foi"]
        elif row["source_id"] == "al-idp-transparency":
            source = next(
                s for s in al_input["sources"] if s["source_id"] == row["source_id"]
            )
            page = next(p for p in source["pages"] if p["role"] == "catalogue")
            links = page["selected_links"]
        else:
            continue
        for link in links:
            _check(safe_url(link["url"]), "unsafe_linked_target")
            targets.append(
                {
                    "source_id": row["source_id"]
                    + ":"
                    + hashlib.sha256(link["url"].encode()).hexdigest()[:12],
                    "parent_source_id": row["source_id"],
                    "entity_id": row["entity_id"],
                    "source_url": link["url"],
                    "retained_receipt_sha256": row["retained_receipt_sha256"],
                    "parent_page_sha256": page["body_sha256"],
                    "parent_observed_at": page["observed_at"],
                    "role": "year_register"
                    if row["entity_id"] == "AL"
                    else "foi_navigation",
                }
            )
    _check(
        len(targets) == COHORT_SIZE
        and Counter(t["entity_id"] for t in targets)
        == Counter({"AL": 2, "GG": 1, "JM": 1, "KY": 1, "UM": 1}),
        "linked_cohort_drift",
    )
    _check(
        len({t["source_id"] for t in targets}) == len(targets),
        "duplicate_linked_target",
    )
    return sorted(targets, key=lambda row: row["source_id"])


async def metadata_get(
    url: str, limit: int, bounds: Bounds
) -> tuple[dict[str, Any], bytes]:
    """Reuse the pinned safe transport; add structure only for successful HTML."""
    record, body = await safe_get(url, limit, bounds)
    if record["outcome"] == "observed" and record["media_type"] in {
        "text/html",
        "application/xhtml+xml",
    }:
        parser = Structure()
        parser.feed(body.decode("utf-8", errors="replace"))
        record["structure"] = parser.result()
    return record, body


def input_pins(track: Path) -> dict[str, str]:
    """Identify exact prior bytes without changing their historical observations."""
    return {
        name: hashlib.sha256((track / name).read_bytes()).hexdigest()
        for name in (BASELINE, AL_INPUT)
    }


async def observe_links(track: Path) -> dict[str, Any]:
    """Observe only six prior links with the unchanged probe bounds and no fan-out."""
    targets = linked_targets(track)
    bounds = Bounds()
    return {
        "schema_version": "archive-govt-nz.foi-linked-observations/v1",
        "input_pins": input_pins(track),
        "bounds": asdict(bounds),
        "targets": targets,
        "sources": await collect_candidates(targets, bounds, get=metadata_get),
    }


def _structure(value: dict[str, Any]) -> None:
    _check(
        set(value)
        == {
            "table_elements",
            "table_row_elements",
            "schema_labels",
            "navigation_labels",
            "attachment_link_counts",
        },
        "structure_fields",
    )
    for key in ("table_elements", "table_row_elements"):
        _check(
            type(value[key]) is int and 0 <= value[key] <= Bounds().max_bytes,
            "invalid_structure_count",
        )
    for key, allowed in (
        ("schema_labels", SCHEMA_LABELS),
        ("navigation_labels", NAVIGATION_LABELS),
    ):
        _check(
            value[key] == sorted(set(value[key])) and set(value[key]) <= allowed,
            "unrecognized_structure_label",
        )
    _check(set(value["attachment_link_counts"]) <= ATTACHMENTS, "attachment_type")
    for count in value["attachment_link_counts"].values():
        _check(
            type(count) is int and 0 < count <= Bounds().max_bytes, "attachment_count"
        )


def assess_links(track: Path, observations: dict[str, Any]) -> dict[str, Any]:
    """Validate linked provenance and assess interface evidence, not permissions."""
    _check(
        observations["schema_version"] == "archive-govt-nz.foi-linked-observations/v1",
        "linked_schema",
    )
    _check(observations["input_pins"] == input_pins(track), "linked_input_drift")
    targets = linked_targets(track)
    _check(observations["targets"] == targets, "linked_target_drift")
    _check(observations["bounds"] == asdict(Bounds()), "linked_bounds_drift")
    records = {r["source_id"]: r for r in observations["sources"]}
    _check(
        len(records) == len(observations["sources"]) == len(targets)
        and set(records) == {t["source_id"] for t in targets},
        "linked_cohort_mismatch",
    )
    output = []
    for target in targets:
        record = records[target["source_id"]]
        for key in ("source_url", "entity_id", "retained_receipt_sha256"):
            _check(record[key] == target[key], "linked_source_mismatch")
        _observation(record, Bounds())
        page = record["homepage"]
        # Failed responses and robots traces must not bypass metadata filtering.
        for trace in [
            *record["robots"],
            *record["redirect_chain"],
            *([page] if page else []),
        ]:
            if "structure" in trace:
                _structure(trace["structure"])
        finding = "access_unverified"
        if page is not None and disposition(page) != "access_unverified":
            _check(
                page["structure"] == record["redirect_chain"][-1]["structure"],
                "structure_trace_mismatch",
            )
            title = _normal(page["title"])
            if "regjistri" in title and "kerkesave" in title and "pergjigjeve" in title:
                structure = page["structure"]
                finding = (
                    "request_response_register_table_observed"
                    if structure["table_elements"] > 0
                    and len(structure["schema_labels"]) >= MIN_REGISTER_LABELS
                    else "register_labelled_landing_observed"
                )
            elif title.startswith("foi ") or any(
                term in title
                for term in ("freedom of information", "access to information", "foia")
            ):
                finding = "foi_information_interface_observed"
            else:
                finding = "foi_scope_unverified"
        output.append(
            {
                "target": target,
                "observation": record,
                "finding": finding,
                "request_denominator": None,
                "country_complete": False,
                "capture_adapter_verified": False,
                "rights": "unchanged_not_assessed",
                "publication_approved": False,
                "schedule_active": False,
            }
        )
    return {
        "schema_version": "archive-govt-nz.foi-linked-assessment/v1",
        "input_pins": observations["input_pins"],
        "observation_content_sha256": hashlib.sha256(
            json.dumps(observations, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "transport_policy_compliance": "not_certified_by_factual_assessment",
        "summary": dict(sorted(Counter(row["finding"] for row in output).items())),
        "scope": "six_previously_linked_interfaces_not_exhaustive_discovery",
        "sources": output,
    }


def report_files(report: dict[str, Any]) -> dict[str, str]:
    """Render paired deterministic reports from the same validated observations."""
    lines = [
        "# Linked FOI factual assessment",
        "",
        json.dumps(report["summary"], sort_keys=True),
        "",
        "Six previously linked URLs only. Prior observations remain unchanged.",
        "Transport policy compliance is not certified by this factual assessment.",
        "Acquisition provenance: [dated receipt](linked-foi-provenance-20260907.json).",
        (
            "Table rows and attachment links are structural counts, "
            "not request denominators."
        ),
        (
            "No original bodies, attachments, capture coverage, rights "
            "or publication credit."
        ),
        "",
        "| Entity | URL | Outcome | Finding |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {r['target']['entity_id']} | {r['target']['source_url']} | "
        f"{r['observation']['outcome']} | {r['finding']} |"
        for r in report["sources"]
    )
    return {
        "linked-foi-assessment.json": json.dumps(report, indent=2, sort_keys=True)
        + "\n",
        "linked-foi-assessment.md": "\n".join(lines) + "\n",
    }
