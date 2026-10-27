# SPDX-License-Identifier: Apache-2.0
"""Evidence-bound rights packages for five reviewed Vote Health headlines."""

from __future__ import annotations

import hashlib
import json
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.overview_gold_query import (
    query_overview,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.source_operations import (
        SourceRequest,
    )

_LEDGER_SHA256 = "c22eac87da9d046b71acd095962e81e8f695e0982673dcd0cc7dd9d83fdddf83"
_MAX_BYTES = 4 * 1024 * 1024
_MAX_EVIDENCE = 12
_SOURCE_PAGE = 2
_FACTS = "vote_health_overview_facts.parquet"
_SCOPE = "page_2_headline_data_and_source_labels_only"


def _require(condition: object) -> None:
    if not condition:
        message = "overview_rights_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def _ledger() -> dict[str, Any]:
    return json.loads(
        verified_snapshot(
            Path(__file__).with_name("overview_rights_20261027.json"),
            _LEDGER_SHA256,
            max_bytes=_MAX_BYTES,
        )
    )


def _safe(path: Path) -> None:
    _require(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))


def _assessment(request: SourceRequest, ledger: dict[str, Any]) -> dict[str, Any]:
    matches = [
        r
        for r in ledger["resources"]
        if r["profile"] == request.profile
        and r["source_vintage"] == request.source_vintage
        and r["source_sha256"] == request.expected_sha256
        and r["source_url"] == request.source_locator
    ]
    _require(len(matches) == 1)
    row = matches[0]
    _require(
        row["scope"] == _SCOPE
        and row["license"] == "CC-BY-4.0"
        and row["license_uri"] == "https://creativecommons.org/licenses/by/4.0/"
    )
    return row


def _evidence(root: Path, pins: dict[str, str]) -> None:
    _safe(root)
    _require(root.is_dir() and 0 < len(pins) <= _MAX_EVIDENCE)
    _require({p.name for p in islice(root.iterdir(), _MAX_EVIDENCE + 1)} == set(pins))
    for name, pin in pins.items():
        _require(Path(name).name == name)
        _safe(root / name)
        verified_snapshot(root / name, pin, max_bytes=_MAX_BYTES)


def qualify_overview_package(
    request: SourceRequest,
    manifest_sha256: str,
    evidence_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Create a fresh scoped Gold manifest after source/evidence verification.

    The original PDF, Silver tables and historical manifests remain unchanged.
    Evidence pins establish the retained publisher observations and legal text;
    their observation format is not represented as original HTTP body capture.
    Qualification applies only to the reviewed headline data and source labels.
    No original-PDF, whole-candidate or external publication approval is granted.
    """
    _safe(output)
    _require(not output.exists() and output.parent.is_dir())
    for protected in (request.source, request.output_dir, evidence_root):
        _safe(protected)
        a, b = output.resolve(), protected.resolve()
        _require(not a.is_relative_to(b) and not b.is_relative_to(a))
    ledger = _ledger()
    row = _assessment(request, ledger)
    pins = ledger["evidence_sha256"]
    _evidence(evidence_root, pins)
    query = query_overview(request, manifest_sha256)
    _require(
        query["row_count"] == 1
        and len(query["records"]) == 1
        and query["records"][0]["source_page"] == _SOURCE_PAGE
        and query["records"][0]["summary_measure"] == "vote_total"
    )
    manifest_path = request.output_dir / "MANIFEST.json"
    original = verified_snapshot(manifest_path, manifest_sha256, max_bytes=_MAX_BYTES)
    manifest = json.loads(original)
    facts = verified_snapshot(
        request.output_dir / _FACTS,
        manifest["output_sha256"][_FACTS],
        max_bytes=_MAX_BYTES,
    )
    decision = {
        "schema_version": "archive-govt-nz.overview-rights-decision/v1",
        "state": "eligible_asserted",
        "assessment": row,
        "evidence_sha256": pins,
        "publication_approval": "not_granted",
        "scope": _SCOPE,
    }
    overlay = {
        "preserved_source_field": "rights_state",
        "source_field_semantics": "unchanged_normalization_time_observation",
        "effective_assessment": "rights.json",
        "applies_to": "resource_rights_data_payloads_only",
    }
    qualified_query = {
        **query,
        "schema_version": "archive-govt-nz.overview-rights-qualified-query/v1",
        "rights": "eligible_asserted",
        "rights_scope": _SCOPE,
        "rights_overlay": overlay,
        "license": row["license"],
        "license_uri": row["license_uri"],
        "attribution": row["attribution"],
    }
    payloads = {
        _FACTS: facts,
        "query.json": _json(qualified_query),
        "rights.json": _json(decision),
        "ATTRIBUTION.txt": (row["attribution"] + "\n").encode(),
    }
    result = {
        "schema_version": "archive-govt-nz.overview-rights-qualified-package/v1",
        "status": "verified_source_data_rights",
        "source_object_sha256": request.expected_sha256,
        "source_silver_manifest_sha256": manifest_sha256,
        "rights_state": "eligible_asserted",
        "rights_scope": _SCOPE,
        "rights_overlay": overlay,
        "license": row["license"],
        "license_uri": row["license_uri"],
        "attribution": row["attribution"],
        "evidence_sha256": pins,
        "output_sha256": {
            name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()
        },
        "publication": "not_performed",
        "release_readiness": "not_assessed",
    }
    result["resource_rights"] = [
        {
            "path": name,
            "payload_sha256": result["output_sha256"][name],
            "state": "eligible_asserted",
            "license": row["license"],
            "evidence_sha256": result["output_sha256"]["rights.json"],
        }
        for name in (_FACTS, "query.json")
    ]
    _evidence(evidence_root, pins)
    _require(
        verified_snapshot(manifest_path, manifest_sha256, max_bytes=_MAX_BYTES)
        == original
    )
    output.mkdir(exist_ok=False)
    for name, payload in {**payloads, "MANIFEST.json": _json(result)}.items():
        with (output / name).open("xb") as stream:
            stream.write(payload)
        _require((output / name).read_bytes() == payload)
    return result
