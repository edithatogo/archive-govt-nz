"""Bootstrap uncertainty, source interruption and exact native execution identity."""

from __future__ import annotations

import io
import json
import subprocess
import zipfile
from typing import TYPE_CHECKING
lazy from pathlib import Path

import httpx
import pytest

from archive_govt_nz.parliament import hosted
from archive_govt_nz.parliament.hosted import bootstrap, github_receipt, github_run, run
from archive_govt_nz.parliament.hosted_transport import POINTER, HostedError, abort
from archive_govt_nz.parliament.publication import publish_batch

from .test_hosted_checkpoint import Remote, initial
from .test_hosted_driver import Batches
from .test_hosted_state import seeded

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class UnknownInitial(Remote):
    """Lose only the response to an initial pointer creation."""

    def __init__(self) -> None:
        """Arm one first-mutation failure."""
        super().__init__()
        self.first = True

    def commit(self, files: dict[str, bytes | Path], parent: str) -> str:
        """Store the mutation, then report an unknown transport outcome once."""
        revision = super().commit(files, parent)
        if self.first and set(files) == {POINTER}:
            self.first = False
            abort("initial_outcome_unknown")
        return revision


def test_bootstrap_unknown_first_pointer_recovers_exact_marker(tmp_path: Path) -> None:
    """Only the original frozen bootstrap may recover an empty shared pointer."""
    root = tmp_path / "source"
    seeded(root)
    index = tmp_path / "index.json"
    index.write_text("{}")
    remote = UnknownInitial()
    with pytest.raises(HostedError, match="initial_outcome_unknown"):
        bootstrap(root, index, remote)
    assert (root / "hosted-authority.json").exists()
    assert (
        run(tmp_path / "scheduled-during-bootstrap", mode="run", transport=remote)[
            "status"
        ]
        == "disabled"
    )
    with pytest.raises(HostedError, match="checkpoint_already_bootstrapped"):
        bootstrap(tmp_path / "imposter", index, remote)
    assert bootstrap(root, index, remote)["status"] == "bootstrap_recovered_disabled"
    assert run(tmp_path / "cold", mode="verify", transport=remote)["objects"] == 0
    with pytest.raises(HostedError, match="checkpoint_already_bootstrapped"):
        bootstrap(root, index, remote)


def test_bootstrap_happy_path_disabled(tmp_path: Path) -> None:
    """A reviewed seed still needs native proof before scheduled acquisition."""
    seeded(tmp_path / "source")
    index = tmp_path / "index.json"
    index.write_text("{}")
    remote = Remote()
    result = bootstrap(tmp_path / "source", index, remote)
    assert result["status"] == "bootstrapped_disabled"
    assert result["checkpoint"]["status"] == "verified"
    assert (
        run(tmp_path / "inactive", mode="run", transport=remote)["status"] == "disabled"
    )


@pytest.mark.parametrize("transient", [False, True])
def test_original_capture_and_one_exact_retry(
    tmp_path: Path, monkeypatch: MonkeyPatch, *, transient: bool
) -> None:
    """Accepted PDFs publish; one transient read retains failure and charges bytes."""
    manager, remote = initial(tmp_path, pending=True)
    manager.release()
    real_client = httpx.AsyncClient
    calls = []

    def request(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        calls.append(req.url.path)
        if transient and len(calls) == 1:
            message = "identified transient"
            raise httpx.ReadTimeout(message, request=req)
        return httpx.Response(
            200,
            content=b"%PDF-1.7\nimmutable original",
            headers={"content-type": "application/pdf"},
        )

    monkeypatch.setattr(
        hosted.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(request), **kw),
    )
    monkeypatch.setattr(
        hosted, "publish_batch", lambda a, b: publish_batch(a, b, hub=Batches(remote))
    )
    result = run(tmp_path / "runner", mode="pilot", transport=remote)
    assert result["summary"]["captured"] == 1
    assert result["summary"]["failed"] == 0
    assert result["attempts"][0]["publication"]["status"] == "verified"
    assert len(calls) == (2 if transient else 1)
    if transient:
        assert result["attempts"][0]["work"]["bytes"] > 64 * 1024 * 1024


