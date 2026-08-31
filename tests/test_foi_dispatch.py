"""Shared dispatcher controls never execute a source or publish raw data."""

from __future__ import annotations

import argparse
import importlib.util
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from archive_govt_nz.foi_queue import _decode
from archive_govt_nz.foi_scheduler import Budget, Job
from archive_govt_nz.foi_state import StateStore, StoredState

SPEC = importlib.util.spec_from_file_location(
    "foi_dispatch_tool", Path(__file__).parents[1] / "tools/foi_dispatch.py"
)
assert SPEC is not None
assert SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)
CATALOGUE = {
    "sources": [
        {"id": "nz-fyi", "origins": ["https://fyi.org.nz"]},
        {"id": "ca-federal-atip", "origins": ["https://open.canada.ca"]},
    ]
}


class SharedFixture:
    """Local real CAS storage stands in for the separately tested GitHub transport."""

    def __init__(self, path: Path) -> None:
        """Initialize private local test storage."""
        self.store = StateStore(path)
        self.keys: set[str] = set()
        self.bootstrapped = False
        self.batch_head = "a" * 40

    def read(self, key: str) -> StoredState | None:
        """Read one independent source key."""
        return self.store.read(key)

    def read_all(self) -> dict[str, StoredState]:
        """Return all current source states."""
        return {
            key: value for key in self.keys if (value := self.read(key)) is not None
        }

    def compare_and_swap(
        self, key: str, version: int | None, document: dict[str, Any]
    ) -> StoredState:
        """Preserve actual optimistic-concurrency behavior."""
        self.keys.add(key)
        result = self.store.compare_and_swap(key, version, document)
        self.batch_head = f"{result.version:040x}"
        return result

    def bootstrap(self) -> str:
        """Record explicit authority creation intent."""
        self.bootstrapped = True
        return self.batch_head


def request(action: str = "enqueue", **changes: object) -> argparse.Namespace:
    """Create an explicit synthetic control request."""
    values = {
        "action": action,
        "source": "rehearsal-1-1",
        "owner_lease": "run-1-1",
        "expected_version": None,
        "acquisition_authorized": False,
        "executor_attached": False,
    }
    values.update(changes)
    return argparse.Namespace(**values)


def test_rehearsal_persists_all_transitions(tmp_path: Path) -> None:
    """A terminal rehearsal persists but never credits public capture."""
    store = SharedFixture(tmp_path / "state")
    initial = TOOL.execute(store, request("plan"), CATALOGUE, 1)
    assert initial["version"] is None
    for action, version, status in [
        ("enqueue", None, "pending"),
        ("reserve", 1, "leased"),
        ("reconcile", 2, "exhausted"),
    ]:
        result = TOOL.execute(
            store, request(action, expected_version=version), CATALOGUE, 2
        )
        assert result["jobs"] == [status]
        assert result["capture_executed"] is False
    assert TOOL.execute(store, request("plan"), CATALOGUE, 3)["version"] == 3


def test_registered_sources_are_plan_only_and_scopes_bound(tmp_path: Path) -> None:
    """No existing donor source is enabled by registry presence or CLI intent."""
    store = SharedFixture(tmp_path / "state")
    assert (
        TOOL.execute(store, request("plan", source="nz-fyi"), CATALOGUE, 1)[
            "disposition"
        ]
        == "blocked"
    )
    assert (
        TOOL.policy("ca-federal-atip.nil-returns", CATALOGUE).disposition == "eligible"
    )
    restricted = {
        "sources": [
            {"id": "ca-federal-atip", "origins": [], "rights_status": "restricted"}
        ]
    }
    assert (
        TOOL.policy("ca-federal-atip.nil-returns", restricted).disposition
        == "restricted"
    )
    for source in ("nz-fyi", "ca-federal-atip.nil-returns"):
        with pytest.raises(ValueError, match="not_authorized"):
            TOOL.execute(
                store, request(source=source, acquisition_authorized=True), CATALOGUE, 1
            )
    with pytest.raises(ValueError, match="unknown_control_scope"):
        TOOL.policy("unknown", CATALOGUE)
    with pytest.raises(ValueError, match="registry_binding"):
        TOOL.policy("us-federal-foia.annual-statistics", CATALOGUE)


