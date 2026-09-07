"""Local generator defaults and canonical opt-in never authorize publication."""

import json
import runpy
import socket
import sys
from pathlib import Path

import pytest

from archive_govt_nz.foi_canonical import build_source_index
from archive_govt_nz.foi_catalogue import catalogue_files
from archive_govt_nz.foi_discovery import build_reviewed_catalogue

ROOT = Path(__file__).parents[1]
main = runpy.run_path(str(ROOT / "tools/build_foi_catalogue.py"))["main"]
TRACK = ROOT / "conductor/tracks/global_foi_public_archive_20260830"
SEEDS = ROOT / "config/foi"


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Any attempted socket connection fails the local-only contract."""

    def deny(*_args: object, **_kwargs: object) -> None:
        pytest.fail("local generator attempted network access")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)


@pytest.mark.parametrize("canonical", [False, True])
def test_cli_parity_and_idempotency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    canonical: bool,
) -> None:
    """Default v1 and explicit v2 match the actual in-memory builders exactly."""
    output = tmp_path / "index"
    args = ["build_foi_catalogue.py", "--output", str(output)]
    if canonical:
        args += ["--canonical-track", str(TRACK)]
    monkeypatch.setattr(sys, "argv", args)
    expected = (
        build_source_index(SEEDS, TRACK)
        if canonical
        else catalogue_files(build_reviewed_catalogue(SEEDS))
    )
    assert main() == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["known_sources"] == (255 if canonical else 30)
    assert summary["total_requests"] is None
    assert {p.name: p.read_bytes() for p in output.iterdir()} == expected
    times = {p.name: p.stat().st_mtime_ns for p in output.iterdir()}
    assert main() == 0
    assert {p.name: p.stat().st_mtime_ns for p in output.iterdir()} == times


def test_bad_pin_creates_no_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An invalid canonical input fails before creating or modifying output."""
    track = tmp_path / "track"
    track.mkdir()
    (track / "canonical-inputs-20260907.json").write_bytes(
        (TRACK / "canonical-inputs-20260907.json").read_bytes()
    )
    (track / "country-rollout-20260831.json").write_text("{}")
    output = tmp_path / "output"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_foi_catalogue.py",
            "--canonical-track",
            str(track),
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert not output.exists()


@pytest.mark.parametrize(
    "mode", ["different_file", "directory", "file_link", "output_link", "parent_file"]
)
def test_output_conflicts_leave_all_bytes_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    """Preflight rejects even late conflicts without writing earlier files."""
    output = tmp_path / "index"
    output.mkdir()
    marker = tmp_path / "marker"
    marker.write_bytes(b"keep")
    if mode == "different_file":
        (output / "manifest.json").write_bytes(b"keep")
    elif mode == "directory":
        (output / "manifest.json").mkdir()
    elif mode == "file_link":
        (output / "manifest.json").symlink_to(marker)
    elif mode == "output_link":
        link = tmp_path / "link"
        link.symlink_to(output, target_is_directory=True)
        output = link
    else:
        output = marker / "child"
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_foi_catalogue.py",
            "--canonical-track",
            str(TRACK),
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert marker.read_bytes() == b"keep"
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == before
    if mode == "different_file":
        assert (output / "manifest.json").read_bytes() == b"keep"


def test_script_entrypoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The existing executable script retains its explicit-seeds v1 invocation."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_foi_catalogue.py",
            "--seeds",
            str(SEEDS),
            "--output",
            str(tmp_path / "out"),
        ],
    )
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(ROOT / "tools/build_foi_catalogue.py"), run_name="__main__")
    assert error.value.code == 0
    assert len((tmp_path / "out/sources.jsonl").read_bytes().splitlines()) == 30
