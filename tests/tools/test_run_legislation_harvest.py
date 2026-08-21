"""Tests for bounded service-backed legislation harvest orchestration."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

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
    path.write_text(
        "name: legislation\nenabled: true\nexecution_mode: dispatch_only\n",
        encoding="utf-8",
    )
    return path


def _paths(tmp_path: Path) -> dict[str, Any]:
    return {
        "config_path": _config(tmp_path),
        "checkpoint_path": tmp_path / "state" / "checkpoint.json",
        "manifest_path": tmp_path / "state" / "manifest.json",
        "receipt_path": tmp_path / "state" / "receipt.json",
        "cas_path": tmp_path / "state" / "cas",
        "batch_id": "batch-2026-08-20-a",
        "search_terms": ["public acts 2024"],
        "max_works": 2,
    }


def test_validate_source_set_config_is_dispatch_only(tmp_path: Path) -> None:
    """Accept only the enabled legislation source set in dispatch-only mode."""
    assert validate_source_set_config(_config(tmp_path))["execution_mode"] == (
        "dispatch_only"
    )
    with pytest.raises(FileNotFoundError):
        validate_source_set_config(tmp_path / "missing.yml")
    invalid = tmp_path / "invalid.yml"
    invalid.write_text("name: other\nenabled: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Expected source-set"):
        validate_source_set_config(invalid)
    disabled = tmp_path / "disabled.yml"
    disabled.write_text("name: legislation\nenabled: false\n", encoding="utf-8")
    with pytest.raises(ValueError, match="disabled"):
        validate_source_set_config(disabled)
    scheduled = tmp_path / "scheduled.yml"
    scheduled.write_text("name: legislation\nenabled: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="dispatch_only"):
        validate_source_set_config(scheduled)


def test_validate_source_set_config_ignores_nested_enabled_flags(
    tmp_path: Path,
) -> None:
    """Nested publication policy cannot overwrite top-level execution authority."""
    config = tmp_path / "legislation.yml"
    config.write_text(
        """name: legislation
enabled: true
execution_mode: dispatch_only
publication_policy:
  huggingface:
    enabled: false
  zenodo:
    enabled: false
""",
        encoding="utf-8",
    )
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


def test_main_accepts_exact_work_id_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Parse an explicit donor work-ID file as an exact discovery scope."""
    arguments = _paths(tmp_path)
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