def test_invalid_and_stale_controls_do_not_write(tmp_path: Path) -> None:
    """Expected owner/version and exact action are enforced before writes."""
    store = SharedFixture(tmp_path / "state")
    with pytest.raises(ValueError, match="invalid_owner_lease"):
        TOOL.execute(store, request(owner_lease=""), CATALOGUE, 1)
    with pytest.raises(ValueError, match="absent_scope"):
        TOOL.execute(store, request(expected_version=1), CATALOGUE, 1)
    with pytest.raises(ValueError, match="expected_control_state"):
        TOOL.execute(store, request("reserve", expected_version=1), CATALOGUE, 1)
    TOOL.execute(store, request(), CATALOGUE, 1)
    for change in (
        {"expected_version": 2},
        {"expected_version": 1, "owner_lease": "stale"},
    ):
        with pytest.raises(ValueError, match="expected_control_state"):
            TOOL.execute(store, request("reserve", **change), CATALOGUE, 2)
    with pytest.raises(ValueError, match="unknown_control_action"):
        TOOL.execute(store, request("bad", expected_version=1), CATALOGUE, 2)


def test_policy_drift_blocks_pending_and_active_jobs(tmp_path: Path) -> None:
    """A changed registry cannot silently change a reserved job's policy."""
    store = SharedFixture(tmp_path / "state")
    TOOL.execute(store, request(), CATALOGUE, 1)
    changed = {"sources": [*CATALOGUE["sources"], {"id": "extra"}]}
    with pytest.raises(ValueError, match="policy_drift"):
        TOOL.execute(store, request("reserve", expected_version=1), changed, 2)
    TOOL.execute(store, request("reserve", expected_version=1), CATALOGUE, 2)
    with pytest.raises(ValueError, match="policy_drift"):
        TOOL.execute(store, request("plan"), changed, 3)


def test_global_limits_include_other_source_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Separate queue documents cannot evade a shared origin or resource ceiling."""
    store = SharedFixture(tmp_path / "state")
    TOOL.execute(store, request(), CATALOGUE, 1)
    TOOL.execute(store, request("reserve", expected_version=1), CATALOGUE, 2)
    second = request(source="rehearsal-2-1", owner_lease="run-2-1")
    TOOL.execute(store, second, CATALOGUE, 2)
    second.action, second.expected_version = "reserve", 1
    with pytest.raises(ValueError, match="global_origin"):
        TOOL.execute(store, second, CATALOGUE, 3)
    job = Job("x", "x", 0, 1, 1, 1)
    policy = TOOL.policy("rehearsal-1-1", CATALOGUE)
    monkeypatch.setattr(TOOL, "GLOBAL_BUDGET", Budget(1, 100, 100))
    with pytest.raises(ValueError, match="global_origin_or_job_budget"):
        TOOL.__dict__["_global_budget"]([job], set(), policy)
    monkeypatch.setattr(TOOL, "GLOBAL_BUDGET", Budget(10, 1, 100))
    with pytest.raises(ValueError, match="global_resource_budget"):
        TOOL.__dict__["_global_budget"]([job], set(), policy)


@pytest.fixture
def ca_source(tmp_path: Path) -> Path:
    """Synthetic official-format metadata is adequate for a real offline restore."""
    path = tmp_path / "source"
    path.mkdir()
    raw = b"year,month,owner_org,owner_org_title\n2025,8,agency,Agency\n"
    dataset = "0797e893-751e-4695-8229-a5066e4fe43c"
    resource = "5a1386a5-ba69-4725-8338-2f26004d7382"
    metadata = {
        "success": True,
        "result": {
            "id": dataset,
            "license_id": "ca-ogl-lgo",
            "license_url": "https://open.canada.ca/en/open-government-licence-canada",
            "private": False,
            "state": "active",
            "resources": [
                {
                    "id": resource,
                    "url": f"https://open.canada.ca/data/dataset/{dataset}/resource/{resource}/download/ati-nil.csv",
                    "format": "CSV",
                    "size": len(raw),
                }
            ],
        },
    }
    (path / "ati-nil.csv").write_bytes(raw)
    (path / "source-metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (path / "ati-schema.json").write_text(
        json.dumps(
            {
                "resources": [
                    {
                        "resource_name": "ati-nil",
                        "fields": [{"id": "year"}, {"id": "month"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def configure_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str = "rehearsal",
    extra: tuple[str, ...] = (),
) -> SharedFixture:
    """Replace only the GitHub transport while retaining real queue transitions."""
    store = SharedFixture(tmp_path / "state")
    monkeypatch.setattr(TOOL, "GitHubStateStore", lambda _client: store)
    monkeypatch.setattr(TOOL, "build_reviewed_catalogue", lambda _path: CATALOGUE)
    monkeypatch.setenv("GH_TOKEN", "synthetic-test-credential")
    source = (
        "ca-federal-atip.nil-returns.1-1" if action == "capture-ca" else "rehearsal-1-1"
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch",
            action,
            "--source",
            source,
            "--owner-lease",
            "run-1-1",
            "--receipt",
            str(tmp_path / "receipt.json"),
            *extra,
        ],
    )
    return store


def test_cli_rehearsal_and_no_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The explicit hosted rehearsal persists four stage receipts."""
    store = configure_cli(tmp_path, monkeypatch, extra=("--bootstrap",))
    assert TOOL.main() == 0
    assert store.bootstrapped is True
    receipt = json.loads((tmp_path / "receipt.json").read_bytes())
    assert len(receipt["outcomes"]) == 4
    assert receipt["capture_executed"] is False
    with pytest.raises(SystemExit):
        TOOL.main()


