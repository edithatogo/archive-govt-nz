"""Validate source review coverage without granting analytical admission."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

TRACK = "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
RIGHTS = Literal[
    "publisher_default_observed_unadjudicated",
    "infoshare_export_not_evaluated",
    "publisher_defaults_observed_exceptions_unadjudicated",
    "pharmac_default_observed_unadjudicated",
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Series(_StrictModel):
    series_id: str
    vintage_or_range: str
    period_basis: str
    rights: RIGHTS
    analytical_status: str
    source_sha256: str | None = None
    source_export: str | None = None
    source_export_acquired_at: str | None = None
    source_export_bytes: int | None = Field(default=None, ge=0)


class _Evidence(_StrictModel):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class _Review(_StrictModel):
    schema_version: str
    observed_at: str
    scope: str
    series: dict[str, _Series]
    series_count: int
    source_families: dict[str, Any]
    evidence: list[_Evidence]


def validate_review(path: Path, root: Path) -> dict[str, Any]:
    """Check source counts and repository evidence, not rights or measure approval."""
    root = root.resolve()
    report = _read_review(path)
    if report.series_count != len(report.series):
        msg = "series_count mismatch"
        raise ValueError(msg)
    evidence = _verify_evidence(report.evidence, root)
    source_path = f"{TRACK}/source-census.json"
    history_path = f"{TRACK}/historical-source-register.json"
    if source_path not in evidence or history_path not in evidence:
        msg = "required source census evidence missing"
        raise ValueError(msg)
    source = _read_json(root / source_path)
    history = _read_json(root / history_path)
    _check_vote_history(report, source["records"])
    _check_budget_history(report, source["records"], history)
    _check_population(report, root)
    return report.model_dump()


def _read_review(path: Path) -> _Review:
    try:
        return _Review.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        msg = "invalid source-measure review schema"
        raise ValueError(msg) from exc


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_evidence(items: list[_Evidence], root: Path) -> set[str]:
    paths: set[str] = set()
    for item in items:
        path = Path(item.path)
        candidate = root / path
        if (
            path.is_absolute()
            or not candidate.resolve().is_relative_to(root)
            or not candidate.is_file()
            or hashlib.sha256(candidate.read_bytes()).hexdigest() != item.sha256
        ):
            msg = "invalid source-measure evidence"
            raise ValueError(msg)
        paths.add(item.path)
    return paths


def _family(report: _Review, name: str) -> dict:
    value = report.source_families.get(name)
    if not isinstance(value, dict):
        raise TypeError
    return value


def _check_vote_history(report: _Review, records: list[dict]) -> None:
    family = _family(report, "vote_health")
    docs = [
        row
        for row in records
        if row.get("family") == "treasury_vote_health_document"
        and row.get("disposition") == "captured"
    ]
    estimates: set[int] = set()
    supplementary: set[int] = set()
    for row in docs:
        title = row.get("title", "")
        if "Estimates of Appropriations" not in title:
            continue
        year = _fiscal_year(title)
        if "Supplementary" in title:
            supplementary.add(year)
        elif (
            "Performance Information" not in title
            and "Information Supporting" not in title
        ):
            estimates.add(year)
    if len(docs) != family["captured_documents"]:
        msg = "Vote Health captured count mismatch"
        raise ValueError(msg)
    if estimates != set(family["estimates_years"]):
        msg = "Vote Health Estimates coverage mismatch"
        raise ValueError(msg)
    if supplementary != set(family["supplementary_years"]):
        msg = "Vote Health Supplementary coverage mismatch"
        raise ValueError(msg)
    years = set(range(1998, 2027))
    if years - estimates != set(family["missing_estimates_years"]):
        msg = "Vote Health missing Estimates mismatch"
        raise ValueError(msg)
    if years - supplementary != set(family["missing_supplementary_years"]):
        msg = "Vote Health missing Supplementary mismatch"
        raise ValueError(msg)
    _check_discovered(family, "discovered_estimates_urls", years - estimates)
    _check_discovered(family, "discovered_supplementary_urls", years - supplementary)


def _check_discovered(family: dict, key: str, missing: set[int]) -> None:
    for year, url in family[key].items():
        if int(year) not in missing or not url.startswith(
            "https://www.treasury.govt.nz/publications/"
        ):
            msg = "invalid discovered Vote Health locator"
            raise ValueError(msg)


def _check_budget_history(report: _Review, records: list[dict], history: dict) -> None:
    locators = history["resource_observations"]
    family = _family(report, "historical_editions")
    editions = sorted({row["edition_year"] for row in locators})
    if (
        len(locators) != family["locator_count"]
        or editions != family["editions_with_locators"]
    ):
        msg = "historical edition locator coverage mismatch"
        raise ValueError(msg)
    missing = sorted(set(family["scoped_years"]) - set(editions))
    if missing != family["editions_missing_locators"]:
        msg = "historical missing edition coverage mismatch"
        raise ValueError(msg)
    complete = bool(family["fully_enumerated_editions"])
    if family["complete"] != complete or (
        complete and family["fully_enumerated_editions"] != family["scoped_years"]
    ):
        msg = "historical completion claim mismatch"
        raise ValueError(msg)
    forecast = _family(report, "budget_befu_hyefu")
    actual = {
        kind: _captured_years(records, kind) for kind in ("budget", "befu", "hyefu")
    }
    expected = {
        kind: forecast[f"captured_{kind}_editions"]
        for kind in ("budget", "befu", "hyefu")
    }
    if actual != expected:
        msg = "captured Budget/BEFU/HYEFU edition mismatch"
        raise ValueError(msg)
    if editions != forecast["known_historical_workbook_locator_register_editions"]:
        msg = "historical workbook locator edition mismatch"
        raise ValueError(msg)


def _captured_years(records: list[dict], kind: str) -> list[int]:
    return sorted(
        {
            int(row["family"].split("_")[1])
            for row in records
            if row.get("family", "").startswith(f"{kind}_")
            and row.get("disposition") == "captured"
        }
    )


def _check_population(report: _Review, root: Path) -> None:
    population = report.series["population"]
    source = _read_json(root / f"{TRACK}/population-annual-context.json")
    if source["table_id"] not in population.series_id:
        msg = "population series mismatch"
        raise ValueError(msg)
    if source["original_sha256"] != population.source_sha256:
        msg = "population source hash mismatch"
        raise ValueError(msg)


def _fiscal_year(title: str) -> int:
    match = re.search(r"\b(19|20)(\d{2})/(\d{2})\b", title)
    if match is None:
        msg = "Vote Health document has no fiscal year"
        raise ValueError(msg)
    return int(match.group(1) + match.group(2))
