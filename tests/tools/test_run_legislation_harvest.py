"""Tests for bounded service-backed legislation harvest orchestration."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest
import yaml

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "run_legislation_harvest.py"
_SPEC = importlib.util.spec_from_file_location("run_legislation_harvest", _TOOL_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

validate_source_set_config = _MODULE.validate_source_set_config
check_credentials_presence = _MODULE.check_credentials_presence
sync_legislation_records = _MODULE.sync_legislation_records
run_harvest = _MODULE.run_harvest
main = _MODULE.main


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "legislation.yml"
    source = Path(__file__).parents[2] / "config/source-sets/legislation.yml"
    document = yaml.safe_load(source.read_text(encoding="utf-8"))
    document["execution"]["mode"] = "dispatch_only"
    document["schedule"]["active"] = False
    document["state"]["checkpoint_path"] = f"build/test-{tmp_path.name}/checkpoint.json"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def _paths(tmp_path: Path) -> dict[str, Any]:
    config_path = _config(tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return {
        "config_path": config_path,
        "checkpoint_path": Path(config["state"]["checkpoint_path"]),
        "manifest_path": tmp_path / "state" / "manifest.json",
        "receipt_path": tmp_path / "state" / "receipt.json",
        "cas_path": tmp_path / "state" / "cas",
        "batch_id": "batch-2026-08-20-a",
        "search_terms": ["public acts 2024"],
        "max_works": 2,
    }


def test_validate_source_set_config_is_dispatch_only(tmp_path: Path) -> None:
    """Accept only the enabled legislation source set in dispatch-only mode."""
    assert (
        validate_source_set_config(_config(tmp_path)).execution.mode == "dispatch_only"
    )
    with pytest.raises(FileNotFoundError):
        validate_source_set_config(tmp_path / "missing.yml")
    invalid = tmp_path / "invalid.yml"
    invalid.write_text(
        _config(tmp_path).read_text().replace("name: legislation", "name: other")
    )
    with pytest.raises(ValueError, match="Expected typed source-set"):
        validate_source_set_config(invalid)
    disabled = tmp_path / "disabled.yml"
    disabled_doc = yaml.safe_load(_config(tmp_path).read_text())
    disabled_doc["enabled"] = False
    disabled_doc["execution"]["activation"] = "inactive"
    disabled_doc["gates"]["acquisition"] = "inactive"
    for adapter in disabled_doc["adapters"]:
        adapter["active"] = False
    disabled.write_text(yaml.safe_dump(disabled_doc, sort_keys=False))
    with pytest.raises(ValueError, match="disabled"):
        validate_source_set_config(disabled)
    scheduled = tmp_path / "scheduled.yml"
    scheduled.write_text("name: legislation\nenabled: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="legacy legislation fields"):
        validate_source_set_config(scheduled)


def test_validate_source_set_config_ignores_nested_enabled_flags(
    tmp_path: Path,
) -> None:
    """Nested publication policy cannot overwrite top-level execution authority."""
    config = tmp_path / "legislation.yml"
    config.write_text(_config(tmp_path).read_text(), encoding="utf-8")
    parsed = validate_source_set_config(config)
    assert parsed["enabled"] is True


def test_credentials_exclude_publication_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inspect only the optional source credential, not publication tokens."""
    monkeypatch.setenv("LEGISLATION_API_KEY", "present")
    assert check_credentials_presence() == {"LEGISLATION_API_KEY": True}


