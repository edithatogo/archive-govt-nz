"""Exclusive Bronze-to-raw-to-canonical input rebuilding with fixed identities."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations import (
    biff8_canonical,
    budget_biff8,
    budget_biff8_adapter,
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
BIFF8_VERSION = "archive-govt-nz.health-canonical-input-recovery/v2"
BIFF8_2018_VERSION = "archive-govt-nz.health-canonical-input-recovery/v3"
BIFF8_2017_VERSION = "archive-govt-nz.health-canonical-input-recovery/v4"
BIFF8_2016_VERSION = "archive-govt-nz.health-canonical-input-recovery/v5"
MAX_EXPANDED_SOURCES = 13
MAX_SOURCES = 5
MAX_BIFF8_SOURCES = 7
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


# Exact observation identities from the admitted Budget2019 source pair.
BIFF8_SOURCES = (
    SourceDefinition(
        "biffbudget-2019",
        "biff8_budget",
        "30602fd66ec1f4fb7d0b47f2766f6560c4d22e90c11e994fba3e404e29ceab48",
        "https://www.treasury.govt.nz/sites/default/files/2019-05/b19-expenditure-data.xls",
        "Budget-2019",
        "2026-10-19T21:46:39.456033+00:00",
        "sha256:4f774ce3135942997d4daa8e2db5c8ac4b5776cb145b554f230580b813ae3215",
    ),
    SourceDefinition(
        "biffrevenue-2019",
        "biff8_revenue",
        "d927995dd91eda6fdfb4020eb2a3e91871a24d5144e837e7801b6725e5f33df8",
        "https://www.treasury.govt.nz/sites/default/files/2019-05/b19-revenue-data.xls",
        "Budget-2019",
        "2026-10-19T21:46:39.456033+00:00",
        "sha256:77275d0dc352a785d9778e0e0498be8a19573de52391008e4d8461bd56d85f6a",
    ),
)

# Exact prior local-inspection tokens; these do not attest a new capture.
BIFF8_2018_SOURCES = (
    SourceDefinition(
        "biffbudget-2018",
        "biff8_budget",
        "fecd70019054313f3a11cbb370be684d8bea0eea8cb3623b69a9e193ac085c24",
        "https://www.treasury.govt.nz/sites/default/files/2018-05/b18-expenditure-data.xls",
        "Budget-2018",
        "2026-10-20T14:44:44.843862+00:00",
        "sha256:af8434e4d018b62907a7d5152edba93eb1d90766520a26ae16e97478b35bf17b",
    ),
    SourceDefinition(
        "biffrevenue-2018",
        "biff8_revenue",
        "4db87e7eddd7a76b5b7523db5a01952d15e7f47b88d03ef9878d37cd077f937f",
        "https://www.treasury.govt.nz/sites/default/files/2018-05/b18-revenue-data.xls",
        "Budget-2018",
        "2026-10-20T14:44:44.843862+00:00",
        "sha256:dc9ae0d69080736adeadc17cc89d78837744297cd088f1ebc5eae26f5a3c4170",
    ),
)


# Exact qualified2017 local observation context, not a new capture.
BIFF8_2017_SOURCES = (
    SourceDefinition(
        "biffbudget-2017",
        "biff8_budget",
        "7e0cc535eb9feb7e82b1a998dd40b7b318e5593e13589aa48ef4a3b5508708fc",
        "https://www.treasury.govt.nz/sites/default/files/2018-04/b17-expenditure-data.xls",
        "Budget-2017",
        "2026-10-20T16:57:19.820018+00:00",
        "sha256:5c4e70842744902ce0cded13b122fa1a2260daa2be4698a18d39a81da876419f",
    ),
    SourceDefinition(
        "biffrevenue-2017",
        "biff8_revenue",
        "e49a706c4a5ac889e8b9e68165dbfd704a9f05b0300bef7f69abf5f5620b7adf",
        "https://www.treasury.govt.nz/sites/default/files/2018-04/b17-revenue-data.xls",
        "Budget-2017",
        "2026-10-20T16:57:19.820018+00:00",
        "sha256:40ac55251ee38cec454d67d4946584c5102d8bc6db4b231363be929e53bcd716",
    ),
)


# Exact qualified2016 local inspection tokens, not new capture attestations.
BIFF8_2016_SOURCES = (
    SourceDefinition(
        "biffbudget-2016",
        "biff8_budget",
        "bce6d2e55c15c1249881bac9d2a1afdf111cd9d1c258c20913bd4b39300f0f5a",
        "https://www.treasury.govt.nz/sites/default/files/2018-04/b16-expenditure-data.xls",
        "Budget-2016",
        "2026-10-20T18:30:09.435785+00:00",
        "sha256:d457d5a5545e3035a8c66008a22a1cf03946b4b40fe8d5b8bbcaaf3fffd5a0fa",
    ),
    SourceDefinition(
        "biffrevenue-2016",
        "biff8_revenue",
        "df34849f2ef7ce1903469edb315047afc8ae716574d163f59691a654c51b957f",
        "https://www.treasury.govt.nz/sites/default/files/2018-04/b16-revenue-data.xls",
        "Budget-2016",
        "2026-10-20T18:30:09.435785+00:00",
        "sha256:fbbecabcc9eaa6ab9824fb3caa5ac37cfafe0bdb8c7b20da88a8b40fb6c105cb",
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


def _biff_profile(spec: SourceDefinition) -> budget_biff8.BiffBudgetProfile:
    profiles = [
        profile
        for profile in budget_biff8.declared_profiles()
        if profile.kind == biff8_canonical.KINDS[spec.kind]
        and budget_biff8_adapter.source_binding(
            profile.profile_id, spec.source_vintage, spec.source_locator, spec.sha256
        )
    ]
    _require(len(profiles) == 1)
    return profiles[0]


def _sources(
    cas: Path, definitions: tuple[SourceDefinition, ...]
) -> dict[str, dict[str, Any]]:
    _require(
        0 < len(definitions) <= MAX_EXPANDED_SOURCES
        and len({s.key for s in definitions}) == len(definitions)
    )
    originals = {}
    for spec in definitions:
        _require(
            re.fullmatch(r"[a-z]+-[0-9]{4}", spec.key) is not None
            and spec.kind in {"historical", "budget", "revenue", *biff8_canonical.KINDS}
            and source_context(
                spec.sha256,
                spec.source_locator,
                spec.source_vintage,
                spec.observation_token,
            )["source_observation_id"]
            == spec.observation_id
        )
        if spec.kind in biff8_canonical.KINDS:
            _biff_profile(spec)
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


def _build_biff(
    spec: SourceDefinition, cas: Path, output: Path
) -> tuple[CanonicalPackageInput, dict[str, Any]]:
    profile = _biff_profile(spec)
    source = cas / spec.sha256[:2] / spec.sha256
    raw = output / ("raw-" + spec.key)
    canonical = output / ("canonical-" + spec.key)
    budget_biff8_adapter.normalize(
        source,
        raw,
        profile=profile.profile_id,
        expected_sha256=spec.sha256,
        source_locator=spec.source_locator,
        source_vintage=spec.source_vintage,
        observed_at=spec.observation_token,
    )
    raw_inventory = _inventory(raw)
    raw_pin = raw_inventory["MANIFEST.json"]["sha256"]
    biff8_canonical.export_canonical(
        raw,
        raw_pin,
        source,
        profile.kind,
        canonical,
        write=True,
        observed_at=spec.observation_token,
    )
    canonical_inventory = _inventory(canonical)
    canonical_pin = canonical_inventory["MANIFEST.json"]["sha256"]
    return CanonicalPackageInput(
        spec.kind, canonical, canonical_pin, source, raw, raw_pin
    ), {
        "definition": asdict(spec),
        "raw_manifest_sha256": raw_pin,
        "canonical_marker_sha256": canonical_pin,
        "raw_inventory": raw_inventory,
        "canonical_inventory": canonical_inventory,
    }


def _build(
    spec: SourceDefinition, cas: Path, output: Path
) -> tuple[CanonicalPackageInput, dict[str, Any]]:
    if spec.kind in biff8_canonical.KINDS:
        return _build_biff(spec, cas, output)
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


def _biff_definitions(editions: tuple[int, ...]) -> tuple[SourceDefinition, ...]:
    _require(
        type(editions) is tuple
        and bool(editions)
        and all(
            type(year) is int and year in {2016, 2017, 2018, 2019} for year in editions
        )
        and len(set(editions)) == len(editions)
    )
    selected: tuple[SourceDefinition, ...] = ()
    for year, definitions in (
        (2019, BIFF8_SOURCES),
        (2018, BIFF8_2018_SOURCES),
        (2017, BIFF8_2017_SOURCES),
        (2016, BIFF8_2016_SOURCES),
    ):
        if year not in editions:
            continue
        _require(
            len(definitions) == len(biff8_canonical.KINDS)
            and {s.kind for s in definitions} == set(biff8_canonical.KINDS)
        )
        selected += definitions
    return selected


def rebuild_canonical_inputs(
    source_cas: Path,
    output: Path,
    *,
    include_biff8: bool = False,
    biff8_editions: tuple[int, ...] = (2019,),
) -> RebuiltCanonicalInputs:
    """Build only exclusive fresh inputs; retain partial attempts on failure.

    Trusted local paths and fixed source definitions are required. Existing
    Silver/canonical packages are not read. No capture, rights or publication
    authority is inferred, and the function never overwrites or resumes outputs.
    """
    _require(
        type(include_biff8) is bool
        and type(biff8_editions) is tuple
        and all(type(year) is int for year in biff8_editions)
        and 0 < len(SOURCES) <= MAX_SOURCES
        and all(spec.kind in {"historical", "budget", "revenue"} for spec in SOURCES)
    )
    _require(include_biff8 or biff8_editions == (2019,))
    definitions_biff = _biff_definitions(biff8_editions) if include_biff8 else ()
    selected = (*SOURCES, *definitions_biff)
    version = VERSION
    if include_biff8:
        version = {
            2016: BIFF8_2016_VERSION,
            2017: BIFF8_2017_VERSION,
            2018: BIFF8_2018_VERSION,
            2019: BIFF8_VERSION,
        }[min(biff8_editions)]
    _require(not output.exists() and not output.is_symlink())
    _require(source_cas.is_dir() and not source_cas.is_symlink())
    target, original_root = output.resolve(), source_cas.resolve()
    _require(
        not target.is_relative_to(original_root)
        and not original_root.is_relative_to(target)
    )
    before = _sources(source_cas, selected)
    definitions = _json([asdict(spec) for spec in selected])
    output.mkdir(parents=True, exist_ok=False)
    products = [_build(spec, source_cas, output) for spec in selected]
    _require(before == _sources(source_cas, selected))
    receipt = {
        "schema_version": version,
        "status": "written_local",
        "scope": "pinned_originals_to_fresh_raw_and_canonical",
        "definitions_sha256": hashlib.sha256(definitions).hexdigest(),
        "source_inputs": before,
        "profiles": {
            spec.key: result[1] for spec, result in zip(selected, products, strict=True)
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
