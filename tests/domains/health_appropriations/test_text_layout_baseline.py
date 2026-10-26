# SPDX-License-Identifier: Apache-2.0
"""The text baseline is pinned, repeatable and explicit about unavailable inputs."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from tests.domains.health_appropriations.test_cpi_adapter import HEADER, META
from tests.domains.health_appropriations.test_moh_indicator_adapter import _payload
from tests.domains.health_appropriations.test_pharmac_adapter import payload
from tests.domains.health_appropriations.test_source_layout_reconciliation import (
    _evidence,
)

from archive_govt_nz.domains.health_appropriations import (
    moh_canonical_projection,
    moh_indicator_adapter,
)
from archive_govt_nz.domains.health_appropriations import (
    text_layout_baseline as baseline,
)
from archive_govt_nz.domains.health_appropriations.adapter_drift import (
    compare_adapter_drift,
)
from archive_govt_nz.domains.health_appropriations.schema_drift import (
    layout_fingerprint,
)
from archive_govt_nz.domains.health_appropriations.source_layout_reconciliation import (
    SourceLayoutReconciliationError,
    reconcile_source_layout_reports,
)

TRACK = (
    Path(__file__).resolve().parents[3]
    / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)


def _cohort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[bytes, bytes, list[Path]]:
    profiles = dict(baseline.PROFILES)
    pins = dict(moh_indicator_adapter.SOURCE_SHA256_BY_PROFILE)
    sources, captures, paths = [], [], []
    for source_id, profile in profiles.items():
        body = (
            _payload(profile.profile)
            if profile.profile.startswith("fig")
            else payload()
            if profile.media_type == "text/html"
            else (HEADER + "CPIQ.SE9A,2026.06,1234" + META).encode()
        )
        digest = hashlib.sha256(body).hexdigest()
        profiles[source_id] = replace(profile, source_sha256=digest)
        if profile.profile.startswith("fig"):
            pins[profile.profile] = digest
        path = tmp_path / digest[:2] / digest
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(body)
        paths.append(path)
        sources.append(
            {
                "source_id": source_id,
                "object_sha256": digest,
                "media_type": profile.media_type,
                "disposition": "captured",
                "url": moh_canonical_projection.PROFILES.get(
                    profile.profile, "https://example.test/retained"
                ),
                "observed_at": "2026-08-29T09:00:17Z",
            }
        )
        captures.append(
            {
                "source_id": source_id,
                "sha256": digest,
                "bytes": len(body),
                "state": "captured",
            }
        )
    monkeypatch.setattr(baseline, "PROFILES", profiles)
    monkeypatch.setattr(moh_indicator_adapter, "SOURCE_SHA256_BY_PROFILE", pins)
    return (
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-source-census/v1",
                "cutoff": "fixture",
                "records": sources,
            }
        ).encode(),
        json.dumps({"cutoff": "fixture", "results": captures}).encode(),
        paths,
    )


def test_four_profiles_repeat_with_layout_schema_and_dispatch_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    census, capture, paths = _cohort(tmp_path, monkeypatch)
    original = [path.read_bytes() for path in paths]
    first = baseline.build_text_layout_baseline_report(census, capture, tmp_path)
    assert first == baseline.build_text_layout_baseline_report(
        census, capture, tmp_path
    )
    assert first["summary"] == {
        "captured_text_source_count": 4,
        "baseline_recorded_count": 4,
        "layout_unavailable_count": 0,
    }
    assert baseline.compare_text_layout_reports(first, first)["status"] == "matching"
    for row in first["text_layouts"]:
        assert len(row["declared_fact_schema_sha256"]) == 64
        drift = row["dispatch_drift"]
        assert compare_adapter_drift(drift, drift)["ordered_output_identical"] is True
    assert original == [path.read_bytes() for path in paths]


@pytest.mark.parametrize("cause", ["missing", "corrupt", "unqualified", "unsupported"])
def test_unavailable_or_unknown_source_is_reason_coded_without_inferred_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cause: str
) -> None:
    census, capture, paths = _cohort(tmp_path, monkeypatch)
    decoded, captured = json.loads(census), json.loads(capture)
    original = baseline.build_text_layout_baseline_report(census, capture, tmp_path)
    expected = {
        "missing": "bronze_object_unavailable",
        "corrupt": "bronze_object_fixity_mismatch",
        "unqualified": "source_profile_identity_not_qualified",
        "unsupported": "source_specific_text_profile_not_registered",
    }[cause]
    if cause == "missing":
        paths[0].unlink()
    elif cause == "corrupt":
        paths[0].write_bytes(b"corrupt")
    elif cause == "unqualified":
        decoded["records"][0]["object_sha256"] = captured["results"][0]["sha256"] = (
            "0" * 64
        )
    else:
        decoded["records"][0]["source_id"] = captured["results"][0]["source_id"] = (
            "unknown"
        )
    report = baseline.build_text_layout_baseline_report(
        json.dumps(decoded).encode(), json.dumps(captured).encode(), tmp_path
    )
    held = [
        row for row in report["text_layouts"] if row["status"] == "layout_unavailable"
    ]
    assert len(held) == 1
    assert held[0]["unavailable_reason"] == expected
    assert "layout_sha256" not in held[0]
    assert baseline.compare_text_layout_reports(original, report)["status"] == "held"


@pytest.mark.parametrize("change", ["layout", "schema"])
def test_text_drift_reports_changed_layout_or_declared_schema(change: str) -> None:
    original = json.loads(
        (TRACK / "source-text-layout-baseline-20261026.json").read_bytes()
    )
    changed = deepcopy(original)
    row = changed["text_layouts"][0]
    if change == "layout":
        row["layout"]["headers"] = list(reversed(row["layout"]["headers"]))
        row["layout_sha256"] = layout_fingerprint(row["layout"])
    else:
        row["declared_fact_schema_sha256"] = "0" * 64
    drift = baseline.compare_text_layout_reports(original, changed)
    assert drift["status"] == "drift"
    assert drift["normalization_approval"] == "not_granted"


def test_reconciliation_adds_the_four_text_baselines_and_rejects_drift() -> None:
    census, _, pdf = _evidence()
    workbook = (TRACK / "bronze-workbook-layout-baseline-20261024.json").read_bytes()
    text = (TRACK / "source-text-layout-baseline-20261026.json").read_bytes()
    report = reconcile_source_layout_reports(
        census,
        workbook,
        pdf,
        workbook,
        pdf,
        text_baseline_bytes=text,
        text_recheck_bytes=text,
    )
    assert report["summary"]["sources_with_structural_baseline"] == 75
    assert report["summary"]["sources_without_structural_baseline"] == 0
    assert report["summary"]["text_layout_source_count"] == 4
    changed: dict[str, Any] = json.loads(text)
    changed["text_layouts"][0]["layout"]["headers"][0] = "changed"
    with pytest.raises(
        SourceLayoutReconciliationError, match="text_layout_fingerprint_invalid"
    ):
        reconcile_source_layout_reports(
            census,
            workbook,
            pdf,
            workbook,
            pdf,
            text_baseline_bytes=text,
            text_recheck_bytes=json.dumps(changed).encode(),
        )
