"""Read-only health checks fail on unfinished expired work, not terminal history."""

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from archive_govt_nz import foi_health
from archive_govt_nz.foi_ownership import OwnerFence
from archive_govt_nz.foi_queue import _encode
from archive_govt_nz.foi_scheduler import Job, Queue
from archive_govt_nz.foi_state import StoredState

SPEC = importlib.util.spec_from_file_location(
    "foi_health_tool", Path(__file__).parents[1] / "tools/foi_health.py"
)
assert SPEC is not None
assert SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


def snapshot(*jobs: Job, version: int = 1) -> dict[str, StoredState]:
    """Create valid synthetic control state without external credentials."""
    owner = OwnerFence("ca", "edithatogo/archive-govt-nz", 1, "owner", 100)
    queue = Queue(
        tuple(jobs), lease_history=tuple(j.lease_id for j in jobs if j.lease_id)
    )
    return {"ca": StoredState(version, _encode(owner, queue), "a" * 64)}


def test_expired_pending_owner_and_capture_are_separate_failures() -> None:
    """Every unfinished owner and expired active capture is surfaced."""
    pending = Job("pending", "ca", 0, 1, 1, 1)
    leased = replace(
        pending,
        id="leased",
        status="leased",
        lease_id="lease",
        attempts=1,
        expires_at=50,
    )
    result = foi_health.evaluate(snapshot(pending, leased), 100)
    assert result["status"] == "failed"
    assert result["finding_counts"] == {
        "owner_expired_with_unfinished_work": 1,
        "capture_lease_expired": 1,
    }
    assert result["affected_sources"] == ["ca"]
    assert result["state_modified"] is False


def test_live_work_is_healthy_and_terminal_old_owners_do_not_fail() -> None:
    """Terminal history does not cause endless alerts after a completed pilot."""
    pending = Job("pending", "ca", 0, 1, 1, 1)
    assert foi_health.evaluate(snapshot(pending), 99)["status"] == "healthy"
    captured = replace(
        pending, id="captured", status="captured", manifest_sha256="a" * 64
    )
    verified = replace(
        pending,
        id="verified",
        status="verified",
        manifest_sha256="a" * 64,
        publication_revision="b" * 40,
    )
    exhausted = replace(pending, id="exhausted", status="exhausted")
    report = foi_health.evaluate(snapshot(captured, verified, exhausted), 10000)
    assert report["status"] == "healthy"
    assert report["job_status_counts"] == {"captured": 1, "verified": 1, "exhausted": 1}
    assert foi_health.evaluate({}, 100)["status"] == "healthy"


def test_capacity_thresholds_are_estimates_and_fail_at_ninety_percent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Near-capacity state needs intervention before the backend rejects writes."""
    assert foi_health.evaluate(snapshot(version=8999), 0)["status"] == "healthy"
    report = foi_health.evaluate(snapshot(version=9000), 0)
    assert report["finding_counts"] == {"state_versions_near_capacity": 1}
    assert report["capacity"]["estimated"] is True
    monkeypatch.setattr(foi_health, "LIMIT", 1)
    assert foi_health.evaluate({}, 0)["finding_counts"] == {
        "state_bytes_near_capacity": 1
    }


@pytest.mark.parametrize("now", [-1, True, "1"])
def test_invalid_clock_rejected(now: int) -> None:
    """A malformed clock cannot suppress an expired lease finding."""
    with pytest.raises(ValueError, match="health_clock"):
        foi_health.evaluate({}, now)


def test_source_identity_and_version_are_checked() -> None:
    """Sanitized findings can contain only bounded source identifiers."""
    state = snapshot()
    for key, stored in [
        ("bad/source", state["ca"]),
        ("other", state["ca"]),
        ("ca", replace(state["ca"], version=True)),
    ]:
        with pytest.raises(ValueError, match="health_source_identity"):
            foi_health.evaluate({key: stored}, 0)


def test_source_details_are_capped_without_losing_failure_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Receipt detail limits cannot turn unresolved failures into success."""
    monkeypatch.setattr(foi_health, "MAX_DETAIL_SOURCES", 0)
    report = foi_health.evaluate(snapshot(Job("a", "ca", 0, 1, 1, 1)), 100)
    assert report["affected_sources"] == []
    assert report["affected_sources_omitted"] == 1
    assert report["affected_source_count"] == 1
    assert report["status"] == "failed"


