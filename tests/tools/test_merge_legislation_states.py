"""Synthetic integrity, algebra and failure tests; no live corpus inputs."""

from __future__ import annotations

import copy
import importlib.util
import io
import os
import runpy
import stat
import sys
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import blake3
import pytest
from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator
from tests.tools import test_verify_final_donor_state as fixtures

from archive_govt_nz.domains.legislation.corpus import LegislationArchiveService

if TYPE_CHECKING:
    from types import ModuleType


def module() -> ModuleType:
    """Allow isolated source-copy mutation without touching tracked code."""
    spec = importlib.util.spec_from_file_location(
        "state_merge",
        os.environ.get("STATE_MERGER_UNDER_TEST", "tools/merge_legislation_states.py"),
    )
    assert spec is not None
    assert spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


M = module()
REVISION = "a" * 40


def fixture(tmp_path: Path, *, donor: bool = False) -> tuple[Path, dict[str, Any]]:
    """Adapt the existing synthetic donor fixture into either parent format."""
    f = fixtures._fixture()  # noqa: SLF001
    archive = fixtures._pack(tmp_path, f)  # noqa: SLF001
    descriptor = {
        "role": "donor" if donor else "target",
        "metadata": f["metadata"],
        "expected": f["expected"],
    }
    if donor:
        with zipfile.ZipFile(archive) as z:
            descriptor["inventory"] = {
                "eligible_for_prompt04": True,
                "artifact_sha256": M.v.sha(archive.read_bytes()),
                "files": [
                    {
                        "path_parts": n.split("/"),
                        "size_bytes": len(z.read(n)),
                        "sha256": M.v.sha(z.read(n)),
                    }
                    for n in z.namelist()
                ],
            }
    else:
        files = {
            n.removeprefix(fixtures.STATE): b
            for n, b in f["files"].items()
            if n.startswith(fixtures.STATE)
        }
        for name in ("manifest", "checkpoint", "harvest"):
            doc = copy.deepcopy(f["docs"][name])
            if name == "harvest":
                doc["works_synced"] = 2
            files[("receipts/" if name == "harvest" else "") + name + ".json"] = (
                M.encoded(doc)
            )
        archive.write_bytes(zip_bytes(list(files.items())))
        descriptor["metadata"]["artifact"].update(
            size_in_bytes=archive.stat().st_size,
            digest="sha256:" + M.v.sha(archive.read_bytes()),
        )
        descriptor["expected"]["artifact"]["digest"] = descriptor["metadata"][
            "artifact"
        ]["digest"]
    return archive, descriptor


def zip_bytes(entries: list[tuple[str | zipfile.ZipInfo, bytes]]) -> bytes:
    """Create a synthetic ZIP in memory."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for name, data in entries:
            z.writestr(name, data)
    return stream.getvalue()


def test_verified_parents_and_complete_readback(tmp_path: Path) -> None:
    """Either independent verifier must pass before a complete package exists."""
    a, b = fixture(tmp_path / "a", donor=True), fixture(tmp_path / "b")
    forward = M.execute([a, b], tmp_path / "forward", REVISION)
    reverse = M.execute([b, a], tmp_path / "reverse", REVISION)
    assert forward == reverse
    assert forward["status"] == "passed"
    assert forward["output"]["records"] == 2
    assert forward["overlap"]["work_id"] == 2
    marker = M.v.load((tmp_path / "forward/COMPLETE.json").read_bytes())
    for entry in marker["files"]:
        path = tmp_path / "forward" / Path(*entry["path_parts"])
        assert M.v.sha(path.read_bytes()) == entry["sha256"]
        assert path.stat().st_mode & 0o222 == 0
    again = M.execute([a, a], tmp_path / "repeat", REVISION)
    assert again["output"] == forward["output"]
    before = (tmp_path / "forward/COMPLETE.json").read_bytes()
    with pytest.raises(FileExistsError):
        M.execute([a, b], tmp_path / "forward", REVISION)
    assert (tmp_path / "forward/COMPLETE.json").read_bytes() == before


def test_cli_and_entrypoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI success and failure produce honest exit codes."""
    archive, descriptor = fixture(tmp_path / "input")
    desc = tmp_path / "descriptor.json"
    desc.write_bytes(M.encoded(descriptor))
    args = [
        "--parent",
        str(archive),
        str(desc),
        "--parent",
        str(archive),
        str(desc),
        "--output",
        str(tmp_path / "out"),
        "--software-commit",
        REVISION,
    ]
    assert M.main(args) == 0
    archive.write_bytes(b"corrupt")
    args[args.index("--output") + 1] = str(tmp_path / "failed")
    assert M.main(args) == 1
    args[args.index("--output") + 1] = str(tmp_path / "entry")
    monkeypatch.setattr(sys, "argv", ["merge", *args])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(M.__file__), run_name="__main__")
    assert exc.value.code == 1


