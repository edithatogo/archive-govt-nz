# SPDX-License-Identifier: Apache-2.0
"""Load the development-only rights reviewer independently of pytest's entrypoint."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "health_rights_review_tool",
    Path(__file__).parents[1] / "tools/health_rights_review.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
RIGHTS_REVIEW = importlib.util.module_from_spec(_SPEC)
# Dataclasses resolve postponed annotations through their registered module.
sys.modules[_SPEC.name] = RIGHTS_REVIEW
_SPEC.loader.exec_module(RIGHTS_REVIEW)
