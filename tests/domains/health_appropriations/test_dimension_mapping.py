"""Synthetic mapping assertions never establish factual equivalence."""

from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st
from tests.domains.health_appropriations.test_budget_classification import inputs

from archive_govt_nz.domains.health_appropriations import dimension_mapping as dm
from archive_govt_nz.domains.health_appropriations.budget_classification import (
    project_budget_classification,
)
from archive_govt_nz.domains.health_appropriations.dimension_mapping import (
    Dimension,
    Mapping,
    compare_mappings,
    dimension_key,
    validate_mappings,
)


def sample() -> Mapping:
    """Return an unresolved synthetic label."""
    return Mapping(Dimension("vote", "synthetic/v1", "Example"), "v1", "m1")


def test_unresolved_and_stability() -> None:
    item = sample()
    assert validate_mappings((item,)) == (item,)
    assert dimension_key(item.dimension) == dimension_key(replace(item).dimension)
    assert dimension_key(item.dimension) != dimension_key(
        replace(item.dimension, label="example")
    )
    assert compare_mappings((item,), (item,)) == ()


def test_evidence_required_and_conflict() -> None:
    item = sample()
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((replace(item, target="synthetic:1"),))
    mapped = replace(
        item, target="synthetic:1", method="asserted", evidence=("a" * 64,)
    )
    assert validate_mappings((mapped,)) == (mapped,)
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((mapped, replace(mapped, target="synthetic:2")))


def test_periods_and_drift() -> None:
    item = sample()
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        dimension_key(
            replace(item.dimension, start=date(2026, 1, 2), end=date(2026, 1, 1))
        )
    newer = replace(item, vintage="v2", version="m2")
    changes = compare_mappings((item,), (newer,))
    assert len(changes) == 1
    assert changes[0].changes == ("vintage", "version")


@pytest.mark.parametrize("kind", sorted(dm.KINDS))
def test_all_kinds(kind: str) -> None:
    assert dimension_key(replace(sample().dimension, kind=kind))


def test_key_components_and_exact_bounds() -> None:
    original = sample().dimension
    period = "2026"
    variants = (
        original,
        replace(original, kind="unit"),
        replace(original, scheme="synthetic/v2"),
        replace(original, label="Another"),
        replace(original, start=date(2026, 1, 1)),
        replace(original, end=date(2026, 1, 1)),
        replace(original, period_token=period),
    )
    assert len({dimension_key(value) for value in variants}) == len(variants)
    assert dimension_key(replace(original, label="x" * dm.MAX_TEXT))
    assert dimension_key(
        replace(original, start=date(2026, 1, 1), end=date(2026, 1, 1))
    )
    evidence = tuple(f"{i:064x}" for i in range(dm.MAX_EVIDENCE))
    assert validate_mappings((replace(mapped(), evidence=evidence),))


@pytest.mark.parametrize("field", ["vintage", "version"])
def test_overlapping_revisions_are_not_selected(field: str) -> None:
    item = sample()
    other = replace(
        item,
        dimension=replace(item.dimension, start=date(2026, 1, 1)),
        **{field: "other"},
    )
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((item, other))


def test_duplicate_unresolved_rejected() -> None:
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((sample(), sample()))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("kind", "unknown"),
        ("kind", []),
        ("scheme", ""),
        ("label", " "),
        ("label", "x" * 4097),
        ("start", "2026-01-01"),
        ("end", False),
        ("period_token", ""),
    ],
)
def test_bad_dimension(field: str, value: object) -> None:
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        dimension_key(replace(sample().dimension, **{field: value}))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("vintage", ""),
        ("version", None),
        ("target", ""),
        ("method", "guess"),
        ("evidence", []),
        ("evidence", ("a" * 64,)),
        ("evidence", ("bad",)),
        ("evidence", (False,)),
        ("evidence", ("a" * 64,) * 33),
    ],
)
def test_bad_mapping(field: str, value: object) -> None:
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((replace(sample(), **{field: value}),))


