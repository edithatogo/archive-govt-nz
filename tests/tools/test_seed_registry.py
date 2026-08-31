"""Governed seed provenance and fail-closed selection checks."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import runpy
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator, ValidationError

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SEED_ID = "historical-work-ids-0001"
SEED_PATH = Path("seeds/reviewed/historical-work-ids-0001.txt")


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "seed_registry",
        os.environ.get("SEED_REGISTRY_UNDER_TEST", "tools/seed_registry.py"),
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _module()


def _content(data: bytes) -> dict[str, Any]:
    return {
        "line_count": data.count(b"\n"),
        "byte_size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


@pytest.fixture
def fixture_root(tmp_path: Path) -> Path:
    """Copy only the governed inputs for isolation from repository originals."""
    shutil.copytree(ROOT / "seeds", tmp_path / "seeds")
    (tmp_path / "schemas").mkdir()
    shutil.copyfile(
        ROOT / "schemas/seed-registry-v1.schema.json",
        tmp_path / "schemas/seed-registry-v1.schema.json",
    )
    return tmp_path


def test_reviewed_seed() -> None:
    """Select exact reviewed bytes by stable ID and authenticate the Prompt 03 pin."""
    selected = V.resolve_seed(ROOT, SEED_ID)
    assert len(selected["work_ids"]) == 500
    assert selected["work_ids"][0] == "act_imperial_1539_1"
    assert selected["work_ids"][-1] == "act_local_1889_22"
    data = (ROOT / SEED_PATH).read_bytes()
    inventory = V.read_json(
        ROOT
        / "evidence/migrations/corpus-legislation-nz/final-donor-state"
        / "verification-02/prompt04-inventory.json"
    )
    original = next(
        item
        for item in inventory["files"]
        if item["path_parts"] == list(SEED_PATH.parts)
    )
    assert len(data) == original["size_bytes"] == 8987
    assert selected["sha256"] == original["sha256"] == hashlib.sha256(data).hexdigest()
    registry = V.read_json(ROOT / "seeds/registry.json")
    entry = registry["entries"][0]
    assert entry["candidate_count"] == 500
    assert entry["candidate_universe"]["count"] == 33693
    assert entry["acquisition"]["record_count"] == 500
    assert entry["publication"]["record_count"] is None
    receipt = V.read_json(
        ROOT / "evidence/seeds/historical-work-ids-0001/provenance-01.json"
    )
    assert (
        receipt["registry_sha256"]
        == hashlib.sha256((ROOT / "seeds/registry.json").read_bytes()).hexdigest()
    )
    assert (
        receipt["schema_sha256"]
        == hashlib.sha256(
            (ROOT / "schemas/seed-registry-v1.schema.json").read_bytes()
        ).hexdigest()
    )
    assert receipt["content"] == entry["content"]
    assert receipt["source"] == entry["source"]
    assert (
        receipt["verification"]["prompt03_inventory_sha256"]
        == hashlib.sha256(
            (
                ROOT
                / "evidence/migrations/corpus-legislation-nz/final-donor-state"
                / "verification-02/prompt04-inventory.json"
            ).read_bytes()
        ).hexdigest()
    )
    Draft202012Validator.check_schema(
        V.read_json(ROOT / "schemas/seed-registry-v1.schema.json")
    )


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        (b"act_public_2000_1", "terminal LF"),
        (b"act_public_2000_1\r\n", "CR line"),
        (b"act_public_2000_1\n\n", "malformed or blank"),
        (b"\n", "malformed or blank"),
        (b"act_public_2000_1\nact_public_2000_1\n", "duplicate work"),
        (b"act_public_2000_2\nact_public_2000_1\n", "noncanonical order"),
        (b"act_public_2000_1/../../x\n", "malformed or blank"),
        (b" act_public_2000_1\n", "malformed or blank"),
        (b"act_public_2000_1\t\n", "malformed or blank"),
        (b"bill_public_20_1\n", "malformed or blank"),
        (b"bill_public_2000_a\n", "malformed or blank"),
    ],
)
def test_invalid_bytes(data: bytes, reason: str) -> None:
    """Reject defects even when a caller recomputes the content hash."""
    with pytest.raises(ValueError, match=reason):
        V.validate_bytes(data, _content(data))


def test_non_ascii() -> None:
    """Reject Unicode lookalikes without normalization."""
    data = "act_public_2000_\uff11\n".encode()
    with pytest.raises(UnicodeDecodeError):
        V.validate_bytes(data, _content(data))


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("line_count", 2, "line count"),
        ("byte_size", 1, "byte size"),
        ("sha256", "0" * 64, "hash mismatch"),
    ],
)
def test_wrong_pin(field: str, value: object, reason: str) -> None:
    """Each independent content pin is enforced."""
    data = b"act_public_2000_1\n"
    content = _content(data)
    content[field] = value
    with pytest.raises(ValueError, match=reason):
        V.validate_bytes(data, content)


@pytest.mark.parametrize(
    "seed_id",
    ["unknown", "../reviewed/historical-work-ids-0001.txt", "", "/outside/seed"],
)
def test_unknown_id(seed_id: str) -> None:
    """A path string never substitutes for registry identity."""
    with pytest.raises(ValueError, match="unknown seed ID"):
        V.resolve_seed(ROOT, seed_id)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("seed_id", "renamed"),
        ("version", 2),
        ("candidate_count", 33693),
        ("path_parts", ["..", "outside.txt"]),
        ("path_parts", ["/outside/seed"]),
        ("publication", {"status": "published", "record_count": 500}),
        ("last_revalidation", "invalid"),
        ("rights", {"redistribution_clearance": True}),
        ("unexpected", "value"),
    ],
)
def test_registry_rejects_drift(fixture_root: Path, field: str, value: object) -> None:
    """Fail closed on unknown fields, dates, unsafe paths and stage inflation."""
    path = fixture_root / "seeds/registry.json"
    registry = V.read_json(path)
    registry["entries"][0][field] = value
    path.write_text(json.dumps(registry))
    with pytest.raises(ValidationError):
        V.resolve_seed(fixture_root, SEED_ID)


@pytest.mark.parametrize("change", ["replace", "reorder"])
def test_repin_existing_version(fixture_root: Path, change: str) -> None:
    """Changing bytes and matching hashes cannot rewrite a reviewed version."""
    path = fixture_root / SEED_PATH
    data = b"act_public_2000_1\n"
    if change == "reorder":
        data = b"\n".join(reversed(path.read_bytes().splitlines())) + b"\n"
    path.write_bytes(data)
    registry_path = fixture_root / "seeds/registry.json"
    registry = V.read_json(registry_path)
    registry["entries"][0]["content"].update(_content(data))
    registry_path.write_text(json.dumps(registry))
    with pytest.raises(ValidationError):
        V.resolve_seed(fixture_root, SEED_ID)


def test_modified_seed(fixture_root: Path) -> None:
    """The stable-ID resolver checks the file, not just registry assertions."""
    path = fixture_root / SEED_PATH
    path.write_bytes(path.read_bytes().replace(b"1539", b"1538"))
    with pytest.raises(ValueError, match="hash mismatch"):
        V.resolve_seed(fixture_root, SEED_ID)


@pytest.mark.parametrize("operation", ["duplicate", "empty", "missing_field"])
def test_invalid_registry_shape(fixture_root: Path, operation: str) -> None:
    """No duplicate identities or incomplete registry objects are accepted."""
    path = fixture_root / "seeds/registry.json"
    registry = V.read_json(path)
    if operation == "duplicate":
        registry["entries"].append(copy.deepcopy(registry["entries"][0]))
    elif operation == "empty":
        registry["entries"] = []
    else:
        del registry["entries"][0]["source"]
    path.write_text(json.dumps(registry))
    with pytest.raises(ValidationError):
        V.resolve_seed(fixture_root, SEED_ID)


@pytest.mark.parametrize(
    "data", ['{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', "{"]
)
def test_ambiguous_json(tmp_path: Path, data: str) -> None:
    """Reject duplicate keys, nonfinite numbers and invalid syntax."""
    path = tmp_path / "bad.json"
    path.write_text(data)
    with pytest.raises(ValueError, match=r"duplicate JSON|NaN|Infinity|property name"):
        V.read_json(path)


@pytest.mark.parametrize("parent", [False, True])
def test_symlink_seed(fixture_root: Path, parent: bool) -> None:  # noqa: FBT001
    """Reject symlink substitution at either file or governed parent boundary."""
    path = fixture_root / (SEED_PATH.parent if parent else SEED_PATH)
    original = path.with_name("original")
    path.rename(original)
    try:
        path.symlink_to(original, target_is_directory=parent)
    except OSError as exc:
        pytest.skip(f"Host cannot create symlinks: {exc}")
    with pytest.raises(ValueError, match="symlink seed path"):
        V.resolve_seed(fixture_root, SEED_ID)


def test_missing_seed(fixture_root: Path) -> None:
    """Missing inputs fail without a fallback inventory."""
    (fixture_root / SEED_PATH).unlink()
    with pytest.raises(FileNotFoundError):
        V.resolve_seed(fixture_root, SEED_ID)


@given(
    st.lists(
        st.integers(min_value=1, max_value=9999), min_size=1, max_size=30, unique=True
    )
)
def test_order_and_uniqueness_property(numbers: list[int]) -> None:
    """Canonical order is lexical, not numeric; every duplicate is rejected."""
    ids = sorted(f"act_public_2000_{number}" for number in numbers)
    data = ("\n".join(ids) + "\n").encode()
    assert V.validate_bytes(data, _content(data)) == tuple(ids)
    doubled = ("\n".join(sorted([*ids, ids[0]])) + "\n").encode()
    with pytest.raises(ValueError, match="duplicate work"):
        V.validate_bytes(doubled, _content(doubled))


def test_cli(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both callable and script entrypoints print only validated JSON."""
    assert V.main([SEED_ID, "--root", str(ROOT)]) == 0
    assert json.loads(capsys.readouterr().out)["seed_id"] == SEED_ID
    monkeypatch.setattr(sys, "argv", ["seed_registry.py", SEED_ID, "--root", str(ROOT)])
    assert V.__file__ is not None
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(V.__file__, run_name="__main__")
    assert exc.value.code == 0
    assert len(json.loads(capsys.readouterr().out)["work_ids"]) == 500
    with pytest.raises(ValueError, match="unknown seed ID"):
        V.main(["unknown", "--root", str(ROOT)])
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("field", ["commit", "package_sha256", "artifact_id", "run_id"])
def test_origin_binding(fixture_root: Path, field: str) -> None:
    """Validly typed origin changes still require a new reviewed contract."""
    path = fixture_root / "seeds/registry.json"
    registry = V.read_json(path)
    source = registry["entries"][0]["source"]
    source[field] = 1 if isinstance(source[field], int) else "0" * len(source[field])
    path.write_text(json.dumps(registry))
    with pytest.raises(ValidationError):
        V.resolve_seed(fixture_root, SEED_ID)
