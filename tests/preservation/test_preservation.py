"""Bounded preservation fixture validator tests."""

from pathlib import Path

from archive_govt_nz.preservation import (
    validate_bagit,
    validate_fixture,
    validate_ocfl,
    validate_ro_crate,
)


def test_synthetic_fixture_hashes_close() -> None:
    """Synthetic fixture files match their declared checksums."""
    root = Path("conductor/tracks/preservation_conformance_20260801/fixtures")
    result = validate_fixture(root)
    assert result["synthetic"] is True
    assert result["valid"] is True


def test_missing_profiles_are_explicitly_bounded(tmp_path: Path) -> None:
    """Absent packaging profiles return explicit non-conformance results."""
    assert validate_ro_crate(tmp_path)["valid"] is False
    assert validate_bagit(tmp_path)["valid"] is False
    result = validate_ocfl(tmp_path)
    assert result["valid"] is False
    assert result["conformance_claim"] == "none"
