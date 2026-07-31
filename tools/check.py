"""Run the complete local repository assurance gate."""

import argparse

from archive_govt_nz.assurance import STAGES, run_stages


def parse_arguments() -> argparse.Namespace:
    """Parse the gate's non-interactive command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list",
        action="store_true",
        help="list stage names without running them",
    )
    return parser.parse_args()


def main() -> int:
    """Run or describe the repository gate."""
    arguments = parse_arguments()
    if arguments.list:
        for stage in STAGES:
            print(stage.name)
        return 0
    return run_stages()


if __name__ == "__main__":
    raise SystemExit(main())
