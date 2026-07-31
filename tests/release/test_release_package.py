"""Deterministic release package contracts."""

from pathlib import Path

from archive_govt_nz.release_package import build_release_package


def test_release_package_is_reproducible_and_explicit(tmp_path: Path) -> None:
    """Only listed files enter a stable, non-published candidate package."""
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    first.write_text("one", encoding="utf-8")
    second.write_text("two", encoding="utf-8")
    package_a = build_release_package([second, first], tmp_path / "a.tar", tmp_path)
    package_b = build_release_package([first, second], tmp_path / "b.tar", tmp_path)
    assert package_a.sha256 == package_b.sha256
    assert package_a.files == ("one.json", "two.json")
    assert package_a.state == "prepared-not-published"
