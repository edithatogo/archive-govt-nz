"""Seed provenance covers the exact bytes consumed by the catalogue importer."""

import json
import shutil
from pathlib import Path

import pytest

from archive_govt_nz.foi_catalogue import load_seeds

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("mode", ["omitted", "duplicate", "substituted", "role"])
def test_provenance_requires_exact_seed_inventory(tmp_path: Path, mode: str) -> None:
    """Valid hashes for other files cannot stand in for a consumed seed."""
    folder = tmp_path / "seeds"
    shutil.copytree(ROOT / "config/foi", folder)
    path = folder / "seed-provenance.json"
    provenance = json.loads(path.read_bytes())
    if mode == "omitted":
        provenance["files"].pop(0)
    elif mode == "duplicate":
        provenance["files"].append(provenance["files"][0])
    elif mode == "substituted":
        shutil.copyfile(folder / "donor-instances.json", folder / "substitute.json")
        provenance["files"][0]["local_file"] = "substitute.json"
    else:
        provenance["universe"], provenance["hf_snapshot"] = (
            provenance["hf_snapshot"],
            provenance["universe"],
        )
    path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError, match="seed provenance"):
        load_seeds(folder)


@pytest.mark.parametrize("name", ["seed-provenance.json", "donor-instances.json"])
def test_symlinked_seed_inputs_fail_closed(tmp_path: Path, name: str) -> None:
    """A matching hash does not permit a seed to escape through a symlink."""
    folder = tmp_path / "seeds"
    shutil.copytree(ROOT / "config/foi", folder)
    path = folder / name
    outside = tmp_path / name
    path.rename(outside)
    try:
        path.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable on this platform")
    with pytest.raises(ValueError, match="seed provenance"):
        load_seeds(folder)


def test_seed_documents_are_parsed_from_verified_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changing a seed on a second read must not inject an unverified document."""
    original = Path.read_bytes
    counts: dict[str, int] = {}

    def read_bytes(path: Path) -> bytes:
        counts[path.name] = counts.get(path.name, 0) + 1
        return original(path)

    def read_text(path: Path, *_args: object, **_kwargs: object) -> str:
        if path.name == "donor-instances.json":
            return '{"instances": []}'
        return original(path).decode("utf-8")

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    monkeypatch.setattr(Path, "read_text", read_text)
    _, instances, _, _ = load_seeds(ROOT / "config/foi")
    assert len(instances) == 23
    assert counts["donor-instances.json"] == 1