def test_sync_routes_discovery_and_state_to_service(tmp_path: Path) -> None:
    """Delegate discovery, capture, manifest, and checkpoint work to sync_works."""
    calls: list[dict[str, object]] = []

    class FakeService:
        async def sync_works(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(
                status="success",
                works_attempted=2,
                works_synced=2,
                records_preserved=3,
                errors=[],
                manifest={
                    "manifest_sha256": "a" * 64,
                    "discovered_works_count": 2,
                },
                checkpoint={"metadata": {"manifest_sha256": "a" * 64}},
            )

    report = sync_legislation_records(
        FakeService(),
        search_terms=["acts"],
        work_ids=None,
        batch_id="batch-a",
        checkpoint_path=tmp_path / "checkpoint.json",
        manifest_path=tmp_path / "manifest.json",
        max_works=2,
    )
    assert calls[0]["search_terms"] == ["acts"]
    assert calls[0]["fail_fast"] is True
    assert report["manifest_sha256"] == "a" * 64


def test_sync_routes_exact_work_ids_to_service(tmp_path: Path) -> None:
    """Explicit donor identities use exact service discovery, not free-text search."""
    calls: list[dict[str, object]] = []

    class FakeService:
        async def sync_works(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(
                status="success",
                works_attempted=2,
                works_synced=2,
                records_preserved=2,
                errors=[],
                manifest={
                    "manifest_sha256": "a" * 64,
                    "discovered_works_count": 2,
                },
                checkpoint={},
            )

    sync_legislation_records(
        FakeService(),
        search_terms=None,
        work_ids=["act_public_2024_1", "act_public_2024_2"],
        batch_id="historical-work-ids-0001",
        checkpoint_path=tmp_path / "checkpoint.json",
        manifest_path=tmp_path / "manifest.json",
        max_works=2,
    )
    assert calls[0]["work_ids"] == ["act_public_2024_1", "act_public_2024_2"]
    assert "search_terms" not in calls[0]


def test_sync_routes_explicit_force_resync_to_service(tmp_path: Path) -> None:
    """A bounded canary can revalidate prior work instead of skipping it."""
    calls: list[dict[str, object]] = []

    class FakeService:
        async def sync_works(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(
                status="no_change",
                works_attempted=1,
                works_synced=0,
                records_preserved=0,
                errors=[],
                manifest={
                    "manifest_sha256": "a" * 64,
                    "discovered_works_count": 1,
                },
                checkpoint={"metadata": {"manifest_sha256": "a" * 64}},
            )

    sync_legislation_records(
        FakeService(),
        search_terms=None,
        work_ids=["act_public_2024_1"],
        batch_id="bounded-live-canary-0001",
        checkpoint_path=tmp_path / "checkpoint.json",
        manifest_path=tmp_path / "manifest.json",
        max_works=1,
        force_resync=True,
    )
    assert calls[0]["force_resync"] is True


@pytest.mark.parametrize(
    ("service_status", "expected"),
    [
        ("success", ("changed", 0, True)),
        ("no_change", ("no_change", 0, True)),
        ("partial", ("partial_retryable", 1, False)),
        ("failed", ("failed", 1, False)),
    ],
)
def test_run_harvest_outcomes_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    service_status: str,
    expected: tuple[str, int, bool],
) -> None:
    """Commit only complete changed/no-change service outcomes."""
    expected_outcome, expected_code, committed = expected
    report = {
        "status": service_status,
        "works_attempted": 2,
        "works_synced": 1,
        "records_preserved": 1,
        "errors": [] if expected_code == 0 else ["bounded failure"],
        "manifest_sha256": "b" * 64,
        "discovered_works_count": 2,
        "checkpoint": {"metadata": {"manifest_sha256": "b" * 64}},
    }

    def _sync(*_args: object, **_kwargs: object) -> dict[str, object]:
        return report

    monkeypatch.setattr(_MODULE, "sync_legislation_records", _sync)
    arguments = _paths(tmp_path)
    code = run_harvest(**arguments)
    receipt = json.loads(arguments["receipt_path"].read_text(encoding="utf-8"))
    assert code == expected_code
    assert receipt["outcome"] == expected_outcome
    assert receipt["state_committed"] is committed


@pytest.mark.parametrize(
    ("batch_id", "search_terms", "max_works"),
    [("", ["acts"], 1), ("batch", [], 1), ("batch", ["acts"], 0)],
)
def test_run_harvest_rejects_unbounded_or_empty_dispatch(
    tmp_path: Path, batch_id: str, search_terms: list[str], max_works: int
) -> None:
    """Fail before discovery when required dispatch scope is missing."""
    arguments = _paths(tmp_path)
    arguments.update(batch_id=batch_id, search_terms=search_terms, max_works=max_works)
    assert run_harvest(**arguments) == 1
    receipt = json.loads(arguments["receipt_path"].read_text(encoding="utf-8"))
    assert receipt["outcome"] == "failed"
    assert receipt["state_committed"] is False


def test_run_harvest_requires_exact_explicit_batch_bound(tmp_path: Path) -> None:
    """An explicit donor batch cannot be silently truncated by max_works."""
    arguments = _paths(tmp_path)
    arguments.update(
        search_terms=None,
        work_ids=["act_public_2024_1", "act_public_2024_2"],
        max_works=1,
    )
    assert run_harvest(**arguments) == 1
    receipt = json.loads(arguments["receipt_path"].read_text(encoding="utf-8"))
    assert receipt["outcome"] == "failed"


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"max_works": 51}, "exceeds configured bound"),
        ({"checkpoint_path": Path("wrong-checkpoint.json")}, "configured authority"),
        ({"work_ids": ["act-1", "act-2"], "search_terms": None}, "does not permit"),
    ],
)
def test_dispatch_is_bound_to_typed_policy(
    tmp_path: Path, change: dict[str, object], error: str
) -> None:
    """Reject dispatch arguments that contradict the typed source-set policy."""
    arguments = _paths(tmp_path)
    arguments.update(change)
    assert run_harvest(**arguments) == 1
    receipt = json.loads(arguments["receipt_path"].read_text(encoding="utf-8"))
    assert error in receipt["errors"][0]


