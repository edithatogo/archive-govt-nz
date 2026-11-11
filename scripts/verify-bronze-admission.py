#!/usr/bin/env python3
"""
Verify Bronze admission byte-matching readback for tobac NZ/AU empirical sources.

This script validates that all artifacts in the Bronze admission manifest
match their SHA-256 hashes exactly, confirming independent byte-matching readback.
"""

import hashlib
import json
import sys
from pathlib import Path

# Artifact ID -> local file path mapping
ARTIFACT_PATHS = {
    "nzhs-adult-statistics-2024-25": "/Volumes/PortableSSD/tobac-p2-nzhs-guide.XfGtJg/adult-statistics.zip",
    "nzhs-indicator-reference-guide-2024-25": "/Volumes/PortableSSD/tobac-p2-nzhs-guide.XfGtJg/indicator-reference-guide-2024-25.xlsx",
    "nzhs-kim-window-incidence": "/Volumes/PortableSSD/tobac-p2-nzhs-guide.XfGtJg/kim-nzhs-window-incidence.csv",
    "nzhs-regional-daily-cigarettes-diagnostic": "/Volumes/PortableSSD/tobac-p2-nzhs-guide.XfGtJg/nzhs-regional-daily-cigarettes-diagnostic.csv",
    "moh-returns-customs-oia-imports": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/customs-oia-imports.pdf",
    "moh-returns-customs-overlap": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/customs-overlap.json",
    "stats-trade-2024-exports": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/2024_Exports_HS10.zip",
    "stats-trade-2024-imports": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/2024_Imports_HS10.zip",
    "stats-trade-2025-exports": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/2025_Exports_HS10.zip",
    "stats-trade-2025-imports": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/2025_Imports_HS10.zip",
    "stats-trade-exports-normalised": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/Exports-header-normalised.csv",
    "stats-trade-imports-normalised": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/Imports-header-normalised.csv",
    "stats-trade-cigarette-bounds": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/cigarette-bounds.json",
    "stats-trade-net-cigarette-bounds": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/net-cigarette-bounds.json",
    "stats-trade-stock-witness": "/Volumes/PortableSSD/tobac-p2-historical-trade.e1sT5C/stock-witness.json",
    "stats-cpi-june-2026": "/Volumes/PortableSSD/tobac-p2-trade2023.3PoIyO/cpi-june-infoshare.csv",
    "stats-cpi-september-2026": "/Volumes/PortableSSD/tobac-p2-trade2023.3PoIyO/cpi-september-infoshare.csv",
    "stats-cpi-lagged-price-candidates": "/Volumes/PortableSSD/tobac-p2-trade2023.3PoIyO/lagged-price-candidates-v2.csv",
    "customs-seizures-oia": "/Volumes/PortableSSD/tobac-p2-seizures.ku7cHn/oia.pdf",
    "police-wbe-2024-supplement": "/Volumes/PortableSSD/tobac-p2-historical-wbe.sEg2Vf/mmc1.docx",
    "bat-nz-cigarettes-tobacco": "/Volumes/PortableSSD/tobac-p2-bat23.jsiQBZ/cigarettes_tobacco.pdf",
    "pharmac-full-data-2026-07": "/Volumes/PortableSSD/tobac-p2-pharmac.Up2f8q/PharmsFullData_2026-07-09.zip",
    "acic-report-15": "/Volumes/PortableSSD/tobac-p2-acic.RvZGbz/15.pdf",
    "acic-report-16": "/Volumes/PortableSSD/tobac-p2-acic.RvZGbz/16.pdf",
    "abs-nhs-2022-table-36-10": "/Volumes/PortableSSD/tobac-p2-abs-sa2.po4I5V/abs-nhs-2022-table-36-10.csv",
    "aihw-ndshs-2025-table-1-33": "/Volumes/PortableSSD/tobac-p2-aihw.q6axfP/ndshs-2025-table-1-33-purchase-bands.csv",
    "aihw-purchase-bounds-replay": "/Volumes/PortableSSD/tobac-p2-aihw.q6axfP/replay-purchase-bounds.py",
    "ato-tax-gap-report": "/Volumes/PortableSSD/tobac-p2-ato.zYOhCK/report.pdf",
    "wang-national-article-xml": "/Volumes/PortableSSD/tobac-p2-wang-national.Mf5A9X/article.xml",
    "wang-national-supp1-pdf": "/Volumes/PortableSSD/tobac-p2-wang-national.Mf5A9X/supp1.pdf",
    "wang-queensland-mmcp1": "/Volumes/PortableSSD/tobac-p2-wang-queensland.GOsVz8/mmc1.docx",
    "kim-nz-2023-supplement-pdf": "/Volumes/PortableSSD/tobac-p2-kim.lBTiOt/mmc1.pdf",
    "kim-nz-2023-candidate-loads": "/Volumes/PortableSSD/tobac-p2-kim.lBTiOt/candidate-loads.csv",
}


def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def main():
    manifest_path = Path(
        "/Volumes/PortableSSD/ArchiveGovtNZ/archive-govt-nz/bronze-admission-tobac-20261110.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"Verifying Bronze admission batch: {manifest['admission_batch']}")
    print(f"Total artifacts in manifest: {len(manifest['artifacts'])}")
    print()

    results = {"verified": 0, "mismatch": 0, "missing": 0, "not_mapped": 0}

    for artifact in manifest["artifacts"]:
        artifact_id = artifact["artifact_id"]
        expected_sha = artifact["sha256"]

        if artifact_id not in ARTIFACT_PATHS:
            print(f"  {artifact_id}: NOT MAPPED (no local path)")
            results["not_mapped"] += 1
            continue

        local_path = ARTIFACT_PATHS[artifact_id]

        if not Path(local_path).exists():
            print(f"  {artifact_id}: MISSING at {local_path}")
            results["missing"] += 1
            continue

        actual_sha = sha256_file(local_path)

        if actual_sha == expected_sha:
            print(f"  ✅ {artifact_id}: VERIFIED ({actual_sha[:16]}...)")
            results["verified"] += 1
        else:
            print(f"  ❌ {artifact_id}: MISMATCH")
            print(f"    Expected: {expected_sha}")
            print(f"    Actual:   {actual_sha}")
            results["mismatch"] += 1

    print()
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Verified:    {results['verified']}")
    print(f"Mismatch:    {results['mismatch']}")
    print(f"Missing:     {results['missing']}")
    print(f"Not mapped:  {results['not_mapped']}")
    print()

    if results["mismatch"] == 0 and results["missing"] == 0:
        print(
            "✅ ALL MAPPED ARTIFACTS VERIFIED - Independent byte-matching readback PASSED"
        )
        return 0
    else:
        print("❌ VERIFICATION FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
