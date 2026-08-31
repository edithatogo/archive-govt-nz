"""Shared workbook integrity and non-overwriting output boundaries."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
    write_workbook_outputs,
)


@pytest.mark.parametrize(
    "name",
    [
        "../outside.parquet",
        "/outside.parquet",
        "x\\outside.parquet",
        "C:outside.parquet",
        "MANIFEST.json",
        "con.parquet",
        "aux.parquet",
        "nul.parquet",
        "com1.parquet",
        "lpt9.parquet",
        "",
    ],
)
def test_unsafe_output_names_fail_before_mkdir(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match="invalid_output_name"):
        write_workbook_outputs(tmp_path / "out", {name: pa.table({"x": [1]})}, {})
    assert not (tmp_path / "out").exists()


def test_empty_outputs_and_invalid_snapshot_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty_outputs"):
        write_workbook_outputs(tmp_path / "out", {}, {})
    with pytest.raises(ValueError, match="invalid_source_limit"):
        verified_snapshot(tmp_path / "absent", "a" * 64, max_bytes=0)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("name", ["con_data.parquet", "com10.parquet", "lpt0.parquet"])
def test_device_name_near_matches_are_regular_files(tmp_path: Path, name: str) -> None:
    write_workbook_outputs(tmp_path / "out", {name: pa.table({"x": [1]})}, {})
    assert (tmp_path / "out" / name).is_file()


def test_snapshot_exact_boundary(tmp_path: Path) -> None:
    source = tmp_path / "object"
    source.write_bytes(b"bytes")
    digest = hashlib.sha256(b"bytes").hexdigest()
    assert verified_snapshot(source, digest, max_bytes=5) == b"bytes"
    with pytest.raises(ValueError, match="source_byte_limit"):
        verified_snapshot(source, digest, max_bytes=4)


def test_manifest_encoding_and_directory_collision(tmp_path: Path) -> None:
    receipt = write_workbook_outputs(
        tmp_path / "out", {"facts.parquet": pa.table({"x": [1]})}, {"label": "Māori"}
    )
    content = (tmp_path / "out/MANIFEST.json").read_bytes()
    assert b"\r" not in content
    assert "Māori" in content.decode("utf-8")
    assert receipt["output_sha256"] == {
        "facts.parquet": hashlib.sha256(
            (tmp_path / "out/facts.parquet").read_bytes()
        ).hexdigest()
    }
    with pytest.raises(FileExistsError):
        write_workbook_outputs(
            tmp_path / "out", {"facts.parquet": pa.table({"x": [2]})}, {}
        )
    assert (tmp_path / "out/MANIFEST.json").read_bytes() == content


def test_file_created_after_directory_reservation_is_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "out"
    real_mkdir = Path.mkdir

    def collide(
        path: Path, mode: int = 0o777, *, parents: bool = False, exist_ok: bool = False
    ) -> None:
        real_mkdir(path, mode, parents=parents, exist_ok=exist_ok)
        if path == output:
            (path / "facts.parquet").write_bytes(b"occupied")

    with monkeypatch.context() as patcher:
        patcher.setattr(Path, "mkdir", collide)
        with pytest.raises(FileExistsError):
            write_workbook_outputs(output, {"facts.parquet": pa.table({"x": [1]})}, {})
    assert (output / "facts.parquet").read_bytes() == b"occupied"
    assert not (output / "MANIFEST.json").exists()