def mapped() -> Mapping:
    """Return an evidence-reference-only synthetic assertion."""
    return replace(sample(), target="test:1", method="fixture", evidence=("a" * 64,))


@pytest.mark.parametrize("evidence", [("b" * 64, "a" * 64), ("a" * 64,) * 2, ()])
def test_evidence_order_uniqueness_and_presence(evidence: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((replace(mapped(), evidence=evidence),))


@pytest.mark.parametrize(
    "evidence",
    [("bad",), ("A" * 64,), ("a" * 63,), tuple(f"{i:064x}" for i in range(33))],
)
def test_mapped_evidence_format_and_bound(evidence: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((replace(mapped(), evidence=evidence),))


def test_overlap_and_inclusive_endpoints() -> None:
    first = replace(
        mapped(), dimension=replace(sample().dimension, end=date(2026, 1, 1))
    )
    second = replace(
        mapped(), dimension=replace(sample().dimension, start=date(2026, 1, 1))
    )
    assert len(validate_mappings((first, second))) == 2
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((first, replace(second, target="test:2")))
    later = replace(
        second,
        target="test:2",
        dimension=replace(second.dimension, start=date(2026, 1, 2)),
    )
    assert len(validate_mappings((first, later))) == 2
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((sample(), later))


def test_limits_and_runtime_types(monkeypatch: pytest.MonkeyPatch) -> None:
    for value in (None, (), "bad"):
        with pytest.raises(ValueError, match="dimension_mapping_contract"):
            dimension_key(cast("Dimension", value))
        with pytest.raises(ValueError, match="dimension_mapping_contract"):
            validate_mappings((cast("Mapping", value),))
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings(cast("tuple[Mapping, ...]", []))
    monkeypatch.setattr(dm, "MAX_ROWS", 1)
    assert validate_mappings((sample(),))
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        validate_mappings((sample(), mapped()))


def test_drift_and_identity_changes() -> None:
    item = mapped()
    updated = replace(item, target="test:2", method="fixture2", evidence=("b" * 64,))
    assert compare_mappings((item,), (updated,))[0].changes == (
        "target",
        "method",
        "evidence",
    )
    assert compare_mappings((), (item,))[0].changes == ("added",)
    assert compare_mappings((item,), ())[0].changes == ("removed",)
    period = "2026"
    moved = replace(item, dimension=replace(item.dimension, period_token=period))
    assert {row.changes for row in compare_mappings((item,), (moved,))} == {
        ("added",),
        ("removed",),
    }


@given(
    st.permutations(
        tuple(
            replace(sample(), dimension=replace(sample().dimension, label=str(i)))
            for i in range(4)
        )
    )
)
def test_order_independent(rows: tuple[Mapping, ...]) -> None:
    result = validate_mappings(tuple(rows))
    assert result == validate_mappings(tuple(reversed(rows)))
    assert compare_mappings(result, tuple(reversed(rows))) == ()


def test_existing_projection_bridge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    table = project_budget_classification(**inputs(tmp_path)).tables[
        "classification_dimension"
    ]
    before = table.to_pylist()
    result = dm.unresolved_classification_dimensions(table)
    assert len(result) == 1
    assert result[0].label == "Health"
    assert table.to_pylist() == before
    assert dm.unresolved_classification_dimensions(table.slice(0, 0)) == ()
    monkeypatch.setattr(dm, "MAX_ROWS", 1)
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        dm.unresolved_classification_dimensions(table)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mapping_state", "mapped"),
        ("normalized_identifier", "test:1"),
        ("scheme", "other"),
        ("scheme_version", "v2"),
    ],
)
def test_bridge_rejects_unproven_scope(tmp_path: Path, field: str, value: str) -> None:
    table = project_budget_classification(**inputs(tmp_path)).tables[
        "classification_dimension"
    ]
    rows = table.to_pylist()
    rows[0][field] = value
    with pytest.raises(ValueError, match="dimension_mapping_contract"):
        dm.unresolved_classification_dimensions(
            type(table).from_pylist(rows, schema=table.schema)
        )
