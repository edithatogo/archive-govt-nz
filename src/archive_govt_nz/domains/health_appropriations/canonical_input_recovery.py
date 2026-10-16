"""Exclusive Bronze-to-raw-to-canonical input rebuilding with fixed identities."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations import (
    budget_revenue_canonical_export,
)
from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)
from archive_govt_nz.domains.health_appropriations.budget_canonical_export import (
    export_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.budget_revenue import (
    normalize_budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.historical import (
    normalize_historical_workbook,
)
from archive_govt_nz.domains.health_appropriations.historical_canonical_export import (
    export_historical_canonical,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.health-canonical-input-recovery/v1"
MAX_SOURCES = 5
MAX_OUTPUT_FILES = 16
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_OUTPUT_BYTES = 128 * 1024 * 1024


@dataclass(frozen=True)
class SourceDefinition:
    """Locked original identity and exact prior local observation context."""

    key: str
    kind: str
    sha256: str
    source_locator: str
    source_vintage: str
    observation_token: str
    observation_id: str


@dataclass(frozen=True)
class RebuiltCanonicalInputs:
    """Fresh package bindings and their payload-free completion receipt."""

    packages: tuple[CanonicalPackageInput, ...]
    receipt: dict[str, Any]


# Reproduce recorded local observation identities, not new HTTP capture claims.
# See the track's canonical-recovery-preflight-20261017.json and cited pilots.
SOURCES = (
    SourceDefinition(
        "historical-2024",
        "historical",
        "769f2e7dd6000878cd29c2d913ad6979f28c5391c971292e6abf6148e83eb32d",
        "data/raw/fiscaltimeseries1972-2024.xlsx",
        "fiscal-2024",
        "2026-08-30T08:28:37.374000+00:00",
        "sha256:d610fb9a74809a229bce682b8773ef7b34af533d22e467ba79acbc57fc4cd8b5",
    ),
    SourceDefinition(
        "historical-2025",
        "historical",
        "de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f",
        "https://budget.govt.nz/budget/excel/fiscal-time-series/fiscaltimeseries1972-2025-year-end25.xlsx",
        "Fiscal-Time-Series-1972-2025",
        "2026-08-31T12:26:32Z",
        "sha256:d431933be47fb66651ed54c3556c96348783e447d9dc00c7a0f97dc2040e5bc4",
    ),
    SourceDefinition(
        "budget-2025",
        "budget",
        "d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338",
        "data/raw/b25-expenditure-data.xlsx",
        "Budget-2025",
        "2026-08-30T00:00:00Z",
        "sha256:c710d5caa5490fa447a9d062a13c300a1d58c6e67fc01a062ba4dfdbe2e25ff6",
    ),
    SourceDefinition(
        "budget-2026",
        "budget",
        "3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0",
        "https://budget.govt.nz/budget/excel/data/b26-expenditure-data.xlsx",
        "Budget-2026",
        "2026-08-31T05:50:00Z",
        "sha256:fd44a04149db3d11b7926373748a0c8810686ef087205345bb1efcbb8526a4ba",
    ),
    SourceDefinition(
        "revenue-2026",
        "revenue",
        "8243f6a3f9575af5ee048133f2695f3c4764ff7d86e7a74849fdafcf478cbfdb",
        "https://budget.govt.nz/budget/excel/data/b26-revenue-data.xlsx",
        "Budget-2026",
        "2026-08-29T09:00:17Z",
        "sha256:ee970e4d024950c89270b0b27257aaae6e02d2502588acc9d97aeff9fd1a6902",
    ),
)


def _require(condition: object) -> None:
    if not condition:
        message = "canonical_input_recovery_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode()


def _sources(cas: Path) -> dict[str, dict[str, Any]]:
    _require(
        0 < len(SOURCES) <= MAX_SOURCES
        and len({s.key for s in SOURCES}) == len(SOURCES)
    )
    originals = {}
    for spec in SOURCES:
        _require(
            re.fullmatch(r"[a-z]+-[0-9]{4}", spec.key) is not None
            and spec.kind in {"historical", "budget", "revenue"}
            and source_context(
                spec.sha256,
                spec.source_locator,
                spec.source_vintage,
                spec.observation_token,
            )["source_observation_id"]
            == spec.observation_id
        )
        source = cas / spec.sha256[:2] / spec.sha256
        _require(not source.is_symlink())
        payload = verified_snapshot(source, spec.sha256, max_bytes=MAX_SOURCE_BYTES)
        originals[spec.key] = {"sha256": spec.sha256, "bytes": len(payload)}
    return originals


def _inventory(root: Path) -> dict[str, dict[str, Any]]:
    paths = sorted(root.iterdir())
    _require(0 < len(paths) <= MAX_OUTPUT_FILES)
    result = {}
    for path in paths:
        _require(not path.is_symlink() and path.is_file())
        with path.open("rb") as stream:
            payload = stream.read(MAX_OUTPUT_BYTES + 1)
        _require(len(payload) <= MAX_OUTPUT_BYTES)
        result[path.name] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
    return result


def _build(
    spec: SourceDefinition, cas: Path, output: Path
) -> tuple[CanonicalPackageInput, dict[str, Any]]:
    source = cas / spec.sha256[:2] / spec.sha256
    raw, canonical = output / ("raw-" + spec.key), output / ("canonical-" + spec.key)
    normalizer = {
        "historical": normalize_historical_workbook,
        "budget": normalize_budget_workbook,
        "revenue": normalize_budget_revenue,
    }[spec.kind]
    normalizer(
        source,
        raw,
        expected_sha256=spec.sha256,
        source_locator=spec.source_locator,
        source_vintage=spec.source_vintage,
        observed_at=spec.observation_token,
    )
    raw_inventory = _inventory(raw)
    raw_pin = raw_inventory["MANIFEST.json"]["sha256"]
    if spec.kind == "historical":
        export_historical_canonical(raw, source, raw_pin, canonical, write=True)
        marker = "LOCAL_CANONICAL.json"
    elif spec.kind == "budget":
        export_budget_appropriations(raw, raw_pin, source, canonical, dry_run=False)
        marker = "LOCAL_BUDGET.json"
    else:
        budget_revenue_canonical_export.export_budget_revenue(
            raw, raw_pin, source, canonical, dry_run=False
        )
        marker = "LOCAL_REVENUE.json"
    canonical_inventory = _inventory(canonical)
    canonical_pin = canonical_inventory[marker]["sha256"]
    package = CanonicalPackageInput(
        spec.kind, canonical, canonical_pin, source, raw, raw_pin
    )
    return package, {
        "definition": asdict(spec),
        "raw_manifest_sha256": raw_pin,
        "canonical_marker_sha256": canonical_pin,
        "raw_inventory": raw_inventory,
        "canonical_inventory": canonical_inventory,
    }


def rebuild_canonical_inputs(source_cas: Path, output: Path) -> RebuiltCanonicalInputs:
    """Build only exclusive fresh inputs; retain partial attempts on failure.

    Trusted local paths and fixed source definitions are required. Existing
    Silver/canonical packages are not read. No capture, rights or publication
    authority is inferred, and the function never overwrites or resumes outputs.
    """
    _require(not output.exists() and not output.is_symlink())
    _require(source_cas.is_dir() and not source_cas.is_symlink())
    target, original_root = output.resolve(), source_cas.resolve()
    _require(
        not target.is_relative_to(original_root)
        and not original_root.is_relative_to(target)
    )
    before = _sources(source_cas)
    definitions = _json([asdict(spec) for spec in SOURCES])
    output.mkdir(parents=True, exist_ok=False)
    products = [_build(spec, source_cas, output) for spec in SOURCES]
    _require(before == _sources(source_cas))
    receipt = {
        "schema_version": VERSION,
        "status": "written_local",
        "scope": "pinned_originals_to_fresh_raw_and_canonical",
        "definitions_sha256": hashlib.sha256(definitions).hexdigest(),
        "source_inputs": before,
        "profiles": {
            spec.key: result[1] for spec, result in zip(SOURCES, products, strict=True)
        },
        "retained_derivatives_consumed": False,
        "observation_context": (
            "exact_prior_local_tokens_replayed_no_new_capture_attestation"
        ),
        "originals_unchanged": True,
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
    with (output / "RECOVERY_INPUTS.json").open("xb") as stream:
        stream.write(_json(receipt))
    return RebuiltCanonicalInputs(tuple(result[0] for result in products), receipt)
