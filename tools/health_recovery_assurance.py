"""Run deterministic, payload-free clean-room Health recovery assurance."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    cpi,
    cpi_canonical_projection,
    crown_expense,
    crown_expense_canonical_projection,
    fiscal_crown_canonical_projection,
    fiscal_crown_literals,
    gdp,
    gdp_canonical_projection,
    gdp_vintage_comparison,
    hyefu_crown_expense,
    hyefu_crown_expense_canonical_projection,
    moh_canonical_projection,
    moh_indicators,
    pharmac,
    pharmac_canonical_projection,
    population_annual_canonical_projection,
    qes,
    qes_canonical_projection,
    vote_health_supplementary_2013_14,
    vote_health_supplementary_2014_15,
    vote_health_supplementary_2015_16,
    vote_health_supplementary_2016_17,
    vote_health_supplementary_2018_19,
    vote_health_supplementary_2019_20,
    vote_health_supplementary_2020_21,
    vote_health_supplementary_2021_22,
    vote_health_supplementary_2022_23,
    vote_health_supplementary_2023_24,
    vote_health_supplementary_2024_25,
    vote_health_supplementary_2025_26,
)
from archive_govt_nz.domains.health_appropriations.analytical_metadata_recovery import (
    recover_analytical_metadata,
)
from archive_govt_nz.domains.health_appropriations.budget_canonical_export import (
    export_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.budget_revenue_canonical_export import (  # noqa: E501
    export_budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.canonical_consumer import (
    query_context_observations,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_export import (
    CrownGoldInput,
    FiscalCrownGoldInput,
    GoldInputs,
    MohGoldInput,
    PharmacGoldInput,
    export_canonical_gold,
)
from archive_govt_nz.domains.health_appropriations.compatibility_export import (
    export_compatibility,
)
from archive_govt_nz.domains.health_appropriations.context_gold import (
    export_context_gold,
)
from archive_govt_nz.domains.health_appropriations.gold_export import export_gold
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)
from archive_govt_nz.domains.health_appropriations.moh_canonical_projection import (
    MohIndicatorInput,
)
from archive_govt_nz.domains.health_appropriations.pharmac_canonical_projection import (
    project_pharmac_cpb,
)
from archive_govt_nz.domains.health_appropriations.plot_export import render_plots
from archive_govt_nz.domains.health_appropriations.population_annual_silver import (
    normalize_population_annual,
)
from archive_govt_nz.domains.health_appropriations.qes_canonical_projection import (
    project_qes_earnings,
)
from archive_govt_nz.domains.health_appropriations.rebuild import (
    execute_rebuild,
    plan_rebuild,
    verify_rebuild,
)
from archive_govt_nz.domains.health_appropriations.rebuild_eight import (
    execute_eight,
    plan_eight,
    verify_eight,
)
from archive_govt_nz.domains.health_appropriations.source_health_report import (
    CaptureEvidence,
    LayoutEvidence,
)
from archive_govt_nz.domains.health_appropriations.source_health_report import (
    build_report as build_source_health_report,
)
from archive_govt_nz.domains.health_appropriations.source_operations import (
    SourceRequest,
    operate_source,
)

TRACK = Path("conductor/tracks/health_appropriations_medallion_assimilation_20260829")
ARCHIVE = Path("/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations")
CONTEXT = {
    "cpi": (
        "raw-cpi-20260831-v1",
        "edb62f4b106948502e717f5f6c5e3da00efc0a64bb10b5dcbafc48cd1a6c257e",
    ),
    "wage": (
        "raw-qes-2026q2-20260831-v3",
        "0bf89bd6c10a0458ef4c578b209c3252292961976d2f50b3c27fe92907c3cb04",
    ),
    "gdp": (
        "raw-stats-gdp-20260831-v1",
        "639b3c7da60f2afa1b860c5f6c8f1c4c0ae24bf17aa7af63bf8a06a1f6471b35",
    ),
    "population": (
        "population-annual-mean-context-20260925-v1",
        "067255c4ac18377312d0a8234dc94804c876ba68866cfba3a483a4dd89415798",
    ),
}
CONTEXT_SERIES = {
    "cpi": (
        "cpi-2026q2",
        "cpi",
        "stats_nz_cpi-053a0705526fac8d",
        "f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d",
    ),
    "wage": (
        "qes-2026q2",
        "qes",
        "stats_nz_qes-faab0efe46470af8",
        "1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97",
    ),
    "gdp": (
        "gdp-stats-2026q1",
        "gdp",
        "stats_nz_gdp-9fc80ed4b7f234b2",
        "a7326e84e7704446a18e5c8942f99901a452b2170af4228e8a5c242a5532ed21",
    ),
}
DONOR_MANIFEST_SHA256 = (
    "893f387e1f361400285ccc84802b497e87802d1ad913826ff7d9055b07a03b74"
)
SOURCE_CENSUS_SHA256 = (
    "aa6f9d55ed8f416c8ea890add9ecc5363cbe4c0333f7efaa02db9fd6d44df272"
)
CONTEXT_CENSUS_SHA256 = (
    "91474db2bf996669f41ce6de6341304a1039887ccb948fd94d9f5634b425a88e"
)
POPULATION_SOURCE_SHA256 = (
    "a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9"
)
CLASSIFICATION_PACKAGES = {
    2025: {
        "path": "canonical-budget-classification-2025-20260831-v1",
        "marker_sha256": (
            "7e4d65d5bedfec72fe83d0882529d395a6401e816545286ab3fa9c8cfca8fcb3"
        ),
        "source_sha256": (
            "d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338"
        ),
        "manifest_sha256": (
            "1b1e5dfd3fa90d98dcf5200997001db236df7b40f4404b658c36f5cb0264d2fe"
        ),
        "rows": 215,
    },
    2026: {
        "path": "canonical-budget-classification-2026-20260831-v1",
        "marker_sha256": (
            "1a5aae6c79d79901c6bcaca9396fa6efa69e3572c9f382bbc011a427c5179c8d"
        ),
        "source_sha256": (
            "3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0"
        ),
        "manifest_sha256": (
            "f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738"
        ),
        "rows": 185,
    },
}
CAPTURE_MANIFEST_NAME = "official-capture-2026-10-03-health-complete.json"
PDF_LAYOUT_BASELINE_NAME = "source-pdf-layout-baseline-20261003.json"
PDF_LAYOUT_BASELINE_SHA256 = (
    "f54157679466382b665e228a5abba26388296f95b603184ff868cb188b1ec698"
)
CAPTURE_MANIFEST_SHA256 = (
    "017b3a9adbda288c60693ef038e4c0da198d8db99b2bca9cf4bb81adbc6efb5f"
)
PHARMAC_SOURCE_SHA256 = (
    "eaf5801b819321f8aed7544fb16e6348779267fd3d5f8fb1d59410803acffbea"
)
MOH_SOURCE_SHA256 = {
    "fig27/v1": "c1e7758667b8255e049603de8325d732f34a76e6099e0fe4de6553a36d48e9fc",
    "fig28/v1": "7b9a51643550e3d890f4f341f27346d3466708fe924702ade4a731d1bb6266e4",
}
MOH_SILVER_MANIFEST_SHA256 = {
    "fig27/v1": "b3a9afc2bab6562373b73d2f5c45b76a244792acbf813bfb54b4e2b66bce76a2",
    "fig28/v1": "714a0dd3fb53fa2ff26100e760983b791e81162fa30fb48d9f1d7131d8e338ed",
}
PHARMAC_SOURCE_OBSERVED_AT = "2026-08-29T09:00:17Z"
CROWN_SOURCE_OBSERVED_AT = "2026-08-29T09:00:17Z"
GDP_JUNE_CAPTURE_SHA256 = (
    "28609dbc48f7a4b68ea14f277267c7af0e2eec9b274d0c369865d7d090a2b868"
)
GDP_JUNE_SOURCE_ID = "stats_nz_gdp-588a47c19c9dbc44"
GDP_JUNE_SOURCE_SHA256 = (
    "b6d2fe15b4656143f600abeb1849432f60d769570667eb90d07ddacd3498e22d"
)
GDP_JUNE_SOURCE_LOCATOR = (
    "https://www.stats.govt.nz/assets/Uploads/Gross-domestic-product/"
    "Gross-domestic-product-June-2026-quarter/Download-data/"
    "gross-domestic-product-june-2026-quarter-current-price-income-and-expenditure.xlsx"
)
GDP_JUNE_OBSERVED_AT = "2026-09-29T21:28:10.739074Z"
GDP_JUNE_FACT_COUNT = 61
DONOR_ROW_COUNT = 312
GDP_JUNE_CAPTURE_SCOPE = (
    "source_capture_and_series_identification_only_no_analytical_"
    "admission_or_legal_approval"
)


def require_evidence(condition: object, message: str) -> None:
    """Fail closed when a recorded source binding is missing or changed."""
    if not condition:
        raise RuntimeError(message)


def bind_recorded_comparison(
    report: dict[str, Any], receipt_path: Path, error_code: str
) -> dict[str, Any]:
    """Verify a deterministic report against its pinned repeat-build receipt."""
    recorded = json.loads(receipt_path.read_bytes())
    require_evidence(isinstance(recorded, dict), f"{error_code}:invalid_receipt")
    recorded_comparison = {
        key: value for key, value in recorded.items() if key != "repeat_identical"
    }
    mismatched_fields = sorted(
        key
        for key in report.keys() | recorded_comparison.keys()
        if report.get(key) != recorded_comparison.get(key)
    )
    require_evidence(
        not mismatched_fields and recorded.get("repeat_identical") is True,
        f"{error_code}:" + ",".join(mismatched_fields),
    )
    return {
        **report,
        "recorded_comparison_sha256": digest(receipt_path),
        "recorded_repeat_identical": True,
    }


def digest(path: Path) -> str:
    """Return a streaming SHA-256 digest for one file."""
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def tree(root: Path) -> dict[str, dict[str, Any]]:
    """Return deterministic file sizes and hashes below a product root."""
    return {
        path.relative_to(root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def compare_product_outputs(first: Path, second: Path, product: str) -> dict[str, Any]:
    """Return first-run pins only when a second clean build matches exactly."""
    first_files = tree(first)
    if first_files != tree(second):
        message = f"{product}_repeat_mismatch"
        raise RuntimeError(message)
    return first_files


def context_source_binding(family: str) -> dict[str, str]:
    """Join a context Silver input to its exact captured census and Bronze pin."""
    context_bytes = (TRACK / "context-census.json").read_bytes()
    require_evidence(
        hashlib.sha256(context_bytes).hexdigest() == CONTEXT_CENSUS_SHA256,
        "context_census_pin_mismatch",
    )
    context = json.loads(context_bytes)
    population = json.loads((TRACK / "population-annual-context.json").read_text())
    if family == "population":
        source_hash = population["original_sha256"]
        require_evidence(
            source_hash == POPULATION_SOURCE_SHA256
            and population["original_storage"] == "external_bronze_cas_sha256"
            and population["rights"] == "not_evaluated",
            "population_context_source_binding_invalid",
        )
        return {
            "source_object_sha256": source_hash,
            "source_locator": population["export_route"],
            "source_vintage": population["release_date"],
            "observed_at": population["retrieved_at"],
        }
    require_evidence(family in CONTEXT_SERIES, f"unknown_context_family:{family}")
    series_id, source_family, source_id, pinned_hash = CONTEXT_SERIES[family]
    matches = [entry for entry in context["series"] if entry["id"] == series_id]
    require_evidence(
        len(matches) == 1 and matches[0]["family"] == source_family,
        f"context_series_binding_invalid:{family}",
    )
    selected = matches[0]
    sources = selected["sources"]
    require_evidence(len(sources) == 1, f"context_source_count_invalid:{family}")
    source = sources[0]
    require_evidence(
        source["source_id"] == source_id and source["object_sha256"] == pinned_hash,
        f"context_source_metadata_drift:{family}",
    )
    census_bytes = (TRACK / "source-census.json").read_bytes()
    require_evidence(
        hashlib.sha256(census_bytes).hexdigest() == SOURCE_CENSUS_SHA256,
        "source_census_pin_mismatch",
    )
    census = json.loads(census_bytes)
    observed = [row for row in census["records"] if row["source_id"] == source_id]
    require_evidence(
        len(observed) == 1,
        f"captured_source_missing_or_ambiguous:{family}",
    )
    row = observed[0]
    require_evidence(
        all(
            row.get(key) == expected
            for key, expected in {
                "disposition": "captured",
                "object_sha256": pinned_hash,
                "url": source["url"],
                "observed_at": source["observed_at"],
            }.items()
        ),
        f"captured_source_binding_mismatch:{family}",
    )
    return {
        "source_object_sha256": pinned_hash,
        "source_locator": source["url"],
        "source_vintage": selected["vintage"],
        "observed_at": source["observed_at"],
    }


def gdp_june_source_binding() -> dict[str, str]:
    """Bind the June GDP successor to its capture receipt, census and Bronze bytes."""
    capture_path = TRACK / "gdp-june-capture-20260930.json"
    capture_bytes = capture_path.read_bytes()
    require_evidence(
        hashlib.sha256(capture_bytes).hexdigest() == GDP_JUNE_CAPTURE_SHA256,
        "gdp_june_capture_receipt_pin_mismatch",
    )
    capture = json.loads(capture_bytes)
    source = capture["source"]
    expected = {
        "source_id": GDP_JUNE_SOURCE_ID,
        "sha256": GDP_JUNE_SOURCE_SHA256,
        "url": GDP_JUNE_SOURCE_LOCATOR,
        "http_status": 200,
        "bytes": 50067,
    }
    require_evidence(
        all(source.get(key) == value for key, value in expected.items())
        and capture.get("observed_at") == GDP_JUNE_OBSERVED_AT
        and capture.get("scope") == GDP_JUNE_CAPTURE_SCOPE
        and capture["selected_series"].get("cell_selector") == "C27:BK27"
        and capture["selected_series"].get("quarter_observations")
        == GDP_JUNE_FACT_COUNT,
        "gdp_june_capture_binding_invalid",
    )
    census_bytes = (TRACK / "source-census.json").read_bytes()
    require_evidence(
        hashlib.sha256(census_bytes).hexdigest() == SOURCE_CENSUS_SHA256,
        "source_census_pin_mismatch",
    )
    census = json.loads(census_bytes)
    matches = [
        row for row in census["records"] if row["source_id"] == GDP_JUNE_SOURCE_ID
    ]
    require_evidence(
        len(matches) == 1
        and all(
            matches[0].get(key) == value
            for key, value in {
                "disposition": "captured",
                "object_sha256": GDP_JUNE_SOURCE_SHA256,
                "url": GDP_JUNE_SOURCE_LOCATOR,
                "observed_at": GDP_JUNE_OBSERVED_AT,
            }.items()
        ),
        "gdp_june_census_binding_invalid",
    )
    bronze = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / GDP_JUNE_SOURCE_SHA256[:2]
        / GDP_JUNE_SOURCE_SHA256
    )
    require_evidence(
        bronze.is_file()
        and not bronze.is_symlink()
        and digest(bronze) == GDP_JUNE_SOURCE_SHA256,
        "gdp_june_bronze_object_mismatch",
    )
    return {
        "source_object_sha256": GDP_JUNE_SOURCE_SHA256,
        "source_locator": GDP_JUNE_SOURCE_LOCATOR,
        "source_vintage": gdp.JUNE_VINTAGE,
        "observed_at": GDP_JUNE_OBSERVED_AT,
    }


def rebuild_gdp_june_silver(root: Path, index: int) -> dict[str, Any]:
    """Rebuild the exact June GDP Silver profile from the pinned Bronze object."""
    binding = gdp_june_source_binding()
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / binding["source_object_sha256"][:2]
        / binding["source_object_sha256"]
    )
    output = root / f"gdp-june-{index}"
    receipt = operate_source(
        SourceRequest(
            source=source,
            output_dir=output,
            profile="gdp-expenditure-actual-2026q2/v1",
            expected_sha256=binding["source_object_sha256"],
            source_vintage=binding["source_vintage"],
            source_locator=binding["source_locator"],
            observed_at=binding["observed_at"],
        ),
        dry_run=False,
    )
    require_evidence(
        receipt.get("status") == "written_local"
        and receipt.get("counts")
        == {
            "facts": GDP_JUNE_FACT_COUNT,
            "lineage": GDP_JUNE_FACT_COUNT * 15,
            "dispositions": 2323,
        },
        "gdp_june_source_operation_failed",
    )
    return {"receipt": receipt, "files": tree(output)}


def gdp_june_recovery_report(
    root: Path, *, silver_roots: tuple[Path, Path] | None = None
) -> dict[str, Any]:
    """Prove Silver and canonical June outputs match without analytical selection."""
    if silver_roots is None:
        source_packages = (root / "gdp-june-1", root / "gdp-june-2")
        first = rebuild_gdp_june_silver(root, 1)
        second = rebuild_gdp_june_silver(root, 2)
    else:
        source_packages = (
            silver_roots[0] / "gdp-june-1",
            silver_roots[1] / "gdp-june-1",
        )
        first = rebuild_gdp_june_silver(silver_roots[0], 1)
        second = rebuild_gdp_june_silver(silver_roots[1], 1)
    files = compare_product_outputs(
        source_packages[0], source_packages[1], "gdp_june_silver"
    )
    require_evidence(first == second, "gdp_june_silver_receipt_mismatch")
    canonical_products = []
    for index, package in enumerate(source_packages, start=1):
        manifest_pin = digest(package / "MANIFEST.json")
        facts, lineage, receipt = gdp_canonical_projection.project_gdp_june(
            package, manifest_pin, ARCHIVE / "bronze-cas" / "sha256"
        )
        target = root / f"gdp-june-canonical-{index}"
        target.mkdir()
        pq.write_table(
            facts, target / "fiscal_context_fact.parquet", compression="zstd"
        )
        pq.write_table(lineage, target / "field_lineage.parquet", compression="zstd")
        (target / "projection-receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        canonical_products.append({"files": tree(target), "receipt": receipt})
    canonical_repeat = canonical_products[0] == canonical_products[1]
    require_evidence(canonical_repeat, "gdp_june_canonical_projection_repeat_mismatch")
    return {
        "source_id": GDP_JUNE_SOURCE_ID,
        "source_object_sha256": GDP_JUNE_SOURCE_SHA256,
        "source_vintage": gdp.JUNE_VINTAGE,
        "source_capture_receipt_sha256": GDP_JUNE_CAPTURE_SHA256,
        "files": files,
        "counts": first["receipt"]["counts"],
        "repeat_identical": True,
        "canonical_projection": {
            "files": canonical_products[0]["files"],
            "repeat_identical": canonical_repeat,
            "manifest_sha256": canonical_products[0]["receipt"][
                "source_manifest_sha256"
            ],
            "fact_count": canonical_products[0]["receipt"]["output_records"],
            "lineage_count": canonical_products[0]["receipt"]["lineage_records"],
            "transformation_id": canonical_products[0]["receipt"]["transformation_id"],
        },
        "currency": "unverified",
        "denominator_selection": "not_performed",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }


def gdp_vintage_comparison_report(root: Path) -> dict[str, Any]:
    """Compare shared GDP periods and verify the pinned comparison receipt."""
    march_path = root / "gdp-canonical-1" / "fiscal_context_fact.parquet"
    june_path = root / "gdp-june-canonical-1" / "fiscal_context_fact.parquet"
    report = gdp_vintage_comparison.compare_gdp_vintages(
        pq.read_table(march_path).to_pylist(),
        pq.read_table(june_path).to_pylist(),
    )
    report["march_source_manifest_sha256"] = (
        gdp_canonical_projection.SOURCE_MANIFEST_SHA256
    )
    report["june_source_manifest_sha256"] = (
        gdp_canonical_projection.JUNE_SOURCE_MANIFEST_SHA256
    )
    return bind_recorded_comparison(
        report,
        TRACK / "gdp-vintage-reconciliation-20260930.json",
        "gdp_vintage_comparison_recorded_mismatch",
    )


def rebuild_context_silver(root: Path, family: str) -> dict[str, Any]:
    """Rebuild one context Silver package directly from its pinned Bronze bytes."""
    package, expected_manifest = CONTEXT[family]
    binding = context_source_binding(family)
    source_hash = binding["source_object_sha256"]
    source = ARCHIVE / "bronze-cas" / "sha256" / source_hash[:2] / source_hash
    output = root / package
    if family == "cpi":
        receipt = cpi.normalize_cpi(
            source,
            output,
            expected_sha256=source_hash,
            **{
                key: binding[key]
                for key in ("source_locator", "source_vintage", "observed_at")
            },
            dry_run=False,
        )
    elif family == "wage":
        receipt = qes.normalize_qes(
            source,
            output,
            expected_sha256=source_hash,
            **{
                key: binding[key]
                for key in ("source_locator", "source_vintage", "observed_at")
            },
            dry_run=False,
        )
    elif family == "gdp":
        receipt = gdp.normalize_gdp(
            source,
            output,
            expected_sha256=source_hash,
            **{
                key: binding[key]
                for key in ("source_locator", "source_vintage", "observed_at")
            },
            dry_run=False,
        )
    elif family == "population":
        receipt = normalize_population_annual(
            source,
            output,
            expected_sha256=source_hash,
            source_locator=binding["source_locator"],
            source_vintage=binding["source_vintage"],
            observed_at=binding["observed_at"],
            dry_run=False,
        )
    else:
        message = f"unknown_context_family:{family}"
        raise RuntimeError(message)
    manifest = output / "MANIFEST.json"
    manifest_hash = digest(manifest)
    if manifest_hash != expected_manifest:
        message = f"context_silver_manifest_drift:{family}:{manifest_hash}"
        raise RuntimeError(message)
    return {
        "files": tree(output),
        "manifest_sha256": manifest_hash,
        "source_object_sha256": source_hash,
        "counts": cast("dict[str, Any]", receipt["counts"]),
    }


def rebuild_eight_stage(root: Path, index: int) -> dict[str, Any]:
    """Rebuild the 12-profile source-native raw Silver run from Bronze CAS."""
    donor_manifest = ARCHIVE / "manifests" / "donor-4668e6c.json"
    output = root / f"eight-stage-{index}"
    plan = plan_eight(
        donor_manifest,
        ARCHIVE / "bronze-cas",
        DONOR_MANIFEST_SHA256,
        "2026-08-30T08:58:00+00:00",
        "de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f",
        crown_receipt=TRACK / "source-census.json",
        crown_receipt_sha256=SOURCE_CENSUS_SHA256,
    )
    completion = execute_eight(plan, ARCHIVE / "bronze-cas", output)
    verified = verify_eight(
        output, ARCHIVE / "bronze-cas", digest(output / "MANIFEST.json")
    )
    if completion != verified:
        message = "eight_stage_readback_mismatch"
        raise RuntimeError(message)
    return {
        "files": tree(output),
        "manifest_sha256": digest(output / "MANIFEST.json"),
        "profile_count": len(completion["stages"]),
        "fact_count": sum(row["facts"] for row in completion["coverage"]),
        "rights_state": completion["rights_state"],
        "gold_selection": completion["gold_selection"],
        "publication": completion["publication"],
    }


def rebuild_vote_health_2018_19_category_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the new bounded Vote Health profile directly from Bronze."""
    profile = vote_health_supplementary_2018_19
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2018-19-category-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=(
            "https://www.treasury.govt.nz/sites/default/files/2019-05/"
            "suppest19health.pdf"
        ),
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 5, "facts": 7}
    ):
        message = "vote_health_2018_19_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2013_14_category_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the pinned six-row 2013/14 Supplementary Estimates profile."""
    profile = vote_health_supplementary_2013_14
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2013-14-category-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 5, "facts": 6}
    ):
        message = "vote_health_2013_14_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2014_15_category_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the pinned seven-row 2014/15 Supplementary Estimates profile."""
    profile = vote_health_supplementary_2014_15
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2014-15-category-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 5, "facts": 7}
    ):
        message = "vote_health_2014_15_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2015_16_category_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the pinned seven-row 2015/16 Supplementary Estimates profile."""
    profile = vote_health_supplementary_2015_16
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2015-16-category-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 5, "facts": 7}
    ):
        message = "vote_health_2015_16_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2016_17_category_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the pinned seven-row 2016/17 Supplementary Estimates profile."""
    profile = vote_health_supplementary_2016_17
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2016-17-category-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T10:08:20Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 4, "facts": 7}
    ):
        message = "vote_health_2016_17_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2019_20_category_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the separately pinned 2019/20 Vote Health profile from Bronze."""
    profile = vote_health_supplementary_2019_20
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2019-20-category-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 5, "facts": 7}
    ):
        message = "vote_health_2019_20_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2020_21_summary_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the separately pinned 2020/21 page-seven summary from Bronze."""
    profile = vote_health_supplementary_2020_21
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2020-21-summary-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 1, "facts": 4}
    ):
        message = "vote_health_2020_21_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2021_22_summary_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the separately pinned 2021/22 page-seven summary from Bronze."""
    profile = vote_health_supplementary_2021_22
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2021-22-summary-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 1, "facts": 4}
    ):
        message = "vote_health_2021_22_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2022_23_summary_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the separately pinned 2022/23 page-five summary from Bronze."""
    profile = vote_health_supplementary_2022_23
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2022-23-summary-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 1, "facts": 4}
    ):
        message = "vote_health_2022_23_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2023_24_summary_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the separately pinned 2023/24 page-five summary from Bronze."""
    profile = vote_health_supplementary_2023_24
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2023-24-summary-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 1, "facts": 4}
    ):
        message = "vote_health_2023_24_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2024_25_summary_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the separately pinned 2024/25 page-five summary from Bronze."""
    profile = vote_health_supplementary_2024_25
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2024-25-summary-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 1, "facts": 5}
    ):
        message = "vote_health_2024_25_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def rebuild_vote_health_2025_26_summary_totals(
    root: Path, index: int
) -> dict[str, Any]:
    """Rebuild the separately pinned 2025/26 page-six summary from Bronze."""
    profile = vote_health_supplementary_2025_26
    source = (
        ARCHIVE
        / "bronze-cas"
        / "sha256"
        / profile.SOURCE_SHA256[:2]
        / profile.SOURCE_SHA256
    )
    output = root / f"vote-health-2025-26-summary-totals-{index}"
    request = SourceRequest(
        source=source,
        output_dir=output,
        profile=profile.PROFILE,
        expected_sha256=profile.SOURCE_SHA256,
        source_vintage=profile.VINTAGE,
        source_locator=profile.SOURCE_LOCATOR,
        observed_at="2026-10-06T00:00:00Z",
    )
    receipt = operate_source(request, dry_run=False)
    if (
        receipt.get("status") != "written_local"
        or receipt.get("profile") != profile.PROFILE
        or receipt.get("source_object_sha256") != profile.SOURCE_SHA256
        or receipt.get("counts") != {"pages": 1, "facts": 6}
    ):
        message = "vote_health_2025_26_recovery_contract"
        raise RuntimeError(message)
    return {"files": tree(output), "operation_receipt": receipt}


