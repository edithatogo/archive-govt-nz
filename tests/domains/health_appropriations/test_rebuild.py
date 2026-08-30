"""Raw-source orchestration retains originals and fails closed on evidence."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator

from archive_govt_nz.cli import health_appropriations_rebuild
from archive_govt_nz.domains.health_appropriations import rebuild
from archive_govt_nz.domains.health_appropriations.rebuild import _hash
from archive_govt_nz.object_store import ContentAddressedStore

OBSERVED = "2026-08-30T00:00:00Z"
PATHS = {
    "budget": "data/raw/b25-expenditure-data.xlsx",
    "befu": "data/raw/befu25-data-expense-tables.xlsx",
    "hyefu": "data/raw/hyefu24-data-expense-tables.xlsx",
    "historical": "data/raw/fiscaltimeseries1972-2024.xlsx",
}


def _inputs(root: Path) -> tuple[Path, Path, str]:
    store_root = root / "bronze"
    store = ContentAddressedStore(store_root)
    objects = []
    for profile, path in PATHS.items():
        receipt = store.put_bytes(profile.encode())
        objects.append({"path": path, "object_id": receipt.object_id})
    manifest = root / "donor.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-donor-manifest/v1",
                "objects": objects,
            }
        )
    )
    return manifest, store_root, hashlib.sha256(manifest.read_bytes()).hexdigest()


def _plan(root: Path) -> dict[str, Any]:
    manifest, store, digest = _inputs(root)
    return rebuild.plan_rebuild(manifest, store, digest, OBSERVED)


def _fake_adapter(source: Path, output: Path, **context: str) -> dict[str, Any]:
    profile = source.read_text()
    output.mkdir()
    names = rebuild.PROFILES[profile].outputs
    hashes = {}
    for name in names:
        (output / name).write_bytes(profile.encode())
        hashes[name] = hashlib.sha256(profile.encode()).hexdigest()
    result = {
        "schema_version": rebuild.PROFILES[profile].schema,
        "status": "passed",
        "source_object_sha256": context["expected_sha256"],
        "source_locator": context["source_locator"],
        "source_vintage": context["source_vintage"],
        "observed_at": "2026-08-30T00:00:00+00:00",
        "output_sha256": hashes,
    }
    (output / "MANIFEST.json").write_text(json.dumps(result))
    return result


def _adapters(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "normalize_budget_workbook",
        "normalize_forecast_workbook",
        "normalize_historical_workbook",
    ):
        monkeypatch.setattr(rebuild, name, _fake_adapter)


def test_preflight_is_read_only_and_pins_all_sources(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    assert set(plan["sources"]) == set(PATHS)
    assert plan["observed_at"] == "2026-08-30T00:00:00+00:00"
    assert not (tmp_path / "output").exists()


def test_run_is_deterministic_and_complete_reuse_verifies_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(tmp_path)
    _adapters(monkeypatch)
    one, two = tmp_path / "one", tmp_path / "two"
    result = rebuild.execute_rebuild(plan, tmp_path / "bronze", one)
    assert result["status"] == "passed"
    assert rebuild.execute_rebuild(plan, tmp_path / "bronze", one) == result
    assert rebuild.execute_rebuild(plan, tmp_path / "bronze", two) == result
    assert (one / "MANIFEST.json").read_bytes() == (two / "MANIFEST.json").read_bytes()
    (one / "budget" / "budget_facts.parquet").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="output_hash_mismatch"):
        rebuild.execute_rebuild(plan, tmp_path / "bronze", one)


@pytest.mark.parametrize("error_type", [ValueError, RuntimeError])
def test_failure_preserves_partial_bytes_and_requires_new_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[Exception],
) -> None:
    plan = _plan(tmp_path)

    def fail(_source: Path, output: Path, **_context: str) -> dict[str, Any]:
        output.mkdir()
        (output / "partial").write_bytes(b"retained")
        msg = "private source diagnostic must not leak"
        raise error_type(msg)

    monkeypatch.setattr(rebuild, "normalize_budget_workbook", fail)
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="stage_failed:budget"):
        rebuild.execute_rebuild(plan, tmp_path / "bronze", output)
    assert (output / "budget" / "partial").read_bytes() == b"retained"
    assert "private" not in (output / "FAILURE.json").read_text()
    assert not (output / "MANIFEST.json").exists()
    with pytest.raises(ValueError, match="incomplete_run"):
        rebuild.execute_rebuild(plan, tmp_path / "bronze", output)


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ([], "invalid_manifest"),
        ({"schema_version": "wrong"}, "invalid_donor_schema"),
        (
            {"schema_version": "archive-govt-nz.health-donor-manifest/v1"},
            "invalid_donor_objects",
        ),
        (
            {
                "schema_version": "archive-govt-nz.health-donor-manifest/v1",
                "objects": [1],
            },
            "invalid_donor_objects",
        ),
        (
            {
                "schema_version": "archive-govt-nz.health-donor-manifest/v1",
                "objects": [],
            },
            "missing_or_ambiguous_source",
        ),
    ],
)
def test_invalid_donor(tmp_path: Path, value: object, reason: str) -> None:
    manifest, store, _ = _inputs(tmp_path)
    manifest.write_text(json.dumps(value))
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    with pytest.raises((ValueError, TypeError), match=reason):
        rebuild.plan_rebuild(manifest, store, digest, OBSERVED)


@pytest.mark.parametrize("change", ["duplicate", "invalid_object_id"])
def test_ambiguous_donor(tmp_path: Path, change: str) -> None:
    manifest, store, _ = _inputs(tmp_path)
    donor = json.loads(manifest.read_bytes())
    if change == "duplicate":
        donor["objects"].append(donor["objects"][0])
    else:
        donor["objects"][0]["object_id"] = None
    manifest.write_text(json.dumps(donor))
    with pytest.raises(ValueError, match="missing_or_ambiguous_source"):
        rebuild.plan_rebuild(
            manifest, store, hashlib.sha256(manifest.read_bytes()).hexdigest(), OBSERVED
        )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("extra", True),
        ("schema_version", "wrong"),
        ("sources", []),
        ("sources", {}),
    ],
)
def test_invalid_plan(tmp_path: Path, key: str, value: object) -> None:
    plan = _plan(tmp_path)
    plan[key] = value
    with pytest.raises(ValueError, match="invalid_rebuild_plan"):
        rebuild.execute_rebuild(plan, tmp_path / "bronze", tmp_path / "run")


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("all", None),
        ("extra", True),
        ("locator", "../outside"),
        ("vintage", "invented"),
        ("sha256", None),
        ("sha256", "bad"),
        ("object_id", "sha256:" + "0" * 64),
    ],
)
def test_invalid_source_plan(tmp_path: Path, key: str, value: object) -> None:
    plan = _plan(tmp_path)
    if key == "all":
        plan["sources"]["budget"] = value
    else:
        plan["sources"]["budget"][key] = value
    with pytest.raises(ValueError, match="invalid_rebuild_source"):
        rebuild.execute_rebuild(plan, tmp_path / "bronze", tmp_path / "run")


@pytest.mark.parametrize("target", ["run", "stage", "manifest", "output"])
def test_symlinks_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    plan = _plan(tmp_path)
    _adapters(monkeypatch)
    root = tmp_path / "run"
    rebuild.execute_rebuild(plan, tmp_path / "bronze", root)
    path = {
        "run": root,
        "stage": root / "budget",
        "manifest": root / "PLAN.json",
        "output": root / "budget" / "budget_facts.parquet",
    }[target]
    moved = tmp_path / "moved"
    path.rename(moved)
    path.symlink_to(moved, target_is_directory=moved.is_dir())
    with pytest.raises(ValueError, match="invalid_"):
        rebuild.execute_rebuild(plan, tmp_path / "bronze", root)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("plan", "run_plan_mismatch"),
        ("run", "run_manifest_mismatch"),
        ("run_extra", "unexpected_run_files"),
        ("stage_extra", "unexpected_stage_files"),
        ("stage_missing", "unexpected_stage_files"),
        ("stage_status", "invalid_stage_receipt"),
        ("stage_hashes", "invalid_stage_outputs"),
        ("stage_names", "invalid_stage_outputs"),
        ("oversize", "manifest_byte_limit"),
    ],
)
def test_invalid_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str, reason: str
) -> None:
    plan = _plan(tmp_path)
    _adapters(monkeypatch)
    root = tmp_path / "run"
    rebuild.execute_rebuild(plan, tmp_path / "bronze", root)
    if change == "plan":
        (root / "PLAN.json").write_text("{}")
    elif change == "run":
        (root / "MANIFEST.json").write_text("{}")
    elif change.endswith("extra"):
        directory = root if change == "run_extra" else root / "budget"
        (directory / "unexpected").write_text("retained")
    elif change == "stage_missing":
        (root / "budget" / "budget_facts.parquet").unlink()
    elif change == "oversize":
        monkeypatch.setattr(rebuild, "_MAX_MANIFEST_BYTES", 1)
    else:
        manifest = root / "budget" / "MANIFEST.json"
        receipt = json.loads(manifest.read_bytes())
        if change == "stage_status":
            receipt["status"] = "partial"
        else:
            receipt["output_sha256"] = [] if change == "stage_hashes" else {}
        manifest.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match=reason):
        rebuild.execute_rebuild(plan, tmp_path / "bronze", root)


def test_output_cannot_write_bronze(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    with pytest.raises(ValueError, match="output_inside_bronze_store"):
        rebuild.execute_rebuild(plan, tmp_path / "bronze", tmp_path / "bronze" / "new")
    assert not (tmp_path / "bronze" / "new").exists()


def test_hash_rejects_nonfile(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid_output_file"):
        _hash(tmp_path)


def test_rebuild_cli_defaults_to_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:

    manifest, store, digest = _inputs(tmp_path)
    args = {
        "donor_manifest": manifest,
        "store_root": store,
        "manifest_sha256": digest,
        "observed_at": OBSERVED,
        "output_dir": tmp_path / "run",
    }
    assert health_appropriations_rebuild(**args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "planned"
    assert not (tmp_path / "run").exists()
    _adapters(monkeypatch)
    assert health_appropriations_rebuild(**args, dry_run=False) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "passed"
    manifest.write_text("private malformed source")
    assert health_appropriations_rebuild(**args) == 2
    assert "private" not in capsys.readouterr().out


def test_duplicate_manifest_keys_rejected(tmp_path: Path) -> None:
    manifest, store, _ = _inputs(tmp_path)
    payload = manifest.read_text().replace('"objects":', '"objects": [], "objects":')
    manifest.write_text(payload)
    with pytest.raises(ValueError, match="duplicate_manifest_key"):
        rebuild.plan_rebuild(
            manifest, store, hashlib.sha256(manifest.read_bytes()).hexdigest(), OBSERVED
        )


def test_completion_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _plan(tmp_path)
    _adapters(monkeypatch)
    receipt = rebuild.execute_rebuild(plan, tmp_path / "bronze", tmp_path / "run")
    schema = json.loads(Path("schemas/health-raw-rebuild-v1.schema.json").read_bytes())
    Draft202012Validator(schema).validate(receipt)
    receipt["stages"]["budget"] = "invalid"
    assert list(Draft202012Validator(schema).iter_errors(receipt))


@settings(max_examples=20, deadline=None)
@given(st.binary(min_size=1, max_size=64).filter(lambda payload: payload != b"budget"))
def test_any_changed_derivative_fails_fixity(payload: bytes) -> None:
    with (
        tempfile.TemporaryDirectory() as directory,
        pytest.MonkeyPatch.context() as patch,
    ):
        root = Path(directory)
        plan = _plan(root)
        _adapters(patch)
        output = root / "run"
        rebuild.execute_rebuild(plan, root / "bronze", output)
        (output / "budget" / "budget_facts.parquet").write_bytes(payload)
        with pytest.raises(ValueError, match="output_hash_mismatch"):
            rebuild.execute_rebuild(plan, root / "bronze", output)
