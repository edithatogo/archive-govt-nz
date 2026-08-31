"""Synthetic, local-only additive inventory contracts."""

from __future__ import annotations

import hashlib
import json
from itertools import permutations
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations import candidate_inventory
from archive_govt_nz.domains.health_appropriations.candidate_inventory import (
    PinnedInput,
    plan_additive_inventory,
)


def _pin(path: Path, value: object) -> PinnedInput:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    return PinnedInput(path, hashlib.sha256(path.read_bytes()).hexdigest())


def _inputs(tmp_path: Path) -> dict[str, Any]:
    profiles = {
        "budget-2026": ("budget", "Budget-2026", "budget_facts", "row_dispositions"),
        "cpi-2026-q2": ("cpi", "Stats-NZ-CPI-2026-Q2", "cpi_facts", "row_dispositions"),
        "befu-2026": ("forecast", "BEFU-2026", "forecast_facts", "cell_dispositions"),
        "hyefu-2025": ("forecast", "HYEFU-2025", "forecast_facts", "cell_dispositions"),
    }
    packages, capture, rights, files = {}, [], [], []
    for name, (family, vintage, facts, dispositions) in profiles.items():
        original = _pin(tmp_path / "base" / "original" / f"{name}.csv", name)
        url = f"https://example.test/{name}.csv"
        resource = {
            "state": "eligible",
            "license": "CC-BY-4.0",
            "evidence": "https://example.test/rights",
            "attribution": "Synthetic agency",
        }
        capture.append(
            {
                "source_id": name,
                "state": "captured",
                "sha256": original.sha256,
                "object_id": "sha256:" + original.sha256,
                "bytes": original.path.stat().st_size,
                "url": url,
                "rights": resource,
            }
        )
        relative = original.path.relative_to(tmp_path / "base").as_posix()
        rights.append(
            {
                "path": relative,
                "source_sha256": original.sha256,
                "source_url": url,
                "license": resource["license"],
                "rights_evidence": resource["evidence"],
                "attribution": resource["attribution"],
            }
        )
        files.append(
            {
                "path": relative,
                "sha256": original.sha256,
                "bytes": original.path.stat().st_size,
            }
        )
        outputs = {}
        for stem in (facts, dispositions, "field_lineage"):
            pin = _pin(tmp_path / name / f"{stem}.parquet", [name, stem])
            outputs[pin.path.name] = pin.sha256
        packages[name] = _pin(
            tmp_path / name / "MANIFEST.json",
            {
                "schema_version": f"archive-govt-nz.health-{family}-extraction/v1",
                "status": "passed",
                "source_vintage": vintage,
                "source_object_sha256": original.sha256,
                "source_locator": url,
                "rights_state": "not_evaluated",
                "output_sha256": outputs,
            },
        )
    rights_pin = _pin(
        tmp_path / "base" / "metadata" / "rights.json", {"resources": rights}
    )
    files.append(
        {
            "path": "metadata/rights.json",
            "sha256": rights_pin.sha256,
            "bytes": rights_pin.path.stat().st_size,
        }
    )
    base = _pin(
        tmp_path / "base" / "MANIFEST.json",
        {
            "schema_version": "archive-govt-nz.health-hf-candidate/v1",
            "dataset": "edithatogo/nz-health-appropriations",
            "files": files,
        },
    )
    return {
        "base": base,
        "capture": _pin(tmp_path / "capture.json", {"results": capture}),
        "rights": rights_pin,
        "packages": packages,
    }


@pytest.fixture
def inputs(tmp_path: Path) -> dict[str, Any]:
    return _inputs(tmp_path)


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_nonfinite_extra_rights_metadata_is_rejected(
    inputs: dict[str, Any], literal: str
) -> None:
    capture = json.loads(inputs["capture"].path.read_bytes())
    capture["results"][0]["rights"]["extra"] = "NONFINITE"
    payload = json.dumps(capture).replace('"NONFINITE"', literal).encode()
    inputs["capture"].path.write_bytes(payload)
    inputs["capture"] = PinnedInput(
        inputs["capture"].path, hashlib.sha256(payload).hexdigest()
    )
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