def canonical_inputs(recovery_root: Path) -> tuple[CanonicalPackageInput, ...]:
    """Rebuild and bind retained historical and Budget canonical packages."""
    historical = (
        (
            "2024",
            "raw-historical-20260830-v1",
            "2f39ad4dbeb7cb872118ddc634985b5e21b18f2ef2421ca3c0a1e9bf90411288",
        ),
        (
            "2025",
            "raw-historical-2025-20260831-v1",
            "aee4578f1ee83f8c1ede63e36e840c6cd2140df8c6f463e71ec93da9e4e7d75a",
        ),
    )
    packages: list[CanonicalPackageInput] = []
    for year, raw_name, raw_pin in historical:
        historical_root = (
            ARCHIVE / "silver" / f"canonical-historical-{year}-20260831-v1"
        )
        marker = historical_root / "LOCAL_CANONICAL.json"
        value = json.loads(marker.read_text())
        original_hash = value["input_fixity"]["original_sha256"]
        original = ARCHIVE / "bronze-cas" / "sha256" / original_hash[:2] / original_hash
        packages.append(
            CanonicalPackageInput(
                "historical",
                historical_root,
                digest(marker),
                original,
                ARCHIVE / "silver" / raw_name,
                raw_pin,
            )
        )
    budget_editions = (
        (
            "Budget-2025",
            "raw-budget-d26e769",
            "03f41d39395b02169202e88e98f04a892a3dbb55c2083a328391d909af8f7d57",
            "d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338",
            export_budget_appropriations,
            "budget",
        ),
        (
            "Budget-2026",
            "raw-budget-2026-20260831-v1",
            "f34000992fd65dca445e7ad251cb06df3c68107410355ea057ea9a2bf8481738",
            "3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0",
            export_budget_appropriations,
            "budget",
        ),
        (
            "Budget-2026-revenue",
            "raw-budget-2026-revenue-20260925-v1",
            "ff0a5494737378b4741663f1d190bf24971e3d6ee7a17da93fe7b3cdbd5ffdb2",
            "8243f6a3f9575af5ee048133f2695f3c4764ff7d86e7a74849fdafcf478cbfdb",
            export_budget_revenue,
            "revenue",
        ),
    )
    raw_root = ARCHIVE / "silver"
    source_cas = ARCHIVE / "bronze-cas" / "sha256"
    for vintage, raw_name, raw_pin, source_sha256, exporter, kind in budget_editions:
        raw_package = raw_root / raw_name
        original = source_cas / source_sha256[:2] / source_sha256
        canonical_root = recovery_root / f"canonical-input-{kind}-{vintage.lower()}"
        exporter(
            raw_package,
            raw_pin,
            original,
            canonical_root,
            dry_run=False,
        )
        marker_name = "LOCAL_BUDGET.json" if kind == "budget" else "LOCAL_REVENUE.json"
        packages.append(
            CanonicalPackageInput(
                kind,
                canonical_root,
                digest(canonical_root / marker_name),
                original,
                raw_package,
                raw_pin,
            )
        )
    return tuple(packages)