def test_native_run_and_artifact_contract(monkeypatch: MonkeyPatch) -> None:
    """Native reads enforce workflow identity, bounded ZIP shape and exact IDs."""
    zipped = io.BytesIO()
    with zipfile.ZipFile(zipped, "w") as archive:
        archive.writestr(
            "receipt.json", json.dumps({"status": "cold_restore_verified"})
        )
    native = {
        "path": ".github/workflows/parliament-continuation.yml",
        "head_branch": "main",
        "event": "workflow_dispatch",
        "status": "completed",
    }

    def gh(args: list[str], **_kw: object) -> subprocess.CompletedProcess[bytes]:
        endpoint = args[-1]
        if endpoint.endswith("/artifacts"):
            data = {
                "artifacts": [
                    {
                        "name": "parliament-receipt-123-1",
                        "expired": False,
                        "id": 42,
                        "size_in_bytes": 100,
                    }
                ]
            }
        elif endpoint.endswith("/zip"):
            return subprocess.CompletedProcess(args, 0, stdout=zipped.getvalue())
        else:
            data = native
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(data).encode())

    monkeypatch.setattr(hosted.subprocess, "run", gh)
    assert github_run("123", "1")["status"] == "completed"
    assert hosted.terminal_owner("gha_123_1")
    assert not hosted.terminal_owner("local_owner")
    assert github_receipt("123")["status"] == "cold_restore_verified"
    with pytest.raises(HostedError, match="github_run_identity"):
        github_run("123/unsafe")
    native["head_branch"] = "untrusted"
    with pytest.raises(HostedError, match="github_run_authority"):
        github_run("123")


@pytest.mark.parametrize(
    ("cycle", "partition", "page"),
    [
        (1, "historical", 80),
        (17, "historical-reconciliation-20261027", 10),
        (19, "late-attachment-reconciliation-20261027", 1),
    ],
)
def test_separate_forward_deep_and_late_lanes(
    tmp_path: Path, cycle: int, partition: str, page: int
) -> None:
    """Page-one title reconciliation cannot reset the independent deep cursor."""
    manager, _remote = initial(tmp_path)
    assert manager.archive is not None
    with manager.archive._connection() as connection:  # noqa: SLF001 - fixture state
        for key, current_page in [
            ("historical", 80),
            ("historical-reconciliation-20261027", 10),
        ]:
            connection.execute(
                "INSERT INTO control VALUES(?,?)",
                (
                    "reports:" + key,
                    json.dumps({"page": current_page, "page_size": 10, "keyword": ""}),
                ),
            )
    manager.cycle = cycle
    hosted.begin(manager)
    assert manager.work is not None
    assert manager.work["partition"] == partition
    assert manager.work["query"]["page"] == page
    assert (
        hosted.controls(manager.archive)["reports:historical-reconciliation-20261027"][
            "page"
        ]
        == 10
    )
    manager.release()


def test_denied_source_pauses_but_cold_verification_can_recover(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """A source restriction stays held while cold verification remains available."""
    manager, remote = initial(tmp_path, pending=True)
    manager.release()
    real_client = httpx.AsyncClient
    requests = []

    def request(req: httpx.Request) -> httpx.Response:
        requests.append(req.url.path)
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(403)

    monkeypatch.setattr(
        hosted.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(request), **kw),
    )
    with pytest.raises(HostedError, match="report_capture_failed"):
        run(tmp_path / "denied", mode="pilot", transport=remote)
    count = len(requests)
    assert (
        run(tmp_path / "paused", mode="pilot", transport=remote)["status"] == "paused"
    )
    verified = run(tmp_path / "verified", mode="verify", transport=remote)
    assert verified["status"] == "cold_restore_verified"
    assert verified["summary"]["failed"] == 1
    assert len(requests) == count


def test_expired_initial_bootstrap_lease_can_recover_under_local_lock(
    tmp_path: Path,
) -> None:
    """A suspended desktop bootstrap renews only its exact frozen marker owner."""
    root = tmp_path / "source"
    seeded(root)
    index = tmp_path / "index.json"
    index.write_text("{}")
    remote = UnknownInitial()
    with pytest.raises(HostedError, match="initial_outcome_unknown"):
        bootstrap(root, index, remote)
    pointer = json.loads(remote.read(POINTER, remote.head()))
    pointer["lease_until"] = 1
    remote.commit({POINTER: json.dumps(pointer).encode()}, remote.head())
    assert bootstrap(root, index, remote)["status"] == "bootstrap_recovered_disabled"
    assert (
        json.loads(remote.read(POINTER, remote.head()))["checkpoint"]["status"]
        == "verified"
    )


@pytest.mark.parametrize("cycle", [1, 17, 19])
def test_recent_only_defers_new_historical_work(tmp_path: Path, cycle: int) -> None:
    """Recurring operation stays recent even at historical selection slots."""
    manager, _remote = initial(tmp_path)
    manager.cycle = cycle
    hosted.begin(manager, recent_only=True)
    assert manager.work is not None
    assert manager.work["partition"] == "recent"
    assert manager.work["query"]["page"] == cycle % 10 + 1
    manager.release()
