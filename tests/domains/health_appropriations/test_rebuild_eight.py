"""Opt-in eight-stage contracts keep legacy plans and consumers unchanged."""

# ruff: noqa: SLF001 -- exercise dispatcher/transaction seams explicitly.

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from archive_govt_nz.cli import (
    health_appropriations_rebuild,
    health_appropriations_verify_rebuild,
)
from archive_govt_nz.domains.health_appropriations import rebuild, rebuild_eight
from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_URL,
)
from archive_govt_nz.object_store import ContentAddressedStore


def inputs(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], Path]:
    """Real CAS and pinned donor inputs; adapters are tested separately."""
    store_path = root / "cas"
    store = ContentAddressedStore(store_path)
    objects = []
    for filename in {
        *(p.filename for p in rebuild.PROFILES.values()),
        *rebuild_eight.EXTRA_FILES.values(),
    }:
        receipt = store.put_bytes(filename.encode())
        objects.append(
            {
                "path": "data/raw/" + filename,
                "sha256": receipt.sha256,
                "object_id": receipt.object_id,
            }
        )
    crown = store.put_bytes(b"direct-crown")
    monkeypatch.setattr(rebuild_eight, "SOURCE_SHA256", crown.sha256)
    census = root / "crown-receipt.json"
    census.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-source-census/v1",
                "record_count": 1,
                "records": [
                    {
                        "source_id": "fiscal_time_series-007",
                        "object_sha256": crown.sha256,
                        "url": SOURCE_URL,
                        "family": "fiscal_time_series",
                        "title": "Historical fiscal indicators 1972-2025",
                        "disposition": "captured",
                        "observed_at": "2026-08-29T09:00:17Z",
                    }
                ],
            }
        )
    )
    donor = root / "donor.json"
    donor.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-donor-manifest/v1",
                "objects": objects,
            }
        )
    )
    plan = rebuild_eight.plan_eight(
        donor,
        store_path,
        hashlib.sha256(donor.read_bytes()).hexdigest(),
        "2026-01-01T00:00:00Z",
        crown.sha256,
        crown_receipt=census,
        crown_receipt_sha256=hashlib.sha256(census.read_bytes()).hexdigest(),
    )
    return plan, store_path


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "donor",
        "crown",
        "duplicate",
        "join",
        "failure",
        "reuse",
        "extra",
        "plan",
    ],
)
def test_orchestration_transactions(  # noqa: C901 -- transaction fault matrix
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    """Real planning/CAS/transaction behavior around separately verified adapters."""
    plan, store = inputs(tmp_path, monkeypatch)
    calls = []

    def dispatch(
        name: str, source: dict[str, Any], root: Path, _plan: dict[str, Any]
    ) -> None:
        calls.append((name, source["observed_at"]))
        (root / name).mkdir()
        if fault == "failure":
            message = "synthetic_adapter_error"
            raise ValueError(message)

    def completion(
        _root: Path, _plan: dict[str, Any], sources: dict[str, Any]
    ) -> dict[str, Any]:
        assert set(sources) == set(rebuild_eight.STAGES)
        return {"schema_version": rebuild_eight.SCHEMA, "status": "passed"}

    monkeypatch.setattr(rebuild_eight, "_dispatch", dispatch)
    monkeypatch.setattr(rebuild_eight, "_completion", completion)
    if fault == "donor":
        plan["donor_manifest_json"] += " "
    elif fault == "crown":
        plan["crown_source_sha256"] = "0" * 64
    elif fault in {"duplicate", "join"}:
        donor = json.loads(plan["donor_manifest_json"])
        if fault == "duplicate":
            donor["objects"].append(donor["objects"][0])
        else:
            donor["objects"][0]["sha256"] = "0" * 64
        plan["donor_manifest_json"] = json.dumps(donor)
        plan["legacy_plan"]["donor_manifest_sha256"] = hashlib.sha256(
            plan["donor_manifest_json"].encode()
        ).hexdigest()
    root = tmp_path / "run"
    if fault in {"donor", "crown", "duplicate", "join", "failure"}:
        with pytest.raises(ValueError, match="eight_stage"):
            rebuild_eight.execute_eight(plan, store, root)
        assert not (root / "MANIFEST.json").exists()
        if fault == "failure":
            assert (root / "FAILURE.json").is_file()
        return
    result = rebuild_eight.execute_eight(plan, store, root)
    assert [name for name, _ in calls] == list(rebuild_eight.STAGES)
    assert calls[-1][1] == "2026-08-29T09:00:17Z"
    if fault == "extra":
        (root / "extra").touch()
    elif fault == "plan":
        (root / "PLAN.json").write_text("{}")
    if fault in {"extra", "plan"}:
        with pytest.raises(ValueError, match="eight_stage"):
            rebuild_eight.execute_eight(plan, store, root)
    else:
        assert rebuild_eight.execute_eight(plan, store, root) == result
        assert len(calls) == len(rebuild_eight.STAGES)


def test_dispatch_and_completion_preserve_stage_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shared v1 dispatcher is called only for v1, with unchanged context."""
    plan, store = inputs(tmp_path, monkeypatch)
    sources = rebuild_eight._sources(plan, store)
    dispatched = []
    verified = []

    def legacy_extract(name: str, path: Path, root: Path, base: dict[str, Any]) -> None:
        assert base == plan["legacy_plan"]
        assert path == sources[name]["path"]
        assert root == tmp_path
        dispatched.append(name)

    def extra(path: Path, output: Path, **context: object) -> None:
        name = output.name
        assert path == sources[name]["path"]
        if name == "revenue":
            assert context == {
                "expected_sha256": sources[name]["sha256"],
                "source_locator": sources[name]["locator"],
                "observed_at": sources[name]["observed_at"],
            }
        else:
            assert context["profile"] == name
            assert (
                cast("dict[str, Any]", context["context"])["source_object_sha256"]
                == sources[name]["sha256"]
            )
        dispatched.append(name)

    def stage(root: Path, name: str, source: dict[str, Any]) -> dict[str, Any]:
        assert root == tmp_path / name
        assert source == sources[name]
        verified.append(name)
        return {"manifest_sha256": name, "stage": name, "record_ids": [name]}

    monkeypatch.setattr(rebuild, "_extract", legacy_extract)
    monkeypatch.setattr(rebuild_eight, "normalize_budget_revenue", extra)
    monkeypatch.setattr(rebuild_eight, "package_admitted_source", extra)
    legacy_checks = []
    monkeypatch.setattr(
        rebuild, "_stage_receipt", lambda _root, name, _plan: legacy_checks.append(name)
    )
    monkeypatch.setattr(rebuild_eight, "verify_stage_coverage", stage)
    for name in rebuild_eight.STAGES:
        rebuild_eight._dispatch(name, sources[name], tmp_path, plan)
    result = rebuild_eight._completion(tmp_path, plan, sources)
    assert dispatched == verified == list(rebuild_eight.STAGES)
    assert legacy_checks == list(rebuild.PROFILES)
    assert result["stages"] == {name: name for name in rebuild_eight.STAGES}
    assert result["gold_selection"] == "not_performed"
    monkeypatch.setattr(
        rebuild_eight,
        "verify_stage_coverage",
        lambda *_: {"manifest_sha256": "pin", "record_ids": ["duplicate"]},
    )
    with pytest.raises(ValueError, match="eight_stage"):
        rebuild_eight._completion(tmp_path, plan, sources)


def test_cli_requires_explicit_optin_and_crown_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Existing CLI reaches v2 only with both explicit flags; dry-run cannot write."""
    plan, store = inputs(tmp_path, monkeypatch)
    args = {
        "donor_manifest": tmp_path / "donor.json",
        "store_root": store,
        "manifest_sha256": plan["legacy_plan"]["donor_manifest_sha256"],
        "observed_at": "2026-01-01T00:00:00Z",
        "output_dir": tmp_path / "output",
    }
    assert health_appropriations_rebuild(**args, eight_stage=True) == 2
    assert (
        health_appropriations_rebuild(
            **args, crown_source_sha256=rebuild_eight.SOURCE_SHA256
        )
        == 2
    )
    assert (
        health_appropriations_rebuild(
            **args,
            eight_stage=True,
            crown_source_sha256=rebuild_eight.SOURCE_SHA256,
            crown_receipt=tmp_path / "crown-receipt.json",
            crown_receipt_sha256=plan["crown_receipt_sha256"],
        )
        == 0
    )
    assert not (tmp_path / "output").exists()
    monkeypatch.setattr(
        rebuild_eight, "execute_eight", lambda *_: {"status": "synthetic_execution"}
    )
    assert (
        health_appropriations_rebuild(
            **args,
            eight_stage=True,
            crown_source_sha256=rebuild_eight.SOURCE_SHA256,
            crown_receipt=tmp_path / "crown-receipt.json",
            crown_receipt_sha256=plan["crown_receipt_sha256"],
            dry_run=False,
        )
        == 0
    )
    monkeypatch.setattr(
        rebuild_eight, "verify_eight", lambda *_: {"status": "synthetic_verification"}
    )
    assert (
        health_appropriations_verify_rebuild(tmp_path, store, "pin", eight_stage=True)
        == 0
    )
    assert "synthetic_verification" in capsys.readouterr().out


def test_profiles_are_explicit_and_legacy_unchanged() -> None:
    """The new orchestration must not mutate the legacy registry."""
    assert set(rebuild.PROFILES) == {"budget", "befu", "hyefu", "historical"}
    assert set(rebuild_eight.STAGES) == {
        *rebuild.PROFILES,
        "revenue",
        "befu-detail",
        "hyefu-detail",
        "crown",
    }


@pytest.mark.parametrize(
    "fault", ["pin", "duplicate", "url", "time", "object", "missing"]
)
def test_crown_receipt_reverified_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    """Execution rechecks embedded evidence, even after receipt re-pinning."""
    plan, store = inputs(tmp_path, monkeypatch)
    value = json.loads(plan["crown_receipt_json"])
    row = value["records"][0]
    if fault == "duplicate":
        value["records"].append(row.copy())
        value["record_count"] = 2
    elif fault == "missing":
        value["records"] = []
        value["record_count"] = 0
    elif fault == "url":
        row["url"] = "https://example.test/other"
    elif fault == "time":
        row["observed_at"] = "2030-01-01T00:00:00Z"
    elif fault == "object":
        row["object_sha256"] = "0" * 64
    plan["crown_receipt_json"] = json.dumps(value)
    plan["crown_receipt_sha256"] = (
        "0" * 64
        if fault == "pin"
        else hashlib.sha256(plan["crown_receipt_json"].encode()).hexdigest()
    )
    with pytest.raises(ValueError, match="crown_receipt"):
        rebuild_eight.execute_eight(plan, store, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_crown_cli_requires_receipt_pair_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Object-only opt-in and stray v1 receipt options cannot launch execution."""
    plan, store = inputs(tmp_path, monkeypatch)
    arguments: dict[str, Any] = {
        "donor_manifest": tmp_path / "donor.json",
        "store_root": store,
        "manifest_sha256": plan["legacy_plan"]["donor_manifest_sha256"],
        "observed_at": "2026-01-01T00:00:00Z",
        "output_dir": tmp_path / "out",
        "dry_run": False,
    }
    for options in (
        {"eight_stage": True, "crown_source_sha256": rebuild_eight.SOURCE_SHA256},
        {
            "eight_stage": True,
            "crown_source_sha256": rebuild_eight.SOURCE_SHA256,
            "crown_receipt": tmp_path / "crown-receipt.json",
        },
        {"crown_receipt": tmp_path / "crown-receipt.json"},
        {"crown_receipt_sha256": plan["crown_receipt_sha256"]},
    ):
        assert (
            health_appropriations_rebuild(
                **arguments, **cast("dict[str, Any]", options)
            )
            == 2
        )
        assert not (tmp_path / "out").exists()


def test_wrong_schema_fails_before_storage(tmp_path: Path) -> None:
    """A v1 or partial plan is not silently upgraded."""
    with pytest.raises(ValueError, match="eight_stage"):
        rebuild_eight.execute_eight(
            {"schema_version": "v1"}, tmp_path / "store", tmp_path / "out"
        )
    assert not (tmp_path / "out").exists()


def test_eight_cli_missing_run_is_structured_failure(tmp_path: Path) -> None:
    """A missing pinned run must fail read-only through the existing CLI."""
    assert (
        health_appropriations_verify_rebuild(
            tmp_path / "missing", tmp_path / "store", "0" * 64, eight_stage=True
        )
        == 2
    )
    assert not (tmp_path / "missing").exists()
