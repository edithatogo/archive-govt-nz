"""Typed orchestration for the repository assurance gate."""

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GateStage:
    """One named, non-interactive repository check."""

    name: str
    command: tuple[str, ...]


STAGES = (
    GateStage("lock", ("uv", "lock", "--check")),
    GateStage("format", ("uv", "run", "--locked", "ruff", "format", "--check", ".")),
    GateStage("lint", ("uv", "run", "--locked", "ruff", "check", ".")),
    GateStage("types", ("uv", "run", "--locked", "pyright")),
    GateStage(
        "tests",
        (
            "uv",
            "run",
            "--locked",
            "pytest",
            "--cov=archive_govt_nz",
            "--cov-branch",
            "--cov-report=term-missing",
        ),
    ),
    GateStage(
        "schemas",
        ("uv", "run", "--locked", "python", "tools/validate_schemas.py"),
    ),
    GateStage(
        "mutation",
        ("uv", "run", "--locked", "python", "tools/mutation_resource_policy.py"),
    ),
    GateStage(
        "mutation-versioning",
        ("uv", "run", "--locked", "python", "tools/mutation_versioning.py"),
    ),
    GateStage(
        "audit",
        ("uv", "run", "--locked", "python", "tools/supply_chain.py", "audit"),
    ),
    GateStage(
        "licenses",
        ("uv", "run", "--locked", "python", "tools/supply_chain.py", "licenses"),
    ),
    GateStage(
        "secrets",
        ("uv", "run", "--locked", "python", "tools/supply_chain.py", "secrets"),
    ),
    GateStage(
        "sbom",
        ("uv", "run", "--locked", "python", "tools/supply_chain.py", "sbom"),
    ),
)

Runner = Callable[[tuple[str, ...]], int]


def run_command(command: tuple[str, ...]) -> int:
    """Run one stage without a shell and return its process status."""
    try:
        return subprocess.run(command, check=False, timeout=180).returncode
    except subprocess.TimeoutExpired:
        return 124


def run_stages(
    stages: Sequence[GateStage] = STAGES,
    *,
    runner: Runner = run_command,
) -> int:
    """Run stages in order, stopping at the first failure."""
    for stage in stages:
        print(f"==> {stage.name}: {' '.join(stage.command)}", flush=True)
        result = runner(stage.command)
        if result != 0:
            return result
    return 0
