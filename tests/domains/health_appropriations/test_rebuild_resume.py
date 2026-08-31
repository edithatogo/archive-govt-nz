"""Read-only planning never promotes partial or unpinned extraction stages."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import rebuild, rebuild_resume
from archive_govt_nz.domains.health_appropriations.rebuild_resume import _CELLS, _FACTS
from archive_govt_nz.object_store import ContentAddressedStore

OBSERVED = "2026-08-30T00:00:00Z"


def _json(path: Path, value: object) -> str:
    payload = json.dumps(value, sort_keys=True).encode()
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _inputs(root: Path) -> dict[str, Any]:
    store = ContentAddressedStore(root / "bronze")
    objects = []
    for name, profile in rebuild.PROFILES.items():
        receipt = store.put_bytes(name.encode())
        objects.append(
            {"path": "data/raw/" + profile.filename, "object_id": receipt.object_id}
        )
    donor = root / "donor.json"
    pin = _json(
        donor,
        {
            "schema_version": "archive-govt-nz.health-donor-manifest/v1",
            "objects": objects,
        },
    )
    plan = rebuild.plan_rebuild(donor, root / "bronze", pin, OBSERVED)
    previous = root / "previous"
    previous.mkdir()
    old_pin = _json(previous / "PLAN.json", plan)
    return {
        "donor_manifest": donor,
        "donor_manifest_sha256": pin,
        "previous_run": previous,
        "previous_plan_sha256": old_pin,
        "store_root": root / "bronze",
        "observed_at": OBSERVED,
        "stage_manifest_sha256": {},
    }


def test_missing_stages_are_readonly_reextraction(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    before = {
        str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    }
    result = rebuild_resume.plan_resume(**inputs)
    assert result["schema_version"] == "archive-govt-nz.health-readonly-resume-plan/v1"
    assert result["source_verification_scope"] == "selected_four_originals_only"
    assert result["selected_source_bytes"] == 25
    assert result["execution"] == "not_performed"
    assert all(
        row["action"] == "reextract" and row["reason"] == "missing_stage"
        for row in result["stages"].values()
    )
    assert {
        str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    } == before
    assert rebuild_resume.plan_resume(**inputs) == result


def test_parquet_metadata_limits_are_supplied_before_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    _stage(inputs, "budget")
    real = pq.ParquetFile
    calls = []

    def bounded(source: object, **kwargs: int) -> pq.ParquetFile:
        assert kwargs == {
            "thrift_string_size_limit": rebuild_resume.MAX_THRIFT_STRING_BYTES,
            "thrift_container_size_limit": rebuild_resume.MAX_THRIFT_CONTAINERS,
        }
        calls.append(True)
        return real(
            source,
            thrift_string_size_limit=kwargs["thrift_string_size_limit"],
            thrift_container_size_limit=kwargs["thrift_container_size_limit"],
        )

    monkeypatch.setattr(rebuild_resume.pq, "ParquetFile", bounded)
    assert (
        rebuild_resume.plan_resume(**inputs)["stages"]["budget"]["action"]
        == "reuse_verified"
    )
    assert len(calls) == 3


@pytest.mark.parametrize("stage", [True, False])
def test_directory_enumeration_is_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, stage: bool
) -> None:
    inputs = _inputs(tmp_path)
    root, _ = _stage(inputs, "budget")
    target = root if stage else inputs["previous_run"]
    maximum = 5 if stage else 7
    original = Path.iterdir
    seen = []

    def bounded(path: Path) -> Iterator[Path]:
        if path == target:
            for index in range(maximum + 1):
                seen.append(index)
                if index == maximum:
                    pytest.fail("read beyond bounded directory window")
                yield target / f"unexpected-{index}"
        else:
            yield from original(path)

    monkeypatch.setattr(Path, "iterdir", bounded)
    if stage:
        assert (
            rebuild_resume.plan_resume(**inputs)["stages"]["budget"]["reason"]
            == "incomplete_stage"
        )
    else:
        with pytest.raises(ValueError, match="resume_input_contract"):
            rebuild_resume.plan_resume(**inputs)
    assert len(seen) == maximum


@pytest.mark.parametrize("key", ["donor_manifest_sha256", "previous_plan_sha256"])
def test_pins_fail_closed(tmp_path: Path, key: str) -> None:
    inputs = _inputs(tmp_path)
    inputs[key] = "0" * 64
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        rebuild_resume.plan_resume(**inputs)


def _stage(inputs: dict[str, Any], name: str) -> tuple[Path, dict[str, Any]]:
    root = inputs["previous_run"] / name
    root.mkdir()
    plan = json.loads((inputs["previous_run"] / "PLAN.json").read_bytes())
    source = plan["sources"][name]
    context = {
        "source_object_sha256": source["sha256"],
        "source_locator": source["locator"],
        "source_vintage": source["vintage"],
        "observed_at": plan["observed_at"],
    }
    schemas = (
        rebuild_resume.HISTORICAL_SCHEMAS
        if name == "historical"
        else dict(
            zip(
                rebuild.PROFILES[name].outputs,
                (
                    _FACTS,
                    rebuild_resume.LINEAGE_SCHEMA,
                    rebuild_resume.DISPOSITION_SCHEMA if name == "budget" else _CELLS,
                ),
                strict=True,
            )
        )
    )
    outputs = {}
    for filename, schema in schemas.items():
        row = {
            field: value for field, value in context.items() if field in schema.names
        }
        if "observed_at" in row:
            row["observed_at"] = datetime.fromisoformat(row["observed_at"])
        pq.write_table(pa.Table.from_pylist([row], schema=schema), root / filename)
        outputs[filename] = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    counts = (
        {"facts": 1, "lineage": 1, "dispositions": 1, "rejected": 0}
        if name == "historical"
        else {"normalized": 1, "rejected": 0, "input": 1, "out_of_scope": 0, "blank": 0}
        if name == "budget"
        else {
            "normalized": 1,
            "rejected": 0,
            "inventoried_cells": 1,
            "context": 0,
            "preserved_only": 0,
        }
    )
    manifest = dict(
        schema_version=rebuild.PROFILES[name].schema,
        status="passed",
        **context,
        output_sha256=outputs,
        counts=counts,
        transformation_id=(
            "budget-expenditure/v1"
            if name == "budget"
            else "treasury-historical-health-gdp/v1"
            if name == "historical"
            else "treasury-health-expense-summary/v1"
        ),
    )
    if name in {"befu", "hyefu"}:
        manifest["profile"] = name
    inputs["stage_manifest_sha256"][name] = _json(root / "MANIFEST.json", manifest)
    return root, manifest


@pytest.mark.parametrize("name", tuple(rebuild.PROFILES))
def test_pinned_transport_stage_is_reusable(tmp_path: Path, name: str) -> None:
    inputs = _inputs(tmp_path)
    _stage(inputs, name)
    result = rebuild_resume.plan_resume(**inputs)
    assert result["stages"][name] == {
        "action": "reuse_verified",
        "reason": "pinned_structure_verified",
        "manifest_sha256": inputs["stage_manifest_sha256"][name],
        "rows": dict.fromkeys(rebuild.PROFILES[name].outputs, 1),
    }
    assert result["stage_manifest_sha256"] == inputs["stage_manifest_sha256"]
    assert result["semantic_validation"] == "not_performed"
    assert result["rights_state"] == "not_evaluated"


@pytest.mark.parametrize(
    ("name", "key"),
    [
        ("budget", "normalized"),
        ("budget", "input"),
        ("befu", "normalized"),
        ("hyefu", "inventoried_cells"),
        ("historical", "facts"),
        ("historical", "lineage"),
        ("historical", "dispositions"),
    ],
)
def test_manifest_counts_must_match_transport(
    tmp_path: Path, name: str, key: str
) -> None:
    inputs = _inputs(tmp_path)
    root, manifest = _stage(inputs, name)
    manifest["counts"][key] = 2
    inputs["stage_manifest_sha256"][name] = _json(root / "MANIFEST.json", manifest)
    assert (
        rebuild_resume.plan_resume(**inputs)["stages"][name]["reason"]
        == "invalid_stage_payload"
    )


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("missing", "incomplete_stage"),
        ("extra", "incomplete_stage"),
        ("corrupt_manifest", "invalid_stage_manifest"),
        ("corrupt_payload", "invalid_stage_payload"),
        ("partial", "stage_not_passed"),
        ("unpinned", "unpinned_stage"),
    ],
)
def test_expected_damage_is_redacted_reextraction(
    tmp_path: Path, kind: str, reason: str
) -> None:
    inputs = _inputs(tmp_path)
    root, manifest = _stage(inputs, "budget")
    if kind == "missing":
        (root / "field_lineage.parquet").rename(root.parent / "retained-lineage")
        (root.parent / "retained-lineage").rename(tmp_path / "retained-lineage")
    elif kind == "extra":
        (root / "unexpected").write_bytes(b"private text")
    elif kind == "corrupt_manifest":
        (root / "MANIFEST.json").write_bytes(b"private text")
    elif kind == "corrupt_payload":
        (root / "field_lineage.parquet").write_bytes(b"private text")
    elif kind == "partial":
        manifest["status"] = "partial"
        inputs["stage_manifest_sha256"]["budget"] = _json(
            root / "MANIFEST.json", manifest
        )
    else:
        inputs["stage_manifest_sha256"] = {}
    result = rebuild_resume.plan_resume(**inputs)
    assert result["stages"]["budget"] == {"action": "reextract", "reason": reason}
    assert "private text" not in json.dumps(result)


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "source_object_sha256",
        "source_locator",
        "source_vintage",
        "observed_at",
    ],
)
def test_stage_context_mismatch_is_global_failure(tmp_path: Path, field: str) -> None:
    inputs = _inputs(tmp_path)
    root, manifest = _stage(inputs, "budget")
    manifest[field] = "contradiction"
    inputs["stage_manifest_sha256"]["budget"] = _json(root / "MANIFEST.json", manifest)
    with pytest.raises(ValueError, match="stage_context_mismatch"):
        rebuild_resume.plan_resume(**inputs)


@pytest.mark.parametrize(
    "kind",
    ["stage", "manifest", "payload", "source", "old_plan", "donor", "root_parent"],
)
def test_symlinks_fail_closed_even_without_stage_pin(tmp_path: Path, kind: str) -> None:
    inputs = _inputs(tmp_path)
    root, _ = _stage(inputs, "budget")
    plan = json.loads((inputs["previous_run"] / "PLAN.json").read_bytes())
    targets = {
        "stage": root,
        "manifest": root / "MANIFEST.json",
        "payload": root / "field_lineage.parquet",
        "source": ContentAddressedStore(inputs["store_root"], create=False).get_path(
            plan["sources"]["budget"]["object_id"]
        ),
        "old_plan": inputs["previous_run"] / "PLAN.json",
        "donor": inputs["donor_manifest"],
        "root_parent": inputs["previous_run"],
    }
    target = targets[kind]
    kept = tmp_path / "kept"
    target.rename(kept)
    target.symlink_to(kept, target_is_directory=kept.is_dir())
    inputs["stage_manifest_sha256"] = {}
    with pytest.raises(ValueError, match="unsafe_resume_path"):
        rebuild_resume.plan_resume(**inputs)


@pytest.mark.parametrize(
    "field", ["observed_at", "donor_manifest_sha256", "sources", "schema_version"]
)
def test_re_pinned_old_plan_cannot_self_assert_context(
    tmp_path: Path, field: str
) -> None:
    inputs = _inputs(tmp_path)
    path = inputs["previous_run"] / "PLAN.json"
    plan = json.loads(path.read_bytes())
    plan[field] = "self-assertion"
    inputs["previous_plan_sha256"] = _json(path, plan)
    with pytest.raises(ValueError, match="resume_plan_context_mismatch"):
        rebuild_resume.plan_resume(**inputs)


@pytest.mark.parametrize(
    "kind", ["duplicate", "missing", "schema", "sha", "size", "bad_object", "bad_rows"]
)
def test_donor_identity_is_not_inferred(tmp_path: Path, kind: str) -> None:
    inputs = _inputs(tmp_path)
    donor = json.loads(inputs["donor_manifest"].read_bytes())
    if kind == "duplicate":
        donor["objects"].append(donor["objects"][0])
    elif kind == "missing":
        donor["objects"].pop()
    elif kind == "schema":
        donor["schema_version"] = "wrong"
    elif kind == "sha":
        donor["objects"][0]["sha256"] = "0" * 64
    elif kind == "size":
        donor["objects"][0]["byte_count"] = 999
    elif kind == "bad_object":
        donor["objects"][0]["object_id"] = "../private"
    else:
        donor["objects"] = ["not-an-object"]
    inputs["donor_manifest_sha256"] = _json(inputs["donor_manifest"], donor)
    with pytest.raises(ValueError, match=r"resume_input_contract|object_id"):
        rebuild_resume.plan_resume(**inputs)


@pytest.mark.parametrize(
    "literal",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b'{"x":1e999}',
        b"[]",
    ],
)
def test_pinned_invalid_json_fails_closed(tmp_path: Path, literal: bytes) -> None:
    inputs = _inputs(tmp_path)
    inputs["donor_manifest"].write_bytes(literal)
    inputs["donor_manifest_sha256"] = hashlib.sha256(literal).hexdigest()
    with pytest.raises(ValueError, match="resume_input_contract"):
        rebuild_resume.plan_resume(**inputs)


@pytest.mark.parametrize(
    "field", ["source_object_sha256", "source_locator", "source_vintage", "observed_at"]
)
def test_row_context_mismatch_fails_closed(tmp_path: Path, field: str) -> None:
    inputs = _inputs(tmp_path)
    root, manifest = _stage(inputs, "budget")
    filename = "budget_facts.parquet"
    table = pq.read_table(root / filename)
    rows = table.to_pylist()
    rows[0][field] = None
    pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), root / filename)
    manifest["output_sha256"][filename] = hashlib.sha256(
        (root / filename).read_bytes()
    ).hexdigest()
    inputs["stage_manifest_sha256"]["budget"] = _json(root / "MANIFEST.json", manifest)
    with pytest.raises(ValueError, match="stage_context_mismatch"):
        rebuild_resume.plan_resume(**inputs)


@pytest.mark.parametrize(
    "kind",
    [
        "schema",
        "metadata",
        "nullability",
        "zero_rows",
        "corrupt",
        "missing_count",
        "boolean_count",
        "missing_hash",
        "bad_hash",
    ],
)
def test_pinned_transport_defects_request_reextraction(
    tmp_path: Path, kind: str
) -> None:
    inputs = _inputs(tmp_path)
    root, manifest = _stage(inputs, "budget")
    filename = "budget_facts.parquet"
    table = pq.read_table(root / filename)
    if kind == "schema":
        table = pa.table({"wrong": [1]})
    elif kind == "metadata":
        table = table.replace_schema_metadata({"wrong": "value"})
    elif kind == "nullability":
        schema = table.schema.set(
            0, table.schema.field(0).with_nullable(nullable=False)
        )
        rows = table.to_pylist()
        rows[0]["record_id"] = "record"
        table = pa.Table.from_pylist(rows, schema=schema)
    elif kind == "zero_rows":
        table = table.slice(0, 0)
    elif kind == "missing_count":
        manifest["counts"].pop("normalized")
    elif kind == "boolean_count":
        manifest["counts"]["normalized"] = True
    pq.write_table(table, root / filename)
    if kind == "corrupt":
        (root / filename).write_bytes(b"private invalid Parquet")
    manifest["output_sha256"][filename] = hashlib.sha256(
        (root / filename).read_bytes()
    ).hexdigest()
    if kind == "missing_hash":
        manifest["output_sha256"].pop(filename)
    elif kind == "bad_hash":
        manifest["output_sha256"][filename] = "invalid"
    inputs["stage_manifest_sha256"]["budget"] = _json(root / "MANIFEST.json", manifest)
    assert (
        rebuild_resume.plan_resume(**inputs)["stages"]["budget"]["reason"]
        == "invalid_stage_payload"
    )


@pytest.mark.parametrize(
    ("constant", "value"), [("MAX_ROWS", 0), ("MAX_EXPANDED_BYTES", 0)]
)
def test_parquet_budgets_precede_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, constant: str, value: int
) -> None:
    inputs = _inputs(tmp_path)
    _stage(inputs, "budget")
    monkeypatch.setattr(rebuild_resume, constant, value)
    assert (
        rebuild_resume.plan_resume(**inputs)["stages"]["budget"]["reason"]
        == "invalid_stage_payload"
    )


def test_source_cap_precedes_any_parquet_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    monkeypatch.setattr(rebuild_resume, "MAX_FILE_BYTES", 5)
    with pytest.raises(ValueError, match="source_byte_limit"):
        rebuild_resume.plan_resume(**inputs)


def test_metadata_cap_is_enforced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    monkeypatch.setattr(rebuild_resume, "MAX_METADATA_BYTES", 1)
    with pytest.raises(ValueError, match="source_byte_limit"):
        rebuild_resume.plan_resume(**inputs)


@pytest.mark.parametrize("name", tuple(rebuild.PROFILES))
def test_unknown_transformation_is_not_reusable(tmp_path: Path, name: str) -> None:
    inputs = _inputs(tmp_path)
    root, manifest = _stage(inputs, name)
    manifest["transformation_id"] = "unknown/v1"
    inputs["stage_manifest_sha256"][name] = _json(root / "MANIFEST.json", manifest)
    with pytest.raises(ValueError, match="stage_context_mismatch"):
        rebuild_resume.plan_resume(**inputs)


@pytest.mark.parametrize("value", [None, 1, True, -1])
@pytest.mark.parametrize("name", tuple(rebuild.PROFILES))
def test_rejected_count_must_be_explicit_zero(
    tmp_path: Path, name: str, value: object
) -> None:
    inputs = _inputs(tmp_path)
    root, manifest = _stage(inputs, name)
    if value is None:
        manifest["counts"].pop("rejected")
    else:
        manifest["counts"]["rejected"] = value
    inputs["stage_manifest_sha256"][name] = _json(root / "MANIFEST.json", manifest)
    assert (
        rebuild_resume.plan_resume(**inputs)["stages"][name]["reason"]
        == "invalid_stage_payload"
    )


@pytest.mark.parametrize("name", ["befu", "hyefu"])
def test_forecast_profile_is_exact(tmp_path: Path, name: str) -> None:
    inputs = _inputs(tmp_path)
    root, manifest = _stage(inputs, name)
    manifest["profile"] = "unknown/v1"
    inputs["stage_manifest_sha256"][name] = _json(root / "MANIFEST.json", manifest)
    with pytest.raises(ValueError, match="stage_context_mismatch"):
        rebuild_resume.plan_resume(**inputs)


def test_valid_extra_metadata_and_exact_original_byte_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    donor = json.loads(inputs["donor_manifest"].read_bytes())
    donor["unused_extra"] = 0.25
    pin = _json(inputs["donor_manifest"], donor)
    inputs["donor_manifest_sha256"] = pin
    plan_path = inputs["previous_run"] / "PLAN.json"
    plan = json.loads(plan_path.read_bytes())
    plan["donor_manifest_sha256"] = pin
    inputs["previous_plan_sha256"] = _json(plan_path, plan)
    monkeypatch.setattr(rebuild_resume, "MAX_FILE_BYTES", 10)
    assert rebuild_resume.plan_resume(**inputs)["selected_source_bytes"] == 25


@pytest.mark.parametrize(
    "constant",
    ["MAX_FILE_BYTES", "MAX_ROWS", "MAX_EXPANDED_BYTES", "MAX_METADATA_BYTES"],
)
def test_exact_stage_budgets_pass_and_one_less_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, constant: str
) -> None:
    inputs = _inputs(tmp_path)
    root, _ = _stage(inputs, "budget")
    paths = [root / name for name in rebuild.PROFILES["budget"].outputs]
    if constant == "MAX_FILE_BYTES":
        limit = max(path.stat().st_size for path in paths)
    elif constant == "MAX_ROWS":
        limit = 1
    elif constant == "MAX_EXPANDED_BYTES":
        limit = sum(
            pq.ParquetFile(path).metadata.row_group(0).total_byte_size for path in paths
        )
    else:
        limit = max(
            path.stat().st_size
            for path in [
                root / "MANIFEST.json",
                inputs["donor_manifest"],
                inputs["previous_run"] / "PLAN.json",
            ]
        )
    monkeypatch.setattr(rebuild_resume, constant, limit)
    assert (
        rebuild_resume.plan_resume(**inputs)["stages"]["budget"]["action"]
        == "reuse_verified"
    )
    monkeypatch.setattr(rebuild_resume, constant, limit - 1)
    if constant == "MAX_METADATA_BYTES":
        # The largest of these synthetic metadata snapshots is the donor input.
        with pytest.raises(ValueError, match="source_byte_limit"):
            rebuild_resume.plan_resume(**inputs)
    else:
        assert (
            rebuild_resume.plan_resume(**inputs)["stages"]["budget"]["reason"]
            == "invalid_stage_payload"
        )


@pytest.mark.parametrize(
    "kind",
    [
        "unknown_stage_pin",
        "invalid_stage_pin",
        "unexpected_root",
        "stage_file",
        "missing_original",
    ],
)
def test_unsafe_top_level_inputs_fail_closed(tmp_path: Path, kind: str) -> None:
    inputs = _inputs(tmp_path)
    if kind == "unknown_stage_pin":
        inputs["stage_manifest_sha256"] = {"unknown": "a" * 64}
    elif kind == "invalid_stage_pin":
        inputs["stage_manifest_sha256"] = {"budget": "invalid"}
    elif kind == "unexpected_root":
        (inputs["previous_run"] / "MANIFEST.json").write_bytes(
            b"complete runs use their existing verifier"
        )
    elif kind == "stage_file":
        (inputs["previous_run"] / "budget").write_bytes(b"not a directory")
    else:
        plan = json.loads((inputs["previous_run"] / "PLAN.json").read_bytes())
        path = ContentAddressedStore(inputs["store_root"], create=False).get_path(
            plan["sources"]["budget"]["object_id"]
        )
        path.rename(tmp_path / "retained-original")
    with pytest.raises(ValueError, match="resume_input_contract"):
        rebuild_resume.plan_resume(**inputs)


def test_failed_attempt_text_is_never_copied_or_modified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    _stage(inputs, "historical")
    failure = inputs["previous_run"] / "FAILURE.json"
    failure.write_bytes(b"sensitive old exception")
    before = {
        str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    }

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("planner attempted output creation")

    monkeypatch.setattr(Path, "mkdir", forbidden)
    result = rebuild_resume.plan_resume(**inputs)
    assert "sensitive old exception" not in json.dumps(result)
    assert {
        str(path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    } == before
