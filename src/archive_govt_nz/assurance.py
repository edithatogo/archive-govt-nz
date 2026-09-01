"""Typed orchestration for the repository assurance gate."""

import os
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass

COMMAND_TIMEOUT_SECONDS = 600


@dataclass(frozen=True, slots=True)
class GateStage:
    """One named, non-interactive repository check."""

    name: str
    command: tuple[str, ...]


_PYTEST_COMMAND = (
    "uv",
    "run",
    "--locked",
    "pytest",
    "--cov=archive_govt_nz",
    "--cov-branch",
    "--cov-report=term-missing",
)
_PYTEST_DISTRIBUTIONS = frozenset({"load", "loadscope", "loadfile", "worksteal"})


def build_stages(
    *,
    pytest_workers: str | None = None,
    pytest_distribution: str = "loadscope",
    include_heavy: bool = False,
) -> tuple[GateStage, ...]:
    """Build the gate sequence with an optional isolated xdist test lane."""
    if pytest_workers is not None and not (
        pytest_workers in {"auto", "logical"} or pytest_workers.isdecimal()
    ):
        msg = "pytest worker count must be auto, logical, or a positive integer"
        raise ValueError(msg)
    if pytest_workers == "0":
        msg = "pytest worker count must be auto, logical, or a positive integer"
        raise ValueError(msg)
    if pytest_distribution not in _PYTEST_DISTRIBUTIONS:
        msg = f"unsupported pytest distribution: {pytest_distribution}"
        raise ValueError(msg)

    pytest_command = _PYTEST_COMMAND
    if pytest_workers is not None:
        pytest_command += ("-n", pytest_workers, "--dist", pytest_distribution)

    stages = (
        GateStage("lock", ("uv", "lock", "--check")),
        GateStage(
            "conductor",
            ("uv", "run", "--locked", "python", "tools/validate_conductor_state.py"),
        ),
        GateStage(
            "format", ("uv", "run", "--locked", "ruff", "format", "--check", ".")
        ),
        GateStage("lint", ("uv", "run", "--locked", "ruff", "check", ".")),
        GateStage("types", ("uv", "run", "--locked", "basedpyright", "--threads", "4")),
        GateStage("tests", pytest_command),
        GateStage(
            "schemas",
            ("uv", "run", "--locked", "python", "tools/validate_schemas.py"),
        ),
        GateStage(
            "parity",
            ("uv", "run", "--locked", "python", "tools/run_differential_parity.py"),
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
            "mutation-redundancy",
            ("uv", "run", "--locked", "python", "tools/mutation_redundancy.py"),
        ),
        GateStage(
            "mutation-archivebox-pilot",
            ("uv", "run", "--locked", "python", "tools/mutation_archivebox_pilot.py"),
        ),
        GateStage(
            "mutation-batch-eligibility",
            ("uv", "run", "--locked", "python", "tools/mutation_batch_eligibility.py"),
        ),
        GateStage(
            "mutation-global-policy",
            ("uv", "run", "--locked", "python", "tools/mutation_global_policy.py"),
        ),
        GateStage(
            "mutation-adapters",
            ("uv", "run", "--locked", "python", "tools/mutation_adapters.py"),
        ),
        GateStage(
            "mutation-gazette",
            ("uv", "run", "--locked", "python", "tools/mutation_gazette.py"),
        ),
        GateStage(
            "mutation-medallion",
            ("uv", "run", "--locked", "python", "tools/mutation_medallion.py"),
        ),
        GateStage(
            "mutation-platinum",
            ("uv", "run", "--locked", "python", "tools/mutation_platinum.py"),
        ),
        GateStage(
            "mutation-nlp-bridge",
            ("uv", "run", "--locked", "python", "tools/mutation_nlp_bridge.py"),
        ),
        GateStage(
            "mutation-foi-controls",
            ("uv", "run", "--locked", "python", "tools/mutation_foi_controls.py"),
        ),
        GateStage(
            "mutation-foi-shared",
            ("uv", "run", "--locked", "python", "tools/mutation_foi_shared.py"),
        ),
        GateStage(
            "slops",
            ("uv", "run", "--locked", "python", "tools/check_slops.py"),
        ),
        GateStage(
            "benchmark-cas",
            ("uv", "run", "--locked", "python", "tools/benchmark_cas.py"),
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
    if include_heavy:
        stages += (
            GateStage(
                "gremlins",
                ("uv", "run", "--locked", "python", "tools/run_gremlins.py"),
            ),
            GateStage(
                "profile-scalene",
                ("uv", "run", "--locked", "python", "tools/profile_scalene.py"),
            ),
        )
    return stages


STAGES = build_stages()

Runner = Callable[[tuple[str, ...]], int]


def run_command(command: tuple[str, ...]) -> int:
    """Run one stage without a shell and return its process status."""
    env = dict(os.environ)
    env.setdefault("COVERAGE_CORE", "ctrace")
    env.setdefault("PYTHON_JIT", "0")
    try:
        return subprocess.run(
            command,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
            env=env,
        ).returncode
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
