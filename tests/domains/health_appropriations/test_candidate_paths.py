"""Portable candidate destinations must be validated before any output exists."""

from __future__ import annotations

import importlib.util
import json
import string
import sys
from pathlib import Path, PurePosixPath

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations.candidate_paths import (
    original_paths,
)

_SPEC = importlib.util.spec_from_file_location(
    "build_health_candidate",
    Path(__file__).parents[3] / "tools" / "build_health_candidate.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
build_health_candidate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(build_health_candidate)


def test_original_paths_preserve_safe_names_and_normalize_suffix() -> None:
    assert original_paths(
        [
            {
                "source_id": "budget_2026-001",
                "url": "https://example.test/B26.XLSX?q=1",
            },
            {"source_id": "pharmac-001", "url": "https://example.test/budget"},
        ]
    ) == [
        PurePosixPath("original/budget_2026-001.xlsx"),
        PurePosixPath("original/pharmac-001"),
    ]


@pytest.mark.parametrize(
    "source_id",
    [
        "../escape",
        "../../escape",
        "/absolute",
        "a/b",
        "a\\b",
        ".",
        "..",
        "",
        "a b",
        "a.",
        "a:",
        "CON",
        "con",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "LPT9",
        "a" * 129,
        "é",
        None,
        1,
    ],
)
def test_unsafe_source_ids_rejected(source_id: object) -> None:
    with pytest.raises(ValueError, match="candidate_original_path"):
        original_paths([{"source_id": source_id, "url": "https://example.test/a.pdf"}])


@pytest.mark.parametrize(
    "url",
    [
        None,
        1,
        "https://example.test/a.bad%20suffix",
        "https://example.test/a.pdf:stream",
        "https://example.test/a.bad\\tail",
        "https://example.test/a.bad\x00tail",
        "https://example.test/a.",
        "https://example.test/a.abcdefghijk",
    ],
)
def test_unsafe_suffix_or_url_type_rejected(url: object) -> None:
    with pytest.raises(ValueError, match="candidate_original_path"):
        original_paths([{"source_id": "safe", "url": url}])


def test_portable_collision_rejected() -> None:
    with pytest.raises(ValueError, match="candidate_duplicate_original_path"):
        original_paths(
            [
                {"source_id": "Same", "url": "https://example.test/a.PDF"},
                {"source_id": "same", "url": "https://example.test/b.pdf"},
            ]
        )


def test_identifier_length_boundary_and_different_extensions() -> None:
    name = "a" * 128
    assert original_paths(
        [
            {"source_id": name, "url": "https://example.test/a.pdf"},
            {"source_id": name, "url": "https://example.test/a.csv"},
        ]
    ) == [
        PurePosixPath("original", name + ".pdf"),
        PurePosixPath("original", name + ".csv"),
    ]
    assert original_paths(
        [{"source_id": "safe", "url": "https://example.test/a.abcdefghij"}]
    ) == [PurePosixPath("original/safe.abcdefghij")]


@pytest.mark.parametrize(
    "identifiers", [["../../escape"], ["safe", "../../escape"], ["Same", "same"]]
)
def test_builder_rejects_unsafe_paths_before_creating_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, identifiers: list[str]
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("original preflight must precede store access and copying")

    monkeypatch.setattr(build_health_candidate, "ContentAddressedStore", forbidden)
    monkeypatch.setattr(build_health_candidate, "_copy", forbidden)
    capture = tmp_path / "capture.json"
    capture.write_text(
        json.dumps(
            {
                "results": [
                    {"source_id": value, "url": "https://example.test/a.pdf"}
                    for value in identifiers
                ]
            }
        )
    )
    output = tmp_path / "candidate"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_health_candidate",
            "--capture-manifest",
            str(capture),
            "--store-root",
            str(tmp_path / "absent-store"),
            "--silver-dir",
            str(tmp_path / "silver"),
            "--gold-dir",
            str(tmp_path / "gold"),
            "--source-census",
            str(tmp_path / "census"),
            "--output-dir",
            str(output),
        ],
    )
    with pytest.raises(
        ValueError, match=r"candidate_(original_path|duplicate_original_path)"
    ):
        build_health_candidate.main()
    assert not output.exists()
    assert not (tmp_path / "escape.pdf").exists()


@settings(max_examples=40)
@given(
    st.text(
        alphabet=string.ascii_letters + string.digits + "_-",
        max_size=100,
    )
)
def test_generated_names_remain_one_portable_component(value: str) -> None:
    name = "source_" + value
    paths = original_paths([{"source_id": name, "url": "https://example.test/a.csv"}])
    assert paths == [PurePosixPath("original", name + ".csv")]
    assert paths[0].parts == ("original", name + ".csv")
