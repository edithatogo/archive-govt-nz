"""Run isolated targeted mutants against Medallion architecture implementation."""

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

MUTANTS = {
    "manifest_fixity": (
        "src/archive_govt_nz/bronze/manifest.py",
        "sha256_manifest = hashlib.sha256(serialized).hexdigest()",
        "sha256_manifest = '0'*64",
        "tests/bronze/test_manifest.py",
    ),
    "bronze_magic_sniffer": (
        "src/archive_govt_nz/bronze/sniffer.py",
        "is_polyglot = detected in (",
        "is_polyglot = False and detected in (",
        "tests/bronze/test_sniffer.py",
    ),
    "bronze_cidv1_multihash": (
        "src/archive_govt_nz/bronze/multihash.py",
        "cid_bytes = _CIDV1_RAW_SHA256_HEADER + sha256_digest",
        'cid_bytes = b"\\x00\\x00\\x00\\x00" + sha256_digest',
        "tests/bronze/test_multihash.py",
    ),
    "bronze_ed25519_attestation": (
        "src/archive_govt_nz/bronze/attestation.py",
        "return lhs == rhs",
        "return True",
        "tests/bronze/test_attestation.py",
    ),
    "silver_table_population": (
        "src/archive_govt_nz/silver/pipeline.py",
        "arrow_table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)",
        "arrow_table = pa.Table.from_pylist([], schema=SILVER_ARROW_SCHEMA)",
        "tests/silver/test_pipeline.py",
    ),
    "gold_view_registration": (
        "src/archive_govt_nz/gold/analytics.py",
        'view_name = f"silver_{domain_dir.name}"',
        'view_name = f"invalid_{domain_dir.name}"',
        "tests/gold/test_analytics.py",
    ),
    "search_embedding_norm": (
        "src/archive_govt_nz/gold/search.py",
        "norm = math.sqrt(sum(x * x for x in vec))",
        "norm = 0.0",
        "tests/gold/test_search.py",
    ),
    "bronze_surveillance_heartbeat": (
        "src/archive_govt_nz/bronze/heartbeat.py",
        "timestamp = checked_at or datetime.now(UTC).strftime(",
        "timestamp = '1970-01-01T00:00:00Z' if False else checked_at or ",
        "tests/bronze/test_heartbeat.py",
    ),
    "core_canonical_urn": (
        "src/archive_govt_nz/core/urn.py",
        '_URN_PREFIX: Final[str] = "urn:nz-govt"',
        '_URN_PREFIX: Final[str] = "urn:corrupted"',
        "tests/core/test_urn.py",
    ),
    "bronze_ots_merkle": (
        "src/archive_govt_nz/bronze/ots.py",
        "return hashlib.sha256(left_bytes + right_bytes).hexdigest()",
        "return '0' * 64",
        "tests/bronze/test_ots.py",
    ),
    "hansard_statutory_extraction": (
        "src/archive_govt_nz/domains/hansard/parser.py",
        'if "Bill" in full_title:',
        'if False and "Bill" in full_title:',
        "tests/domains/hansard/test_parser.py",
    ),
    "hansard_silver_normalizer_urn": (
        "src/archive_govt_nz/domains/hansard/normalizer.py",
        'work_id = f"{debate.document_id}_{speech.speech_id}"',
        'work_id = "corrupted_id"',
        "tests/domains/hansard/test_normalizer.py",
    ),
}


def _run_single_mutant(
    name: str, target_file: str, needle: str, replacement: str, test_file: str
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="medallion-mutant-") as directory:
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
        ]
        result = subprocess.run(
            cmd,
            cwd=ROOT,
            env={"PYTHONPATH": str(root), **os.environ},
            capture_output=True,
            text=True,
            check=False,
        )
        return {"name": name, "killed": result.returncode != 0}


def main() -> int:
    """Run all targeted mutants and emit a machine-readable receipt."""
    results: list[dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(_run_single_mutant, name, target, needle, repl, test): name
            for name, (target, needle, repl, test) in MUTANTS.items()
        }
        results.extend(
            future.result() for future in concurrent.futures.as_completed(futures)
        )

    # Sort results deterministically by mutant name
    results.sort(key=lambda x: x["name"])

    payload = {
        "schema_version": "archive-govt-nz.mutation-medallion/v1",
        "mutants": results,
        "all_killed": all(r["killed"] for r in results),
    }
    out = Path("build/mutation-medallion.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_killed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
