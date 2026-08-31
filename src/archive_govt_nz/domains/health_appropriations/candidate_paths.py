"""Portable original-object destinations, not a publication or rights gate."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}


def original_paths(records: Sequence[Mapping[str, object]]) -> list[PurePosixPath]:
    """Return exclusive portable relative paths before any candidate writes.

    This validates destination names only. Source URLs, rights evidence, payload
    hashes, derivative provenance and release readiness need separate checks.
    """
    paths: list[PurePosixPath] = []
    seen: set[str] = set()
    for record in records:
        source_id, url = record.get("source_id"), record.get("url")
        if (
            not isinstance(source_id, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", source_id) is None
            or source_id.upper() in _RESERVED
            or not isinstance(url, str)
        ):
            message = "candidate_original_path"
            raise ValueError(message)
        suffix = PurePosixPath(urlsplit(url).path).suffix.lower()
        if re.fullmatch(r"(?:\.[a-z0-9]{1,10})?", suffix) is None:
            message = "candidate_original_path"
            raise ValueError(message)
        relative = PurePosixPath("original", source_id + suffix)
        key = relative.as_posix().casefold()
        if key in seen:
            message = "candidate_duplicate_original_path"
            raise ValueError(message)
        seen.add(key)
        paths.append(relative)
    return paths
