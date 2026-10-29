"""Run the PR or release assurance profile, or selected named stages."""

import argparse

from archive_govt_nz.assurance import build_stages, run_stages


def parse_arguments() -> argparse.Namespace:
    """Parse the gate's non-interactive command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=("pr", "release"),
        default="pr",
        help="pr keeps full tests/security; release adds mutations and benchmarks",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list stage names without running them",
    )
    parser.add_argument(
        "--pytest-workers",
        metavar="COUNT",
        help="run pytest through xdist with auto, logical, or a positive count",
    )
    parser.add_argument(
        "--pytest-distribution",
        choices=("load", "loadscope", "loadfile", "worksteal"),
        default="loadscope",
        help="xdist scheduling policy (default: loadscope)",
    )
    parser.add_argument(
        "--pytest-diagnostics",
        action="store_true",
        help="emit named test progress, durations and build/pytest-results.xml",
    )
    parser.add_argument(
        "--include-heavy",
        action="store_true",
        help="append bounded pytest-gremlins and Scalene evidence lanes",
    )
    parser.add_argument(
        "--stage",
        action="append",
        metavar="NAME",
        help="run only this named gate; repeat to select multiple gates",
    )
    return parser.parse_args()


def main() -> int:
    """Run or describe the repository gate."""
    arguments = parse_arguments()
    try:
        stages = build_stages(
            pytest_workers=arguments.pytest_workers,
            pytest_distribution=arguments.pytest_distribution,
            pytest_diagnostics=arguments.pytest_diagnostics,
            include_heavy=arguments.include_heavy,
            profile="release" if arguments.stage else arguments.profile,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if arguments.stage:
        available = {stage.name for stage in stages}
        unknown = sorted(set(arguments.stage) - available)
        if unknown:
            names = ", ".join(unknown)
            message = f"unknown assurance stage(s): {names}"
            raise SystemExit(message)
        selected = set(arguments.stage)
        stages = tuple(stage for stage in stages if stage.name in selected)
    if arguments.list:
        for stage in stages:
            print(stage.name)
        return 0
    return run_stages(stages)


if __name__ == "__main__":
    raise SystemExit(main())
