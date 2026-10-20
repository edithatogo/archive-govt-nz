"""Fresh canonical inputs require originals and preserve exact observation tokens."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from tests.domains.health_appropriations.test_budget_biff8 import _fixture

from archive_govt_nz.domains.health_appropriations import budget_biff8
from archive_govt_nz.domains.health_appropriations import (
    canonical_input_recovery as recovery,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    read_verified_canonical_tables,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import source_context


def inventory(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


@pytest.fixture
def sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, list[str]]:
    cas = tmp_path / "bronze"
    cas.mkdir()
    definitions = []
    for kind in ("historical", "budget", "revenue"):
        payload = ("original-" + kind).encode()
        pin = hashlib.sha256(payload).hexdigest()
        source = cas / pin[:2] / pin
        source.parent.mkdir(exist_ok=True)
        source.write_bytes(payload)
        locator, vintage, token = (
            kind + ".xlsx",
            "fixture-" + kind,
            "2001-01-01T00:00:00Z",
        )
        definition = recovery.SourceDefinition(
            key=kind + "-2001",
            kind=kind,
            sha256=pin,
            source_locator=locator,
            source_vintage=vintage,
            observation_token=token,
            observation_id=source_context(pin, locator, vintage, token)[
                "source_observation_id"
            ],
        )
        definitions.append(definition)
    monkeypatch.setattr(recovery, "SOURCES", tuple(definitions))
    calls: list[str] = []

    def normalize(source: Path, output: Path, **kwargs: object) -> dict[str, object]:
        assert kwargs["observed_at"] == "2001-01-01T00:00:00Z"
        assert source.parent.parent == cas
        calls.append(str(kwargs["source_vintage"]))
        output.mkdir()
        (output / "MANIFEST.json").write_text(json.dumps(kwargs, sort_keys=True) + "\n")
        (output / "facts.parquet").write_bytes(source.read_bytes())
        return {}

    def persist(
        raw: Path, source: Path, pin: str, output: Path, marker: str
    ) -> dict[str, object]:
        assert raw.parent == output.parent
        assert source.parent.parent == cas
        assert hashlib.sha256((raw / "MANIFEST.json").read_bytes()).hexdigest() == pin
        output.mkdir()
        (output / marker).write_text(
            json.dumps({"raw_pin": pin}, sort_keys=True) + "\n"
        )
        (output / "facts.parquet").write_bytes((raw / "facts.parquet").read_bytes())
        if marker == "LOCAL_BUDGET.json":
            (output / "lineage_accounting.jsonl").write_text(
                '{"source_record_id":"fixture-budget-record"}\n'
            )
        return {}

    def historical(
        raw: Path, source: Path, pin: str, output: Path, *, write: bool
    ) -> dict[str, object]:
        assert write
        return persist(raw, source, pin, output, "LOCAL_CANONICAL.json")

    def budget(
        raw: Path, pin: str, source: Path, output: Path, *, dry_run: bool
    ) -> dict[str, object]:
        assert not dry_run
        return persist(raw, source, pin, output, "LOCAL_BUDGET.json")

    def revenue(
        raw: Path, pin: str, source: Path, output: Path, *, dry_run: bool
    ) -> dict[str, object]:
        assert not dry_run
        return persist(raw, source, pin, output, "LOCAL_REVENUE.json")

    for name in (
        "normalize_historical_workbook",
        "normalize_budget_workbook",
        "normalize_budget_revenue",
    ):
        monkeypatch.setattr(recovery, name, normalize)
    monkeypatch.setattr(recovery, "export_historical_canonical", historical)
    monkeypatch.setattr(recovery, "export_budget_appropriations", budget)
    monkeypatch.setattr(
        recovery.budget_revenue_canonical_export, "export_budget_revenue", revenue
    )
    return cas, calls


def test_locked_definitions_preserve_recorded_observation_identity() -> None:
    assert len(recovery.SOURCES) == 5
    for spec in recovery.SOURCES:
        assert (
            source_context(
                spec.sha256,
                spec.source_locator,
                spec.source_vintage,
                spec.observation_token,
            )["source_observation_id"]
            == spec.observation_id
        )


def test_fresh_inputs_repeat_without_retained_silver(
    tmp_path: Path, sources: tuple[Path, list[str]]
) -> None:
    cas, calls = sources
    before = inventory(cas)
    first = recovery.rebuild_canonical_inputs(cas, tmp_path / "first")
    second = recovery.rebuild_canonical_inputs(cas, tmp_path / "second")
    assert first.receipt == second.receipt
    schema = json.loads(
        (
            Path(__file__).parents[3]
            / "schemas"
            / "health-canonical-input-recovery-v1.schema.json"
        ).read_bytes()
    )
    Draft202012Validator(schema).validate(first.receipt)
    assert inventory(tmp_path / "first") == inventory(tmp_path / "second")
    assert first.receipt["retained_derivatives_consumed"] is False
    assert len(first.packages) == 3
    assert len(calls) == 6
    for value in first.packages:
        assert value.root.is_relative_to(tmp_path / "first")
        assert value.raw_root.is_relative_to(tmp_path / "first")
        assert value.original.is_relative_to(cas)
        assert (
            hashlib.sha256((value.raw_root / "MANIFEST.json").read_bytes()).hexdigest()
            == value.raw_manifest_sha256
        )
    assert before == inventory(cas)
    with pytest.raises(ValueError, match="canonical_input_recovery_contract"):
        recovery.rebuild_canonical_inputs(cas, tmp_path / "first")


@pytest.mark.parametrize("case", ["source_changed", "source_missing", "identity"])
def test_invalid_source_or_token_fails_before_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sources: tuple[Path, list[str]],
    case: str,
) -> None:
    cas, calls = sources
    spec = recovery.SOURCES[0]
    if case == "source_changed":
        (cas / spec.sha256[:2] / spec.sha256).write_bytes(b"changed")
    elif case == "source_missing":
        (cas / spec.sha256[:2] / spec.sha256).unlink()
    else:
        changed = replace(
            spec, observation_token=spec.observation_token.replace("Z", "+00:00")
        )
        monkeypatch.setattr(recovery, "SOURCES", (changed, *recovery.SOURCES[1:]))
    expected = FileNotFoundError if case == "source_missing" else ValueError
    pattern = (
        None
        if case == "source_missing"
        else r"canonical_input_recovery_contract|source_hash_mismatch"
    )
    with pytest.raises(
        expected,
        match=pattern,
    ):
        recovery.rebuild_canonical_inputs(cas, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()
    assert calls == []


def test_interruption_preserves_partial_attempt_without_completion_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sources: tuple[Path, list[str]]
) -> None:
    cas, _calls = sources
    before = inventory(cas)

    def interrupted(*_args: object, **_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(recovery, "normalize_budget_workbook", interrupted)
    output = tmp_path / "partial"
    with pytest.raises(KeyboardInterrupt):
        recovery.rebuild_canonical_inputs(cas, output)
    assert output.is_dir()
    assert list(output.rglob("LOCAL_CANONICAL.json"))
    assert not (output / "RECOVERY_INPUTS.json").exists()
    assert before == inventory(cas)


def _biff_sources(cas: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    definitions = []
    token = "2026-10-19T21:46:39.456033+00:00"
    for native, kind, key in (
        ("expenditure", "biff8_budget", "biffbudget-2019"),
        ("revenue", "biff8_revenue", "biffrevenue-2019"),
    ):
        payload, profile = _fixture(native)
        monkeypatch.setitem(budget_biff8.PROFILES, native, profile)
        path = cas / profile.source_sha256[:2] / profile.source_sha256
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(payload)
        definitions.append(
            recovery.SourceDefinition(
                key,
                kind,
                profile.source_sha256,
                profile.source_locator,
                "Budget-2019",
                token,
                source_context(
                    profile.source_sha256, profile.source_locator, "Budget-2019", token
                )["source_observation_id"],
            )
        )
    monkeypatch.setattr(recovery, "BIFF8_SOURCES", tuple(definitions), raising=False)


def test_explicit_biff_recovery_repeats_from_bronze_with_complete_witnesses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sources: tuple[Path, list[str]]
) -> None:
    cas, _calls = sources
    _biff_sources(cas, monkeypatch)
    before = inventory(cas)
    first = recovery.rebuild_canonical_inputs(
        cas, tmp_path / "first", include_biff8=True
    )
    second = recovery.rebuild_canonical_inputs(
        cas, tmp_path / "second", include_biff8=True
    )
    assert first.receipt == second.receipt
    assert inventory(tmp_path / "first") == inventory(tmp_path / "second")
    assert (
        first.receipt["schema_version"]
        == "archive-govt-nz.health-canonical-input-recovery/v2"
    )
    schema = json.loads(
        (
            Path(__file__).parents[3]
            / "schemas/health-canonical-input-recovery-v2.schema.json"
        ).read_bytes()
    )
    Draft202012Validator(schema).validate(first.receipt)
    assert len(first.packages) == 5
    for package in first.packages:
        if package.kind.startswith("biff8_"):
            tables, _receipt = read_verified_canonical_tables(package)
            fact_name = (
                "appropriation_fact"
                if package.kind == "biff8_budget"
                else "revenue_fact"
            )
            fact = tables[fact_name].to_pylist()[0]
            assert fact["value_token"] is None
            assert fact["value_basis"] == "biff8_stored_integer/v1"
            assert (
                fact["numeric_evidence_id"]
                in tables["numeric_evidence"]["numeric_evidence_id"].to_pylist()
            )
            assert package.root.is_relative_to(tmp_path / "first")
            assert package.raw_root.is_relative_to(tmp_path / "first")
    assert first.receipt["retained_derivatives_consumed"] is False
    assert before == inventory(cas)


def test_missing_last_biff_original_fails_before_any_derivative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sources: tuple[Path, list[str]]
) -> None:
    cas, calls = sources
    _biff_sources(cas, monkeypatch)
    spec = recovery.BIFF8_SOURCES[-1]
    (cas / spec.sha256[:2] / spec.sha256).unlink()
    with pytest.raises(FileNotFoundError):
        recovery.rebuild_canonical_inputs(cas, tmp_path / "missing", include_biff8=True)
    assert not (tmp_path / "missing").exists()
    assert calls == []
