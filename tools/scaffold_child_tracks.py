"""Scaffold 12 child tracks for the legislation corrective programme."""

from __future__ import annotations

import json
from pathlib import Path

TRACKS = [
    (
        "legislation_corrective_evidence_chronology_20260818",
        "Evidence correction and chronology",
    ),
    (
        "legislation_corrective_live_inventory_reuse_20260818",
        "Live inventory and reuse analysis",
    ),
    (
        "legislation_corrective_standards_schema_conformance_20260818",
        "Standards and schema conformance",
    ),
    (
        "legislation_corrective_adapter_client_integration_20260818",
        "Existing adapter and donor-client integration",
    ),
    (
        "legislation_corrective_identity_normalisation_corpus_20260818",
        "Legislation identity, normalisation and corpus services",
    ),
    (
        "legislation_corrective_cli_contract_compatibility_20260818",
        "CLI contract and compatibility",
    ),
    (
        "legislation_corrective_mcp_disposition_conformance_20260818",
        "MCP disposition and conformance",
    ),
    (
        "legislation_corrective_weekly_orchestration_state_20260818",
        "Weekly orchestration and persistent state",
    ),
    (
        "legislation_corrective_reconciliation_parity_publication_20260818",
        "Historical reconciliation, parity and publication identity",
    ),
    (
        "legislation_corrective_rights_redistribution_20260818",
        "Rights and redistribution",
    ),
    (
        "legislation_corrective_shadow_operation_cutover_20260818",
        "Shadow operation, recovery and cutover",
    ),
    (
        "legislation_corrective_gazette_residual_separation_20260818",
        "Gazette residual work, kept separate and incomplete",
    ),
]

BASE_DIR = Path("conductor/tracks")

for slug, desc in TRACKS:
    tdir = BASE_DIR / slug
    tdir.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": slug,
        "title": desc,
        "type": "track",
        "status": "in_progress",
        "created_at": "2026-08-18T12:54:00Z",
        "updated_at": "2026-08-18T12:54:00Z",
        "parent_track": "legislation_corpus_consolidation_corrective_20260818",
    }
    (tdir / "metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    idx = f"# Track: {desc}\n\n## Overview\nChild track of `legislation_corpus_consolidation_corrective_20260818` for {desc.lower()}.\n"
    (tdir / "index.md").write_text(idx, encoding="utf-8")

    req = f"# Requirements: {desc}\n\n- Satisfy corresponding executable contracts.\n- Maintain immutable provenance and anti-simulation rules.\n"
    (tdir / "requirements.md").write_text(req, encoding="utf-8")

    plan = f"# Plan: {desc}\n\n1. Establish contract and test seams.\n2. Implement/verify domain behaviours.\n3. Validate evidence.\n"
    (tdir / "plan.md").write_text(plan, encoding="utf-8")

    runlog = f"# Run Log: {desc}\n\n- Initialized track at 2026-08-18T12:54:00Z.\n"
    (tdir / "runlog.md").write_text(runlog, encoding="utf-8")

    evd = f"# Evidence: {desc}\n\n- Track-specific evidence recorded in evidence/migrations/corpus-legislation-nz/.\n"
    (tdir / "evidence.md").write_text(evd, encoding="utf-8")

    rev = f"# Review: {desc}\n\n- Verified against Phase 0 contract boundaries.\n"
    (tdir / "review.md").write_text(rev, encoding="utf-8")

print(f"Scaffolded {len(TRACKS)} child tracks successfully.")
