"""Tests for the read-only CKAN licence evidence probe."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "fetch_health_dataset_licences.py"
_SPEC = importlib.util.spec_from_file_location(
    "fetch_health_dataset_licences", _TOOL_PATH
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

load_dataset_ids = _MODULE.load_dataset_ids
extract_licence_id = _MODULE.extract_licence_id
preserve_raw_response = _MODULE.preserve_raw_response
build_map_offline = _MODULE.build_map_offline


def _envelope(licence_id: str | None, field: str = "license_id") -> bytes:
    result: dict[str, object] = {"id": "ds-1", "title": "T"}
    if licence_id is not None:
        result[field] = licence_id
    return json.dumps({"success": True, "result": result}).encode("utf-8")


def _snapshot(tmp_path: Path, dataset_ids: list[str]) -> Path:
    snap = tmp_path / "snap.json"
    resources = [{"dataset_id": d, "resource_id": f"r-{d}"} for d in dataset_ids]
    snap.write_text(json.dumps({"resources": resources}), encoding="utf-8")
    return snap


class TestLoadDatasetIds:
    """Snapshot dataset-ID extraction coverage."""

    def test_distinct_first_seen_order(self, tmp_path: Path) -> None:
        """Duplicate and empty dataset IDs collapse to distinct ordered IDs."""
        """Duplicate and empty dataset IDs collapse to distinct ordered IDs."""
        snap = tmp_path / "snap.json"
        snap.write_text(
            json.dumps(
                {
                    "resources": [
                        {"dataset_id": "b"},
                        {"dataset_id": "a"},
                        {"dataset_id": "b"},
                        {"dataset_id": ""},
                    ]
                }
            ),
            encoding="utf-8",
        )
        assert load_dataset_ids(snap) == ["b", "a"]


class TestExtractLicenceId:
    """Envelope licence extraction coverage."""

    def test_extracts_licence(self) -> None:
        """CKAN's license_id field is extracted from valid envelopes."""
        assert extract_licence_id(_envelope("cc-by-4.0")) == "cc-by-4.0"

    def test_licence_spelling_fallback(self) -> None:
        """The licence_id spelling is accepted defensively."""
        assert extract_licence_id(_envelope("ogl-nz", field="licence_id")) == "ogl-nz"

    def test_missing_licence_returns_empty(self) -> None:
        """A present-but-null licence yields an empty string."""
        assert extract_licence_id(_envelope(None)) == ""

    def test_missing_result_raises(self) -> None:
        """An envelope without a result object fails closed."""
        body = json.dumps({"success": True}).encode("utf-8")
        with pytest.raises(TypeError, match="result"):
            extract_licence_id(body)


class TestPreserveRawResponse:
    """Raw-response preservation coverage."""

    def test_writes_body_and_sidecar(self, tmp_path: Path) -> None:
        """Raw body and checksum sidecar are both persisted."""
        raw_dir = tmp_path / "raw"
        body = b"{}"
        preserve_raw_response(raw_dir, "ds-1", body, "f" * 64)
        assert (raw_dir / "ds-1.json").read_bytes() == body
        sidecar = (raw_dir / "ds-1.sha256").read_text(encoding="utf-8")
        assert "f" * 64 in sidecar


class TestBuildMapOffline:
    """Offline replay and fail-closed coverage."""

    def test_rebuilds_map_from_preserved_responses(self, tmp_path: Path) -> None:
        """Preserved responses rebuild the full licence map."""
        raw_dir = tmp_path / "raw"
        preserve_raw_response(raw_dir, "ds-1", _envelope("cc-by-4.0"), "a" * 64)
        preserve_raw_response(raw_dir, "ds-2", _envelope("ogl-nz"), "b" * 64)

        licence_map, records = build_map_offline(["ds-1", "ds-2"], raw_dir)
        assert licence_map == {"ds-1": "cc-by-4.0", "ds-2": "ogl-nz"}
        assert all(r["status"] == "observed" for r in records)

    def test_missing_raw_fails_closed(self, tmp_path: Path) -> None:
        """Missing raw responses are reported without mapping."""
        licence_map, records = build_map_offline(["ds-x"], tmp_path / "raw")
        assert licence_map == {}
        assert records[0]["status"] == "missing-raw-response"

    def test_unparseable_raw_fails_closed(self, tmp_path: Path) -> None:
        """Unparseable raw responses are reported without mapping."""
        raw_dir = tmp_path / "raw"
        preserve_raw_response(raw_dir, "ds-1", b"not-json{", "c" * 64)
        licence_map, records = build_map_offline(["ds-1"], raw_dir)
        assert licence_map == {}
        assert records[0]["status"] == "unparseable-response"

    def test_null_licence_observed_but_not_mapped(self, tmp_path: Path) -> None:
        """A present-but-empty licence is observed honestly without mapping."""
        raw_dir = tmp_path / "raw"
        preserve_raw_response(raw_dir, "ds-1", _envelope(None), "d" * 64)
        licence_map, records = build_map_offline(["ds-1"], raw_dir)
        assert licence_map == {}
        assert records[0]["status"] == "observed"
        assert records[0]["licence_id"] == ""
