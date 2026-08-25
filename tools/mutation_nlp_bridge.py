"""Run isolated targeted mutants against Medallion NLP Bi-Directional Bridge."""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MUTANTS: dict[str, tuple[str, str, str, str]] = {
    "mcp_domain_list_count": (
        "src/archive_govt_nz/mcp_server.py",
        '"count": len(DOMAIN_REGISTRY),',
        '"count": 0,',
        "tests/mcp/test_dynamic_domain_tools.py",
    ),
    "silver_checkpoint_resume": (
        "src/archive_govt_nz/silver/pipeline.py",
        'start_index = int(cp_data.get("last_processed_index", -1)) + 1',
        "start_index = 0",
        "tests/silver/test_checkpoint_recovery.py",
    ),
    "gold_knowledge_graph_view": (
        "src/archive_govt_nz/gold/analytics.py",
        "CREATE OR REPLACE VIEW v_gold_extracted_entities AS",
        "CREATE OR REPLACE VIEW v_gold_broken_entities AS",
        "tests/gold/test_knowledge_graph_feedback.py",
    ),
}


def _run_single_mutant(
    name: str, target_file: str, needle: str, replacement: str, test_file: str
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="nlp-bridge-mutant-") as directory:
        root = Path(directory)
        package = root / "archive_govt_nz"
        shutil.copytree(ROOT / "src/archive_govt_nz", package)

        rel_path = Path(target_file).relative_to("src/archive_govt_nz")
        mutated = package / rel_path
        text = mutated.read_text(encoding="utf-8")
        if needle not in text:
            msg = f"mutant target missing in {target_file}: {name}"
            raise RuntimeError(msg)
        mutated.write_text(text.replace(needle, replacement, 1), encoding="utf-8")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_file,
            "-q",
            "--no-cov",
            "--override-ini=addopts=",
        ]
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{root}:{env.get('PYTHONPATH', '')}"

        proc = subprocess.run(  # noqa: S603
            cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, check=False
        )
        killed = proc.returncode != 0
        return {
            "name": name,
            "killed": killed,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-200:] if proc.stdout else "",
            "stderr": proc.stderr[-200:] if proc.stderr else "",
        }


def run_mutation_tests() -> dict[str, Any]:
    """Execute all mutation tests concurrently and verify all mutants are killed."""
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(
                _run_single_mutant,
                name,
                target_file,
                needle,
                replacement,
                test_file,
            ): name
            for name, (
                target_file,
                needle,
                replacement,
                test_file,
            ) in MUTANTS.items()
        }
        results.extend(
            future.result() for future in concurrent.futures.as_completed(futures)
        )

    total = len(results)
    killed = sum(1 for r in results if r["killed"])
    survived = total - killed

    return {
        "suite": "medallion_nlp_bridge",
        "total_mutants": total,
        "killed_mutants": killed,
        "survived_mutants": survived,
        "mutation_score": round((killed / total) * 100, 2) if total else 100.0,
        "mutants": results,
    }


def main() -> int:
    """Run CLI entrypoint for mutation testing."""
    report = run_mutation_tests()
    print(json.dumps(report, indent=2))
    return 0 if report["survived_mutants"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
