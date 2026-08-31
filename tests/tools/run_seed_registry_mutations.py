"""Run explicit integrity mutants against the full focused seed-registry suite."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Preserve every attempt; only ordinary assertion failures kill a mutant."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path("tools/seed_registry.py").read_text()
    definitions = json.loads(Path("tests/tools/seed_registry_mutants.json").read_text())
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/tools/test_seed_registry.py",
        "-q",
    ]
    baseline = subprocess.run(command, capture_output=True, check=False, timeout=120)
    (args.output / "baseline.log").write_bytes(baseline.stdout + baseline.stderr)
    if baseline.returncode != 0:
        return 1
    outcomes = []
    for index, mutant in enumerate(definitions):
        if source.count(mutant["old"]) != 1:
            return 1
        path = args.output / f"mutant-{index:02}.py"
        path.write_text(source.replace(mutant["old"], mutant["new"]))
        environment = dict(os.environ, SEED_REGISTRY_UNDER_TEST=str(path.resolve()))
        result = subprocess.run(
            command, env=environment, capture_output=True, check=False, timeout=120
        )
        log = result.stdout + result.stderr
        (args.output / f"mutant-{index:02}.log").write_bytes(log)
        outcomes.append(
            {
                "name": mutant["name"],
                "exit_code": result.returncode,
                "killed": result.returncode == 1,
                "log_sha256": hashlib.sha256(log).hexdigest(),
            }
        )
    receipt = {
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "mutants": outcomes,
        "all_killed": all(item["killed"] for item in outcomes),
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return 0 if receipt["all_killed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
