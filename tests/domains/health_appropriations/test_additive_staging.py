"""Exclusive staging is copy integrity, never publication approval."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from tests.domains.health_appropriations.test_candidate_inventory import inputs

from archive_govt_nz.domains.health_appropriations import additive_staging
from archive_govt_nz.domains.health_appropriations.additive_staging import (
    MAX_BYTES,
    StagingInputs,
    _copy_inputs,
    _encoded,
    _preflight,
    _readback,
    _snapshot,
    _write,
    stage_additive_bundle,
)
from archive_govt_nz.domains.health_appropriations.candidate_inventory import (
    PinnedInput,
    plan_additive_inventory,
)

__all__ = ["inputs"]


@pytest.fixture
def staging(inputs: dict[str, Any], tmp_path: Path) -> StagingInputs:
    card = inputs["base"].path.parent / "README.md"
    card.write_bytes(b"Historical base card: formerly published candidate.\n")
    manifest = json.loads(inputs["base"].path.read_bytes())
    manifest["files"].append(
        {
            "path": "README.md",
            "sha256": hashlib.sha256(card.read_bytes()).hexdigest(),
            "bytes": card.stat().st_size,
        }
    )
    inputs["base"].path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    inputs["base"] = PinnedInput(
        inputs["base"].path,
        hashlib.sha256(inputs["base"].path.read_bytes()).hexdigest(),
    )
    plan = plan_additive_inventory(**inputs)
    path = tmp_path / "inventory.json"
    path.write_bytes((json.dumps(plan, sort_keys=True) + "\n").encode("utf-8"))
    return StagingInputs(
        **inputs,
        inventory=PinnedInput(path, hashlib.sha256(path.read_bytes()).hexdigest()),
    )


def _output(tmp_path: Path, name: str) -> Path:
    # Inputs and destinations have separate roots, including capture metadata.
    return tmp_path.parent / (tmp_path.name + "-" + name)


def test_inventory_fixture_uses_canonical_utf8_lf(staging: StagingInputs) -> None:
    """The byte-pinned fixture must not inherit platform newline translation."""
    payload = staging.inventory.path.read_bytes()
    assert payload.endswith(b"\n")
    assert b"\r" not in payload
    assert payload == (json.dumps(json.loads(payload), sort_keys=True) + "\n").encode(
        "utf-8"
    )


def test_repinned_crlf_inventory_rejected_before_output(
    staging: StagingInputs, tmp_path: Path
) -> None:
    """A matching digest cannot authorize noncanonical inventory bytes."""
    payload = staging.inventory.path.read_bytes().replace(b"\n", b"\r\n")
    staging.inventory.path.write_bytes(payload)
    changed = replace(
        staging,
        inventory=PinnedInput(
            staging.inventory.path, hashlib.sha256(payload).hexdigest()
        ),
    )
    output = _output(tmp_path, "crlf-inventory")
    with pytest.raises(ValueError, match="additive_staging_contract"):
        stage_additive_bundle(
            changed, output, forbidden_roots=(tmp_path / "candidates",)
        )
    assert not output.exists()


def test_two_builds_preserve_every_input_and_are_not_candidates(
    staging: StagingInputs, tmp_path: Path
) -> None:
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    first, second = _output(tmp_path, "first"), _output(tmp_path, "second")
    forbidden = (tmp_path / "candidates",)
    result = stage_additive_bundle(staging, first, forbidden_roots=forbidden)
    assert result == stage_additive_bundle(staging, second, forbidden_roots=forbidden)
    assert result["status"] == "local_staging_complete"
    assert result["publication_approval"] == "not_granted"
    assert result["semantic_validation"] == "not_performed"
    assert result["new_derivative_rights_state"] == "not_evaluated"
    assert result["base_approval_inherited"] is False
    assert not (first / "MANIFEST.json").exists()
    assert (first / "LOCAL_STAGING.json").is_file()
    assert "not a publication candidate" in (first / "README.md").read_text()
    history = first / "base-history" / staging.base.sha256
    assert (history / "MANIFEST.json").read_bytes() == staging.base.path.read_bytes()
    assert (history / "README.md").read_bytes() == (
        staging.base.path.parent / "README.md"
    ).read_bytes()
    plan = json.loads(staging.inventory.path.read_bytes())
    manifest = json.loads(staging.base.path.read_bytes())
    expected_paths = {
        f"base-history/{staging.base.sha256}/{row['path']}" for row in manifest["files"]
    }
    expected_paths |= {"additions/" + row["path"] for row in plan["additions"]}
    expected_paths |= {
        f"base-history/{staging.base.sha256}/MANIFEST.json",
        "INVENTORY.json",
        "README.md",
    }
    assert {row["path"] for row in result["files"]} == expected_paths
    assert {
        path.relative_to(first).as_posix()
        for path in first.rglob("*")
        if path.is_file()
    } == expected_paths | {"LOCAL_STAGING.json"}
    assert result["scope"] == "staging_copy_integrity_only"
    assert result["schema_version"] == "archive-govt-nz.health-additive-staging/v1"
    assert result["inventory_sha256"] == staging.inventory.sha256
    assert result["base_manifest_sha256"] == staging.base.sha256
    assert json.loads((first / "LOCAL_STAGING.json").read_bytes()) == result
    assert result["files"] == sorted(result["files"], key=lambda row: row["path"])
    assert (
        first / "INVENTORY.json"
    ).read_bytes() == staging.inventory.path.read_bytes()
    for file in result["files"]:
        expected_role = (
            "base_history"
            if file["path"].startswith("base-history/")
            else "addition"
            if file["path"].startswith("additions/")
            else "inventory"
            if file["path"] == "INVENTORY.json"
            else "local_staging_notice"
        )
        assert file["role"] == expected_role
        payload = (first / file["path"]).read_bytes()
        assert payload == (second / file["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == file["sha256"]
        assert len(payload) == file["bytes"]
    assert before == {
        path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    }


def test_changed_plan_is_rejected_before_creating_output(
    staging: StagingInputs, tmp_path: Path
) -> None:
    staging.inventory.path.write_bytes(b"changed")
    output = _output(tmp_path, "failed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        stage_additive_bundle(
            staging, output, forbidden_roots=(tmp_path / "candidates",)
        )
    assert not output.exists()


def test_existing_and_forbidden_roots_are_untouched(
    staging: StagingInputs, tmp_path: Path
) -> None:
    output = _output(tmp_path, "existing")
    output.mkdir()
    sentinel = output / "sentinel"
    sentinel.write_bytes(b"keep")
    with pytest.raises(ValueError, match="additive_staging_contract"):
        stage_additive_bundle(
            staging, output, forbidden_roots=(tmp_path / "candidates",)
        )
    with pytest.raises(ValueError, match="additive_staging_contract"):
        stage_additive_bundle(
            staging,
            tmp_path / "candidates/new",
            forbidden_roots=(tmp_path / "candidates",),
        )
    assert sentinel.read_bytes() == b"keep"
    assert not (tmp_path / "candidates").exists()


def test_failure_keeps_partial_bytes_and_redacted_receipt(
    staging: StagingInputs, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = _output(tmp_path, "partial")

    def fail(*_args: object, **_kwargs: object) -> None:
        message = "synthetic private diagnostic"
        raise OSError(message)

    monkeypatch.setattr(additive_staging, "_readback", fail)
    with pytest.raises(OSError, match="synthetic private diagnostic"):
        stage_additive_bundle(
            staging, output, forbidden_roots=(tmp_path / "candidates",)
        )
    assert not (output / "LOCAL_STAGING.json").exists()
    assert (output / "README.md").is_file()
    receipt = json.loads((output / "FAILURE.json").read_bytes())
    assert receipt == {
        "schema_version": "archive-govt-nz.health-additive-staging-failure/v1",
        "status": "incomplete",
        "error_class": "OSError",
    }
    assert "private" not in json.dumps(receipt)


def test_repinned_wrong_inventory_is_not_authority(
    staging: StagingInputs, tmp_path: Path
) -> None:
    plan = json.loads(staging.inventory.path.read_bytes())
    plan["publication_approval"] = "granted"
    staging.inventory.path.write_bytes(
        (json.dumps(plan, sort_keys=True) + "\n").encode("utf-8")
    )
    changed = replace(
        staging,
        inventory=PinnedInput(
            staging.inventory.path,
            hashlib.sha256(staging.inventory.path.read_bytes()).hexdigest(),
        ),
    )
    output = _output(tmp_path, "wrong-plan")
    with pytest.raises(ValueError, match="additive_staging_contract"):
        stage_additive_bundle(changed, output, forbidden_roots=(tmp_path,))
    assert not output.exists()


@pytest.mark.parametrize(
    "case",
    [
        "empty",
        "inside",
        "equal",
        "ancestor",
        "input",
        "missing-parent",
        "symlink-parent",
        "dangling",
    ],
)
def test_destination_preflight_is_nonmutating(
    staging: StagingInputs, tmp_path: Path, case: str
) -> None:
    output = _output(tmp_path, case)
    forbidden = (tmp_path,)
    if case == "empty":
        forbidden = ()
    elif case == "inside":
        output.mkdir()
        forbidden = (output,)
        output = output / "new"
    elif case == "equal":
        forbidden = (output,)
    elif case == "ancestor":
        forbidden = (output / "nested",)
    elif case == "input":
        output = staging.base.path.parent / "new"
    elif case == "missing-parent":
        output = output / "new"
    elif case == "symlink-parent":
        output.symlink_to(tmp_path, target_is_directory=True)
        output = output / "new"
    elif case == "dangling":
        output.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="additive_staging_contract"):
        stage_additive_bundle(staging, output, forbidden_roots=forbidden)
    assert not output.exists()


@pytest.mark.parametrize("kind", ["base", "capture", "rights", "package"])
def test_changed_pinned_input_rejected_before_output(
    staging: StagingInputs, tmp_path: Path, kind: str
) -> None:
    pin = (
        staging.packages["budget-2026"] if kind == "package" else getattr(staging, kind)
    )
    pin.path.write_bytes(b"changed")
    output = _output(tmp_path, "changed-" + kind)
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        stage_additive_bundle(staging, output, forbidden_roots=(tmp_path,))
    assert not output.exists()


@pytest.mark.parametrize("kind", ["extra", "symlink", "corrupt", "size"])
def test_full_readback_rejects_copy_integrity_failures(
    staging: StagingInputs, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    original = _readback

    def alter(root: Path, files: list[dict[str, Any]]) -> None:
        if kind == "extra":
            (root / "extra").write_bytes(b"unexpected")
        elif kind == "symlink":
            (root / "link").symlink_to(staging.inventory.path)
        elif kind == "corrupt":
            (root / files[0]["path"]).write_bytes(b"corrupt")
        else:
            files[0]["bytes"] += 1
        original(root, files)

    monkeypatch.setattr(additive_staging, "_readback", alter)
    output = _output(tmp_path, "readback-" + kind)
    with pytest.raises(
        ValueError, match=r"additive_staging_contract|source_hash_mismatch"
    ):
        stage_additive_bundle(staging, output, forbidden_roots=(tmp_path,))
    assert not (output / "LOCAL_STAGING.json").exists()
    assert json.loads((output / "FAILURE.json").read_bytes())["status"] == "incomplete"
    before = {
        p: p.read_bytes()
        for p in output.rglob("*")
        if p.is_file() and not p.is_symlink()
    }
    with pytest.raises(ValueError, match="additive_staging_contract"):
        stage_additive_bundle(staging, output, forbidden_roots=(tmp_path,))
    assert before == {
        p: p.read_bytes()
        for p in output.rglob("*")
        if p.is_file() and not p.is_symlink()
    }


def test_copy_rechecks_input_after_preflight(
    staging: StagingInputs, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _copy_inputs

    def alter(
        inputs: StagingInputs, root: Path, plan: dict[str, Any]
    ) -> list[dict[str, Any]]:
        inputs.base.path.write_bytes(b"changed after preflight")
        return original(inputs, root, plan)

    monkeypatch.setattr(additive_staging, "_copy_inputs", alter)
    output = _output(tmp_path, "raced-input")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        stage_additive_bundle(staging, output, forbidden_roots=(tmp_path,))
    assert not (output / "LOCAL_STAGING.json").exists()
    assert (output / "FAILURE.json").is_file()


def test_partial_completion_bytes_are_quarantined(
    staging: StagingInputs, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _write

    def fail(root: Path, relative: str, payload: bytes, role: str) -> dict[str, Any]:
        if relative == "LOCAL_STAGING.json":
            (root / relative).write_bytes(payload[:20])
            message = "synthetic completion failure"
            raise OSError(message)
        return original(root, relative, payload, role)

    monkeypatch.setattr(additive_staging, "_write", fail)
    output = _output(tmp_path, "partial-marker")
    with pytest.raises(OSError, match="synthetic completion failure"):
        stage_additive_bundle(staging, output, forbidden_roots=(tmp_path,))
    assert not (output / "LOCAL_STAGING.json").exists()
    assert (output / "INCOMPLETE_LOCAL_STAGING.json").stat().st_size == 20
    assert (output / "FAILURE.json").is_file()


def test_failed_receipt_preserves_original_error(
    staging: StagingInputs, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    failure = RuntimeError("synthetic original error")

    def fail(root: Path, _files: list[dict[str, Any]]) -> None:
        # An existing receipt prevents exclusive creation without permissions tricks.
        (root / "FAILURE.json").write_bytes(b"retain existing bytes")
        raise failure

    monkeypatch.setattr(additive_staging, "_readback", fail)
    output = _output(tmp_path, "receipt-failed")
    with pytest.raises(RuntimeError) as raised:
        stage_additive_bundle(staging, output, forbidden_roots=(tmp_path,))
    assert raised.value is failure
    assert (output / "FAILURE.json").read_bytes() == b"retain existing bytes"


@pytest.mark.parametrize("parent", [False, True])
def test_inventory_symlink_rejected_before_output(
    staging: StagingInputs, tmp_path: Path, *, parent: bool
) -> None:
    link = tmp_path / "inventory-link"
    if parent:
        link.symlink_to(tmp_path, target_is_directory=True)
        path = link / staging.inventory.path.name
    else:
        link.symlink_to(staging.inventory.path)
        path = link
    changed = replace(staging, inventory=PinnedInput(path, staging.inventory.sha256))
    output = _output(tmp_path, "linked-inventory")
    with pytest.raises(ValueError, match="additive_staging_contract"):
        stage_additive_bundle(changed, output, forbidden_roots=(tmp_path,))
    assert not output.exists()


def test_exclusive_copy_does_not_overwrite_raced_file(
    staging: StagingInputs, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def race(
        inputs: StagingInputs, root: Path, plan: dict[str, Any]
    ) -> list[dict[str, Any]]:
        target = root / "base-history" / inputs.base.sha256 / "MANIFEST.json"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"raced sentinel")
        return _copy_inputs(inputs, root, plan)

    monkeypatch.setattr(additive_staging, "_copy_inputs", race)
    output = _output(tmp_path, "copy-race")
    with pytest.raises(FileExistsError):
        stage_additive_bundle(staging, output, forbidden_roots=(tmp_path,))
    assert (
        output / "base-history" / staging.base.sha256 / "MANIFEST.json"
    ).read_bytes() == b"raced sentinel"
    assert not (output / "LOCAL_STAGING.json").exists()


def test_snapshot_retains_explicit_memory_bound(
    staging: StagingInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert MAX_BYTES == 67_108_864
    calls: list[tuple[Path, str, int]] = []

    def snapshot(path: Path, digest: str, *, max_bytes: int) -> bytes:
        calls.append((path, digest, max_bytes))
        return b"bounded snapshot"

    monkeypatch.setattr(additive_staging, "verified_snapshot", snapshot)
    assert _snapshot(staging.inventory) == b"bounded snapshot"
    assert calls == [(staging.inventory.path, staging.inventory.sha256, 67_108_864)]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_staging_encoder_rejects_nonfinite_json(value: float) -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        _encoded({"extra": value})


def test_raced_output_reservation_is_not_modified(
    staging: StagingInputs, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def race(
        inputs: StagingInputs, output: Path, forbidden: tuple[Path, ...]
    ) -> tuple[dict[str, Any], bytes]:
        result = _preflight(inputs, output, forbidden)
        output.mkdir()
        (output / "sentinel").write_bytes(b"keep")
        return result

    monkeypatch.setattr(additive_staging, "_preflight", race)
    output = _output(tmp_path, "mkdir-race")
    with pytest.raises(FileExistsError):
        stage_additive_bundle(staging, output, forbidden_roots=(tmp_path,))
    assert list(output.iterdir()) == [output / "sentinel"]
    assert (output / "sentinel").read_bytes() == b"keep"
