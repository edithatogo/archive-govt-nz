"""Bounded CPI calendar evidence adoption; original reports remain reproducible."""

from __future__ import annotations

import copy
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations import cpi_source_evidence
from archive_govt_nz.domains.health_appropriations.source_health_report import (
    CPIEvidence,
    SourceHealthReportError,
    build_report,
    render_markdown,
)

TRACK = (
    Path(__file__).parents[3]
    / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)


def _inputs() -> tuple:
    source = (TRACK / "source-census.json").read_bytes()
    context = (TRACK / "context-census.json").read_bytes()
    return json.loads(source), source, json.loads(context), context


def _evidence(monkeypatch: pytest.MonkeyPatch) -> CPIEvidence:
    report = json.loads(
        (TRACK / "cpi-source-evidence-report-20261017.json").read_bytes()
    )
    monkeypatch.setattr(
        cpi_source_evidence,
        "inspect_cpi_source_evidence",
        lambda *_: copy.deepcopy(report),
    )
    return CPIEvidence(Path("unused-cas"), Path("unused-warcs"))


def test_verified_period_grid_preserves_na_other_rows_and_v1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _inputs()
    before = build_report(*inputs)
    legacy_bytes = json.dumps(before, sort_keys=True).encode()
    legacy_markdown = render_markdown(before)
    evidence = _evidence(monkeypatch)
    report = build_report(*inputs, cpi_evidence=evidence)
    assert report == build_report(*inputs, cpi_evidence=evidence)
    assert report["schema_version"] == "archive-govt-nz.health-source-health-report/v2"
    assert report["resources"] == before["resources"]
    for old, new in zip(
        before["context_series_vintages"],
        report["context_series_vintages"],
        strict=True,
    ):
        if old["entity_id"] != "cpi-2026q2":
            assert old == new
        else:
            assert (
                new["temporal_coverage_state"]
                == "quarter_labels_complete_publisher_NA_retained"
            )
            assert {k: v for k, v in new.items() if k != "temporal_coverage_state"} == {
                k: v for k, v in old.items() if k != "temporal_coverage_state"
            }
    periods = report["cpi_period_evidence"]["periods"]
    assert (
        periods["observed_labels"],
        periods["numeric"],
        periods["publisher_NA"],
    ) == (449, 422, 27)
    assert periods["missing_labels"] == []
    assert periods["numeric_continuity"] == "not_asserted; publisher_NA_retained"
    assert "27" in render_markdown(report)
    assert json.dumps(build_report(*inputs), sort_keys=True).encode() == legacy_bytes
    assert render_markdown(build_report(*inputs)) == legacy_markdown


@pytest.mark.parametrize(
    "fault",
    [
        "source_bytes",
        "context_bytes",
        "vintage",
        "body",
        "source_url",
        "observation",
        "report",
    ],
)
def test_mismatched_census_or_self_consistent_counterfeit_cannot_admit_grid(
    monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    source, source_bytes, context, context_bytes = _inputs()
    evidence = _evidence(monkeypatch)
    if fault == "source_bytes":
        source["cutoff"] = "unbound"
    elif fault == "context_bytes":
        context["base_commit"] = "0" * 40
    elif fault in {"source_url", "observation"}:
        field = "url" if fault == "source_url" else "observed_at"
        value = (
            "https://invalid.example/cpi"
            if fault == "source_url"
            else "2026-10-17T00:00:00Z"
        )
        next(
            r
            for r in source["records"]
            if r["source_id"] == "stats_nz_cpi-053a0705526fac8d"
        )[field] = value
        next(r for r in context["series"] if r["id"] == "cpi-2026q2")["sources"][0][
            field
        ] = value
        source_bytes = json.dumps(source).encode()
        context_bytes = json.dumps(context).encode()
    elif fault in {"vintage", "body"}:
        row = next(r for r in context["series"] if r["id"] == "cpi-2026q2")
        if fault == "vintage":
            row["vintage"] = "Stats-NZ-CPI-2026-Q3"
        else:
            row["sources"][0]["object_sha256"] = "0" * 64
        context_bytes = json.dumps(context).encode()
    else:
        forged = json.loads(
            (TRACK / "cpi-source-evidence-report-20261017.json").read_bytes()
        )
        forged["periods"]["publisher_NA"] = 0
        forged["periods"]["numeric"] = 449
        monkeypatch.setattr(
            cpi_source_evidence, "inspect_cpi_source_evidence", lambda *_: forged
        )
    with pytest.raises(SourceHealthReportError, match="cpi_source_health_"):
        build_report(
            source, source_bytes, context, context_bytes, cpi_evidence=evidence
        )


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["--cpi-cas-root", "unused"], "required together"),
        (["--cpi-cas-root", "unused", "--cpi-warc-root", "unused"], "distinct new"),
    ],
)
def test_cpi_tool_requires_paired_roots_and_preserves_historical_outputs(
    arguments: list[str],
    message: str,
) -> None:
    result = subprocess.run(
        [sys.executable, "tools/build_health_source_health_report.py", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert message in result.stderr


def test_v2_existing_output_is_not_implicitly_used_as_prior_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _evidence(monkeypatch)
    destination = tmp_path / "existing.json"
    destination.write_bytes(b"preserve-existing-output\n")
    markdown = tmp_path / "must-stay-absent.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_health_source_health_report.py",
            "--cpi-cas-root",
            "unused",
            "--cpi-warc-root",
            "unused",
            "--json-output",
            str(destination),
            "--markdown-output",
            str(markdown),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            "tools/build_health_source_health_report.py", run_name="__main__"
        )
    assert exc.value.code == 2
    assert destination.read_bytes() == b"preserve-existing-output\n"
    assert not markdown.exists()
