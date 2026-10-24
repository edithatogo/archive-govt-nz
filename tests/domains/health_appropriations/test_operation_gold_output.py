"""Native output object pinning, replacement resistance and failure cleanup."""

from __future__ import annotations

import os
from contextlib import nullcontext
from pathlib import Path
from typing import NoReturn

import pytest

from archive_govt_nz.domains.health_appropriations.operation_gold_output import (
    reserve_gold_directory,
)


@pytest.mark.skipif(os.name != "nt", reason="native Windows directory sharing")
@pytest.mark.parametrize("outcome", ["success", "interrupt"])
def test_windows_leaf_and_ancestor_replacement_blocked_until_handles_close(
    tmp_path: Path, outcome: str
) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    output = parent / "output"
    protected = parent / "input"
    protected.mkdir()
    (protected / "original").write_bytes(b"immutable")
    expected = (
        pytest.raises(InterruptedError) if outcome == "interrupt" else nullcontext()
    )
    with expected, reserve_gold_directory(output) as directory:
        for victim in (output, parent):
            with pytest.raises(PermissionError):
                victim.rename(victim.with_name(victim.name + "-swapped"))
        directory.write("payload", b"exact")
        if outcome == "interrupt":
            raise InterruptedError
    assert (output / "payload").read_bytes() == b"exact"
    assert [path.name for path in protected.iterdir()] == ["original"]
    assert (protected / "original").read_bytes() == b"immutable"
    # Both operations must work after success or interruption: no retained locks.
    output.rename(parent / "moved-output")
    parent.rename(tmp_path / "moved-parent")


def test_substitution_immediately_after_reservation_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protected = tmp_path / "input"
    protected.mkdir()
    (protected / "original").write_bytes(b"immutable")
    output = tmp_path / "output"
    original = Path.mkdir

    def swapped(path: Path, *args: object, **kwargs: object) -> None:
        original(path, *args, **kwargs)  # type: ignore[arg-type]
        if path == output:
            path.rename(tmp_path / "reserved")
            try:
                path.symlink_to(protected, target_is_directory=True)
            except OSError:
                pytest.skip("directory symlink creation unavailable")

    monkeypatch.setattr(Path, "mkdir", swapped)
    with (
        pytest.raises((OSError, ValueError)),
        reserve_gold_directory(output) as directory,
    ):
        directory.write("new", b"must not reach input")
    assert [path.name for path in protected.iterdir()] == ["original"]
    assert (protected / "original").read_bytes() == b"immutable"


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptors")
@pytest.mark.parametrize("failure", ["fstat", "fdopen", "body"])
def test_pinned_descriptors_close_on_reservation_write_and_body_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    original_open, original_close = os.open, os.close
    opened: list[int] = []
    closed: list[int] = []

    def opened_descriptor(*args: object, **kwargs: object) -> int:
        descriptor = original_open(*args, **kwargs)  # type: ignore[arg-type]
        opened.append(descriptor)
        return descriptor

    def closed_descriptor(descriptor: int) -> None:
        closed.append(descriptor)
        original_close(descriptor)

    def fail(*_args: object, **_kwargs: object) -> NoReturn:
        message = "injected"
        raise OSError(message)

    monkeypatch.setattr(os, "open", opened_descriptor)
    monkeypatch.setattr(os, "close", closed_descriptor)
    if failure in {"fstat", "fdopen"}:
        monkeypatch.setattr(os, failure, fail)

    def run() -> None:
        with reserve_gold_directory(tmp_path / "output") as directory:
            if failure == "body":
                fail()
            directory.write("payload", b"exact")

    with pytest.raises(OSError, match="injected"):
        run()
    assert opened
    assert closed == list(reversed(opened))
