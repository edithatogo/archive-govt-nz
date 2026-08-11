"""Bounded preservation fixture validator tests."""

import hashlib
import json
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
    assert validate_ro_crate(root)["valid"] is True
    assert validate_bagit(root / "bagit")["valid"] is True
    assert validate_ocfl(root / "ocfl")["valid"] is True


def test_missing_profiles_are_explicitly_bounded(tmp_path: Path) -> None:
    """Absent packaging profiles return explicit non-conformance results."""
    assert validate_ro_crate(tmp_path)["valid"] is False
    assert validate_bagit(tmp_path)["valid"] is False
    result = validate_ocfl(tmp_path)
    assert result["valid"] is False
    assert result["conformance_claim"] == "none"


def test_valid_profile_closures_and_invalid_entries(tmp_path: Path) -> None:
    """Bounded validators accept closed fixtures and reject broken entries."""
    payload = tmp_path / "data"
    payload.mkdir()
    source = payload / "value.txt"
    source.write_text("value", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()

    ro = tmp_path / "ro"
    ro.mkdir()
    (ro / "ro-crate-metadata.jsonld").write_text(
        json.dumps({"@graph": [{"@type": "CreativeWork"}]}), encoding="utf-8"
    )
    assert validate_ro_crate(ro)["valid"] is True
    (ro / "ro-crate-metadata.jsonld").write_text("{}", encoding="utf-8")
    assert validate_ro_crate(ro)["valid"] is False

    bag = tmp_path / "bag"
    (bag / "data").mkdir(parents=True)
    (bag / "data" / "value.txt").write_text("value", encoding="utf-8")
    (bag / "bagit.txt").write_text("BagIt-Version: 1.0\n", encoding="utf-8")
    (bag / "manifest-sha256.txt").write_text(
        f"{digest}  data/value.txt\n", encoding="utf-8"
    )
    assert validate_bagit(bag)["valid"] is True
    (bag / "manifest-sha256.txt").write_text("bad  data/value.txt\n", encoding="utf-8")
    assert validate_bagit(bag)["valid"] is False

    ocfl = tmp_path / "ocfl"
    ocfl.mkdir()
    (ocfl / "v1" / "content").mkdir(parents=True)
    (ocfl / "v1" / "content" / "value.txt").write_text("value", encoding="utf-8")
    (ocfl / "inventory.json").write_text(
        json.dumps({"id": "obj-1", "head": "v1", "versions": {"v1": {}}}),
        encoding="utf-8",
    )
    assert validate_ocfl(ocfl)["valid"] is True
    (ocfl / "inventory.json").write_text(
        json.dumps({"id": "obj-1", "head": "v2", "versions": {"v1": {}}}),
        encoding="utf-8",
    )
    assert validate_ocfl(ocfl)["valid"] is False