@given(st.lists(st.integers(min_value=1, max_value=8), min_size=1, max_size=12))
def test_union_algebra(numbers: list[int]) -> None:
    """Union is order independent, idempotent, retains versions and shared CAS."""
    f = fixtures._fixture(1)  # noqa: SLF001
    template = f["records"][0]
    digest = template["raw_cas_hash_sha256"]
    data = f["files"][fixtures.CAS + digest[:2] + "/" + digest]
    parents = []
    for n in numbers:
        record = copy.deepcopy(template)
        record["manifestation_id"] = record["manifestation_id"].replace(
            "2001-01-01", f"2001-01-{n:02d}"
        )
        record["canonical_uri"] = record["manifestation_id"]
        record["expression_id"] = record["expression_id"].replace(
            "2001-01-01", f"2001-01-{n:02d}"
        )
        parents.append(
            {
                "manifest": {"records": [record]},
                "checkpoint": f["docs"]["checkpoint"],
                "objects": {digest: data},
            }
        )
    merged = M.canonical_merge(parents)
    assert merged == M.canonical_merge(list(reversed(parents)))
    assert merged == M.canonical_merge([merged, merged])
    assert merged["manifest"]["total_records"] == len(set(numbers))
    assert len(merged["objects"]) == 1
    assert len(merged["versions_by_work"][template["work_id"]]) == len(set(numbers))


@pytest.mark.parametrize(
    "field", ["title", "rights_statement", "canonical_uri", "source_url"]
)
def test_metadata_conflicts(tmp_path: Path, field: str) -> None:
    """Same identity metadata is not silently replaced, even with identical bytes."""
    a = M.parent(*fixture(tmp_path))
    b = copy.deepcopy(a)
    b["manifest"]["records"][0][field] = "conflicting value"
    result = M.canonical_merge([a, b])
    assert result == M.canonical_merge([b, a])
    assert result["status"] == "failed"
    assert result["conflicts"][0]["class"] == "manifestation_metadata_conflict"
    assert result["conflicts"][0]["resolution"] == "blocked_no_winner"


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        (
            "2026-09-01T00:30:00+10:00",
            "2026-08-31T23:00:00Z",
            "2026-08-31T23:00:00Z",
        ),
        (
            "2026-08-31T23:00:00Z",
            "2026-09-01T09:00:00+10:00",
            "2026-09-01T09:00:00+10:00",
        ),
        (
            "2026-08-31T22:00:00Z",
            "2026-08-31T23:00:00Z",
            "2026-08-31T23:00:00Z",
        ),
    ],
)
def test_checkpoint_chronology_is_order_independent(
    tmp_path: Path, first: str, second: str, expected: str
) -> None:
    """Latest instant wins; equal instants retain a deterministic source spelling."""
    a = M.parent(*fixture(tmp_path))
    b = copy.deepcopy(a)
    a["checkpoint"]["last_updated"] = first
    b["checkpoint"]["last_updated"] = second
    result = M.canonical_merge([a, b])
    assert result["checkpoint"]["last_updated"] == expected
    assert result["manifest"]["generated_at"] == expected
    assert result == M.canonical_merge([b, a])
    assert result == M.canonical_merge([result, result])


