"""Deterministic release package contracts."""

from pathlib import Path

from archive_govt_nz.release_package import (
    architecture_release_inputs,
    build_release_package,
)


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


def test_architecture_release_inputs_are_canonical_and_packageable() -> None:
    """Future immutable packages include every canonical architecture surface."""
    root = Path.cwd()
    inputs = architecture_release_inputs(root)
    assert tuple(path.relative_to(root).as_posix() for path in inputs) == (
        "docs/archive-system-architecture.md",
        "docs/archive-system-architecture.mmd",
        "docs/archive-system-architecture.svg",
    )
