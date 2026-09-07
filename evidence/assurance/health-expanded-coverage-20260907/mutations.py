"""Cold, in-memory guard mutations; never edit production or parent files."""

# ruff: noqa: INP001 -- standalone scoped evidence recipe.

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SOURCE = "src/archive_govt_nz/domains/health_appropriations/expanded_coverage.py"
TEST = "tests/domains/health_appropriations/test_expanded_coverage.py"
GUARDS = (
    'data[digest_key] == row["source_object_sha256"]',
    'data["source_locator"] == row["source_locator"]',
    'data["source_vintage"] == row["vintage"]',
    'completion["stages"][name] == row["receipt_sha256"]',
    'coverage["manifest_sha256"] == row["receipt_sha256"]',
    'coverage["facts"] == count',
    'data["profile"] == name',
    'item.sha256 == row["receipt_sha256"]',
    'data["schema_version"] == PROFILES[row["profile"]][1]',
    'data["rights_state"] == "not_evaluated"',
    "key not in seen",
    'row["family"] == PROFILES[row["profile"]][0]',
)
RUNNER = """
import sys, types, pytest
from pathlib import Path
name = 'archive_govt_nz.domains.health_appropriations.expanded_coverage'
source = Path(sys.argv[1]).read_text().replace(sys.argv[2], 'True')
module = types.ModuleType(name)
sys.modules[name] = module
exec(compile(source, sys.argv[1], 'exec'), module.__dict__)
sys.exit(pytest.main(['-q', sys.argv[3]]))
"""


def main() -> None:
    """Emit bounded outcome hashes; pytest failures alone count as kills."""
    source = Path(SOURCE).read_text()
    results = []
    for guard in GUARDS:
        if guard not in source:
            message = "mutation_guard_not_found"
            raise ValueError(message)
        result = subprocess.run(  # noqa: S603 -- fixed local interpreter/tests.
            [sys.executable, "-c", RUNNER, SOURCE, guard, TEST],
            capture_output=True,
            check=False,
            timeout=30,
        )
        results.append(
            {
                "guard": guard,
                "exit_code": result.returncode,
                "outcome": "killed" if result.returncode == 1 else "not_killed",
                "output_sha256": hashlib.sha256(
                    result.stdout + result.stderr
                ).hexdigest(),
            }
        )
    print(json.dumps(results, sort_keys=True, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