def test_finite_extra_rights_number_is_retained(inputs: dict[str, Any]) -> None:
    capture = json.loads(inputs["capture"].path.read_bytes())
    capture["results"][0]["rights"]["extra"] = 1.25
    inputs["capture"] = _pin(inputs["capture"].path, capture)
    result = plan_additive_inventory(**inputs)
    package = next(row for row in result["packages"] if row["profile"] == "budget-2026")
    assert package["rights_join"]["recorded_source_rights"]["extra"] == 1.25


def test_inventory_is_deterministic_readonly_and_not_approval(
    inputs: dict[str, Any], tmp_path: Path
) -> None:
    before = {
        str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    }
    result = plan_additive_inventory(**inputs)
    assert result == plan_additive_inventory(**inputs)
    assert result["status"] == "local_inventory_verified"
    assert result["publication_approval"] == "not_granted"
    assert result["semantic_validation"] == "not_performed"
    assert result["candidate_build"] == "not_performed"
    assert result["metadata_overhead"] == "not_planned"
    assert result["change_scope"] == "payload_inventory_only"
    assert (
        result["base_manifest_handling"]
        == "retain_pinned_provenance_new_root_manifest_not_planned"
    )
    assert result["schema_version"] == "archive-govt-nz.health-additive-inventory/v1"
    assert result["base_manifest_sha256"] == inputs["base"].sha256
    assert result["capture_manifest_sha256"] == inputs["capture"].sha256
    assert result["rights_manifest_sha256"] == inputs["rights"].sha256
    assert len(result["additions"]) == 16
    assert result["base_files"] == 5
    assert result["replaced_files"] == []
    assert result["removed_files"] == []
    assert {row["derivative_rights_state"] for row in result["packages"]} == {
        "not_evaluated"
    }
    assert len({row["path"].casefold() for row in result["additions"]}) == 16
    assert result["added_bytes"] == sum(row["bytes"] for row in result["additions"])
    base_manifest = json.loads(inputs["base"].path.read_text())
    assert result["base_bytes"] == sum(row["bytes"] for row in base_manifest["files"])
    for summary in result["packages"]:
        name = summary["profile"]
        package = inputs["packages"][name]
        source = json.loads(package.path.read_text())
        assert summary["manifest_sha256"] == package.sha256
        assert summary["source_vintage"] == source["source_vintage"]
        assert summary["namespace"] == f"data/silver/raw-{name}/v1"
        join = summary["rights_join"]
        assert join["source_id"] == name
        assert join["source_sha256"] == source["source_object_sha256"]
        assert join["source_url"] == source["source_locator"]
        assert join["original_path"] == f"original/{name}.csv"
        assert join["recorded_source_rights"] == {
            "state": "eligible",
            "license": "CC-BY-4.0",
            "evidence": "https://example.test/rights",
            "attribution": "Synthetic agency",
        }
    for row in result["additions"]:
        profile = row["path"].split("/")[2].removeprefix("raw-")
        path = inputs["packages"][profile].path.parent / Path(row["path"]).name
        assert row["bytes"] == path.stat().st_size
        assert row["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert before == {
        str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    }


@pytest.mark.parametrize(
    "target", ["base", "capture", "rights", "package", "base_file", "package_file"]
)
def test_mutated_inputs_rejected(inputs: dict[str, Any], target: str) -> None:
    path = (
        inputs[target].path
        if target in {"base", "capture", "rights"}
        else inputs["packages"]["budget-2026"].path
    )
    if target == "base_file":
        path = inputs["base"].path.parent / "original/budget-2026.csv"
    if target == "package_file":
        path = path.parent / "budget_facts.parquet"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sha256", "0" * 64),
        ("object_id", "sha256:" + "0" * 64),
        ("state", "restricted"),
        ("url", "https://example.test/wrong-vintage"),
        ("bytes", 0),
        ("bytes", True),
        ("source_id", None),
        ("source_id", " "),
    ],
)
def test_capture_join_must_match_exact_original(
    inputs: dict[str, Any], field: str, value: object
) -> None:
    receipt = json.loads(inputs["capture"].path.read_text())
    receipt["results"][0][field] = value
    inputs["capture"] = _pin(inputs["capture"].path, receipt)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


