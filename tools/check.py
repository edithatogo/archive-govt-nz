"""Run the complete local repository assurance gate."""

import argparse

from archive_govt_nz.assurance import STAGES, build_stages, run_stages


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
    return parser.parse_args()


def main() -> int:
    """Run or describe the repository gate."""
    arguments = parse_arguments()
    if arguments.list:
        for stage in STAGES:
            print(stage.name)
        return 0
    try:
        stages = build_stages(
            pytest_workers=arguments.pytest_workers,
            pytest_distribution=arguments.pytest_distribution,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    return run_stages(stages)


if __name__ == "__main__":
    raise SystemExit(main())
