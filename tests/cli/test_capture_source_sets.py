"""Config-driven source-set capture tests (multi_source_capture_activation)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx
import pytest

from archive_govt_nz.cli import capture
from archive_govt_nz.source_sets import (
    SourceSetConfigError,
    find_source_set_dir,
    load_source_set,
    parse_source_set_config,
)

if TYPE_CHECKING:
    from pathlib import Path

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


def test_capture_reports_failed_when_all_targets_fail(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All targets failing produces a fail-closed exit with per-target errors."""
    _write_config(tmp_path, "webset")
    monkeypatch.chdir(tmp_path)

    transport = httpx.MockTransport(lambda _request: httpx.Response(500))
    original_init = httpx.AsyncClient.__init__

    def patched_init(
        self: httpx.AsyncClient,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Force the failing mock transport into every client instance."""
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)
    code = capture(
        "https://x.example",
        source_type="webset",
        format="json",
        config_dir=tmp_path,
        store_root=tmp_path / "cas",
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "failed"
    assert payload["failed_count"] == 1
    assert payload["errors"]


def test_capture_reports_partial_outcome_on_mixed_results(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mixed captured/failed targets produce a partial outcome with exit 0."""
    config = _write_config(tmp_path, "webset")
    config.write_text(
        config.read_text(encoding="utf-8") + '  - "https://example.govt.nz/second"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("notice"):
            return httpx.Response(200, content=b"official gazette notice")
        return httpx.Response(503)

    transport = httpx.MockTransport(_handler)
    original_init = httpx.AsyncClient.__init__

    def patched_init(
        self: httpx.AsyncClient,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Force the split-outcome mock transport into every client."""
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)
    code = capture(
        "https://x.example",
        source_type="webset",
        format="json",
        config_dir=tmp_path,
        store_root=tmp_path / "cas",
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["status"] == "partial"
    assert payload["captured_count"] == 1
    assert payload["failed_count"] == 1


def test_find_source_set_dir_walks_upward(tmp_path: Path) -> None:
    """Locate config/source-sets from a nested working directory."""
    (tmp_path / "config" / "source-sets").mkdir(parents=True)
    nested = tmp_path / "deeply" / "nested"
    nested.mkdir(parents=True)
    assert find_source_set_dir(nested) == tmp_path / "config" / "source-sets"


def test_find_source_set_dir_returns_none_when_absent(tmp_path: Path) -> None:
    """Return None when no ancestor contains a source-set directory."""
    assert find_source_set_dir(tmp_path) is None


def test_load_source_set_fails_closed_on_bad_state(tmp_path: Path) -> None:
    """Missing directory, name mismatch, and absence all fail closed."""
    missing_dir = tmp_path / "nowhere"
    with pytest.raises(FileNotFoundError):
        load_source_set("anything", config_dir=missing_dir)

    mismatched = tmp_path / "webset.yml"
    mismatched.write_text('name: "other"\nenabled: true\n', encoding="utf-8")
    with pytest.raises(SourceSetConfigError, match="name mismatch"):
        load_source_set("webset", config_dir=tmp_path)


def test_parser_nested_non_list_line_ends_list_collection(
    tmp_path: Path,
) -> None:
    """An indented scalar after a list block does not become a list item."""
    config_path = tmp_path / "mixed.yml"
    config_path.write_text(
        'name: "mixed"\n'
        "enabled: true\n"
        "targets:\n"
        '  - "https://one.govt.nz"\n'
        "  description: trailing nested scalar\n",
        encoding="utf-8",
    )
    parsed = parse_source_set_config(config_path)
    assert parsed["targets"] == ["https://one.govt.nz"]
