# ruff: noqa: D100,D103
from __future__ import annotations

import pytest
from typing import Any, cast

from archive_govt_nz.health_scope import deduplicate_dataset_ids, scope_manifest


def test_scope_manifest_is_https_metadata_only() -> None:
    manifest = scope_manifest(observed_at="2026-08-01T00:00:00Z")
    assert manifest["schema_version"] == "archive-govt-nz.health-scope/v1"
    assert manifest["catalogue"] == "https://catalogue.data.govt.nz"
    assert manifest["payload_capture"] == "prohibited"
    assert len(cast("list[Any]", manifest["scopes"])) == 2


def test_scope_manifest_rejects_unbounded_page_size() -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        scope_manifest(observed_at="2026-08-01T00:00:00Z", page_size=0)


def test_deduplication_is_stable_across_scopes() -> None:
    assert deduplicate_dataset_ids({"q": ["a", "b"], "group": ["b", "c"]}) == (
        "a",
        "b",
        "c",
    )


def test_deduplication_rejects_malformed_results() -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        deduplicate_dataset_ids({"q": ["a", 3]})