def test_ambiguous_receipt_rejected(inputs: dict[str, Any]) -> None:
    receipt = json.loads(inputs["capture"].path.read_text())
    receipt["results"].append(receipt["results"][0])
    inputs["capture"] = _pin(inputs["capture"].path, receipt)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize("extra", ["extra.parquet", "MANIFEST.JSON"])
def test_extra_package_files_rejected(inputs: dict[str, Any], extra: str) -> None:
    (inputs["packages"]["budget-2026"].path.parent / extra).write_bytes(b"extra")
    with pytest.raises(
        ValueError, match=r"candidate_inventory_contract|source_hash_mismatch"
    ):
        plan_additive_inventory(**inputs)


def _update_base(inputs: dict[str, Any], manifest: dict[str, Any]) -> None:
    inputs["base"] = _pin(inputs["base"].path, manifest)


@pytest.mark.parametrize(
    "value",
    [
        "../escape",
        "/absolute",
        "a//b",
        "a\\b",
        "a/./b",
        "a/../b",
        "CON.txt",
        "a.",
        "",
        ".",
        "é",
        "a b",
        "a:stream",
        "x" * 129,
    ],
)
def test_nonportable_manifest_paths_rejected(
    inputs: dict[str, Any], value: str
) -> None:
    manifest = json.loads(inputs["base"].path.read_text())
    manifest["files"][0]["path"] = value
    _update_base(inputs, manifest)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize(
    "value",
    [
        "original",
        "ORIGINAL/BUDGET-2026.CSV",
        "original/budget-2026.csv",
        "MANIFEST.json",
    ],
)
def test_casefold_and_parent_collisions_rejected(
    inputs: dict[str, Any], value: str
) -> None:
    manifest = json.loads(inputs["base"].path.read_text())
    manifest["files"].append({**manifest["files"][0], "path": value})
    _update_base(inputs, manifest)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize("target", ["base", "capture", "rights"])
@pytest.mark.parametrize("payload", [b"[]", b'{"duplicate":1,"duplicate":2}'])
def test_malformed_pinned_json_rejected(
    inputs: dict[str, Any], target: str, payload: bytes
) -> None:
    path = inputs[target].path
    path.write_bytes(payload)
    inputs[target] = PinnedInput(path, hashlib.sha256(payload).hexdigest())
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "wrong/v1"),
        ("status", "failed"),
        ("rights_state", "eligible"),
        ("source_vintage", "Budget-2025"),
        ("output_sha256", {}),
    ],
)
def test_repinning_does_not_relax_package_profile(
    inputs: dict[str, Any], field: str, value: object
) -> None:
    pin = inputs["packages"]["budget-2026"]
    manifest = json.loads(pin.path.read_text())
    manifest[field] = value
    inputs["packages"]["budget-2026"] = _pin(pin.path, manifest)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("state", "restricted"),
        ("license", ""),
        ("evidence", " "),
        ("attribution", None),
    ],
)
def test_missing_recorded_rights_fail_closed(
    inputs: dict[str, Any], field: str, value: object
) -> None:
    manifest = json.loads(inputs["capture"].path.read_text())
    manifest["results"][0]["rights"][field] = value
    inputs["capture"] = _pin(inputs["capture"].path, manifest)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize(
    "field",
    [
        "source_url",
        "license",
        "rights_evidence",
        "attribution",
        "path",
        "source_sha256",
        "duplicate",
    ],
)
def test_base_resource_rights_must_agree(inputs: dict[str, Any], field: str) -> None:
    manifest = json.loads(inputs["rights"].path.read_text())
    if field == "duplicate":
        manifest["resources"].append(manifest["resources"][0])
    else:
        manifest["resources"][0][field] = "different"
    inputs["rights"] = _pin(inputs["rights"].path, manifest)
    base = json.loads(inputs["base"].path.read_text())
    base["files"][-1].update(
        sha256=inputs["rights"].sha256, bytes=inputs["rights"].path.stat().st_size
    )
    _update_base(inputs, base)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize("kind", ["file", "directory", "extra"])