def test_changed_bytes_and_failed_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changed bytes create individual events; no successful package is emitted."""
    pair = fixture(tmp_path / "a")
    a = M.parent(*pair)
    b = copy.deepcopy(a)
    r = b["manifest"]["records"][0]
    old = r["raw_cas_hash_sha256"]
    data = b"<changed/>"
    digest = M.v.sha(data)
    b["objects"].pop(old)
    b["objects"][digest] = data
    r.update(
        raw_sha256=digest,
        raw_cas_hash_sha256=digest,
        raw_blake3=blake3.blake3(data).hexdigest(),
        raw_cas_hash_blake3=blake3.blake3(data).hexdigest(),
        byte_size=len(data),
    )
    sequence = iter([a, b])
    monkeypatch.setattr(M, "parent", lambda *_args: next(sequence))
    result = M.execute([pair, pair], tmp_path / "out", REVISION)
    assert result["status"] == "failed"
    assert result["conflicts"][0]["class"] == "manifestation_bytes_changed"
    assert not (tmp_path / "out/COMPLETE.json").exists()
    assert not (tmp_path / "out/manifest.json").exists()


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ("missing", "missing_object"),
        ("sha", "object_sha256"),
        ("b3", "object_blake3"),
        ("size", "object_size"),
        ("alias", "hash_alias"),
        ("orphan", "orphan_object"),
        ("duplicate", "duplicate_identity"),
        ("identity", "work_identity"),
    ],
)
def test_objects_fail_closed(tmp_path: Path, change: str, code: str) -> None:
    """No missing, corrupt, ambiguously identified or unreferenced CAS passes."""
    a = M.parent(*fixture(tmp_path))
    records = a["manifest"]["records"]
    files = {M.CAS + d[:2] + "/" + d: data for d, data in a["objects"].items()}
    first = next(iter(files))
    if change == "missing":
        files.pop(first)
    elif change == "sha":
        files[first] = b"bad"
    elif change == "b3":
        records[0]["raw_cas_hash_blake3"] = "b" * 64
    elif change == "size":
        records[0]["byte_size"] += 1
    elif change == "alias":
        records[0]["raw_sha256"] = "c" * 64
    elif change == "orphan":
        files[M.CAS + "orphan"] = b"x"
    elif change == "duplicate":
        records.append(records[0])
    else:
        records[0]["work_id"] = "act_public_2000_9"
    with pytest.raises(M.v.VerificationError, match=code):
        M.objects_for(records, files)


def test_optional_media_and_mutated_input(tmp_path: Path) -> None:
    """Declared media is checked and already verified in-memory bytes rehash."""
    state = M.parent(*fixture(tmp_path))
    state["manifest"]["records"][0]["media_type"] = "application/xml"
    assert M.canonical_merge([state])["status"] == "passed"
    state["objects"][next(iter(state["objects"]))] = b"tampered"
    with pytest.raises(M.v.VerificationError, match="input_object_changed"):
        M.canonical_merge([state])


@pytest.mark.parametrize(
    "name", ["/abs", "../escape", "a/../b", "a//b", "a\\b", "C:drive", "unlisted.json"]
)
def test_archive_paths(name: str) -> None:
    """Reject ambiguous or unexpected ZIP paths before extraction."""
    with pytest.raises(M.v.VerificationError):
        M.read_target(zip_bytes([(name, b"x")]))


def test_archive_structural_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise independent count, expansion, per-member and special-file guards."""
    with pytest.raises(M.v.VerificationError, match="member_count"):
        M.read_target(zip_bytes([]))
    info = zipfile.ZipInfo("manifest.json")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(M.v.VerificationError, match="member_type"):
        M.read_target(zip_bytes([(info, b"link")]))
    with pytest.raises(M.v.VerificationError, match="duplicate_member"):
        M.read_target(zip_bytes([("manifest.json", b"{}"), ("MANIFEST.JSON", b"{}")]))
    with pytest.raises(M.v.VerificationError, match="documents_missing"):
        M.read_target(zip_bytes([("manifest.json", b"{}")]))
    monkeypatch.setattr(M.v, "MAX_MEMBER", 1)
    with pytest.raises(M.v.VerificationError, match="member_size"):
        M.read_target(zip_bytes([("manifest.json", b"{}")]))
    monkeypatch.setattr(M.v, "MAX_EXPANDED", 1)
    with pytest.raises(M.v.VerificationError, match="expanded_size"):
        M.read_target(zip_bytes([("manifest.json", b"{}")]))


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("state_committed", False, "receipt_commit"),
        ("errors", ["error"], "receipt_errors"),
        ("outcome", "unknown", "receipt_outcome"),
        ("works_attempted", 3, "receipt_accounting"),
        ("records_preserved", True, "receipt_counts"),
        ("batch_id", "other", "receipt_batch"),
        ("manifest_sha256", "0" * 64, "receipt_root"),
        ("discovered_works_count", 9, "receipt_inventory"),
        ("schema_version", "wrong", "receipt_schema"),
    ],
)
def test_receipt_corruption(
    tmp_path: Path, field: str, value: object, code: str
) -> None:
    """Target receipt counts describe the batch, not the entire cumulative state."""
    archive, _ = fixture(tmp_path)
    files = M.read_target(archive.read_bytes())
    receipt = M.v.load(files["receipts/harvest.json"])
    receipt[field] = value
    files["receipts/harvest.json"] = M.encoded(receipt)
    with pytest.raises(M.v.VerificationError, match=code):
        M.target_state(files)