def test_real_offline_capture_through_shared_controls(
    ca_source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Actual prepare and cold restore terminate a lease without public credit."""
    output = tmp_path / "package"
    store = configure_cli(
        tmp_path,
        monkeypatch,
        "capture-ca",
        (
            "--input-root",
            str(ca_source),
            "--output-root",
            str(output),
            "--acquisition-authorized",
        ),
    )
    assert TOOL.main() == 0
    stored = store.read("ca-federal-atip.nil-returns.1-1")
    assert stored is not None
    _, queue = _decode(stored.document)
    assert queue.jobs[0].status == "captured"
    assert queue.jobs[0].publication_revision == ""
    assert (output / "ati-nil.csv").read_bytes() == (
        ca_source / "ati-nil.csv"
    ).read_bytes()
    receipt = json.loads((tmp_path / "receipt.json").read_bytes())
    assert receipt["capture_executed"] is True
    assert receipt["outcomes"][-1]["raw_publication_verified"] is False


def test_failed_executor_leaves_lease_and_unknown_capture(
    ca_source: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A timeout or uncertain executor result retains its lease for reconciliation."""
    store = configure_cli(
        tmp_path,
        monkeypatch,
        "capture-ca",
        (
            "--input-root",
            str(ca_source),
            "--output-root",
            str(tmp_path / "out"),
            "--acquisition-authorized",
        ),
    )

    def failed(*_args: object) -> dict:
        message = "private input must not appear"
        raise ValueError(message)

    monkeypatch.setattr(TOOL, "_pilot_step", failed)
    assert TOOL.main() == 1
    stored = store.read("ca-federal-atip.nil-returns.1-1")
    assert stored is not None
    assert _decode(stored.document)[1].jobs[0].status == "leased"
    result = json.loads(capsys.readouterr().out)
    assert result["capture_executed"] is None
    assert "private input" not in json.dumps(result)


def test_missing_credentials_and_wrong_rehearsal_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing identity never reaches the authority backend."""
    store = configure_cli(tmp_path, monkeypatch)
    monkeypatch.delenv("GH_TOKEN")
    assert TOOL.main() == 1
    assert store.keys == set()
    (tmp_path / "receipt.json").unlink()
    monkeypatch.setenv("GH_TOKEN", "synthetic-test-credential")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch",
            "rehearsal",
            "--source",
            "nz-fyi",
            "--receipt",
            str(tmp_path / "receipt.json"),
        ],
    )
    assert TOOL.main() == 1


def test_plan_and_receipt_disk_failure_preserve_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A receipt write failure cannot become a false success or overwrite bytes."""
    configure_cli(tmp_path, monkeypatch, "plan")
    original: Any = Path.open

    def failed(path: Path, *args: object, **kwargs: object) -> object:
        if path.name == "receipt.json":
            message = "private disk detail"
            raise OSError(message)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failed)
    assert TOOL.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "receipt_save_failed"
    assert result["outcomes"][0]["status"] == "planned"


