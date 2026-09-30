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
    pharmac,
    pharmac_canonical_projection,
    population_annual_canonical_projection,
    qes,
    qes_canonical_projection,
)
from archive_govt_nz.domains.health_appropriations.canonical_consumer import (
    query_context_observations,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_export import (
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
    "edc9c7a2635112bb8b2ba763bf7f4bd8c507ac2d5c879bacce52d5a03f09a294"
)
CONTEXT_CENSUS_SHA256 = (
    "e1190342e10808cc78603f57ae7cc032e635cbbced0a7573544d4f9a651f6aa6"
)
POPULATION_SOURCE_SHA256 = (
    "a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9"
)
PHARMAC_SOURCE_SHA256 = (
    "eaf5801b819321f8aed7544fb16e6348779267fd3d5f8fb1d59410803acffbea"
)
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


def gdp_june_recovery_report(root: Path) -> dict[str, Any]:
    """Prove Silver and canonical June outputs match without analytical selection."""
    first = rebuild_gdp_june_silver(root, 1)
    second = rebuild_gdp_june_silver(root, 2)
    files = compare_product_outputs(
        root / "gdp-june-1", root / "gdp-june-2", "gdp_june_silver"
    )
    require_evidence(first == second, "gdp_june_silver_receipt_mismatch")
    canonical_products = []
    for index in (1, 2):
        package = root / f"gdp-june-{index}"
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
    """Compare shared March/June periods from verified canonical facts."""
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
    return report


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


def canonical_inputs() -> tuple[CanonicalPackageInput, ...]:
    """Assemble the two independently pinned historical canonical packages."""
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
        root = ARCHIVE / "silver" / f"canonical-historical-{year}-20260831-v1"
        marker = root / "LOCAL_CANONICAL.json"
        value = json.loads(marker.read_text())
        original_hash = value["input_fixity"]["original_sha256"]
        original = ARCHIVE / "bronze-cas" / "sha256" / original_hash[:2] / original_hash
        packages.append(
            CanonicalPackageInput(
                "historical",
                root,
                digest(marker),
                original,
                ARCHIVE / "silver" / raw_name,
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
    canonical = canonical_inputs()
    if not canonical:
        return {
            "status": "blocked",
            "reason": "no_retained_canonical_inputs_passed_independent_source_binding",
        }
    for index in (1, 2):
        export_canonical_gold(canonical, root / f"canonical-{index}", write=True)
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


def run() -> dict[str, Any]:  # noqa: C901, PLR0915 - recovery products share a clean-room root.
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
        outputs["gdp_june_successor_silver"] = gdp_june_recovery_report(root)
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
        outputs["pharmac_canonical_projection"] = _pharmac_recovery_report(root)
        outputs["canonical_gold"] = _canonical_gold_recovery_report(root)
        canonical_quality = outputs["canonical_gold"].get("quality_report") or {}
        outputs["donor_and_canonical_reports"] = {
            "donor_parity": donor_parity_recovery_report(),
            "canonical_quality": canonical_quality or None,
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
            "canonical_source_health_classification_drift_revision_and_cross_source_reports",
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
