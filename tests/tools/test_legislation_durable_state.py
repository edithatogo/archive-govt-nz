"""Offline durable-package integrity tests; fixtures are synthetic."""

from __future__ import annotations

import copy
import importlib.util
import io
import os
import runpy
import stat
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator
from tests.tools import test_legislation_parent_state as native
from tests.tools import test_merge_legislation_states as merged

if TYPE_CHECKING:
    from types import ModuleType


def module() -> ModuleType:
    """Load exact source or a fresh mutation copy."""
    spec = importlib.util.spec_from_file_location(
        "durable",
        os.environ.get("DURABLE_UNDER_TEST", "tools/legislation_durable_state.py"),
    )
    assert spec is not None
    assert spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    vars(result)["ROOT"] = Path.cwd()
    result.P.ROOT = Path.cwd()
    return result


D = module()
RIGHTS = {"payload": "blocked", "decision_id": None, "authority_commit": None}
REVISION = "a" * 40


def fixture(tmp: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Canonical synthetic merge with intact originals and both parents."""
    a = merged.fixture(tmp / "donor", donor=True)
    b = merged.fixture(tmp / "target")
    out = tmp / "merged"
    receipt = D.M.execute([a, b], out, REVISION)
    assert receipt["status"] == "passed"
    files = D.P.read_state(out)
    pin = {
        "schema_version": "archive-govt-nz.legislation-durable-input/v1",
        "kind": "merged",
        "marker_sha256": D.v.sha(files["COMPLETE.json"]),
        "receipt_sha256": D.v.sha(files["final-state-merge-receipt.json"]),
        "manifest_sha256": receipt["output"]["manifest_sha256"],
        "source": D.P.source_identity(""),
        "parent_reference": None,
    }
    return files, pin


def repin(files: dict[str, bytes], pin: dict[str, Any]) -> None:
    """Rebind outer fixture pins to isolate deeper semantic guards."""
    inventory = [
        {k: v for k, v in e.items() if k != "blake3"}
        for e in D.inventory({n: b for n, b in files.items() if n != "COMPLETE.json"})
    ]
    files["COMPLETE.json"] = D.M.encoded(
        {"files": inventory, "inventory_sha256": D.v.sha(D.M.encoded(inventory))}
    )
    pin["marker_sha256"] = D.v.sha(files["COMPLETE.json"])
    pin["receipt_sha256"] = D.v.sha(files["final-state-merge-receipt.json"])


def archive_files(raw: bytes) -> dict[str, bytes]:
    """Unpack a synthetic package for tampering, not restoration."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return {n: z.read(n) for n in z.namelist()}


def test_roundtrip_determinism_cold_restore(tmp_path: Path) -> None:
    """Identical state gives identical bytes and restores without source access."""
    files, pin = fixture(tmp_path)
    before = copy.deepcopy(files)
    raw = D.build(files, pin, RIGHTS, REVISION)
    assert raw == D.build(dict(reversed(list(files.items()))), pin, RIGHTS, REVISION)
    document, originals = D.verify(raw, D.v.sha(raw))
    assert originals == before
    assert document["files"] == D.inventory(before)
    package = tmp_path / "state.zip"
    package.write_bytes(raw)
    receipt = D.restore(D.read_package(package), D.v.sha(raw), tmp_path / "restored")
    assert receipt["status"] == "verified_local_restore"
    assert receipt["prompt10_acceptance"] is False
    assert D.P.read_state(tmp_path / "restored") == before
    with pytest.raises(D.v.VerificationError, match="output_exists"):
        D.restore(raw, D.v.sha(raw), tmp_path / "restored")


@pytest.mark.parametrize(
    "field", ["marker_sha256", "receipt_sha256", "manifest_sha256"]
)
def test_wrong_pins(tmp_path: Path, field: str) -> None:
    """External state pins cannot be silently replaced."""
    files, pin = fixture(tmp_path)
    pin[field] = "f" * 64
    with pytest.raises(D.v.VerificationError, match="pinned_"):
        D.build(files, pin, RIGHTS, REVISION)


@pytest.mark.parametrize(
    "change",
    [
        "object",
        "missing",
        "orphan",
        "versions",
        "checkpoint",
        "receipt",
        "parent",
        "descriptor",
        "commit",
        "parent_count",
        "parent_missing",
        "member",
        "source",
    ],
)
def test_inner_state_tampering(tmp_path: Path, change: str) -> None:  # noqa: C901, PLR0912 - independent negative cases
    """Rebound outer pins cannot hide inner object or lineage corruption."""
    files, pin = fixture(tmp_path)
    obj = next(n for n in files if n.startswith("cas/"))
    receipt = D.v.load(files["final-state-merge-receipt.json"])
    parent = receipt["parents"][0]
    if change == "object":
        files[obj] += b"changed"
    elif change == "missing":
        del files[obj]
    elif change == "orphan":
        files["cas/sha256/" + "f" * 2 + "/" + "f" * 64] = b"orphan"
    elif change == "versions":
        files["versions_by_work.json"] = b"{}"
    elif change == "checkpoint":
        c = D.v.load(files["checkpoint.json"])
        c["metadata"]["conditional_requests"] = {"bad": []}
        files["checkpoint.json"] = D.M.encoded(c)
    elif change == "receipt":
        receipt["output"]["objects"] += 1
    elif change == "parent":
        files["parents/" + parent["artifact_sha256"] + "/artifact.zip"] += b"changed"
    elif change == "descriptor":
        parent["descriptor_sha256"] = "f" * 64
    elif change == "commit":
        parent["repository_commit"] = "0" * 40
    elif change == "parent_count":
        receipt["parents"] = []
    elif change == "parent_missing":
        files["parents/" + "f" * 64 + "/descriptor.json"] = b"{}"
    elif change == "member":
        files["receipts/harvest.json"] = b"{}"
    else:
        pin["source"] = D.P.source_identity("historical-work-ids-0001")
    files["final-state-merge-receipt.json"] = D.M.encoded(receipt)
    repin(files, pin)
    with pytest.raises((D.v.VerificationError, ValueError, KeyError, TypeError)):
        D.build(files, pin, RIGHTS, REVISION)


@pytest.mark.parametrize(
    "change",
    [
        "completion",
        "unexpected",
        "metadata",
        "roots",
        "inventory",
        "instructions",
        "canonical_json",
        "encoding",
    ],
)
def test_package_tampering(tmp_path: Path, change: str) -> None:
    """An outer digest alone cannot bless malformed package contents."""
    files, pin = fixture(tmp_path)
    raw = D.build(files, pin, RIGHTS, REVISION)
    parts = archive_files(raw)
    doc = D.v.load(parts["package.json"])
    if change == "completion":
        parts["state/COMPLETE.json"] = b"{}"
    elif change == "unexpected":
        parts["state/unexpected.txt"] = b"x"
    elif change == "metadata":
        doc["unreviewed"] = True
    elif change == "roots":
        doc["roots"]["records"] += 1
    elif change == "inventory":
        doc["files"][0]["blake3"] = "f" * 64
    elif change == "instructions":
        parts["RESTORE.txt"] = b"unsafe instructions"
    parts["package.json"] = D.M.encoded(doc)
    if change == "canonical_json":
        parts["package.json"] += b" "
    altered = D.zip_bytes(parts)
    if change == "encoding":
        altered += b"trailing"
    with pytest.raises((D.v.VerificationError, KeyError)):
        D.verify(altered, D.v.sha(altered))


@pytest.mark.parametrize(
    "change", ["duplicate", "traversal", "symlink", "compressed", "name_normalization"]
)
def test_archive_abuse(tmp_path: Path, change: str) -> None:
    """Duplicate and hostile archive members never reach disk."""
    files, pin = fixture(tmp_path)
    raw = D.build(files, pin, RIGHTS, REVISION)
    parts = archive_files(raw)
    if change in {"symlink", "compressed"}:
        del parts["state/checkpoint.json"]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for name, data in parts.items():
            info = zipfile.ZipInfo(name)
            info.external_attr = (stat.S_IFREG | 0o444) << 16
            z.writestr(info, data)
        info = zipfile.ZipInfo(
            "state/manifest.json" if change == "duplicate" else "state/checkpoint.json"
        )
        info.external_attr = (stat.S_IFREG | 0o444) << 16
        if change == "traversal":
            info.filename = "state/../escape"
        if change == "symlink":
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
        if change == "compressed":
            info.compress_type = zipfile.ZIP_DEFLATED
        if change == "name_normalization":
            info.filename = "state/manifest.jsonX"
        z.writestr(info, b"x" * 10000)
    altered = stream.getvalue()
    if change == "name_normalization":
        altered = altered.replace(b"state/manifest.jsonX", b"state/manifest.json\x00")
    code = {
        "duplicate": "package_duplicate",
        "traversal": "package_path",
        "symlink": "package_member_type",
        "compressed": "package_member_type",
        "name_normalization": "package_spelling",
    }[change]
    with pytest.raises(D.v.VerificationError, match=code):
        D.verify(altered, D.v.sha(altered))


def test_limits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Archive bounds and expected digest apply before restoration."""
    files, pin = fixture(tmp_path)
    raw = D.build(files, pin, RIGHTS, REVISION)
    with pytest.raises(D.v.VerificationError, match="expected_digest"):
        D.verify(raw, "bad")
    with pytest.raises(D.v.VerificationError, match="package_digest"):
        D.verify(raw, "f" * 64)
    monkeypatch.setattr(D, "MAX_PACKAGE", 1)
    with pytest.raises(D.v.VerificationError, match="package_limit"):
        D.verify(raw, D.v.sha(raw))
    with pytest.raises(D.v.VerificationError, match="package_limit"):
        D.zip_bytes(files)
    p = tmp_path / "oversized"
    p.write_bytes(raw)
    with pytest.raises(D.v.VerificationError, match="package_limit"):
        D.read_package(p)
    monkeypatch.setattr(D, "MAX_PACKAGE", 256 * 1024 * 1024)
    monkeypatch.setattr(D.v, "MAX_FILES", 1)
    with pytest.raises(D.v.VerificationError, match="package_count"):
        D.verify(raw, D.v.sha(raw))
    monkeypatch.setattr(D.v, "MAX_FILES", 4096)
    monkeypatch.setattr(D.v, "MAX_MEMBER", 1)
    with pytest.raises(D.v.VerificationError, match="package_member_size"):
        D.verify(raw, D.v.sha(raw))


def test_rights_partial_upload_and_idempotence(tmp_path: Path) -> None:
    """Plans exclude blocked payload and never infer remote success."""
    files, pin = fixture(tmp_path)
    observed = {
        "repository": "edithatogo/corpus-legislation-nz",
        "revision": None,
        "files": {},
    }
    raw = D.build(files, pin, RIGHTS, REVISION)
    blocked = D.publication_plan(raw, D.v.sha(raw), observed)
    assert blocked["payload_blocked"] is True
    assert len(blocked["uploads"]) == 1
    assert blocked["uploads"][0]["path_parts"][-1] == "metadata.json"
    assert b"artifact.zip" not in D.M.encoded(blocked)
    assert b"canonical_uri" not in D.M.encoded(blocked)
    assert blocked["published_revision"] is None
    assert blocked["readback_verified"] is False
    rights = {
        "payload": "public_approved",
        "decision_id": "SYNTHETIC-ONLY",
        "authority_commit": REVISION,
    }
    raw = D.build(files, pin, rights, REVISION)
    plan = D.publication_plan(raw, D.v.sha(raw), observed)
    assert len(plan["uploads"]) == 2
    assert plan["requires_explicit_publication_approval"] is True
    observed["revision"] = REVISION
    first = plan["uploads"][0]
    observed["files"]["/".join(first["path_parts"])] = {
        k: first[k] for k in ("sha256", "size_bytes")
    }
    partial = D.publication_plan(raw, D.v.sha(raw), observed)
    assert [x["action"] for x in partial["uploads"]] == [
        "verify_existing_bytes",
        "upload_after_approval",
    ]
    assert partial == D.publication_plan(raw, D.v.sha(raw), observed)
    observed["files"]["/".join(first["path_parts"])]["sha256"] = "f" * 64
    with pytest.raises(D.v.VerificationError, match="remote_conflict"):
        D.publication_plan(raw, D.v.sha(raw), observed)
    observed["repository"] = "other/repository"
    with pytest.raises(D.v.VerificationError, match="schema_"):
        D.publication_plan(raw, D.v.sha(raw), observed)
    with pytest.raises(D.v.VerificationError, match="schema_"):
        D.build(files, pin, {**RIGHTS, "payload": "public_approved"}, REVISION)


def test_restore_failure_retention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Partial output is retained in quarantine, never promoted or overwritten."""
    files, pin = fixture(tmp_path)
    raw = D.build(files, pin, RIGHTS, REVISION)
    output = tmp_path / "restored"

    def fail(*_args: object) -> None:
        message = "synthetic write failure"
        raise OSError(message)

    monkeypatch.setattr(D.P, "write_new", fail)
    with pytest.raises(OSError, match="synthetic"):
        D.restore(raw, D.v.sha(raw), output)
    assert not output.exists()
    assert (tmp_path / "restored.quarantine").exists()
    with pytest.raises(FileExistsError):
        D.restore(raw, D.v.sha(raw), output)


def test_native_continuation(tmp_path: Path) -> None:
    """Prompt 08 sealed continuations retain and verify their lineage."""
    ref, meta, raw = native.fixture(tmp_path / "native")
    paths = {"output": tmp_path / "state", "quarantine": tmp_path / "q"}
    result = native.P.restore(
        native.request(ref), paths, native.client(meta, raw), "synthetic", native.NOW
    )
    assert result["status"] == "verified"
    files = native.P.read_state(paths["output"])
    (paths["output"] / "receipts/harvest.json").write_bytes(native.v3_harvest(files))
    native.P.seal(paths["output"], native.CONTEXT, paths["quarantine"])
    files = D.P.read_state(paths["output"])
    ref["roots"] = D.P.state_roots(files)
    ref["lineage_sha256"] = D.v.sha(files[D.P.SEAL])
    ref["state_schemas"] = dict(D.P.VERSIONS)
    pin = {
        "schema_version": "archive-govt-nz.legislation-durable-input/v1",
        "kind": "continuation",
        "marker_sha256": ref["lineage_sha256"],
        "receipt_sha256": D.v.sha(files["receipts/harvest.json"]),
        "manifest_sha256": ref["roots"]["manifest_sha256"],
        "source": ref["source"],
        "parent_reference": ref,
    }
    package = D.build(files, pin, RIGHTS, REVISION)
    assert D.verify(package, D.v.sha(package))[1] == files
    pin["marker_sha256"] = "f" * 64
    with pytest.raises(D.v.VerificationError, match="pinned_seal"):
        D.build(files, pin, RIGHTS, REVISION)


def test_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline commands enforce exclusive outputs and explicit inputs."""
    files, pin = fixture(tmp_path)
    p = tmp_path / "pin.json"
    p.write_bytes(D.M.encoded(pin))
    r = tmp_path / "rights.json"
    r.write_bytes(D.M.encoded(RIGHTS))
    package = tmp_path / "package.zip"
    args = [
        "build",
        "--input",
        str(tmp_path / "merged"),
        "--output",
        str(package),
        "--pin",
        str(p),
        "--rights",
        str(r),
        "--software-commit",
        REVISION,
    ]
    assert D.main(args) == 0
    raw = package.read_bytes()
    assert D.main(args) == 1
    args = [
        "verify",
        "--input",
        str(package),
        "--output",
        str(tmp_path / "verified.json"),
        "--digest",
        D.v.sha(raw),
    ]
    assert D.main(args) == 0
    args[0] = "restore"
    args[4] = str(tmp_path / "cold")
    assert D.main(args) == 0
    assert D.P.read_state(tmp_path / "cold") == files
    observation = tmp_path / "observed.json"
    observation.write_bytes(
        D.M.encoded(
            {
                "repository": "edithatogo/corpus-legislation-nz",
                "revision": None,
                "files": {},
            }
        )
    )
    args[0] = "plan"
    args[4] = str(tmp_path / "plan.json")
    assert D.main(args) == 1
    assert D.main([*args, "--observation", str(observation)]) == 0
    assert (
        D.main(["build", "--input", str(tmp_path), "--output", str(tmp_path / "bad")])
        == 1
    )
    monkeypatch.setattr(
        sys, "argv", ["durable", *args, "--observation", str(observation)]
    )
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path("tools/legislation_durable_state.py", run_name="__main__")
    assert exit_info.value.code == 1


@given(st.binary(min_size=1, max_size=80))
@settings(max_examples=20)
def test_arbitrary_corruption_requires_exact_digest(raw: bytes) -> None:
    """Arbitrary bytes cannot pass an unrelated expected hash."""
    with pytest.raises(D.v.VerificationError, match="package_digest"):
        D.verify(raw, "a" * 64)


def test_schemas() -> None:
    """Every new schema is a valid Draft 2020-12 definition."""
    for name in [
        "legislation-durable-input",
        "legislation-durable-package",
        "legislation-preservation-policy",
        "legislation-publication-observation",
    ]:
        schema = D.v.load((Path("schemas") / (name + "-v1.schema.json")).read_bytes())
        Draft202012Validator.check_schema(schema)


@given(offset=st.integers(min_value=0, max_value=10000), reverse=st.booleans())
@settings(max_examples=12, deadline=None)
def test_state_permutation_and_object_mutation(offset: int, *, reverse: bool) -> None:
    """Permutation preserves package identity; altered object bytes never do."""
    with tempfile.TemporaryDirectory() as temp:
        files, pin = fixture(Path(temp).resolve())
        raw = D.build(files, pin, RIGHTS, REVISION)
        reordered = dict(reversed(list(files.items()))) if reverse else dict(files)
        assert D.build(reordered, pin, RIGHTS, REVISION) == raw
        name = next(n for n in files if n.startswith("cas/"))
        data = bytearray(files[name])
        data[offset % len(data)] ^= 1
        files[name] = bytes(data)
        repin(files, pin)
        with pytest.raises(D.v.VerificationError, match="object_sha256"):
            D.build(files, pin, RIGHTS, REVISION)


@pytest.mark.parametrize("change", ["readback", "race", "symlink"])
def test_promotion_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    """Writes remain quarantined if readback or destination exclusivity changes."""
    files, pin = fixture(tmp_path)
    raw = D.build(files, pin, RIGHTS, REVISION)
    output = tmp_path / "restored"
    if change == "symlink":
        output.symlink_to(tmp_path / "merged", target_is_directory=True)
        code = "workspace_symlink"
    elif change == "readback":
        monkeypatch.setattr(D.P, "read_state", lambda _path: {})
        code = "restore_readback"
    else:
        original = D.P.write_new

        def competing(path: Path, data: bytes) -> None:
            original(path, data)
            output.mkdir(exist_ok=True)

        monkeypatch.setattr(D.P, "write_new", competing)
        code = "output_race"
    with pytest.raises(D.v.VerificationError, match=code):
        D.restore(raw, D.v.sha(raw), output)


def test_completion_marker_and_unknown_member(tmp_path: Path) -> None:
    """A newly pinned marker still needs an exact inventory of originals."""
    files, pin = fixture(tmp_path)
    files["COMPLETE.json"] = b"{}"
    pin["marker_sha256"] = D.v.sha(files["COMPLETE.json"])
    with pytest.raises(D.v.VerificationError, match="completion_inventory"):
        D.build(files, pin, RIGHTS, REVISION)
    files["unexpected"] = b"x"
    with pytest.raises(D.v.VerificationError, match="state_member"):
        D.build(files, pin, RIGHTS, REVISION)


def test_verified_package_must_fit_restore_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verification cannot bless state too large for the shared local restorer."""
    files, pin = fixture(tmp_path)
    raw = D.build(files, pin, RIGHTS, REVISION)
    monkeypatch.setattr(D.v, "MAX_EXPANDED", 1)
    with pytest.raises(D.v.VerificationError, match="state_expansion"):
        D.verify(raw, D.v.sha(raw))


def test_package_input_requires_regular_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Special/directory inputs are rejected before any potentially blocking open."""

    def unexpected_open(*_args: object, **_kwargs: object) -> None:
        message = "non-file input was opened"
        raise AssertionError(message)

    monkeypatch.setattr(Path, "open", unexpected_open)
    with pytest.raises(D.v.VerificationError, match="package_regular_file"):
        D.read_package(tmp_path)
