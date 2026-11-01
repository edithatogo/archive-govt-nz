"""Resume always creates a separate attempt; synthetic originals stay immutable."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.domains.health_appropriations.test_budget import (
    ROW,
)
from tests.domains.health_appropriations.test_budget import (
    _source as budget_source,
)
from tests.domains.health_appropriations.test_forecast import _source as forecast_source
from tests.domains.health_appropriations.test_historical import (
    _source as historical_source,
)

from archive_govt_nz.domains.health_appropriations import rebuild, rebuild_resume
from archive_govt_nz.domains.health_appropriations import resume_execution as module
from archive_govt_nz.object_store import ContentAddressedStore


def _json(path: Path, value: object) -> str:
    payload = json.dumps(value, sort_keys=True).encode()
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _files(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


def _inputs(root: Path, amount: int = 123) -> dict[str, Any]:
    source = root / "synthetic.xlsx"
    store = ContentAddressedStore(root / "bronze")
    objects = []
    for name, profile in rebuild.PROFILES.items():
        if name == "budget":
            row = list(ROW)
            row[5] = amount
            budget_source(source, [row])
        elif name == "historical":
            source = historical_source(root)
        else:
            forecast_source(source, name)
        receipt = store.put_bytes(source.read_bytes())
        objects.append(
            {"path": "data/raw/" + profile.filename, "object_id": receipt.object_id}
        )
    donor = root / "donor.json"
    pin = _json(
        donor,
        {
            "schema_version": "archive-govt-nz.health-donor-manifest/v1",
            "objects": objects,
        },
    )
    old = root / "previous"
    old.mkdir()
    plan = rebuild.plan_rebuild(donor, root / "bronze", pin, "2026-08-30T00:00:00Z")
    kwargs = {
        "donor_manifest": donor,
        "donor_manifest_sha256": pin,
        "previous_run": old,
        "previous_plan_sha256": _json(old / "PLAN.json", plan),
        "store_root": root / "bronze",
        "observed_at": "2026-08-30T00:00:00Z",
        "stage_manifest_sha256": {},
    }
    path = root / "resume.json"
    return dict(
        **kwargs,
        resume_plan=path,
        resume_plan_sha256=_json(path, rebuild_resume.plan_resume(**kwargs)),
    )


def test_default_dry_run_has_no_state(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    before = _files(tmp_path)
    result = module.execute_resume(**inputs, output_dir=tmp_path / "attempt")
    assert result["status"] == "planned"
    assert result["execution"] == "not_performed"
    assert _files(tmp_path) == before


def test_new_attempt_rebuild_and_envelope_verify(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    before = _files(tmp_path)
    attempt = tmp_path / "attempt"
    result = module.execute_resume(**inputs, output_dir=attempt, dry_run=False)
    assert result["status"] == "passed"
    pin = hashlib.sha256((attempt / "RESUME_RECEIPT.json").read_bytes()).hexdigest()
    assert module.verify_resume(attempt, inputs["store_root"], pin) == result
    assert {k: (tmp_path / k).read_bytes() for k in before} == before
    assert {p.name for p in attempt.iterdir()} == {
        "RESUME_PLAN.json",
        "run",
        "RESUME_RECEIPT.json",
    }


@pytest.mark.parametrize("value", [None, 0, 1, "false", [], {}])
def test_nonbool_dry_flag_rejected_without_state(tmp_path: Path, value: object) -> None:
    inputs = _inputs(tmp_path)
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=tmp_path / "attempt", dry_run=value)  # pyright: ignore[reportArgumentType] - malformed public input.
    assert not (tmp_path / "attempt").exists()


def _replan(inputs: dict[str, Any]) -> None:
    kwargs = {
        k: v
        for k, v in inputs.items()
        if k not in {"resume_plan", "resume_plan_sha256"}
    }
    inputs["resume_plan_sha256"] = _json(
        inputs["resume_plan"], rebuild_resume.plan_resume(**kwargs)
    )


@pytest.mark.parametrize("mask", range(16))
def test_every_action_combination_matches_fresh_bytes(
    tmp_path: Path, mask: int
) -> None:
    inputs = _inputs(tmp_path)
    plan = json.loads((inputs["previous_run"] / "PLAN.json").read_bytes())
    fresh = tmp_path / "fresh"
    rebuild.execute_rebuild(plan, inputs["store_root"], fresh)
    for index, name in enumerate(rebuild.PROFILES):
        if mask & (1 << index):
            shutil.copytree(fresh / name, inputs["previous_run"] / name)
            inputs["stage_manifest_sha256"][name] = hashlib.sha256(
                (fresh / name / "MANIFEST.json").read_bytes()
            ).hexdigest()
    _replan(inputs)
    before = _files(tmp_path)
    one, two = tmp_path / "one", tmp_path / "two"
    result = module.execute_resume(**inputs, output_dir=one, dry_run=False)
    if mask == 5:
        assert module.execute_resume(**inputs, output_dir=two, dry_run=False) == result
        assert _files(one) == _files(two)
    assert _files(one / "run") == _files(fresh)
    assert (
        sum(action == "reuse_verified" for action in result["actions"].values())
        == mask.bit_count()
    )
    assert {k: (tmp_path / k).read_bytes() for k in before} == before


@pytest.mark.parametrize(
    "target",
    ["existing", "file", "bronze", "previous", "missing_parent", "symlink", "dangling"],
)
def test_output_collisions_preserve_inputs(tmp_path: Path, target: str) -> None:
    inputs = _inputs(tmp_path)
    output = tmp_path / "out"
    if target == "existing":
        output.mkdir()
    elif target == "file":
        output.write_bytes(b"keep")
    elif target in {"bronze", "previous"}:
        output = tmp_path / target / "new"
    elif target == "missing_parent":
        output = tmp_path / "missing" / "new"
    else:
        output.symlink_to(
            tmp_path / ("previous" if target == "symlink" else "absent"),
            target_is_directory=True,
        )
    before = _files(tmp_path)
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=output, dry_run=False)
    assert _files(tmp_path) == before


@pytest.mark.parametrize(
    "error", [ValueError("sensitive"), KeyboardInterrupt("private"), SystemExit(4)]
)
def test_adapter_error_preserves_partial_and_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> None:
    inputs = _inputs(tmp_path)
    output = tmp_path / "attempt"

    def fail(name: str, run: Path, *_args: object) -> None:
        (run / name).mkdir()
        (run / name / "partial").write_bytes(b"preserve")
        raise error

    monkeypatch.setattr(module, "_extract", fail)
    with pytest.raises(type(error)) as raised:
        module.execute_resume(**inputs, output_dir=output, dry_run=False)
    assert (
        raised.value is error
        if isinstance(error, (KeyboardInterrupt, SystemExit))
        else str(raised.value) == "resume_execution_failed"
    )
    assert (output / "run/budget/partial").read_bytes() == b"preserve"
    assert not (output / "run/MANIFEST.json").exists()
    assert not (output / "RESUME_RECEIPT.json").exists()
    assert "sensitive" not in (output / "FAILURE.json").read_text()


def test_envelope_failure_does_not_invalidate_independent_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    output = tmp_path / "attempt"
    real = module.verify_resume

    def fail(*_args: object) -> None:
        message = "private"
        raise OSError(message)

    monkeypatch.setattr(module, "verify_resume", fail)
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=output, dry_run=False)
    child = output / "run/MANIFEST.json"
    assert (
        rebuild.verify_rebuild(
            output / "run",
            inputs["store_root"],
            hashlib.sha256(child.read_bytes()).hexdigest(),
        )["status"]
        == "passed"
    )
    assert (output / "FAILURE.json").exists()
    receipt_pin = hashlib.sha256(
        (output / "RESUME_RECEIPT.json").read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError, match="resume_verification_failed"):
        real(output, inputs["store_root"], receipt_pin)


@pytest.mark.parametrize(
    "payload",
    [
        b"[]",
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e999}',
        b'{"x":1.0}',
        b'{"x":1,"x":2}',
    ],
)
def test_malformed_json_rejected_before_state(tmp_path: Path, payload: bytes) -> None:
    inputs = _inputs(tmp_path)
    inputs["resume_plan"].write_bytes(payload)
    inputs["resume_plan_sha256"] = hashlib.sha256(payload).hexdigest()
    before = _files(tmp_path)
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=tmp_path / "attempt", dry_run=False)
    assert _files(tmp_path) == before


def _reuse_budget(inputs: dict[str, Any]) -> None:
    plan = json.loads((inputs["previous_run"] / "PLAN.json").read_bytes())
    source = plan["sources"]["budget"]
    path = ContentAddressedStore(inputs["store_root"], create=False).get_path(
        source["object_id"]
    )
    stage = inputs["previous_run"] / "budget"
    module.normalize_budget_workbook(
        path,
        stage,
        expected_sha256=source["sha256"],
        source_locator=source["locator"],
        source_vintage=source["vintage"],
        observed_at=plan["observed_at"],
    )
    inputs["stage_manifest_sha256"]["budget"] = hashlib.sha256(
        (stage / "MANIFEST.json").read_bytes()
    ).hexdigest()
    _replan(inputs)


@pytest.mark.parametrize("dry", [True, False])
@pytest.mark.parametrize("alias", ["float", "bool"])
def test_re_pinned_numeric_alias_rejected_before_claim(
    tmp_path: Path, *, dry: bool, alias: str
) -> None:
    inputs = _inputs(tmp_path)
    _reuse_budget(inputs)
    plan = json.loads(inputs["resume_plan"].read_bytes())
    if alias == "float":
        plan["selected_source_bytes"] = float(plan["selected_source_bytes"])
    else:
        plan["stages"]["budget"]["rows"]["budget_facts.parquet"] = True
    inputs["resume_plan_sha256"] = _json(inputs["resume_plan"], plan)
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=tmp_path / "attempt", dry_run=dry)
    assert not (tmp_path / "attempt").exists()


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_exact_reuse_snapshot_aggregate_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, offset: int
) -> None:
    inputs = _inputs(tmp_path)
    _reuse_budget(inputs)
    size = sum(
        len(payload) for payload in _files(inputs["previous_run"] / "budget").values()
    )
    monkeypatch.setattr(module, "MAX_REUSE_BYTES", size + offset)
    if offset < 0:
        with pytest.raises(ValueError, match="resume_execution_failed"):
            module.execute_resume(**inputs, output_dir=tmp_path / "attempt")
    else:
        assert (
            module.execute_resume(**inputs, output_dir=tmp_path / "attempt")["status"]
            == "planned"
        )
    assert not (tmp_path / "attempt").exists()


@settings(
    max_examples=5, deadline=None
)  # Synthetic workbook I/O, not a timing property.
@given(amount=st.integers(min_value=-10_000, max_value=10_000))
def test_exact_amount_survives_resume(amount: int) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        inputs = _inputs(root, amount)
        _reuse_budget(inputs)
        before = _files(root)
        output = root / "attempt"
        module.execute_resume(**inputs, output_dir=output, dry_run=False)
        rows = pq.read_table(output / "run/budget/budget_facts.parquet").to_pylist()
        assert rows[0]["amount"] == Decimal(amount)
        assert {k: (root / k).read_bytes() for k in before} == before


@pytest.mark.parametrize(
    "point", ["RESUME_PLAN.json", "PLAN.json", "MANIFEST.json", "RESUME_RECEIPT.json"]
)
def test_exclusive_write_failures_preserve_partial_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, point: str
) -> None:
    inputs = _inputs(tmp_path)
    original = module._write  # noqa: SLF001 - controlled output boundary fault.
    output = tmp_path / "attempt"

    def write(path: Path, payload: bytes, owners: dict[Path, tuple[int, int]]) -> None:
        if path.name == point:
            message = "sensitive filesystem detail"
            raise OSError(message)
        original(path, payload, owners)

    monkeypatch.setattr(module, "_write", write)
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=output, dry_run=False)
    assert (output / "FAILURE.json").is_file()
    assert not (output / "RESUME_RECEIPT.json").exists()
    assert "sensitive" not in (output / "FAILURE.json").read_text()


def test_failure_receipt_error_does_not_mask_original_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    interrupt = KeyboardInterrupt("preserve original")
    original = module._write  # noqa: SLF001 - controlled output boundary fault.

    def write(path: Path, payload: bytes, owners: dict[Path, tuple[int, int]]) -> None:
        if path.name == "PLAN.json":
            raise interrupt
        if path.name == "FAILURE.json":
            message = "second failure"
            raise OSError(message)
        original(path, payload, owners)

    monkeypatch.setattr(module, "_write", write)
    with pytest.raises(KeyboardInterrupt) as raised:
        module.execute_resume(**inputs, output_dir=tmp_path / "attempt", dry_run=False)
    assert raised.value is interrupt


def test_replaced_run_stops_writes_without_touching_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    output = tmp_path / "attempt"
    original = module._extract  # noqa: SLF001 - controlled ownership race.

    def replace(name: str, run: Path, plan: dict[str, Any], store: Path) -> None:
        original(name, run, plan, store)
        run.rename(output / "displaced")
        run.mkdir()
        (run / "sentinel").write_bytes(b"other owner")

    monkeypatch.setattr(module, "_extract", replace)
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=output, dry_run=False)
    assert _files(output / "run") == {"sentinel": b"other owner"}
    assert (output / "displaced/budget/MANIFEST.json").is_file()
    assert not (output / "FAILURE.json").exists()


@pytest.mark.parametrize("target", ["donor", "old_plan", "resume_plan", "original"])
def test_drift_before_child_marker_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    inputs = _inputs(tmp_path)
    output = tmp_path / "attempt"
    real = module.describe_rebuild_completion

    def drift(run: Path, store: Path, plan: dict[str, Any]) -> dict[str, Any]:
        result = real(run, store, plan)
        paths = {
            "donor": inputs["donor_manifest"],
            "old_plan": inputs["previous_run"] / "PLAN.json",
            "resume_plan": inputs["resume_plan"],
            "original": ContentAddressedStore(store, create=False).get_path(
                plan["sources"]["budget"]["object_id"]
            ),
        }
        paths[target].write_bytes(b"drifted by another actor")
        return result

    monkeypatch.setattr(module, "describe_rebuild_completion", drift)
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=output, dry_run=False)
    assert not (output / "run/MANIFEST.json").exists()
    assert (output / "FAILURE.json").exists()


@pytest.mark.parametrize(
    "change",
    ["extra", "execution", "rights", "reason", "stage_extra", "pin", "count_bool"],
)
def test_verifier_rejects_repinned_malformed_saved_plan(
    tmp_path: Path, change: str
) -> None:
    inputs = _inputs(tmp_path)
    output = tmp_path / "attempt"
    module.execute_resume(**inputs, output_dir=output, dry_run=False)
    plan_path = output / "RESUME_PLAN.json"
    plan = json.loads(plan_path.read_bytes())
    if change == "extra":
        plan["unreviewed"] = True
    elif change == "execution":
        plan["execution"] = "performed"
    elif change == "rights":
        plan["rights_state"] = "approved"
    elif change == "reason":
        plan["stages"]["budget"]["reason"] = "secret arbitrary reason"
    elif change == "stage_extra":
        plan["stages"]["budget"]["unexpected"] = True
    elif change == "pin":
        plan["previous_plan_sha256"] = "not_a_digest"
    else:
        plan["selected_source_bytes"] = True
    receipt_path = output / "RESUME_RECEIPT.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["resume_plan_sha256"] = _json(plan_path, plan)
    pin = _json(receipt_path, receipt)
    with pytest.raises(ValueError, match="resume_verification_failed"):
        module.verify_resume(output, inputs["store_root"], pin)


def test_public_transport_stage_verification_precedes_legacy_decode(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)
    plan = json.loads((inputs["previous_run"] / "PLAN.json").read_bytes())
    fresh = tmp_path / "fresh"
    complete = rebuild.execute_rebuild(plan, inputs["store_root"], fresh)
    before = _files(tmp_path)
    checked = rebuild_resume.verify_resume_stages(fresh, plan, complete["stages"])
    assert set(checked) == set(rebuild.PROFILES)
    assert all(stage["action"] == "reuse_verified" for stage in checked.values())
    assert _files(tmp_path) == before


def test_bad_reextracted_transform_never_gets_child_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    real = module._extract  # noqa: SLF001 - inject malformed adapter boundary output.

    def wrong(name: str, run: Path, plan: dict[str, Any], store: Path) -> None:
        real(name, run, plan, store)
        path = run / name / "MANIFEST.json"
        value = json.loads(path.read_bytes())
        value["transformation_id"] = "unreviewed"
        _json(path, value)

    monkeypatch.setattr(module, "_extract", wrong)
    output = tmp_path / "attempt"
    with pytest.raises(ValueError, match="resume_execution_failed"):
        module.execute_resume(**inputs, output_dir=output, dry_run=False)
    assert not (output / "run/MANIFEST.json").exists()
    assert (output / "FAILURE.json").exists()


@pytest.mark.parametrize(
    "kind",
    [
        "missing_pin",
        "extra_pin",
        "bad_pin",
        "plan_extra",
        "schema",
        "donor_pin",
        "sources",
        "source_extra",
        "source_hash",
        "object_id",
        "locator",
        "vintage",
        "observed",
        "missing_stage",
    ],
)
def test_public_stage_helper_rejects_ambiguous_context(
    tmp_path: Path, kind: str
) -> None:
    inputs = _inputs(tmp_path)
    plan = json.loads((inputs["previous_run"] / "PLAN.json").read_bytes())
    fresh = tmp_path / "fresh"
    pins = rebuild.execute_rebuild(plan, inputs["store_root"], fresh)["stages"]
    if kind == "missing_pin":
        del pins["budget"]
    elif kind == "extra_pin":
        pins["unknown"] = "0" * 64
    elif kind == "bad_pin":
        pins["budget"] = "not_a_pin"
    elif kind == "plan_extra":
        plan["unknown"] = 1
    elif kind in {"schema", "donor_pin", "observed"}:
        key = {
            "schema": "schema_version",
            "donor_pin": "donor_manifest_sha256",
            "observed": "observed_at",
        }[kind]
        plan[key] = "unknown"
    elif kind == "sources":
        del plan["sources"]["budget"]
    elif kind == "source_extra":
        plan["sources"]["budget"]["unknown"] = 1
    elif kind == "source_hash":
        plan["sources"]["budget"]["sha256"] = "invalid"
    elif kind in {"object_id", "locator", "vintage"}:
        plan["sources"]["budget"][kind] = "unknown"
    else:
        (fresh / "budget").rename(tmp_path / "preserved-budget")
    before = _files(tmp_path)
    with pytest.raises(ValueError, match=r"resume_input_contract|Invalid isoformat"):
        rebuild_resume.verify_resume_stages(fresh, plan, pins)
    assert _files(tmp_path) == before


@pytest.mark.parametrize(
    "kind",
    [
        "extra",
        "reason",
        "pin",
        "rows_extra",
        "rows_bool",
        "rows_wrong",
        "rows_zero",
        "rows_too_many",
    ],
)
def test_saved_reuse_metadata_is_closed_and_matches_child(
    tmp_path: Path, kind: str
) -> None:
    inputs = _inputs(tmp_path)
    _reuse_budget(inputs)
    output = tmp_path / "attempt"
    module.execute_resume(**inputs, output_dir=output, dry_run=False)
    path = output / "RESUME_PLAN.json"
    plan = json.loads(path.read_bytes())
    stage = plan["stages"]["budget"]
    if kind == "extra":
        stage["unexpected"] = True
    elif kind == "reason":
        stage["reason"] = "claimed_semantic_approval"
    elif kind == "pin":
        stage["manifest_sha256"] = "0" * 64
    elif kind == "rows_extra":
        stage["rows"]["extra"] = 1
    else:
        stage["rows"]["budget_facts.parquet"] = {
            "rows_bool": True,
            "rows_wrong": 2,
            "rows_zero": 0,
            "rows_too_many": 100001,
        }[kind]
    receipt_path = output / "RESUME_RECEIPT.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["resume_plan_sha256"] = _json(path, plan)
    pin = _json(receipt_path, receipt)
    with pytest.raises(ValueError, match="resume_verification_failed"):
        module.verify_resume(output, inputs["store_root"], pin)


@pytest.mark.parametrize("change", ["plan", "failure"])
def test_envelope_reverifies_saved_plan_and_shape_after_child_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    inputs = _inputs(tmp_path)
    output = tmp_path / "attempt"
    module.execute_resume(**inputs, output_dir=output, dry_run=False)
    pin = hashlib.sha256((output / "RESUME_RECEIPT.json").read_bytes()).hexdigest()
    original = module.read_verified_run

    def drift(
        run: Path, store: Path, child_pin: str
    ) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
        result = original(run, store, child_pin)
        target = output / ("RESUME_PLAN.json" if change == "plan" else "FAILURE.json")
        target.write_bytes(b"changed after verified snapshot")
        return result

    monkeypatch.setattr(module, "read_verified_run", drift)
    with pytest.raises(ValueError, match="resume_verification_failed"):
        module.verify_resume(output, inputs["store_root"], pin)
