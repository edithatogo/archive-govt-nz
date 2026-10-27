# SPDX-License-Identifier: Apache-2.0
"""Rights packages bind exact source context, evidence and unchanged facts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations import overview_rights as rights
from archive_govt_nz.domains.health_appropriations.source_operations import (
    SourceRequest,
)


@pytest.fixture
def qualified_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[SourceRequest, dict[str, Any], Path, bytes, bytes]:
    source = tmp_path / "original.pdf"
    source.write_bytes(b"synthetic source; upstream extraction tested separately")
    silver = tmp_path / "silver"
    silver.mkdir()
    facts = b"synthetic verified Parquet snapshot"
    (silver / "vote_health_overview_facts.parquet").write_bytes(facts)
    manifest_bytes = json.dumps(
        {
            "output_sha256": {
                "vote_health_overview_facts.parquet": hashlib.sha256(facts).hexdigest()
            }
        }
    ).encode()
    (silver / "MANIFEST.json").write_bytes(manifest_bytes)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "observation.json").write_bytes(b"synthetic publisher evidence")
    pin = hashlib.sha256(source.read_bytes()).hexdigest()
    request = SourceRequest(
        source,
        silver,
        "fixture/v1",
        pin,
        "fixture",
        "https://example.test/source.pdf",
        "2026-10-27T00:00:00Z",
    )
    assessment = {
        "profile": request.profile,
        "source_vintage": request.source_vintage,
        "source_sha256": pin,
        "source_url": request.source_locator,
        "scope": "page_2_headline_data_and_source_labels_only",
        "license": "CC-BY-4.0",
        "license_uri": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": "Synthetic test attribution",
        "exception_checks": {"test_fixture": True},
    }
    ledger = {
        "resources": [assessment],
        "evidence_sha256": {
            "observation.json": hashlib.sha256(
                (evidence / "observation.json").read_bytes()
            ).hexdigest()
        },
    }
    monkeypatch.setattr(rights, "_ledger", lambda: ledger)
    query = {
        "schema_version": "fixture",
        "status": "verified_source_faithful",
        "source_silver_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_object_sha256": pin,
        "profile": request.profile,
        "row_count": 1,
        "records": [
            {
                "source_page": 2,
                "summary_measure": "vote_total",
                "value": "1.000",
                "rights_state": "not_evaluated",
            }
        ],
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
    monkeypatch.setattr(rights, "query_overview", lambda *_args: query.copy())
    return request, query, evidence, facts, manifest_bytes


def test_qualified_package_is_repeatable_and_rejects_changed_evidence(
    tmp_path: Path,
    qualified_inputs: tuple[SourceRequest, dict[str, Any], Path, bytes, bytes],
) -> None:
    request, query, evidence, facts, manifest_bytes = qualified_inputs
    silver = request.output_dir
    inventories = []
    for name in ("first", "second"):
        output = tmp_path / name
        result = rights.qualify_overview_package(
            request, query["source_silver_manifest_sha256"], evidence, output
        )
        assert result["rights_state"] == "eligible_asserted"
        assert {r["path"] for r in result["resource_rights"]} == {
            "vote_health_overview_facts.parquet",
            "query.json",
        }
        assert all(
            r["evidence_sha256"] == result["output_sha256"]["rights.json"]
            for r in result["resource_rights"]
        )
        assert result["publication"] == "not_performed"
        assert result["release_readiness"] == "not_assessed"
        assert (output / "vote_health_overview_facts.parquet").read_bytes() == facts
        saved = json.loads((output / "query.json").read_text())
        assert (
            saved["schema_version"]
            == "archive-govt-nz.overview-rights-qualified-query/v1"
        )
        assert saved["records"] == query["records"]
        assert saved["rights"] == "eligible_asserted"
        assert saved["records"][0]["rights_state"] == "not_evaluated"
        assert saved["rights_overlay"]["effective_assessment"] == "rights.json"
        assert result["rights_overlay"] == saved["rights_overlay"]
        assert query["rights"] == "not_evaluated"
        inventories.append({p.name: p.read_bytes() for p in output.iterdir()})
    assert inventories[0] == inventories[1]
    assert (silver / "MANIFEST.json").read_bytes() == manifest_bytes
    with pytest.raises(ValueError, match="overview_rights_contract"):
        rights.qualify_overview_package(
            request,
            query["source_silver_manifest_sha256"],
            evidence,
            tmp_path / "first",
        )
    with pytest.raises(ValueError, match="overview_rights_contract"):
        rights.qualify_overview_package(
            replace(request, source_locator="https://example.test/other.pdf"),
            query["source_silver_manifest_sha256"],
            evidence,
            tmp_path / "wrong-source",
        )
    with pytest.raises(ValueError, match="overview_rights_contract"):
        rights.qualify_overview_package(
            request, query["source_silver_manifest_sha256"], evidence, silver / "nested"
        )
    query["records"][0]["source_page"] = 3
    with pytest.raises(ValueError, match="overview_rights_contract"):
        rights.qualify_overview_package(
            request,
            query["source_silver_manifest_sha256"],
            evidence,
            tmp_path / "wrong-scope",
        )
    query["records"][0]["source_page"] = 2
    (evidence / "observation.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        rights.qualify_overview_package(
            request,
            query["source_silver_manifest_sha256"],
            evidence,
            tmp_path / "bad-evidence",
        )
    assert not (tmp_path / "bad-evidence").exists()
    (evidence / "observation.json").write_bytes(b"synthetic publisher evidence")
    (evidence / "unreferenced.json").write_bytes(b"unqualified")
    with pytest.raises(ValueError, match="overview_rights_contract"):
        rights.qualify_overview_package(
            request,
            query["source_silver_manifest_sha256"],
            evidence,
            tmp_path / "extra-evidence",
        )
    assert not (tmp_path / "extra-evidence").exists()


def test_production_ledger_is_exactly_five_source_specific_decisions() -> None:
    ledger = rights._ledger()  # noqa: SLF001 - fixed public assessment inventory
    assert len(ledger["resources"]) == 5
    assert len({r["source_sha256"] for r in ledger["resources"]}) == 5
    assert len(ledger["evidence_sha256"]) == 12
    assert ledger["publication_approval"] == "not_granted"
    assert all(
        r["scope"] == "page_2_headline_data_and_source_labels_only"
        for r in ledger["resources"]
    )