def test_output_and_descriptor_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid descriptors and I/O failures produce no completion marker."""
    pair = fixture(tmp_path / "input")
    with pytest.raises(M.v.VerificationError, match="software_revision"):
        M.execute([pair, pair], tmp_path / "rev", "bad")
    with pytest.raises(M.v.VerificationError, match="two_parents"):
        M.execute([pair], tmp_path / "one", REVISION)
    with pytest.raises(M.v.VerificationError, match="external_staging"):
        M.execute([pair, pair], M.v.ROOT / "forbidden-output", REVISION)
    failed = M.execute(
        [(tmp_path / "missing", {}), pair], tmp_path / "missing-out", REVISION
    )
    assert failed["status"] == "failed"
    assert failed["mismatches"] == ["invalid_or_unreadable_input_output"]
    link = tmp_path / "symlink.zip"
    link.symlink_to(pair[0])
    with pytest.raises(M.v.VerificationError, match="archive_symlink"):
        M.parent(link, pair[1])
    with pytest.raises(FileExistsError):
        M.write_exclusive(pair[0], b"overwritten")
    monkeypatch.setattr(M.v, "MAX_ZIP", 1)
    with pytest.raises(M.v.VerificationError, match="archive_size"):
        M.parent(*pair)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ("eligible", "donor_eligible"),
        ("inventory", "donor_inventory_digest"),
        ("names", "donor_inventory_names"),
        ("size", "donor_inventory_size"),
        ("role", "parent_role"),
        ("digest", "archive_digest"),
    ],
)
def test_parent_binding(tmp_path: Path, change: str, code: str) -> None:
    """Authentic artifact and exact Prompt 03 inventory are both necessary."""
    archive, descriptor = fixture(tmp_path, donor=True)
    if change == "eligible":
        descriptor["inventory"]["eligible_for_prompt04"] = False
    elif change == "inventory":
        descriptor["inventory"]["files"][0]["sha256"] = "0" * 64
    elif change == "names":
        descriptor["inventory"]["files"].pop()
    elif change == "size":
        descriptor["inventory"]["files"][0]["size_bytes"] += 1
    elif change == "role":
        descriptor["role"] = "other"
    else:
        descriptor["metadata"]["artifact"]["digest"] = "sha256:" + "0" * 64
        descriptor["expected"]["artifact"]["digest"] = descriptor["metadata"][
            "artifact"
        ]["digest"]
    with pytest.raises(M.v.VerificationError, match=code):
        M.parent(archive, descriptor)


@pytest.mark.parametrize(
    ("document", "field", "value"),
    [
        ("manifest", "manifest_sha256", "0" * 64),
        ("checkpoint", "processed_work_ids", ["different"]),
        ("checkpoint", "last_processed_index", 999),
        ("checkpoint", "total_records_preserved", 1),
    ],
)
def test_parent_roots_and_membership(
    tmp_path: Path, document: str, field: str, value: object
) -> None:
    """Corrupt roots or checkpoint membership cannot enter the union."""
    archive, _ = fixture(tmp_path)
    files = M.read_target(archive.read_bytes())
    doc = M.v.load(files[document + ".json"])
    doc[field] = value
    files[document + ".json"] = M.encoded(doc)
    with pytest.raises(M.v.VerificationError):
        M.target_state(files)


@pytest.mark.parametrize("limit", ["MAX_FILES", "MAX_EXPANDED", "MAX_MEMBER"])
def test_donor_resource_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    """An inventory cannot waive archive resource bounds."""
    pair = fixture(tmp_path, donor=True)
    monkeypatch.setattr(M.v, limit, 1)
    with pytest.raises(M.v.VerificationError):
        M.parent(*pair)


def test_schema_and_native_consumer(tmp_path: Path) -> None:
    """Receipts validate and native consumers accept the canonical continuation."""
    pair = fixture(tmp_path / "parent")
    output = tmp_path / "out"
    receipt = M.execute([pair, pair], output, REVISION)
    schema = M.v.load(
        Path("schemas/legislation-state-merge-v1.schema.json").read_bytes()
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    assert not list(validator.iter_errors(receipt))
    invalid = copy.deepcopy(receipt)
    invalid["conflicts"] = [{}]
    assert list(validator.iter_errors(invalid))
    manifest = LegislationArchiveService.load_manifest(output / "manifest.json")
    assert manifest is not None
    assert manifest["total_records"] == 2
    LegislationArchiveService.validate_checkpoint(
        M.v.load((output / "checkpoint.json").read_bytes())
    )


def test_repeated_archive_descriptor_conflict(tmp_path: Path) -> None:
    """One artifact cannot silently discard a distinct parent descriptor."""
    archive, descriptor = fixture(tmp_path / "parent")
    other = copy.deepcopy(descriptor)
    other["expected"]["audit_context"] = "distinct_pin_context"
    output = tmp_path / "out"
    result = M.execute([(archive, descriptor), (archive, other)], output, REVISION)
    assert result["status"] == "failed"
    assert result["mismatches"] == ["repeated_artifact_descriptor_conflict"]
    assert not (output / "COMPLETE.json").exists()
