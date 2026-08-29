"""Run the complete local repository assurance gate."""

import argparse

from archive_govt_nz.assurance import build_stages, run_stages


def parse_arguments() -> argparse.Namespace:
    """Parse the gate's non-interactive command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
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
        "--include-heavy",
        action="store_true",
        help="append bounded pytest-gremlins and Scalene evidence lanes",
    )
    return parser.parse_args()


def main() -> int:
    """Run or describe the repository gate."""
    arguments = parse_arguments()
    try:
        stages = build_stages(
            pytest_workers=arguments.pytest_workers,
            pytest_distribution=arguments.pytest_distribution,
            include_heavy=arguments.include_heavy,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if arguments.list:
        for stage in stages:
            print(stage.name)
        return 0
    return run_stages(stages)


if __name__ == "__main__":
    raise SystemExit(main())