def test_capture_requires_an_actual_reservation(
    ca_source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A no-op reserve cannot start filesystem work."""
    configure_cli(
        tmp_path,
        monkeypatch,
        "capture-ca",
        (
            "--input-root",
            str(ca_source),
            "--output-root",
            str(tmp_path / "out"),
            "--acquisition-authorized",
        ),
    )
    monkeypatch.setattr(TOOL, "reserve", lambda state, *_args: state)
    assert TOOL.main() == 1
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("damage", ["inputs", "exists", "missing", "bytes"])
def test_executor_admission_rejects_invalid_files(
    ca_source: Path, tmp_path: Path, damage: str
) -> None:
    """Malformed local paths and oversized originals fail before reserving work."""
    store = SharedFixture(tmp_path / "state")
    args = request(
        source="ca-federal-atip.nil-returns.1-1",
        input_root=ca_source,
        output_root=tmp_path / "out",
        acquisition_authorized=True,
    )
    if damage == "inputs":
        args.input_root = None
    elif damage == "exists":
        args.output_root.mkdir()
    elif damage == "missing":
        (ca_source / "ati-nil.csv").unlink()
    else:
        with (ca_source / "ati-nil.csv").open("r+b") as handle:
            handle.truncate(24 * 1024 * 1024 + 1)
    with pytest.raises(
        ValueError,
        match=r"offline_executor_inputs|offline_executor_paths|offline_executor_bytes",
    ):
        TOOL.capture_ca(store, args, CATALOGUE, [])
    assert store.keys == set()


@pytest.mark.parametrize(
    ("code", "stdout", "reason"),
    [
        (1, "", "failed"),
        (0, "x" * 65537, "failed"),
        (0, "[]", "receipt"),
        (0, '{"public_upload":true}', "receipt"),
    ],
    ids=["nonzero-exit", "oversized-output", "wrong-envelope", "public-claim"],
)
def test_offline_subprocess_rejects_untrusted_receipts(
    code: int, stdout: str, reason: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A nonzero or malformed child result cannot become retained-byte evidence."""
    monkeypatch.setattr(
        TOOL.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=code, stdout=stdout),
    )
    with pytest.raises(ValueError, match=reason):
        TOOL.__dict__["_pilot_step"]([], TOOL.time.monotonic() + 60)
    with pytest.raises(ValueError, match="runtime_budget"):
        TOOL.__dict__["_pilot_step"]([], -1)


def test_admit_missing_version_and_real_reconciliation_are_blocked(
    tmp_path: Path,
) -> None:
    """Unknown durable reservations and unbound terminal receipts stay fenced."""
    store = SharedFixture(tmp_path / "state")
    with pytest.raises(ValueError, match="reservation_changed"):
        TOOL.__dict__["_admit"](store, request(), 1, 1)
    args = request(
        source="ca-federal-atip.nil-returns.1-1",
        acquisition_authorized=True,
        executor_attached=True,
    )
    TOOL.execute(store, args, CATALOGUE, 1)
    args.action, args.expected_version = "reconcile", 1
    with pytest.raises(ValueError, match="terminal_receipt_required"):
        TOOL.execute(store, args, CATALOGUE, 2)


@pytest.mark.parametrize("damage", ["restore", "bytes", "race"])
def test_late_executor_failure_retains_honest_stages(
    ca_source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Preserve preparation evidence when a later executor stage fails."""
    store = configure_cli(
        tmp_path,
        monkeypatch,
        "capture-ca",
        (
            "--input-root",
            str(ca_source),
            "--output-root",
            str(tmp_path / "out"),
            "--acquisition-authorized",
        ),
    )
    calls = 0

    def step(arguments: list[str], _deadline: float) -> dict[str, str]:
        nonlocal calls
        calls += 1
        folder = Path(arguments[arguments.index("--output") + 1])
        folder.mkdir()
        (folder / "test").write_bytes(b"x")
        if calls == 2:
            if damage == "restore":
                return {"manifest_sha256": "b" * 64}
            if damage == "bytes":
                monkeypatch.setattr(TOOL, "BATCH_BUDGET", Budget(1, 1, 60))
            else:
                stored = store.read("ca-federal-atip.nil-returns.1-1")
                assert stored is not None
                store.compare_and_swap(
                    "ca-federal-atip.nil-returns.1-1", stored.version, stored.document
                )
        return {"manifest_sha256": "a" * 64}

    monkeypatch.setattr(TOOL, "_pilot_step", step)
    assert TOOL.main() == 1
    receipt = json.loads((tmp_path / "receipt.json").read_bytes())
    assert receipt["capture_executed"] is True
    assert any(row["status"] == "package_prepared" for row in receipt["outcomes"])
    assert receipt["local_verification_completed"] is (damage == "race")


def test_entrypoint_missing_credentials_fails_safely(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real script entrypoint uses the same fail-closed command path."""
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch",
            "plan",
            "--source",
            "rehearsal-1-1",
            "--receipt",
            str(tmp_path / "receipt.json"),
        ],
    )
    assert TOOL.__file__ is not None
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(TOOL.__file__, run_name="__main__")
    assert caught.value.code == 1
