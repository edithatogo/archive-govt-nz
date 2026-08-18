"""Test suite for archive-govt-nz CLI subcommands and compatibility wrappers."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from archive_govt_nz.cli import (
    archive,
    capabilities,
    capture,
    derivatives,
    doctor,
    main,
    provenance,
    publish,
    replay,
    search,
    sources,
    verify,
    version,
)
from archive_govt_nz.cli_compat import (
    compat_nz_govt_social_main,
    compat_sm_govt_nz_main,
)

if TYPE_CHECKING:
    import pytest


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate version text and JSON outputs."""
    version(format="text")
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out

    version(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "version"
    assert payload["status"] == "success"


def test_cli_doctor(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate doctor diagnostics."""
    doctor(format="text")
    captured = capsys.readouterr()
    assert "doctor: status=healthy" in captured.out

    doctor(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "doctor"
    assert payload["status"] == "healthy"


def test_cli_capabilities(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate capabilities list."""
    capabilities(format="text")
    captured = capsys.readouterr()
    assert "cas_dual_hash" in captured.out

    capabilities(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "capabilities"
    assert payload["count"] > 0


def test_cli_sources(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate sources list from seed directory."""
    sources(format="text", registry_path="registry/seeds")
    captured = capsys.readouterr()
    assert "Registered sources" in captured.out

    sources(format="json", registry_path="registry/seeds")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "sources"
    assert payload["registered_sources_count"] > 0


def test_cli_capture(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate capture trigger."""
    capture("https://health.govt.nz", format="text")
    captured = capsys.readouterr()
    assert "Queued capture" in captured.out

    capture("https://health.govt.nz", format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "capture"
    assert payload["status"] == "queued"


def test_cli_archive(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate archive verification."""
    archive(action="verify", format="text")
    captured = capsys.readouterr()
    assert "Archive action 'verify' complete" in captured.out

    archive(action="count", format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "archive"
    assert payload["status"] == "verified"


def test_cli_derivatives(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate derivatives catalog."""
    derivatives(format="text")
    captured = capsys.readouterr()
    assert "parquet_curated_records" in captured.out

    derivatives(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "derivatives"
    assert len(payload["derivatives"]) > 0


def test_cli_search(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate search interface."""
    search("health policy", format="text")
    captured = capsys.readouterr()
    assert "Search for 'health policy'" in captured.out

    search("health policy", format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "search"
    assert payload["query"] == "health policy"


def test_cli_publish(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate publish dry run."""
    publish(target="dry-run", format="text")
    captured = capsys.readouterr()
    assert "Publication target 'dry-run': ready" in captured.out

    publish(target="dry-run", format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "publish"
    assert payload["status"] == "ready"


def test_cli_replay(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate replay interface."""
    replay(verify_all=True, format="text")
    captured = capsys.readouterr()
    assert "Replay fixity drill complete" in captured.out

    replay(verify_all=True, format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "replay"
    assert payload["status"] == "verified"


def test_cli_verify(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate verify interface."""
    verify(format="text")
    captured = capsys.readouterr()
    assert "All 19 integrity checks passed." in captured.out

    verify(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "verify"
    assert payload["status"] == "passed"


def test_cli_provenance(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate provenance interface."""
    provenance(format="text")
    captured = capsys.readouterr()
    assert "Provenance ledger synced" in captured.out

    provenance(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "provenance"
    assert payload["ledger_status"] == "synced"


def test_compat_wrappers(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate legacy compatibility entrypoint deprecation notices."""
    monkeypatch.setattr("archive_govt_nz.cli.app", lambda: None)

    compat_sm_govt_nz_main()
    captured = capsys.readouterr()
    assert "DEPRECATION NOTICE: `sm-govt-nz`" in captured.err

    compat_nz_govt_social_main()
    captured = capsys.readouterr()
    assert "DEPRECATION NOTICE: `nz-govt-social`" in captured.err


def test_main_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate main entrypoint invokes cyclopts app."""
    called = []
    monkeypatch.setattr("archive_govt_nz.cli.app", lambda: called.append(True))
    main()
    assert called == [True]