def test_main_accepts_exact_work_id_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Parse an explicit donor work-ID file as an exact discovery scope."""
    arguments = _paths(tmp_path)
    config = yaml.safe_load(arguments["config_path"].read_text(encoding="utf-8"))
    config["execution"]["lane_type"] = "exact_inventory"
    config["scope"].update(
        {
            "type": "exact_inventory",
            "identifier": "test-exact-inventory",
            "seed_id": "test-seed",
            "inventory_sha256": hashlib.sha256(
                b"act_public_2024_1\nact_public_2024_2\n"
            ).hexdigest(),
            "candidate_count": 2,
        }
    )
    arguments["config_path"].write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    work_ids_path = tmp_path / "batch.txt"
    work_ids_path.write_text("act_public_2024_1\nact_public_2024_2\n", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_legislation_harvest.py",
            "--source-set-config",
            str(arguments["config_path"]),
            "--checkpoint-path",
            str(arguments["checkpoint_path"]),
            "--manifest-path",
            str(arguments["manifest_path"]),
            "--receipt-path",
            str(arguments["receipt_path"]),
            "--cas-path",
            str(arguments["cas_path"]),
            "--batch-id",
            arguments["batch_id"],
            "--work-ids-file",
            str(work_ids_path),
            "--max-works",
            "2",
        ],
    )
    captured: dict[str, object] = {}

    def _no_change(*_args: object, **kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"status": "no_change", "errors": [], "checkpoint": {}}

    monkeypatch.setattr(_MODULE, "sync_legislation_records", _no_change)
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
    assert captured["work_ids"] == ["act_public_2024_1", "act_public_2024_2"]
    assert captured["search_terms"] is None


def test_main_requires_explicit_state_and_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Parse explicit batch, discovery, bound, and full state locations."""
    arguments = _paths(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_legislation_harvest.py",
            "--source-set-config",
            str(arguments["config_path"]),
            "--checkpoint-path",
            str(arguments["checkpoint_path"]),
            "--manifest-path",
            str(arguments["manifest_path"]),
            "--receipt-path",
            str(arguments["receipt_path"]),
            "--cas-path",
            str(arguments["cas_path"]),
            "--batch-id",
            arguments["batch_id"],
            "--search-term",
            arguments["search_terms"][0],
            "--max-works",
            str(arguments["max_works"]),
        ],
    )

    def _no_change(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "status": "no_change",
            "errors": [],
            "checkpoint": {},
        }

    monkeypatch.setattr(_MODULE, "sync_legislation_records", _no_change)
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


@pytest.mark.parametrize(
    ("execution_mode", "expected_ok"),
    [
        ("dispatch_only", True),
        ("scheduled", True),
        ("scheduled_and_dispatch", True),
        ("unbounded", False),
    ],
)
def test_execution_mode_gate_accepts_promoted_modes_only(
    tmp_path: Path, execution_mode: str, *, expected_ok: bool
) -> None:
    """Steady-state promotion allows scheduled modes; everything else fails closed."""
    config = tmp_path / "legislation.yml"
    config.write_text(_config(tmp_path).read_text(), encoding="utf-8")
    document = yaml.safe_load(config.read_text())
    document["execution"]["mode"] = execution_mode
    document["schedule"]["active"] = execution_mode in {
        "scheduled",
        "scheduled_and_dispatch",
    }
    config.write_text(yaml.safe_dump(document, sort_keys=False))
    if expected_ok:
        parsed = validate_source_set_config(config)
        assert parsed.execution.mode == execution_mode
    else:
        with pytest.raises(ValueError, match=r"execution|mode"):
            validate_source_set_config(config)