def rebuild_donor_products(root: Path, index: int) -> dict[str, Any]:
    """Rebuild the pinned donor-to-SQLite/Gold/plot chain once."""
    donor_manifest = ARCHIVE / "manifests" / "donor-4668e6c.json"
    donor_pin = "893f387e1f361400285ccc84802b497e87802d1ad913826ff7d9055b07a03b74"
    store_root = ARCHIVE / "bronze-cas"
    run_root = root / f"donor-run-{index}"
    plan = plan_rebuild(
        donor_manifest, store_root, donor_pin, "2026-08-30T08:58:00+00:00"
    )
    execute_rebuild(plan, store_root, run_root)
    run_pin = digest(run_root / "MANIFEST.json")
    verify_rebuild(run_root, store_root, run_pin)
    compatibility_root = root / f"compatibility-{index}"
    compatibility = export_compatibility(
        run_root, store_root, run_pin, compatibility_root, dry_run=False
    )
    gold_root = root / f"donor-gold-{index}"
    gold = export_gold(run_root, store_root, run_pin, gold_root, dry_run=False)
    gold_pin = digest(gold_root / "MANIFEST.json")
    plots_root = root / f"donor-plots-{index}"
    plots = render_plots(gold_root, gold_pin, plots_root, dry_run=False)
    return {
        "raw": tree(run_root),
        "compatibility": tree(compatibility_root),
        "gold": tree(gold_root),
        "plots": tree(plots_root),
        "raw_manifest_sha256": run_pin,
        "compatibility_facts": compatibility["facts"],
        "gold_selected_facts": gold["selected_facts"],
        "plot_count": sum(name.endswith(".png") for name in plots["output_sha256"]),
    }


