"""Config-driven source-set capture tests (multi_source_capture_activation)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx

from archive_govt_nz.cli import capture

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_CONFIG_DIR = "config/source-sets"


def _write_config(
    directory: Path, name: str, *, enabled: bool = True, targets: bool = True
) -> Path:
    """Write one minimal source-set config into *directory*."""
    lines = [
        f'name: "{name}"',
        f"enabled: {str(enabled).lower()}",
        "adapters:",
        '  - "feeds"',
        '  - "threads"',
    ]
    if targets:
        lines += ["targets:", '  - "https://example.govt.nz/notice"']
    path = directory / f"{name}.yml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_capture_unknown_source_set_fails_closed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify capture gate and honest-status behaviour."""
    code = capture("https://x.example", source_type="does-not-exist", format="json")
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "not_configured"


def test_capture_disabled_source_set_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify capture gate and honest-status behaviour."""
    _write_config(tmp_path, "gated", enabled=False)
    code = capture(
        "https://x.example",
        source_type="gated",
        format="json",
        config_dir=tmp_path,
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "disabled"


def test_capture_redirects_source_set_with_dedicated_workflow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify capture gate and honest-status behaviour."""
    config = _write_config(tmp_path, "gazetted", targets=False)
    config.write_text(
        config.read_text(encoding="utf-8")
        + 'dedicated_workflow: "scheduled-gazette-harvest.yml"\n',
        encoding="utf-8",
    )
    code = capture(
        "https://x.example",
        source_type="gazetted",
        format="json",
        config_dir=tmp_path,
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["status"] == "redirected"
    assert payload["dedicated_workflow"] == "scheduled-gazette-harvest.yml"


def test_capture_capability_pending_without_targets(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify capture gate and honest-status behaviour."""
    _write_config(tmp_path, "social", targets=False)
    monkeypatch.chdir(tmp_path)
    code = capture(
        "https://x.example",
        source_type="social",
        format="json",
        config_dir=tmp_path,
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["status"] == "capability_pending"
    assert payload["captured_count"] == 0
    pending_names = [entry["adapter"] for entry in payload["pending_adapters"]]
    assert "threads" in pending_names


def test_capture_runs_real_bounded_capture_for_url_targets(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify capture gate and honest-status behaviour."""
    _write_config(tmp_path, "webset")
    monkeypatch.chdir(tmp_path)

    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, content=b"official gazette notice")
    )
    original_init = httpx.AsyncClient.__init__

    def patched_init(
        self: httpx.AsyncClient,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Force the mock transport into every client instance."""
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)
    store_root = tmp_path / "cas"
    with patch.object(httpx.AsyncClient, "__init__", patched_init):
        code = capture(
            "https://x.example",
            source_type="webset",
            format="json",
            config_dir=tmp_path,
            store_root=store_root,
        )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["status"] == "captured"
    assert payload["captured_count"] == 1
    target_entry = payload["targets"][0]
    assert target_entry["sha256"]
    assert (store_root / "sha256").is_dir()
