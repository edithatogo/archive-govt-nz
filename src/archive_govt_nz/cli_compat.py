"""Compatibility CLI wrappers for legacy donor command names."""

from __future__ import annotations

import sys

from archive_govt_nz.cli import main


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


def compat_nzlc_main() -> None:
    """Execute nzlc CLI with deprecation warning."""
    sys.stderr.write(
        "DEPRECATION NOTICE: `nzlc` is deprecated and will be removed "
        "in v1.0. Please use `archive-govt-nz` instead.\n"
    )
    main()