def _query_context_consumer(root: Path) -> dict[str, Any]:
    """Exercise the pinned canonical projection and return bounded evidence."""
    manifest_sha256 = digest(root / "MANIFEST.json")
    table = query_context_observations(root, manifest_sha256)
    return {
        "status": "verified_read_only_projection",
        "manifest_sha256": manifest_sha256,
        "observation_count": table.num_rows,
        "source_families": sorted(set(table.column("family").to_pylist())),
    }


def _cpi_canonical_recovery_report(
    silver_root: Path, output_root: Path
) -> dict[str, Any]:
    """Project rebuilt CPI Silver twice and compare canonical outputs."""
    package = silver_root / CONTEXT["cpi"][0]
    manifest_pin = digest(package / "MANIFEST.json")
    cas_root = ARCHIVE / "bronze-cas" / "sha256"
    products = []
    for index in (1, 2):
        facts, lineage, receipt = cpi_canonical_projection.project_cpi(
            package, manifest_pin, cas_root
        )
        target = output_root / f"cpi-canonical-{index}"
        target.mkdir()
        pq.write_table(
            facts, target / "price_population_fact.parquet", compression="zstd"
        )
        lineage_rows = [
            {
                key: value.isoformat() if hasattr(value, "isoformat") else value
                for key, value in row.items()
                if value is not None
            }
            for row in lineage.to_pylist()
        ]
        (target / "field_lineage.jsonl").write_text(
            "".join(
                json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
                for row in lineage_rows
            ),
            encoding="utf-8",
        )
        (target / "projection-receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        products.append({"files": tree(target), "receipt": receipt})
    repeat = products[0] == products[1]
    require_evidence(repeat, "cpi_canonical_projection_repeat_mismatch")
    return {
        "files": products[0]["files"],
        "repeat_identical": repeat,
        "source_object_sha256": products[0]["receipt"]["source_object_sha256"],
        "source_manifest_sha256": manifest_pin,
        "fact_count": products[0]["receipt"]["output_records"],
        "lineage_count": products[0]["receipt"]["lineage_records"],
        "rights_state": products[0]["receipt"]["rights_state"],
        "index_base": products[0]["receipt"]["index_base"],
        "inflation_adjustment": products[0]["receipt"]["inflation_adjustment"],
    }


def _population_canonical_recovery_report(
    silver_root: Path, output_root: Path
) -> dict[str, Any]:
    """Project rebuilt annual population Silver twice and compare every output."""
    package = silver_root / CONTEXT["population"][0]
    manifest_pin = digest(package / "MANIFEST.json")
    cas_root = ARCHIVE / "bronze-cas" / "sha256"
    products = []
    for index in (1, 2):
        facts, lineage, receipt = (
            population_annual_canonical_projection.project_population_annual(
                package, manifest_pin, cas_root
            )
        )
        target = output_root / f"population-canonical-{index}"
        target.mkdir()
        pq.write_table(
            facts, target / "price_population_fact.parquet", compression="zstd"
        )
        pq.write_table(lineage, target / "field_lineage.parquet", compression="zstd")
        (target / "projection-receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        products.append({"files": tree(target), "receipt": receipt})
    repeat = products[0] == products[1]
    require_evidence(repeat, "population_canonical_projection_repeat_mismatch")
    return {
        "files": products[0]["files"],
        "repeat_identical": repeat,
        "source_object_sha256": products[0]["receipt"]["source_object_sha256"],
        "source_manifest_sha256": manifest_pin,
        "fact_count": products[0]["receipt"]["output_records"],
        "lineage_count": products[0]["receipt"]["lineage_records"],
        "rights_state": products[0]["receipt"]["rights_state"],
        "analytical_selection": products[0]["receipt"]["analytical_selection"],
    }


def _gdp_canonical_recovery_report(
    silver_root: Path, output_root: Path
) -> dict[str, Any]:
    """Project rebuilt GDP Silver twice and compare canonical output digests."""
    package = silver_root / CONTEXT["gdp"][0]
    manifest_pin = digest(package / "MANIFEST.json")
    cas_root = ARCHIVE / "bronze-cas" / "sha256"
    products = []
    for index in (1, 2):
        facts, lineage, receipt = gdp_canonical_projection.project_gdp(
            package, manifest_pin, cas_root
        )
        target = output_root / f"gdp-canonical-{index}"
        target.mkdir()
        pq.write_table(
            facts, target / "fiscal_context_fact.parquet", compression="zstd"
        )
        pq.write_table(lineage, target / "field_lineage.parquet", compression="zstd")
        (target / "projection-receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        products.append({"files": tree(target), "receipt": receipt})
    repeat = products[0] == products[1]
    require_evidence(repeat, "gdp_canonical_projection_repeat_mismatch")
    return {
        "files": products[0]["files"],
        "repeat_identical": repeat,
        "source_object_sha256": products[0]["receipt"]["source_object_sha256"],
        "source_manifest_sha256": manifest_pin,
        "fact_count": products[0]["receipt"]["output_records"],
        "lineage_count": products[0]["receipt"]["lineage_records"],
        "currency": products[0]["receipt"]["currency"],
        "rights_state": products[0]["receipt"]["rights_state"],
        "denominator_selection": products[0]["receipt"]["denominator_selection"],
    }


def _rebuild_pharmac_canonical(root: Path, index: int) -> dict[str, Any]:
    """Rebuild pinned Pharmac Silver from Bronze and project canonical facts."""
    source_cas = ARCHIVE / "bronze-cas" / "sha256"
    source = source_cas / PHARMAC_SOURCE_SHA256[:2] / PHARMAC_SOURCE_SHA256
    silver = root / f"pharmac-silver-{index}"
    pharmac.normalize_pharmac_budget(
        source,
        silver,
        expected_sha256=PHARMAC_SOURCE_SHA256,
        source_locator=pharmac_canonical_projection.SOURCE_LOCATOR,
        source_vintage=pharmac_canonical_projection.SOURCE_VINTAGE,
        observed_at=PHARMAC_SOURCE_OBSERVED_AT,
        dry_run=False,
    )
    pin = digest(silver / "MANIFEST.json")
    facts, lineage, receipt = project_pharmac_cpb(
        silver, pin, source_cas, PHARMAC_SOURCE_SHA256
    )
    encode = lambda table: json.dumps(  # noqa: E731 - same canonical evidence codec.
        table.to_pylist(),
        default=str,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "silver_files": tree(silver),
        "source_manifest_sha256": pin,
        "source_object_sha256": PHARMAC_SOURCE_SHA256,
        "canonical_fact_sha256": hashlib.sha256(encode(facts)).hexdigest(),
        "canonical_lineage_sha256": hashlib.sha256(encode(lineage)).hexdigest(),
        "projection": receipt,
    }


def _rebuild_qes_canonical(root: Path, index: int) -> dict[str, Any]:
    """Rebuild pinned QES Silver from Bronze and project canonical earnings."""
    source_cas = ARCHIVE / "bronze-cas" / "sha256"
    source = source_cas / qes_canonical_projection.SOURCE_SHA256[:2]
    source = source / qes_canonical_projection.SOURCE_SHA256
    silver = root / f"qes-silver-{index}"
    qes.normalize_qes(
        source,
        silver,
        expected_sha256=qes_canonical_projection.SOURCE_SHA256,
        source_locator=qes_canonical_projection.SOURCE_LOCATOR,
        source_vintage=qes_canonical_projection.SOURCE_VINTAGE,
        observed_at=qes_canonical_projection.OBSERVED_AT,
        dry_run=False,
    )
    pin = digest(silver / "MANIFEST.json")
    facts, lineage, receipt = project_qes_earnings(silver, pin, source_cas)
    encode = lambda table: json.dumps(  # noqa: E731 - stable recovery evidence codec.
        table.to_pylist(),
        default=str,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "silver_files": tree(silver),
        "source_manifest_sha256": pin,
        "source_object_sha256": qes_canonical_projection.SOURCE_SHA256,
        "canonical_fact_sha256": hashlib.sha256(encode(facts)).hexdigest(),
        "canonical_lineage_sha256": hashlib.sha256(encode(lineage)).hexdigest(),
        "projection": receipt,
    }


def _rebuild_crown_canonical(root: Path, index: int) -> dict[str, Any]:
    """Rebuild the retained BEFU Crown package and canonical context from Bronze."""
    source_cas = ARCHIVE / "bronze-cas" / "sha256"
    source = source_cas / crown_expense.SOURCE_SHA256[:2]
    source = source / crown_expense.SOURCE_SHA256
    silver = root / f"crown-silver-{index}"
    crown_expense.normalize_befu_core_expense(
        source,
        silver,
        expected_sha256=crown_expense.SOURCE_SHA256,
        source_locator=crown_expense.SOURCE_LOCATOR,
        source_vintage=crown_expense.SOURCE_VINTAGE,
        observed_at=CROWN_SOURCE_OBSERVED_AT,
        dry_run=False,
    )
    pin = digest(silver / "MANIFEST.json")
    facts, lineage, receipt = (
        crown_expense_canonical_projection.project_befu_core_expense(
            silver, pin, source_cas
        )
    )
    encode = lambda table: json.dumps(  # noqa: E731 - stable recovery evidence codec.
        table.to_pylist(),
        default=str,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "silver_files": tree(silver),
        "source_manifest_sha256": pin,
        "source_object_sha256": crown_expense.SOURCE_SHA256,
        "canonical_fact_sha256": hashlib.sha256(encode(facts)).hexdigest(),
        "canonical_lineage_sha256": hashlib.sha256(encode(lineage)).hexdigest(),
        "projection": receipt,
    }


def _pharmac_recovery_report(root: Path) -> dict[str, Any]:
    """Require two matching Bronze-to-canonical Pharmac projections."""
    runs = {str(index): _rebuild_pharmac_canonical(root, index) for index in (1, 2)}
    if runs["1"] != runs["2"]:
        message = "pharmac_canonical_projection_repeat_mismatch"
        raise RuntimeError(message)
    return {**runs["1"], "repeat_identical": True}


def _rebuild_moh_profile(root: Path, profile: str, index: int) -> dict[str, Any]:
    """Rebuild one pinned HAIR2024 profile from Bronze and return its pins."""
    source_sha256 = MOH_SOURCE_SHA256[profile]
    source_cas = ARCHIVE / "bronze-cas" / "sha256"
    source = source_cas / source_sha256[:2] / source_sha256
    silver = root / f"moh-{profile.replace('/', '-')}-{index}"
    moh_indicators.normalize_moh_indicators(
        source,
        silver,
        expected_sha256=source_sha256,
        profile=profile,
        source_vintage=moh_canonical_projection.SOURCE_VINTAGE,
        observed_at="2026-08-29T09:00:17Z",
        source_locator=moh_canonical_projection.PROFILES[profile],
        dry_run=False,
    )
    manifest_sha256 = digest(silver / "MANIFEST.json")
    require_evidence(
        manifest_sha256 == MOH_SILVER_MANIFEST_SHA256[profile],
        "moh_silver_manifest_pin_mismatch",
    )
    return {
        "silver_files": tree(silver),
        "source_manifest_sha256": manifest_sha256,
        "source_object_sha256": source_sha256,
        "fact_count": len(
            pq.read_table(silver / "moh_indicator_facts.parquet").to_pylist()
        ),
        "lineage_count": len(
            pq.read_table(silver / "field_lineage.parquet").to_pylist()
        ),
    }


def _moh_recovery_report(root: Path) -> dict[str, Any]:
    """Require both official HAIR2024 profiles to rebuild to their retained pins."""
    profiles: dict[str, Any] = {}
    first_builds: list[MohIndicatorInput] = []
    for profile in moh_canonical_projection.PROFILES:
        runs = {
            str(index): _rebuild_moh_profile(root, profile, index) for index in (1, 2)
        }
        require_evidence(runs["1"] == runs["2"], "moh_silver_repeat_mismatch")
        profiles[profile] = {**runs["1"], "repeat_identical": True}
        silver = root / f"moh-{profile.replace('/', '-')}-1"
        first_builds.append(
            MohIndicatorInput(
                profile,
                silver,
                runs["1"]["source_manifest_sha256"],
                MOH_SOURCE_SHA256[profile],
            )
        )
    source_cas = ARCHIVE / "bronze-cas" / "sha256"
    facts, lineage, projection = moh_canonical_projection.project_moh_indicators(
        MohGoldInput(tuple(first_builds), source_cas)
    )
    return {
        "status": "complete",
        "profiles": profiles,
        "rights_state": "not_evaluated",
        "methodology": "published_indicators_not_recomputed",
        "canonical_projection": projection,
        "canonical_fact_sha256": hashlib.sha256(
            json.dumps(
                facts.to_pylist(), default=str, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest(),
        "canonical_lineage_sha256": hashlib.sha256(
            json.dumps(
                lineage.to_pylist(), default=str, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest(),
    }


def _qes_recovery_report(root: Path) -> dict[str, Any]:
    """Require two matching Bronze-to-canonical QES projections."""
    runs = {str(index): _rebuild_qes_canonical(root, index) for index in (1, 2)}
    if runs["1"] != runs["2"]:
        message = "qes_canonical_projection_repeat_mismatch"
        raise RuntimeError(message)
    return {**runs["1"], "repeat_identical": True}


def _crown_recovery_report(root: Path) -> dict[str, Any]:
    """Require two matching Bronze-to-canonical Crown projections."""
    runs = {str(index): _rebuild_crown_canonical(root, index) for index in (1, 2)}
    if runs["1"] != runs["2"]:
        message = "crown_canonical_projection_repeat_mismatch"
        raise RuntimeError(message)
    return {**runs["1"], "repeat_identical": True}


def _rebuild_hyefu_crown_canonical(root: Path, index: int) -> dict[str, Any]:
    """Rebuild the retained HYEFU Crown package and canonical context from Bronze."""
    source_cas = ARCHIVE / "bronze-cas" / "sha256"
    source = source_cas / hyefu_crown_expense.SOURCE_SHA256[:2]
    source = source / hyefu_crown_expense.SOURCE_SHA256
    silver = root / f"hyefu-crown-silver-{index}"
    hyefu_crown_expense.normalize_hyefu_core_expense(
        source,
        silver,
        expected_sha256=hyefu_crown_expense.SOURCE_SHA256,
        source_locator=hyefu_crown_expense.SOURCE_LOCATOR,
        source_vintage=hyefu_crown_expense.SOURCE_VINTAGE,
        observed_at=CROWN_SOURCE_OBSERVED_AT,
        dry_run=False,
    )
    pin = digest(silver / "MANIFEST.json")
    facts, lineage, receipt = (
        hyefu_crown_expense_canonical_projection.project_hyefu_core_expense(
            silver, pin, source_cas
        )
    )
    encode = lambda table: json.dumps(  # noqa: E731 - stable recovery evidence codec.
        table.to_pylist(),
        default=str,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "silver_files": tree(silver),
        "source_manifest_sha256": pin,
        "source_object_sha256": hyefu_crown_expense.SOURCE_SHA256,
        "canonical_fact_sha256": hashlib.sha256(encode(facts)).hexdigest(),
        "canonical_lineage_sha256": hashlib.sha256(encode(lineage)).hexdigest(),
        "projection": receipt,
    }


def _hyefu_crown_recovery_report(root: Path) -> dict[str, Any]:
    """Require two matching Bronze-to-canonical HYEFU Crown projections."""
    runs = {str(index): _rebuild_hyefu_crown_canonical(root, index) for index in (1, 2)}
    if runs["1"] != runs["2"]:
        message = "hyefu_crown_canonical_projection_repeat_mismatch"
        raise RuntimeError(message)
    return {**runs["1"], "repeat_identical": True}


def _rebuild_fiscal_crown_canonical(root: Path, index: int) -> dict[str, Any]:
    """Rebuild historical Crown canonical facts directly from pinned Bronze."""
    source_cas = ARCHIVE / "bronze-cas" / "sha256"
    source = source_cas / fiscal_crown_literals.SOURCE_SHA256[:2]
    source = source / fiscal_crown_literals.SOURCE_SHA256
    facts, lineage, receipt = fiscal_crown_canonical_projection.project_fiscal_crown(
        source
    )
    output = root / f"fiscal-crown-canonical-{index}"
    output.mkdir()
    pq.write_table(facts, output / "fiscal_context_fact.parquet")
    pq.write_table(lineage, output / "field_lineage.parquet")
    (output / "RECEIPT.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    )
    encode = lambda table: json.dumps(  # noqa: E731 - stable recovery evidence codec.
        table.to_pylist(),
        default=str,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "source_object_sha256": fiscal_crown_literals.SOURCE_SHA256,
        "canonical_fact_sha256": hashlib.sha256(encode(facts)).hexdigest(),
        "canonical_lineage_sha256": hashlib.sha256(encode(lineage)).hexdigest(),
        "output_files": tree(output),
        "projection": receipt,
        "build_index": index,
    }


def _fiscal_crown_recovery_report(root: Path) -> dict[str, Any]:
    """Require two matching direct Bronze-to-canonical historical projections."""
    runs = {
        str(index): _rebuild_fiscal_crown_canonical(root, index) for index in (1, 2)
    }
    for run in runs.values():
        run.pop("build_index")
    if runs["1"] != runs["2"]:
        message = "fiscal_crown_canonical_projection_repeat_mismatch"
        raise RuntimeError(message)
    return {**runs["1"], "repeat_identical": True}


def _canonical_gold_recovery_report(root: Path) -> dict[str, Any]:
    """Rebuild and compare canonical Gold or retain its binding blocker."""
    canonical = canonical_inputs(root)
    if not canonical:
        return {
            "status": "blocked",
            "reason": "no_retained_canonical_inputs_passed_independent_source_binding",
        }
    pharmac_silver = root / "pharmac-silver-1"
    pharmac_input = PharmacGoldInput(
        root=pharmac_silver,
        manifest_sha256=digest(pharmac_silver / "MANIFEST.json"),
        source_cas_root=ARCHIVE / "bronze-cas" / "sha256",
        source_sha256=PHARMAC_SOURCE_SHA256,
    )
    moh_input = MohGoldInput(
        tuple(
            MohIndicatorInput(
                profile,
                root / f"moh-{profile.replace('/', '-')}-1",
                MOH_SILVER_MANIFEST_SHA256[profile],
                MOH_SOURCE_SHA256[profile],
            )
            for profile in moh_canonical_projection.PROFILES
        ),
        ARCHIVE / "bronze-cas" / "sha256",
    )
    befu_silver = root / "crown-silver-1"
    hyefu_silver = root / "hyefu-crown-silver-1"
    crown_input = CrownGoldInput(
        befu_root=befu_silver,
        befu_manifest_sha256=crown_expense_canonical_projection.SOURCE_MANIFEST_SHA256,
        hyefu_root=hyefu_silver,
        hyefu_manifest_sha256=hyefu_crown_expense_canonical_projection.SOURCE_MANIFEST_SHA256,
        source_cas_root=ARCHIVE / "bronze-cas" / "sha256",
    )
    fiscal_source = ARCHIVE / "bronze-cas" / "sha256"
    fiscal_source = fiscal_source / fiscal_crown_literals.SOURCE_SHA256[:2]
    fiscal_source = fiscal_source / fiscal_crown_literals.SOURCE_SHA256
    fiscal_crown_input = FiscalCrownGoldInput(source_path=fiscal_source)
    for index in (1, 2):
        export_canonical_gold(
            canonical,
            root / f"canonical-{index}",
            write=True,
            inputs=GoldInputs(
                pharmac=pharmac_input,
                moh=moh_input,
                crown=crown_input,
                fiscal_crown=fiscal_crown_input,
            ),
        )
    files = compare_product_outputs(
        root / "canonical-1", root / "canonical-2", "canonical_gold"
    )
    manifest = json.loads((root / "canonical-1" / "MANIFEST.json").read_bytes())
    quality = manifest.get("quality_report")
    require_evidence(
        isinstance(quality, dict)
        and quality.get("schema_version")
        == "archive-govt-nz.health-canonical-gold-quality/v1"
        and quality.get("unaccounted_input_records") == 0,
        "canonical_gold_quality_report_invalid",
    )
    classification_report = manifest.get("classification_drift_report")
    require_evidence(
        isinstance(classification_report, dict)
        and classification_report.get("schema_version")
        == "archive-govt-nz.health-classification-drift/v1"
        and classification_report.get("mapping") == "not_inferred"
        and classification_report.get("cross_source_comparison") == "not_performed"
        and isinstance(classification_report.get("candidates"), list),
        "canonical_gold_classification_drift_report_invalid",
    )
    revision_report = manifest.get("revision_reconciliation_report")
    revision_path = root / "canonical-1" / "historical_revision_reconciliation.json"
    revision_output = manifest.get("outputs", {}).get(
        "historical_revision_reconciliation.json"
    )
    require_evidence(
        isinstance(revision_report, dict)
        and revision_report.get("schema_version")
        == "archive-govt-nz.health-revision-reconciliation/v1"
        and revision_report.get("key_fields")
        == [
            "recordset",
            "measure",
            "source_label",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "institutional_coverage",
            "accounting_basis",
            "period_token",
        ]
        and revision_report.get("completeness")
        == "historical_budget_revenue_pharmac_moh_crown_product_rows"
        and revision_report.get("difference_interpretation") == "not_assessed"
        and revision_report.get("other_product_revisions") == "not_assessed"
        and revision_report.get("cross_source_comparison") == "not_performed"
        and isinstance(revision_report.get("product_revisions"), dict)
        and set(revision_report["product_revisions"])
        == {"budget", "revenue", "pharmac", "moh", "crown"}
        and isinstance(revision_report.get("candidates"), list)
        and revision_report.get("changed_candidate_count")
        == len(revision_report["candidates"])
        and revision_path.is_file()
        and isinstance(revision_output, dict)
        and revision_output.get("sha256") == digest(revision_path)
        and json.loads(revision_path.read_bytes()) == revision_report,
        "canonical_gold_revision_reconciliation_report_invalid",
    )
    return {
        "files": files,
        "repeat_identical": True,
        "quality_report": {
            "schema_version": quality["schema_version"],
            "input_record_count": quality["input_record_count"],
            "input_records_with_product": quality["input_records_with_product"],
            "unaccounted_input_records": quality["unaccounted_input_records"],
            "products": quality["products"],
            "unresolved_reports": quality["unresolved_reports"],
        },
        "classification_drift_report": {
            "schema_version": classification_report["schema_version"],
            "scope": classification_report["scope"],
            "source_families": classification_report["source_families"],
            "candidate_count": len(classification_report["candidates"]),
            "mapping": classification_report["mapping"],
            "cross_source_comparison": classification_report["cross_source_comparison"],
        },
        "revision_reconciliation_report": {
            "schema_version": revision_report["schema_version"],
            "scope": revision_report["scope"],
            "key_fields": revision_report["key_fields"],
            "completeness": revision_report["completeness"],
            "shared_series_period_count": revision_report["shared_series_period_count"],
            "unchanged_series_period_count": revision_report[
                "unchanged_series_period_count"
            ],
            "ambiguous_series_period_count": revision_report[
                "ambiguous_series_period_count"
            ],
            "changed_candidate_count": revision_report["changed_candidate_count"],
            "difference_interpretation": revision_report["difference_interpretation"],
            "other_product_revisions": revision_report["other_product_revisions"],
            "cross_source_comparison": revision_report["cross_source_comparison"],
            "product_revisions": {
                name: {
                    "shared_series_period_count": product_report[
                        "shared_series_period_count"
                    ],
                    "unchanged_series_period_count": product_report[
                        "unchanged_series_period_count"
                    ],
                    "ambiguous_series_period_count": product_report[
                        "ambiguous_series_period_count"
                    ],
                    "changed_candidate_count": product_report[
                        "changed_candidate_count"
                    ],
                }
                for name, product_report in sorted(
                    revision_report["product_revisions"].items()
                )
            },
        },
    }


def source_health_recovery_report() -> dict[str, Any]:
    """Rebuild the pinned whole-census health report and verify Bronze capture."""
    source_bytes = (TRACK / "source-census.json").read_bytes()
    context_bytes = (TRACK / "context-census.json").read_bytes()
    manifest_path = ARCHIVE / "manifests" / CAPTURE_MANIFEST_NAME
    manifest_bytes = manifest_path.read_bytes()
    require_evidence(
        hashlib.sha256(source_bytes).hexdigest() == SOURCE_CENSUS_SHA256,
        "source_health_census_pin_mismatch",
    )
    require_evidence(
        hashlib.sha256(context_bytes).hexdigest() == CONTEXT_CENSUS_SHA256,
        "source_health_context_census_pin_mismatch",
    )
    require_evidence(
        hashlib.sha256(manifest_bytes).hexdigest() == CAPTURE_MANIFEST_SHA256,
        "source_health_capture_manifest_pin_mismatch",
    )
    capture = CaptureEvidence(
        manifest=json.loads(manifest_bytes),
        manifest_bytes=manifest_bytes,
        manifest_name=manifest_path.name,
        cas_root=ARCHIVE / "bronze-cas" / "sha256",
    )
    layout_path = TRACK / PDF_LAYOUT_BASELINE_NAME
    layout_bytes = layout_path.read_bytes()
    require_evidence(
        hashlib.sha256(layout_bytes).hexdigest() == PDF_LAYOUT_BASELINE_SHA256,
        "source_health_layout_baseline_pin_mismatch",
    )
    layout = LayoutEvidence(json.loads(layout_bytes), layout_bytes)
    source_census = json.loads(source_bytes)
    context_census = json.loads(context_bytes)
    recorded_path = TRACK / "source-health-report.json"
    recorded = json.loads(recorded_path.read_bytes())
    first = build_source_health_report(
        source_census,
        source_bytes,
        context_census,
        context_bytes,
        capture,
        layout_evidence=layout,
    )
    second = build_source_health_report(
        source_census,
        source_bytes,
        context_census,
        context_bytes,
        capture,
        layout_evidence=layout,
    )
    require_evidence(first == second, "source_health_report_repeat_mismatch")
    require_evidence(first == recorded, "source_health_report_recorded_mismatch")
    summary = first["summary"]
    reconciliation = first["capture_reconciliation"]
    captured_count = summary["resource_dispositions"].get("captured", 0)
    require_evidence(
        reconciliation["state"] == "capture_manifest_and_bronze_objects_verified"
        and reconciliation["matched_resource_count_verified"] == captured_count
        and reconciliation["bronze_object_count_verified"] == captured_count,
        "source_health_capture_reconciliation_incomplete",
    )
    return {
        "status": "verified_repeat_identical",
        "report_sha256": digest(recorded_path),
        "source_census_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "context_census_sha256": hashlib.sha256(context_bytes).hexdigest(),
        "capture_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "pdf_layout_baseline_sha256": hashlib.sha256(layout_bytes).hexdigest(),
        "summary": summary,
        "capture_reconciliation": reconciliation,
        "limitations": first["limitations"],
    }


def donor_parity_recovery_report() -> dict[str, Any]:
    """Replay the pinned donor reconciliation and retain its non-approval state."""
    script = TRACK / "donor-parity-replay.py"
    spec = importlib.util.spec_from_file_location("health_donor_parity_replay", script)
    if spec is None or spec.loader is None:
        message = "donor_replay_unavailable"
        raise RuntimeError(message)
    replay_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay_module)
    first = replay_module.replay(ARCHIVE)
    second = replay_module.replay(ARCHIVE)
    require_evidence(first == second, "donor_parity_report_repeat_mismatch")
    require_evidence(
        first["gold"]["status"] == "exact_parity"
        and first["gold"]["matched_rows"] == DONOR_ROW_COUNT
        and first["raw"]["status"] == "explained_deviations"
        and first["historical_deviation_dispositions"]
        == "accepted_retain_both_no_replacement",
        "donor_parity_report_contract_failed",
    )
    return {
        "status": "verified_with_nonmutating_deviations",
        "donor_manifest_sha256": first["donor_manifest_sha256"],
        "raw_manifest_sha256": first["raw_manifest_sha256"],
        "donor_objects_verified": first["donor_objects_verified"],
        "donor_bytes_verified": first["donor_bytes_verified"],
        "gold": {
            "status": first["gold"]["status"],
            "matched_rows": first["gold"]["matched_rows"],
            "table_counts": first["gold"]["table_counts"],
        },
        "raw": {
            "status": first["raw"]["status"],
            "matched_rows": first["raw"]["matched_rows"],
            "unresolved_rows": first["raw"]["unresolved_rows"],
            "explained_rows": first["raw"]["explained_rows"],
            "table_counts": first["raw"]["table_counts"],
        },
        "historical_counts": first["historical_counts"],
        "historical_deviation_count": len(first["exact_decimal_deviations"]),
        "historical_deviation_dispositions": first["historical_deviation_dispositions"],
        "binary_representation_flags": first["binary_representation_flags"],
        "repair_approval": first["repair_approval"],
        "rights_state": first["rights_state"],
        "publication_state": first["publication_state"],
        "repeat_identical": True,
    }


def classification_label_occurrence_report() -> dict[str, Any]:
    """Verify retained Budget label packages and compare exact literal counts."""
    packages: dict[str, dict[str, Any]] = {}
    for year, pin in CLASSIFICATION_PACKAGES.items():
        package = ARCHIVE / "silver" / pin["path"]
        marker_path = package / "LOCAL_CLASSIFICATION.json"
        marker_bytes = marker_path.read_bytes()
        require_evidence(
            hashlib.sha256(marker_bytes).hexdigest() == pin["marker_sha256"],
            f"classification_marker_pin_mismatch:{year}",
        )
        marker = json.loads(marker_bytes)
        require_evidence(
            marker["schema_version"] == "archive-govt-nz.health-local-classification/v1"
            and marker["source_vintage"] == f"Budget-{year}"
            and marker["original_sha256"] == pin["source_sha256"]
            and marker["input_manifest_sha256"] == pin["manifest_sha256"]
            and marker["authoritative_mapping"] == "not_performed"
            and marker["publication_approval"] == "not_granted"
            and marker["rights_state"] == "not_evaluated",
            f"classification_marker_contract_failed:{year}",
        )
        expected_files = {item["path"]: item for item in marker["files"]}
        require_evidence(
            set(expected_files)
            == {
                "classification_dimension.parquet",
                "field_lineage.parquet",
                "lineage_accounting.jsonl",
                "projection_receipt.json",
            },
            f"classification_file_inventory_invalid:{year}",
        )
        for name, file_pin in expected_files.items():
            file_path = package / name
            require_evidence(
                file_path.is_file()
                and file_path.stat().st_size == file_pin["bytes"]
                and digest(file_path) == file_pin["sha256"],
                f"classification_package_file_pin_failed:{year}:{name}",
            )
        dimension_path = package / "classification_dimension.parquet"
        dimension_meta = pq.read_metadata(dimension_path)
        dimension_schema_sha = hashlib.sha256(
            dimension_meta.schema.to_arrow_schema().serialize().to_pybytes()
        ).hexdigest()
        require_evidence(
            dimension_meta.num_rows == pin["rows"]
            and expected_files[dimension_path.name]["rows"] == pin["rows"]
            and expected_files[dimension_path.name]["bytes"]
            == dimension_path.stat().st_size
            and expected_files[dimension_path.name]["sha256"] == digest(dimension_path)
            and expected_files[dimension_path.name]["schema_sha256"]
            == dimension_schema_sha,
            f"classification_dimension_pin_failed:{year}",
        )
        table = pq.read_table(
            dimension_path,
            columns=[
                "source_vintage",
                "source_object_sha256",
                "source_label",
                "scheme",
                "scheme_version",
                "normalized_identifier",
                "mapping_state",
                "valid_time_status",
                "rights_state",
            ],
        )
        labels: dict[str, int] = {}
        for row in table.to_pylist():
            require_evidence(
                row["source_vintage"] == f"Budget-{year}"
                and row["source_object_sha256"] == pin["source_sha256"]
                and row["scheme"]
                == "budget_workbook_functional_classification_source_label"
                and row["scheme_version"] is None
                and row["normalized_identifier"] is None
                and row["mapping_state"] == "unmapped"
                and row["valid_time_status"] == "not_established"
                and row["rights_state"] == "not_evaluated",
                f"classification_row_contract_failed:{year}",
            )
            label = row["source_label"]
            require_evidence(
                isinstance(label, str) and label != "",
                f"classification_label_invalid:{year}",
            )
            labels[label] = labels.get(label, 0) + 1
        require_evidence(
            sum(labels.values()) == pin["rows"],
            f"classification_row_count_failed:{year}",
        )
        packages[str(year)] = {
            "source_vintage": f"Budget-{year}",
            "package_marker_sha256": pin["marker_sha256"],
            "source_object_sha256": pin["source_sha256"],
            "input_manifest_sha256": pin["manifest_sha256"],
            "dimension_rows": pin["rows"],
            "dimension_sha256": digest(dimension_path),
            "dimension_schema_sha256": dimension_schema_sha,
            "literal_label_occurrences": dict(sorted(labels.items())),
            "rights": "not_evaluated",
            "authoritative_mapping": "not_performed",
        }
    first_labels = packages["2025"]["literal_label_occurrences"]
    second_labels = packages["2026"]["literal_label_occurrences"]
    all_labels = sorted(set(first_labels) | set(second_labels))
    changes = [
        {
            "source_label": label,
            "budget_2025_occurrences": first_labels.get(label, 0),
            "budget_2026_occurrences": second_labels.get(label, 0),
            "occurrence_delta": second_labels.get(label, 0)
            - first_labels.get(label, 0),
        }
        for label in all_labels
        if first_labels.get(label, 0) != second_labels.get(label, 0)
    ]
    report = {
        "schema_version": "archive-govt-nz.health-classification-label-occurrences/v1",
        "status": "verified_exact_literal_occurrence_counts",
        "comparison_scope": "exact_literal_label_occurrence_counts",
        "packages": packages,
        "changes": changes,
        "classification_system_identity": "not_established",
        "authoritative_crosswalk": "not_performed",
        "valid_time": "not_assessed",
        "rights": "not_evaluated",
        "comparability": "not_asserted",
        "drift_disposition": "observed_surface_change_unmapped",
        "repeat_identical": True,
    }
    return bind_recorded_comparison(
        {key: value for key, value in report.items() if key != "repeat_identical"},
        TRACK / "classification-label-occurrences-20260930.json",
        "classification_label_comparison_recorded_mismatch",
    )


def run() -> dict[str, Any]:  # noqa: C901, PLR0912, PLR0915 - recovery products share a clean-room root.
    """Rebuild supported products in a disposable derivative root."""
    if not ARCHIVE.is_dir():
        message = "pinned_external_bronze_unavailable"
        raise RuntimeError(message)
    original_snapshot = tree(ARCHIVE / "bronze-cas")
    outputs: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="health-recovery-clean-") as temporary:
        root = Path(temporary)
        silver_roots = (root / "silver-one", root / "silver-two")
        for silver in silver_roots:
            silver.mkdir()
        context_silver: dict[str, Any] = {}
        for family, (package, _pin) in CONTEXT.items():
            first = rebuild_context_silver(silver_roots[0], family)
            second = rebuild_context_silver(silver_roots[1], family)
            files = compare_product_outputs(
                silver_roots[0] / package,
                silver_roots[1] / package,
                f"{family}_silver",
            )
            context_silver[family] = {
                "files": files,
                "manifest_sha256": first["manifest_sha256"],
                "source_object_sha256": first["source_object_sha256"],
                "counts": first["counts"],
                "repeat_identical": first == second,
            }
            if first != second:
                message = f"{family}_silver_repeat_mismatch"
                raise RuntimeError(message)
        outputs["context_source_native_silver"] = context_silver
        outputs["gdp_june_successor_silver"] = gdp_june_recovery_report(
            root, silver_roots=silver_roots
        )
        if "cpi" in CONTEXT:
            outputs["cpi_canonical_projection"] = _cpi_canonical_recovery_report(
                silver_roots[0], root
            )
        if "population" in CONTEXT:
            outputs["population_canonical_projection"] = (
                _population_canonical_recovery_report(silver_roots[0], root)
            )
        if "gdp" in CONTEXT:
            outputs["gdp_canonical_projection"] = _gdp_canonical_recovery_report(
                silver_roots[0], root
            )
            outputs["gdp_vintage_comparison"] = gdp_vintage_comparison_report(root)
        donor_products = {
            str(index): rebuild_donor_products(root, index) for index in (1, 2)
        }
        donor_repeat = all(
            donor_products["1"][name] == donor_products["2"][name]
            for name in ("raw", "compatibility", "gold", "plots")
        )
        if not donor_repeat:
            message = "donor_product_repeat_mismatch"
            raise RuntimeError(message)
        outputs["donor_sqlite_gold_plots"] = {
            "products": {
                category: donor_products["1"][category]
                for category in ("raw", "compatibility", "gold", "plots")
            },
            "repeat_identical": donor_repeat,
            "raw_manifest_sha256": donor_products["1"]["raw_manifest_sha256"],
            "compatibility_facts": donor_products["1"]["compatibility_facts"],
            "gold_selected_facts": donor_products["1"]["gold_selected_facts"],
            "plot_count": donor_products["1"]["plot_count"],
        }
        eight_stage = {str(index): rebuild_eight_stage(root, index) for index in (1, 2)}
        eight_stage_files = compare_product_outputs(
            root / "eight-stage-1", root / "eight-stage-2", "eight_stage_silver"
        )
        outputs["donor_source_native_silver"] = {
            "files": eight_stage_files,
            "manifest_sha256": eight_stage["1"]["manifest_sha256"],
            "profile_count": eight_stage["1"]["profile_count"],
            "fact_count": eight_stage["1"]["fact_count"],
            "rights_state": eight_stage["1"]["rights_state"],
            "gold_selection": eight_stage["1"]["gold_selection"],
            "publication": eight_stage["1"]["publication"],
            "repeat_identical": eight_stage["1"] == eight_stage["2"],
        }
        if eight_stage["1"] != eight_stage["2"]:
            message = "eight_stage_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_totals = {
            str(index): rebuild_vote_health_2018_19_category_totals(root, index)
            for index in (1, 2)
        }
        vote_health_totals_files = compare_product_outputs(
            root / "vote-health-2018-19-category-totals-1",
            root / "vote-health-2018-19-category-totals-2",
            "vote_health_2018_19_category_totals",
        )
        outputs["vote_health_supplementary_2018_19_category_totals"] = {
            "files": vote_health_totals_files,
            "operation_receipt": vote_health_totals["1"]["operation_receipt"],
            "repeat_identical": (vote_health_totals["1"] == vote_health_totals["2"]),
        }
        if vote_health_totals["1"] != vote_health_totals["2"]:
            message = "vote_health_2018_19_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2013_14_totals = {
            str(index): rebuild_vote_health_2013_14_category_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2013_14_files = compare_product_outputs(
            root / "vote-health-2013-14-category-totals-1",
            root / "vote-health-2013-14-category-totals-2",
            "vote_health_2013_14_category_totals",
        )
        outputs["vote_health_supplementary_2013_14_category_totals"] = {
            "files": vote_health_2013_14_files,
            "operation_receipt": vote_health_2013_14_totals["1"]["operation_receipt"],
            "repeat_identical": (
                vote_health_2013_14_totals["1"] == vote_health_2013_14_totals["2"]
            ),
        }
        if vote_health_2013_14_totals["1"] != vote_health_2013_14_totals["2"]:
            message = "vote_health_2013_14_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2014_15_totals = {
            str(index): rebuild_vote_health_2014_15_category_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2014_15_files = compare_product_outputs(
            root / "vote-health-2014-15-category-totals-1",
            root / "vote-health-2014-15-category-totals-2",
            "vote_health_2014_15_category_totals",
        )
        outputs["vote_health_supplementary_2014_15_category_totals"] = {
            "files": vote_health_2014_15_files,
            "operation_receipt": vote_health_2014_15_totals["1"]["operation_receipt"],
            "repeat_identical": (
                vote_health_2014_15_totals["1"] == vote_health_2014_15_totals["2"]
            ),
        }
        if vote_health_2014_15_totals["1"] != vote_health_2014_15_totals["2"]:
            message = "vote_health_2014_15_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2015_16_totals = {
            str(index): rebuild_vote_health_2015_16_category_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2015_16_files = compare_product_outputs(
            root / "vote-health-2015-16-category-totals-1",
            root / "vote-health-2015-16-category-totals-2",
            "vote_health_2015_16_category_totals",
        )
        outputs["vote_health_supplementary_2015_16_category_totals"] = {
            "files": vote_health_2015_16_files,
            "operation_receipt": vote_health_2015_16_totals["1"]["operation_receipt"],
            "repeat_identical": (
                vote_health_2015_16_totals["1"] == vote_health_2015_16_totals["2"]
            ),
        }
        if vote_health_2015_16_totals["1"] != vote_health_2015_16_totals["2"]:
            message = "vote_health_2015_16_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2016_17_totals = {
            str(index): rebuild_vote_health_2016_17_category_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2016_17_files = compare_product_outputs(
            root / "vote-health-2016-17-category-totals-1",
            root / "vote-health-2016-17-category-totals-2",
            "vote_health_2016_17_category_totals",
        )
        outputs["vote_health_supplementary_2016_17_category_totals"] = {
            "files": vote_health_2016_17_files,
            "operation_receipt": vote_health_2016_17_totals["1"]["operation_receipt"],
            "repeat_identical": (
                vote_health_2016_17_totals["1"] == vote_health_2016_17_totals["2"]
            ),
        }
        if vote_health_2016_17_totals["1"] != vote_health_2016_17_totals["2"]:
            message = "vote_health_2016_17_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2019_20_totals = {
            str(index): rebuild_vote_health_2019_20_category_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2019_20_totals_files = compare_product_outputs(
            root / "vote-health-2019-20-category-totals-1",
            root / "vote-health-2019-20-category-totals-2",
            "vote_health_2019_20_category_totals",
        )
        outputs["vote_health_supplementary_2019_20_category_totals"] = {
            "files": vote_health_2019_20_totals_files,
            "operation_receipt": vote_health_2019_20_totals["1"]["operation_receipt"],
            "repeat_identical": (
                vote_health_2019_20_totals["1"] == vote_health_2019_20_totals["2"]
            ),
        }
        if vote_health_2019_20_totals["1"] != vote_health_2019_20_totals["2"]:
            message = "vote_health_2019_20_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2020_21_summaries = {
            str(index): rebuild_vote_health_2020_21_summary_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2020_21_summary_files = compare_product_outputs(
            root / "vote-health-2020-21-summary-totals-1",
            root / "vote-health-2020-21-summary-totals-2",
            "vote_health_2020_21_summary_totals",
        )
        outputs["vote_health_supplementary_2020_21_summary_totals"] = {
            "files": vote_health_2020_21_summary_files,
            "operation_receipt": vote_health_2020_21_summaries["1"][
                "operation_receipt"
            ],
            "repeat_identical": (
                vote_health_2020_21_summaries["1"] == vote_health_2020_21_summaries["2"]
            ),
        }
        if vote_health_2020_21_summaries["1"] != vote_health_2020_21_summaries["2"]:
            message = "vote_health_2020_21_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2021_22_summaries = {
            str(index): rebuild_vote_health_2021_22_summary_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2021_22_summary_files = compare_product_outputs(
            root / "vote-health-2021-22-summary-totals-1",
            root / "vote-health-2021-22-summary-totals-2",
            "vote_health_2021_22_summary_totals",
        )
        outputs["vote_health_supplementary_2021_22_summary_totals"] = {
            "files": vote_health_2021_22_summary_files,
            "operation_receipt": vote_health_2021_22_summaries["1"][
                "operation_receipt"
            ],
            "repeat_identical": (
                vote_health_2021_22_summaries["1"] == vote_health_2021_22_summaries["2"]
            ),
        }
        if vote_health_2021_22_summaries["1"] != vote_health_2021_22_summaries["2"]:
            message = "vote_health_2021_22_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2022_23_summaries = {
            str(index): rebuild_vote_health_2022_23_summary_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2022_23_summary_files = compare_product_outputs(
            root / "vote-health-2022-23-summary-totals-1",
            root / "vote-health-2022-23-summary-totals-2",
            "vote_health_2022_23_summary_totals",
        )
        outputs["vote_health_supplementary_2022_23_summary_totals"] = {
            "files": vote_health_2022_23_summary_files,
            "operation_receipt": vote_health_2022_23_summaries["1"][
                "operation_receipt"
            ],
            "repeat_identical": (
                vote_health_2022_23_summaries["1"] == vote_health_2022_23_summaries["2"]
            ),
        }
        if vote_health_2022_23_summaries["1"] != vote_health_2022_23_summaries["2"]:
            message = "vote_health_2022_23_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2023_24_summaries = {
            str(index): rebuild_vote_health_2023_24_summary_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2023_24_summary_files = compare_product_outputs(
            root / "vote-health-2023-24-summary-totals-1",
            root / "vote-health-2023-24-summary-totals-2",
            "vote_health_2023_24_summary_totals",
        )
        outputs["vote_health_supplementary_2023_24_summary_totals"] = {
            "files": vote_health_2023_24_summary_files,
            "operation_receipt": vote_health_2023_24_summaries["1"][
                "operation_receipt"
            ],
            "repeat_identical": (
                vote_health_2023_24_summaries["1"] == vote_health_2023_24_summaries["2"]
            ),
        }
        if vote_health_2023_24_summaries["1"] != vote_health_2023_24_summaries["2"]:
            message = "vote_health_2023_24_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2024_25_summaries = {
            str(index): rebuild_vote_health_2024_25_summary_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2024_25_summary_files = compare_product_outputs(
            root / "vote-health-2024-25-summary-totals-1",
            root / "vote-health-2024-25-summary-totals-2",
            "vote_health_2024_25_summary_totals",
        )
        outputs["vote_health_supplementary_2024_25_summary_totals"] = {
            "files": vote_health_2024_25_summary_files,
            "operation_receipt": vote_health_2024_25_summaries["1"][
                "operation_receipt"
            ],
            "repeat_identical": (
                vote_health_2024_25_summaries["1"] == vote_health_2024_25_summaries["2"]
            ),
        }
        if vote_health_2024_25_summaries["1"] != vote_health_2024_25_summaries["2"]:
            message = "vote_health_2024_25_repeat_mismatch"
            raise RuntimeError(message)
        vote_health_2025_26_summaries = {
            str(index): rebuild_vote_health_2025_26_summary_totals(root, index)
            for index in (1, 2)
        }
        vote_health_2025_26_summary_files = compare_product_outputs(
            root / "vote-health-2025-26-summary-totals-1",
            root / "vote-health-2025-26-summary-totals-2",
            "vote_health_2025_26_summary_totals",
        )
        outputs["vote_health_supplementary_2025_26_summary_totals"] = {
            "files": vote_health_2025_26_summary_files,
            "operation_receipt": vote_health_2025_26_summaries["1"][
                "operation_receipt"
            ],
            "repeat_identical": (
                vote_health_2025_26_summaries["1"] == vote_health_2025_26_summaries["2"]
            ),
        }
        if vote_health_2025_26_summaries["1"] != vote_health_2025_26_summaries["2"]:
            message = "vote_health_2025_26_repeat_mismatch"
            raise RuntimeError(message)
        context_one, context_two = root / "context-one", root / "context-two"
        cas_objects = ARCHIVE / "bronze-cas" / "sha256"
        export_context_gold(silver_roots[0], cas_objects, context_one, write=True)
        export_context_gold(silver_roots[1], cas_objects, context_two, write=True)
        context_files = compare_product_outputs(
            context_one, context_two, "context_gold"
        )
        outputs["context_gold"] = {
            "files": context_files,
            "repeat_identical": True,
        }
        outputs["canonical_context_consumer"] = _query_context_consumer(context_one)
        outputs["qes_canonical_projection"] = _qes_recovery_report(root)
        outputs["crown_canonical_projection"] = _crown_recovery_report(root)
        outputs["hyefu_crown_canonical_projection"] = _hyefu_crown_recovery_report(root)
        outputs["historical_fiscal_crown_canonical_projection"] = (
            _fiscal_crown_recovery_report(root)
        )
        # The Gold product consumes the verified Pharmac Silver build below.
        outputs["pharmac_canonical_projection"] = _pharmac_recovery_report(root)
        outputs["moh_indicators_canonical_projection"] = _moh_recovery_report(root)
        outputs["canonical_gold"] = _canonical_gold_recovery_report(root)
        analytical = recover_analytical_metadata(
            ARCHIVE, root / "analytical-metadata", write=True
        )
        outputs["fiscal_analytical_gold_reports_interfaces"] = analytical[
            "fiscal_recovery"
        ]
        outputs["analytical_gold_and_metadata_recovery"] = analytical
        outputs["source_health_report"] = source_health_recovery_report()
        outputs["classification_label_occurrences"] = (
            classification_label_occurrence_report()
        )
        canonical_quality = outputs["canonical_gold"].get("quality_report") or {}
        outputs["donor_and_canonical_reports"] = {
            "donor_parity": donor_parity_recovery_report(),
            "canonical_quality": canonical_quality or None,
            "source_health": outputs["source_health_report"],
            "classification_label_occurrences": outputs[
                "classification_label_occurrences"
            ],
            "canonical_classification_drift": outputs["canonical_gold"].get(
                "classification_drift_report"
            ),
            "unresolved_canonical_reports": canonical_quality.get(
                "unresolved_reports", ["canonical_gold_not_rebuilt"]
            ),
        }
    unchanged = original_snapshot == tree(ARCHIVE / "bronze-cas")
    if not unchanged:
        message = "bronze_mutation_detected"
        raise RuntimeError(message)
    return {
        "schema_version": "archive-govt-nz.health-clean-room-recovery/v1",
        "status": "partial_with_blockers",
        "source": "pinned external Bronze CAS and reviewed retained Silver packages",
        "clean_derivative_root": "temporary_directory_removed_after_run",
        "products_rebuilt": outputs,
        "bronze_objects_unchanged": unchanged,
        "required_but_not_rebuilt": [
            "cross_source_comparison",
            "remaining_source_native_silver_profiles_and_canonical_adapters",
            "platinum_dcat_croissant_ro_crate_prov_complete_profile",
        ],
        "rights": "not_evaluated",
        "publication": "not_performed",
        "final_gate": (
            "blocked_until_all_required_products_are_built_from_bronze_and_validated"
        ),
    }


def main() -> int:
    """Write and display the recovery assurance receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
