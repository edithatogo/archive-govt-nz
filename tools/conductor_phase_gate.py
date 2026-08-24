"""Automated Conductor Phase Gate and Review Harness.

Executes targeted code quality, schema, typing, and unit test verifications
for individual Conductor phases, producing immutable review receipts without
running redundant full test suites.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = REPOSITORY_ROOT / "build" / "conductor-reviews"

PHASE_TARGETS: dict[str, dict[str, Any]] = {
    "phase_1_bronze": {
        "title": "Phase 1: Bronze Ingestion Layer",
        "test_targets": [
            "tests/bronze/test_manifest.py",
            "tests/bronze/test_adapter.py",
            "tests/domains/test_courts_notices.py",
            "tests/domains/test_health_bronze.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/",
            "src/archive_govt_nz/domains/gazette/courts_notices.py",
            "src/archive_govt_nz/domains/health/",
        ],
        "schemas": ["schemas/bronze-ingestion-manifest-v1.schema.json"],
    },
    "phase_2_silver": {
        "title": "Phase 2: Silver Layer Parquet Pipelines",
        "test_targets": [
            "tests/silver/",
        ],
        "source_paths": [
            "src/archive_govt_nz/silver/",
        ],
        "schemas": [],
    },
    "phase_3_silver_interlink": {
        "title": "Phase 3: Silver Cross-Domain Interlinking & Relational Lineage Graph",
        "test_targets": [
            "tests/silver/test_interlink.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/silver/interlink.py",
        ],
        "schemas": [],
    },
    "phase_4_gold_duckdb": {
        "title": "Phase 4: Gold Layer DuckDB Analytical Engine & DCAT-AP",
        "test_targets": [
            "tests/gold/test_analytics.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/gold/analytics.py",
        ],
        "schemas": [],
    },
    "phase_5_gold_lancedb": {
        "title": "Phase 5: Gold Layer Embedded LanceDB Hybrid Vector Index",
        "test_targets": [
            "tests/gold/test_search.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/gold/search.py",
        ],
        "schemas": [],
    },
    "phase_6_cli_mcp": {
        "title": "Phase 6: Unified CLI & MCP Query Surface",
        "test_targets": [
            "tests/cli/test_query_cli.py",
            "tests/cli/test_mcp_cli_contract.py",
            "tests/mcp/",
        ],
        "source_paths": [
            "src/archive_govt_nz/cli.py",
            "src/archive_govt_nz/mcp_server.py",
        ],
        "schemas": [],
    },
    "phase_7_gates": {
        "title": "Phase 7: Quality Gates, Mutation Testing & End-to-End Evidence",
        "test_targets": [
            "tests/bronze/",
            "tests/silver/",
            "tests/gold/",
            "tests/cli/test_query_cli.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/",
            "src/archive_govt_nz/silver/",
            "src/archive_govt_nz/gold/",
        ],
        "schemas": [],
        "extra_commands": [
            (
                ["uv", "run", "--locked", "python", "tools/mutation_medallion.py"],
                "Medallion Mutation Gate",
            ),
        ],
    },
    "bronze_harden_p1": {
        "title": "Bronze Hardening Phase 1: Magic Byte Filter & MIME Signature Engine",
        "test_targets": [
            "tests/bronze/test_sniffer.py",
            "tests/bronze/test_adapter.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/sniffer.py",
            "src/archive_govt_nz/bronze/adapter.py",
        ],
        "schemas": ["schemas/bronze-ingestion-manifest-v1.schema.json"],
    },
    "bronze_harden_p2": {
        "title": "Bronze Hardening Phase 2: Streaming Multi-Hash Engine (CIDv1)",
        "test_targets": [
            "tests/bronze/test_multihash.py",
            "tests/bronze/test_manifest.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/multihash.py",
            "src/archive_govt_nz/bronze/manifest.py",
        ],
        "schemas": ["schemas/bronze-ingestion-manifest-v1.schema.json"],
    },
    "bronze_harden_p3": {
        "title": "Bronze Hardening Phase 3: Structural Schema Fingerprinting & Drift Detection",
        "test_targets": [
            "tests/bronze/test_fingerprint.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/fingerprint.py",
        ],
        "schemas": [],
    },
    "bronze_harden_p4": {
        "title": "Bronze Hardening Phase 4: Offline Ed25519 Manifest Sealing",
        "test_targets": [
            "tests/bronze/test_attestation.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/attestation.py",
        ],
        "schemas": [],
    },
    "bronze_harden_p5": {
        "title": "Bronze Hardening Phase 5: Quality Gates & Certification",
        "test_targets": [
            "tests/bronze/",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/",
        ],
        "schemas": ["schemas/bronze-ingestion-manifest-v1.schema.json"],
        "extra_commands": [
            (
                ["uv", "run", "--locked", "python", "tools/mutation_medallion.py"],
                "Medallion Mutation Gate",
            ),
        ],
    },
    "bronze_surv_p1": {
        "title": "Surveillance Phase 1: Compact Surveillance Heartbeat Ledger",
        "test_targets": [
            "tests/bronze/test_heartbeat.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/heartbeat.py",
        ],
        "schemas": [],
    },
    "bronze_surv_p2": {
        "title": "Surveillance Phase 2: Canonical URN Protocol & Federation Encoders",
        "test_targets": [
            "tests/core/test_urn.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/core/urn.py",
        ],
        "schemas": [],
    },
    "bronze_surv_p3": {
        "title": "Surveillance Phase 3: Zero-Copy Cross-Repository Federated SQL Views",
        "test_targets": [
            "tests/gold/test_federation_views.py",
        ],
        "source_paths": [
            "src/archive_govt_nz/gold/analytics.py",
        ],
        "schemas": [],
    },
    "bronze_surv_p4": {
        "title": "Surveillance Phase 4: Asynchronous OpenTimestamps Proof-of-Existence Batcher",
        "test_targets": [
            "tests/tools/test_ots_batch_anchoring.py",
        ],
        "source_paths": [
            "tools/ots_batch_anchoring.py",
        ],
        "schemas": [],
    },
    "bronze_surv_p5": {
        "title": "Surveillance Phase 5: Quality Gates & Federation Certification",
        "test_targets": [
            "tests/bronze/",
            "tests/gold/",
        ],
        "source_paths": [
            "src/archive_govt_nz/bronze/",
            "src/archive_govt_nz/gold/",
        ],
        "schemas": [],
        "extra_commands": [
            (
                ["uv", "run", "--locked", "python", "tools/mutation_medallion.py"],
                "Medallion Mutation Gate",
            ),
        ],
    },
    "hansard_p1": {
        "title": "Hansard Phase 1: Domain Schemas, XML Streaming Parser & Raw Bronze Acquisition",
        "test_targets": [
            "tests/domains/hansard/",
        ],
        "source_paths": [
            "src/archive_govt_nz/domains/hansard/",
        ],
        "schemas": ["schemas/hansard-debate-v1.schema.json"],
    },
    "hansard_p2": {
        "title": "Hansard Phase 2: Silver Bitemporal Normalization & Speaker Entity Reconciliation",
        "test_targets": [
            "tests/domains/hansard/",
            "tests/silver/",
        ],
        "source_paths": [
            "src/archive_govt_nz/domains/hansard/",
        ],
        "schemas": ["schemas/hansard-debate-v1.schema.json"],
    },
    "hansard_p3": {
        "title": "Hansard Phase 3: Gold Analytical Engine, Semantic Search & Mutation Gates",
        "test_targets": [
            "tests/domains/hansard/",
            "tests/gold/",
        ],
        "source_paths": [
            "src/archive_govt_nz/domains/hansard/",
            "src/archive_govt_nz/gold/",
        ],
        "schemas": ["schemas/hansard-debate-v1.schema.json"],
        "extra_commands": [
            (
                ["uv", "run", "--locked", "python", "tools/mutation_medallion.py"],
                "Medallion Mutation Gate",
            ),
        ],
    },
}


MAX_LOG_CHARS = 1000


def run_stage(command: list[str], description: str) -> dict[str, Any]:
    """Execute a single gate stage and record timing and output."""
    proc = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "description": description,
        "command": command,
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout": proc.stdout[-MAX_LOG_CHARS:]
        if len(proc.stdout) > MAX_LOG_CHARS
        else proc.stdout,
        "stderr": proc.stderr[-MAX_LOG_CHARS:]
        if len(proc.stderr) > MAX_LOG_CHARS
        else proc.stderr,
    }


def execute_phase_review(phase_id: str) -> int:
    """Execute rigorous, targeted verification for a specific phase."""
    if phase_id not in PHASE_TARGETS:
        print(
            f"Unknown phase_id: {phase_id}. Choose from: {list(PHASE_TARGETS.keys())}"
        )
        return 1

    config = PHASE_TARGETS[phase_id]
    print(f"=== Conductor Review & Gate: {config['title']} ===")

    stages: list[dict[str, Any]] = []

    # 1. Format Check
    stages.append(
        run_stage(
            ["uv", "run", "--locked", "ruff", "format", "--check", "."],
            "Ruff Code Formatting Check",
        )
    )

    # 2. Lint Check
    stages.append(
        run_stage(
            ["uv", "run", "--locked", "ruff", "check", "."],
            "Ruff Code Linter & Rule Enforcement",
        )
    )

    # 3. Schema Validation
    stages.append(
        run_stage(
            ["uv", "run", "--locked", "python", "tools/validate_schemas.py"],
            "JSON Schema & Fixture Verification",
        )
    )

    # 4. Target-Specific Unit Tests (Minimizing unnecessary testing)
    test_targets = [t for t in config["test_targets"] if (REPOSITORY_ROOT / t).exists()]
    if test_targets:
        test_cmd = ["uv", "run", "--locked", "pytest", *test_targets]
        stages.append(run_stage(test_cmd, f"Targeted Unit Tests: {test_targets}"))

    # 5. Extra Verification Commands (e.g. mutation testing)
    for cmd, desc in config.get("extra_commands", []):
        stages.append(run_stage(cmd, desc))

    # Compute aggregate status
    all_passed = all(stage["passed"] for stage in stages)
    status = "passed" if all_passed else "failed"

    # Generate immutable review receipt
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    receipt_data = {
        "schema_version": "archive-govt-nz.conductor-phase-review/v1",
        "phase_id": phase_id,
        "title": config["title"],
        "reviewed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "stages": stages,
    }
    serialized = json.dumps(receipt_data, indent=2, sort_keys=True)
    receipt_sha = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    receipt_data["receipt_sha256"] = receipt_sha

    receipt_file = REVIEW_DIR / f"{phase_id}-review-receipt.json"
    receipt_file.write_text(
        json.dumps(receipt_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"\nPhase Review Outcome: {status.upper()}")
    print(f"Receipt written to: {receipt_file} (SHA256: {receipt_sha[:16]}...)")

    for stage in stages:
        mark = "✓" if stage["passed"] else "✗"
        print(f"  [{mark}] {stage['description']}")

    return 0 if all_passed else 1


def main() -> int:
    """CLI entrypoint for phase review."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=list(PHASE_TARGETS.keys()),
        required=True,
        help="Conductor phase identifier to review and verify",
    )
    args = parser.parse_args()
    return execute_phase_review(args.phase)


if __name__ == "__main__":
    sys.exit(main())
