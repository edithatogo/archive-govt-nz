"""Compatibility CLI wrappers for legacy donor command names."""

from __future__ import annotations

import sys
from typing import Literal

from archive_govt_nz.cli import legislation, main


def compat_sm_govt_nz_main() -> None:
    """Execute sm-govt-nz CLI with deprecation warning."""
    sys.stderr.write(
        "DEPRECATION NOTICE: `sm-govt-nz` is deprecated and will be removed "
        "in v1.0. Please use `archive-govt-nz` instead.\n"
    )
    main()


def compat_nz_govt_social_main() -> None:
    """Execute nz-govt-social CLI with deprecation warning."""
    sys.stderr.write(
        "DEPRECATION NOTICE: `nz-govt-social` is deprecated and will be "
        "removed in v1.0. Please use `archive-govt-nz` instead.\n"
    )
    main()


def compat_nzlc_main() -> int:
    """Execute nzlc CLI with legacy argument mapping and deprecation notice."""
    sys.stderr.write(
        "DEPRECATION NOTICE: `nzlc` is deprecated and will be removed "
        "in v1.0. Please use `archive-govt-nz legislation` instead.\n"
    )

    args = sys.argv[1:]
    if not args:
        return legislation(action="status", format="text")

    cmd = args[0].lower().replace("_", "-")
    format_val: Literal["text", "json"] = (
        "json" if "--json" in args or "-j" in args else "text"
    )

    mapping: dict[
        str,
        Literal[
            "doctor",
            "discover",
            "sync",
            "validate",
            "manifest",
            "coverage",
            "changes",
            "status",
            "replay",
            "publication-plan",
            "publication-verify",
        ],
    ] = {
        "doctor": "doctor",
        "discover": "discover",
        "sync": "sync",
        "validate": "validate",
        "manifest": "manifest",
        "coverage": "coverage",
        "coverage-report": "coverage",
        "changes": "changes",
        "feed-change-detect": "changes",
        "status": "status",
        "replay": "replay",
        "publication-plan": "publication-plan",
        "hf-upload": "publication-plan",
        "zenodo-upload": "publication-plan",
        "publication-verify": "publication-verify",
    }

    if cmd in mapping:
        return legislation(action=mapping[cmd], format=format_val)

    sys.stderr.write(f"Unknown nzlc action: {cmd}\n")
    return 5