def test_cli_anonymous_read_and_private_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CLI has no authorization header or mutation calls."""
    client_factory = MagicMock()
    store_factory = MagicMock()
    store_factory.return_value.read_all.return_value = {}
    store_factory.return_value.batch_head = "a" * 40
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(TOOL.httpx, "Client", client_factory)
    monkeypatch.setattr(TOOL, "GitHubStateStore", store_factory)
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(sys, "argv", ["health", "--receipt", str(receipt)])
    assert TOOL.main() == 0
    client_factory.assert_called_once_with(
        timeout=10.0, trust_env=False, follow_redirects=False, headers={}
    )
    assert store_factory.return_value.method_calls == [("read_all", (), {})]
    assert json.loads(receipt.read_bytes())["status"] == "healthy"
    assert receipt.stat().st_mode & 0o777 == 0o600


def test_network_failure_saves_only_error_class(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Private exception text cannot escape in failure evidence."""
    factory = MagicMock(side_effect=httpx.TimeoutException("private detail"))
    monkeypatch.setattr(TOOL.httpx, "Client", factory)
    receipt = tmp_path / "failure.json"
    monkeypatch.setattr(sys, "argv", ["health", "--receipt", str(receipt)])
    assert TOOL.main() == 1
    assert json.loads(receipt.read_bytes())["error_class"] == "TimeoutException"
    assert b"private detail" not in receipt.read_bytes()


def test_receipt_failure_preserves_existing_bytes_and_reports_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failed local receipt never overwrites previous evidence or implies success."""
    factory = MagicMock()
    factory.return_value.read_all.return_value = {}
    factory.return_value.batch_head = "a" * 40
    monkeypatch.setattr(TOOL, "GitHubStateStore", factory)
    receipt = tmp_path / "existing.json"
    receipt.write_bytes(b"previous")
    monkeypatch.setattr(sys, "argv", ["health", "--receipt", str(receipt)])
    assert TOOL.main() == 1
    assert receipt.read_bytes() == b"previous"
    assert json.loads(capsys.readouterr().out)["receipt_saved"] is False


def test_receipt_size_limit_fails_before_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unexpectedly expanded reports cannot fill the evidence destination."""
    monkeypatch.setattr(TOOL, "RECEIPT_LIMIT", 1)
    with pytest.raises(ValueError, match="health_receipt_budget"):
        TOOL.write_receipt(tmp_path / "large.json", {})
    assert not (tmp_path / "large.json").exists()


def test_missing_receipt_parent_is_created_privately(tmp_path: Path) -> None:
    """Create private evidence directories in a fresh workflow checkout."""
    path = tmp_path / "build" / "health.json"
    TOOL.write_receipt(path, {"status": "healthy"})
    assert json.loads(path.read_bytes())["status"] == "healthy"
    assert path.parent.stat().st_mode & 0o777 == 0o700


def test_optional_token_is_only_sent_to_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rate-limit authentication never appears in the health receipt."""
    client = MagicMock()
    factory = MagicMock()
    factory.return_value.read_all.return_value = {}
    factory.return_value.batch_head = "b" * 40
    monkeypatch.setattr(TOOL.httpx, "Client", client)
    monkeypatch.setattr(TOOL, "GitHubStateStore", factory)
    monkeypatch.setenv("GH_TOKEN", "synthetic-health-token")
    receipt = tmp_path / "health.json"
    monkeypatch.setattr(sys, "argv", ["health", "--receipt", str(receipt)])
    assert TOOL.main() == 0
    assert client.call_args.kwargs["headers"] == {
        "Authorization": "Bearer synthetic-health-token"
    }
    assert json.loads(receipt.read_bytes())["authority_commit_sha"] == "b" * 40
    assert b"synthetic-health-token" not in receipt.read_bytes()


@pytest.mark.parametrize("head", [None, "wrong"])
def test_unbound_authority_is_failure_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, head: object
) -> None:
    """A health result must name the exact verified authority commit."""
    factory = MagicMock()
    factory.return_value.read_all.return_value = {}
    factory.return_value.batch_head = head
    monkeypatch.setattr(TOOL, "GitHubStateStore", factory)
    receipt = tmp_path / "health.json"
    monkeypatch.setattr(sys, "argv", ["health", "--receipt", str(receipt)])
    assert TOOL.main() == 1
    assert json.loads(receipt.read_bytes())["error_class"] == "ValueError"
