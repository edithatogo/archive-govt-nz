"""Kill bounded source-preflight integrity mutants with retained execution logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

MUTANTS = (
    ("missing-credential", "if not credential.strip():", "if False:"),
    ("status-acceptance", "response.status_code == httpx.codes.OK", "True"),
    ("redirect-boundary", "follow_redirects=False", "follow_redirects=True"),
    (
        "state-fixity",
        'if before == after and source["status"] == "passed":',
        'if source["status"] == "passed":',
    ),
    ("state-size", "> MAX_STATE_BYTES", "> MAX_STATE_BYTES + 1000"),
    ("cas-size", "> MAX_CAS_BYTES", "> MAX_CAS_BYTES + 1000"),
    ("cas-count", "> MAX_CAS_OBJECTS", "> MAX_CAS_OBJECTS + 1000"),
    ("auth-header", '"X-Api-Key": credential', '"X-Api-Key": ""'),
)


def main() -> int:
    """Preserve baseline and every mutant outcome; reject non-assertion failures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    source = Path("tools/legislation_source_preflight.py").read_text()
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/tools/test_legislation_source_preflight.py",
        "-q",
        "--no-cov",
        "--maxfail=1",
    ]
    baseline = subprocess.run(command, capture_output=True, check=False, timeout=120)
    (output / "baseline.log").write_bytes(baseline.stdout + baseline.stderr)
    if baseline.returncode:
        return 1
    outcomes = []
    for name, old, new in MUTANTS:
        if source.count(old) != 1:
            return 1
        path = output / (name + ".py")
        path.write_text(source.replace(old, new))
        result = subprocess.run(
            command,
            env=dict(os.environ, SOURCE_PREFLIGHT_UNDER_TEST=str(path.resolve())),
            capture_output=True,
            check=False,
            timeout=120,
        )
        log = result.stdout + result.stderr
        (output / (name + ".log")).write_bytes(log)
        outcomes.append(
            {
                "name": name,
                "exit_code": result.returncode,
                "killed": result.returncode == 1
                and b"FAILED tests/tools/test_legislation_source_preflight.py" in log
                and b"ERROR collecting" not in log,
                "log_sha256": hashlib.sha256(log).hexdigest(),
            }
        )
    receipt = {
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "mutants": outcomes,
        "all_killed": all(item["killed"] for item in outcomes),
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return 0 if receipt["all_killed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
