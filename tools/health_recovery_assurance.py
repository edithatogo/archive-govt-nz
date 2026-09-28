"""Run deterministic, payload-free clean-room Health recovery assurance."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, cast

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
from archive_govt_nz.domains.health_appropriations.plot_export import render_plots
from archive_govt_nz.domains.health_appropriations.population_annual_silver import (
    normalize_population_annual,
)
from archive_govt_nz.domains.health_appropriations.rebuild import (
    execute_rebuild,
    plan_rebuild,
    verify_rebuild,
)

TRACK = Path("conductor/tracks/health_appropriations_medallion_assimilation_20260829")
ARCHIVE = Path("/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations")
CONTEXT = {
    "cpi": (
        "raw-cpi-20260831-v1",
        "edb62f4b106948502e717f5f6c5e3da00efc0a64bb10b5dcbafc48cd1a6c257e",
    ),
    "wage": (
        "raw-qes-2026q2-20260831-v2",
        "35114105c86085ee49aeb97ac9f8d8b696ef72692b5eea12d348496a8b920d41",
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


def run() -> dict[str, Any]:  # noqa: PLR0915 - explicit staged recovery receipt
    """Rebuild supported products in a disposable derivative root."""
    if not ARCHIVE.is_dir():
        message = "pinned_external_bronze_unavailable"
        raise RuntimeError(message)
    original_snapshot = tree(ARCHIVE / "bronze-cas")
    outputs: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="health-recovery-clean-") as temporary:
        root = Path(temporary)
        silver = root / "silver"
        gold = root / "gold"
        silver.mkdir()
        gold.mkdir()
        population_hash = (
            "a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9"
        )
        population_source = (
            ARCHIVE / "bronze-cas" / "sha256" / population_hash[:2] / population_hash
        )
        census = json.loads((TRACK / "population-annual-context.json").read_text())
        population_output = root / "population-rebuilt"
        silver_receipt = normalize_population_annual(
            population_source,
            population_output,
            expected_sha256=population_hash,
            observed_at=census["retrieved_at"],
            source_vintage=census["release_date"],
            source_locator=census["export_route"],
            dry_run=False,
        )
        counts = cast("dict[str, Any]", silver_receipt["counts"])
        outputs["population_silver"] = tree(population_output) | {
            "records": counts["facts"]
        }
        for family, (package, pin) in CONTEXT.items():
            existing = ARCHIVE / "silver" / package
            if not existing.is_dir():
                message = f"missing_pinned_silver:{family}"
                raise RuntimeError(message)
            if digest(existing / "MANIFEST.json") != pin:
                message = f"silver_manifest_pin_mismatch:{family}"
                raise RuntimeError(message)
            shutil.copytree(existing, silver / package)
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
        context_one, context_two = root / "context-one", root / "context-two"
        cas_objects = ARCHIVE / "bronze-cas" / "sha256"
        export_context_gold(silver, cas_objects, context_one, write=True)
        export_context_gold(silver, cas_objects, context_two, write=True)
        outputs["context_gold"] = {
            "files": tree(context_one),
            "repeat_identical": tree(context_one) == tree(context_two),
        }
        if not outputs["context_gold"]["repeat_identical"]:
            message = "context_gold_repeat_mismatch"
            raise RuntimeError(message)
        canonical = canonical_inputs()
        if canonical:
            for index in (1, 2):
                target = root / f"canonical-{index}"
                export_canonical_gold(canonical, target, write=True)
            outputs["canonical_gold"] = {
                "files": tree(root / "canonical-1"),
                "repeat_identical": tree(root / "canonical-1")
                == tree(root / "canonical-2"),
            }
        else:
            outputs["canonical_gold"] = {
                "status": "blocked",
                "reason": (
                    "no_retained_canonical_inputs_passed_independent_source_binding"
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
            "donor_and_canonical_reports",
            "all_source_native_silver",
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