def test_symlinks_rejected(inputs: dict[str, Any], tmp_path: Path, kind: str) -> None:
    target = inputs["base"].path.parent / "original/budget-2026.csv"
    if kind == "directory":
        target = target.parent
    moved = tmp_path / "retained-target"
    target.rename(moved)
    try:
        target.symlink_to(moved, target_is_directory=kind == "directory")
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {type(error).__name__}")
    if kind == "extra":
        target.rename(target.with_name("extra.csv"))
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


def test_byte_bounds_are_not_disabled(
    inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(candidate_inventory, "MAX_TOTAL_BYTES", 0)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)
    monkeypatch.setattr(candidate_inventory, "MAX_BYTES", 1)
    with pytest.raises(ValueError, match="source_byte_limit"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize("value", [True, 0, -1, "10"])
def test_base_byte_counts_are_exact_integers(
    inputs: dict[str, Any], value: object
) -> None:
    manifest = json.loads(inputs["base"].path.read_text())
    manifest["files"][0]["bytes"] = value
    _update_base(inputs, manifest)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize("order", list(permutations(candidate_inventory.PROFILES)))
def test_profile_order_does_not_define_output(order: tuple[str, ...]) -> None:
    with TemporaryDirectory() as directory:
        values = _inputs(Path(directory))
        expected = plan_additive_inventory(**values)
        values["packages"] = {key: values["packages"][key] for key in order}
        assert plan_additive_inventory(**values) == expected


@given(st.text(max_size=80))
def test_invalid_pins_rejected_before_local_access(value: str) -> None:
    pin = PinnedInput(Path("absent-input"), "!" + value)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(base=pin, capture=pin, rights=pin, packages={})


@pytest.mark.parametrize("field", ["schema_version", "dataset"])
def test_wrong_base_identity_rejected(inputs: dict[str, Any], field: str) -> None:
    manifest = json.loads(inputs["base"].path.read_text())
    manifest[field] = "other"
    _update_base(inputs, manifest)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


def test_all_four_packages_are_required(inputs: dict[str, Any]) -> None:
    inputs["packages"].pop("budget-2026")
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize("target", ["base", "package", "rights"])
def test_alternate_manifest_locations_rejected(
    inputs: dict[str, Any], target: str, tmp_path: Path
) -> None:
    if target == "package":
        pin = inputs["packages"]["budget-2026"]
        path = tmp_path / "different.json"
        path.write_bytes(pin.path.read_bytes())
        inputs["packages"]["budget-2026"] = PinnedInput(path, pin.sha256)
    else:
        pin = inputs[target]
        path = tmp_path / "different.json"
        path.write_bytes(pin.path.read_bytes())
        inputs[target] = PinnedInput(path, pin.sha256)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize("kind", ["missing", "duplicate"])
def test_original_join_requires_exactly_one_base_original(
    inputs: dict[str, Any], kind: str
) -> None:
    base = json.loads(inputs["base"].path.read_text())
    row = base["files"][0]
    source = inputs["base"].path.parent / row["path"]
    copy = inputs["base"].path.parent / "original/second.csv"
    if kind == "missing":
        copy = inputs["base"].path.parent / "not-original.csv"
        source.rename(copy)
        row["path"] = "not-original.csv"
    else:
        copy.write_bytes(source.read_bytes())
        base["files"].append({**row, "path": "original/second.csv"})
    _update_base(inputs, base)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)


@pytest.mark.parametrize(
    "path",
    [
        "data/silver/raw-budget-2026/v1/budget_facts.parquet",
        "DATA/SILVER/RAW-BUDGET-2026/V1/BUDGET_FACTS.PARQUET",
        "data/silver/raw-budget-2026",
    ],
)
def test_additions_cannot_replace_or_overlap_base(
    inputs: dict[str, Any], path: str
) -> None:
    base = json.loads(inputs["base"].path.read_text())
    pin = _pin(inputs["base"].path.parent / path, "retained base")
    base["files"].append(
        {"path": path, "sha256": pin.sha256, "bytes": pin.path.stat().st_size}
    )
    _update_base(inputs, base)
    with pytest.raises(ValueError, match="candidate_inventory_contract"):
        plan_additive_inventory(**inputs)
