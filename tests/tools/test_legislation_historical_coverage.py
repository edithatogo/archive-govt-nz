"""Tests for fixity-bound historical legislation coverage analysis."""

# ruff: noqa: D103, PT011, TC003

from __future__ import annotations

import importlib.util
import json
import tempfile
from hashlib import sha256
from pathlib import Path
from types import ModuleType

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

_PATH = Path(__file__).parents[2] / "tools/legislation_historical_coverage.py"
_SPEC = importlib.util.spec_from_file_location("legislation_historical_coverage", _PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(MODULE)


def _donor(tmp_path: Path) -> Path:
    root = tmp_path / "donor"
    reviewed = root / "seeds/reviewed"
    reviewed.mkdir(parents=True)
    ids = [f"work_{index:05d}" for index in range(33_693)]
    for number in range(68):
        values = ids[number * 500 : (number + 1) * 500]
        (reviewed / f"historical-work-ids-{number + 1:04d}.txt").write_text(
            "\n".join(values) + "\n", encoding="ascii"
        )
    payload = "\n".join(ids) + "\n"
    (root / "seeds/work_ids.txt").write_text(
        "# provenance\n" + payload, encoding="ascii"
    )
    return root


def _patch_expected_hash(monkeypatch: pytest.MonkeyPatch, donor: Path) -> None:
    reviewed = donor / "seeds/reviewed"
    raw = b"".join(path.read_bytes() for path in sorted(reviewed.glob("*.txt")))
    monkeypatch.setattr(MODULE, "EXPECTED_CANDIDATE_SHA256", sha256(raw).hexdigest())


def _evidence(tmp_path: Path, *, mismatch: bool = False) -> Path:
    base = tmp_path / "target/evidence/migrations/corpus-legislation-nz"
    directory = base / "final-state-merge/execution-02"
    directory.mkdir(parents=True)
    output = {
        "records": 552,
        "work_ids": 552,
        "objects": 552,
        "manifest_sha256": "a" * 64,
        "inventory_sha256": "b" * 64,
    }
    receipt = {
        "status": "passed",
        "output": output,
        "parents": [{"records": 500}, {"records": 52}],
    }
    readback = {"status": "passed", "output": {**output}}
    if mismatch:
        readback["output"]["records"] = 551
    (directory / "final-state-merge-receipt.json").write_text(json.dumps(receipt))
    (directory / "independent-readback.json").write_text(json.dumps(readback))
    inventory = []
    for index in range(552):
        digest = sha256(f"object-{index}".encode()).hexdigest()
        inventory.append(
            {
                "path_parts": ["cas", "sha256", digest[:2], digest],
                "sha256": digest,
                "size_bytes": index + 1,
            }
        )
    (directory / "package-inventory.json").write_text(
        json.dumps({"files": inventory, "inventory_sha256": "b" * 64})
    )
    return tmp_path / "target"


def _public(root: Path) -> None:
    path = (
        root
        / "evidence/migrations/corpus-legislation-nz/historical-coverage"
        / "public-surface-observations.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "archive-govt-nz.prompt14-public-surface-observations/v1"
                ),
                "observed_at": "2026-09-01T12:31:29Z",
                "method": "anonymous revision-pinned HTTP observation",
                "surfaces": [
                    {
                        "surface_id": "huggingface:example/one",
                        "platform": "huggingface",
                        "api_url": "https://huggingface.co/api/datasets/example/one",
                        "api_response_sha256": "c" * 64,
                        "http_status": 200,
                        "public": True,
                        "disabled": False,
                        "observed_revision": "d" * 40,
                        "published_row_count": None,
                        "file_inventory": {
                            "total_files": 3,
                            "parquet_files": 1,
                            "raw_xml_files": 1,
                            "records_jsonl_files": 1,
                        },
                    }
                ],
            }
        )
    )


def test_build_report_preserves_distinct_counts_and_unknowns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    donor = _donor(tmp_path)
    _patch_expected_hash(monkeypatch, donor)
    target = _evidence(tmp_path)
    _public(target)
    (target / "seeds").mkdir()
    reviewed = target / "seeds/reviewed/historical-work-ids-0001.txt"
    reviewed.parent.mkdir()
    reviewed.write_bytes(
        (donor / "seeds/reviewed/historical-work-ids-0001.txt").read_bytes()
    )
    (target / "seeds/registry.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "seed_id": "historical-work-ids-0001",
                        "candidate_count": 500,
                        "path_parts": [
                            "seeds",
                            "reviewed",
                            "historical-work-ids-0001.txt",
                        ],
                        "content": {
                            "sha256": sha256(reviewed.read_bytes()).hexdigest(),
                            "line_count": 500,
                            "unique": True,
                        },
                    }
                ]
            }
        )
    )
    (target / "claim.md").write_text("33,693 acquired records", encoding="utf-8")

    report, corrections = MODULE.build_report(donor, target, target)

    assert report["populations"]["candidate_ids"]["value"] == 33_693
    assert report["populations"]["target_governed_reviewed_ids"]["value"] == 500
    assert report["reconciliation"]["candidate_ids_outside_governed_subset"] == 33_193
    assert report["populations"]["canonical_state_works"]["value"] == 552
    assert report["populations"]["successfully_retrieved_works"]["value"] is None
    assert report["populations"]["attempted_works"]["value"] is None
    assert report["populations"]["published_rows"]["value"] is None
    assert report["candidate_inventory"]["inventory_comment_or_blank_lines"] == 1
    assert corrections["inputs"][0]["path"] == "claim.md"
    assert "unknown" in MODULE.render_markdown(report)


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "reordered", "crlf", "hash"]
)
def test_batch_audit_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    donor = _donor(tmp_path)
    _patch_expected_hash(monkeypatch, donor)
    batch = donor / "seeds/reviewed/historical-work-ids-0001.txt"
    lines = batch.read_text().splitlines()
    if mutation == "missing":
        batch.unlink()
    elif mutation == "duplicate":
        lines[1] = lines[0]
        batch.write_text("\n".join(lines) + "\n")
    elif mutation == "reordered":
        lines[0], lines[1] = lines[1], lines[0]
        batch.write_text("\n".join(lines) + "\n")
    elif mutation == "crlf":
        batch.write_bytes(("\r\n".join(lines) + "\r\n").encode())
    else:
        monkeypatch.setattr(MODULE, "EXPECTED_CANDIDATE_SHA256", "0" * 64)
    with pytest.raises(ValueError):
        MODULE.audit_batches(donor)


def test_target_receipt_mismatch_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="mismatch"):
        MODULE.audit_target_state(_evidence(tmp_path, mismatch=True))


@pytest.mark.parametrize("mutation", ["missing_entry", "wrong_identity"])
def test_target_package_inventory_fails_closed(tmp_path: Path, mutation: str) -> None:
    """Reject incomplete or path/hash-divergent CAS package inventories."""
    target = _evidence(tmp_path)
    path = (
        target
        / "evidence/migrations/corpus-legislation-nz"
        / "final-state-merge/execution-02/package-inventory.json"
    )
    document = json.loads(path.read_text(encoding="utf-8"))
    inventory = document["files"]
    if mutation == "missing_entry":
        inventory.pop()
        expected = "CAS count mismatch"
    else:
        inventory[0]["path_parts"][-1] = "f" * 64
        expected = "malformed package inventory CAS identity"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match=expected):
        MODULE.audit_target_state(target)


def test_unbound_seed_does_not_reduce_unknown_candidate_outcomes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    donor = _donor(tmp_path)
    _patch_expected_hash(monkeypatch, donor)
    target = _evidence(tmp_path)
    _public(target)
    (target / "seeds").mkdir()
    (target / "seeds/registry.json").write_text(
        json.dumps({"entries": [{"candidate_count": 500}]})
    )
    report, _ = MODULE.build_report(donor, target, target)
    assert report["populations"]["target_governed_reviewed_ids"]["value"] is None
    assert report["reconciliation"]["candidate_ids_outside_governed_subset"] is None


def test_claim_inventory_excludes_generated_outputs(tmp_path: Path) -> None:
    generated = (
        tmp_path
        / "evidence/migrations/corpus-legislation-nz/historical-coverage"
        / "historical-coverage-report.json"
    )
    generated.parent.mkdir(parents=True)
    generated.write_text('{"candidate_ids": 33693}', encoding="utf-8")
    track = (
        tmp_path
        / "conductor/tracks/legislation_historical_coverage_20260901"
        / "evidence.md"
    )
    track.parent.mkdir(parents=True)
    track.write_text("33,693 candidate IDs", encoding="utf-8")
    source = tmp_path / "source.md"
    source.write_text("33,693 acquired works", encoding="utf-8")

    assert [row["path"] for row in MODULE.find_claim_inputs(tmp_path)] == ["source.md"]


def test_reviewed_seed_must_be_a_candidate_subset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    donor = _donor(tmp_path)
    _patch_expected_hash(monkeypatch, donor)
    target = _evidence(tmp_path)
    _public(target)
    seed = target / "seeds/reviewed/historical-work-ids-0001.txt"
    seed.parent.mkdir(parents=True)
    seed_ids = [f"outside_{index:04d}" for index in range(500)]
    seed.write_text("\n".join(seed_ids) + "\n", encoding="ascii")
    (target / "seeds/registry.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "seed_id": "historical-work-ids-0001",
                        "candidate_count": 500,
                        "path_parts": [
                            "seeds",
                            "reviewed",
                            "historical-work-ids-0001.txt",
                        ],
                        "content": {
                            "sha256": sha256(seed.read_bytes()).hexdigest(),
                            "line_count": 500,
                            "unique": True,
                        },
                    }
                ]
            }
        )
    )

    report, _ = MODULE.build_report(donor, target, target)

    assert report["populations"]["target_governed_reviewed_ids"]["value"] is None
    assert report["reconciliation"]["candidate_ids_outside_governed_subset"] is None


def test_public_observations_reject_duplicate_surface(tmp_path: Path) -> None:
    target = _evidence(tmp_path)
    _public(target)
    path = (
        target
        / "evidence/migrations/corpus-legislation-nz/historical-coverage"
        / "public-surface-observations.json"
    )
    document = json.loads(path.read_text())
    document["surfaces"].append(dict(document["surfaces"][0]))
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="duplicate"):
        MODULE.audit_public_observations(target)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("http_status", 404),
        ("api_url", "http://huggingface.co/api/datasets/example/one"),
        ("public", False),
        ("disabled", True),
        ("observed_revision", "not-a-revision"),
    ],
)
def test_public_observations_reject_invalid_identity_or_status(
    tmp_path: Path, field: str, value: object
) -> None:
    target = _evidence(tmp_path)
    _public(target)
    path = (
        target
        / "evidence/migrations/corpus-legislation-nz/historical-coverage"
        / "public-surface-observations.json"
    )
    document = json.loads(path.read_text())
    document["surfaces"][0][field] = value
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        MODULE.audit_public_observations(target)


def test_public_observations_reject_inventory_over_total(tmp_path: Path) -> None:
    target = _evidence(tmp_path)
    _public(target)
    path = (
        target
        / "evidence/migrations/corpus-legislation-nz/historical-coverage"
        / "public-surface-observations.json"
    )
    document = json.loads(path.read_text())
    document["surfaces"][0]["file_inventory"]["raw_xml_files"] = 3
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="exceeds total"):
        MODULE.audit_public_observations(target)


@given(
    st.lists(
        st.text(alphabet="abc", min_size=1, max_size=6),
        min_size=1,
        max_size=30,
        unique=True,
    )
)
@settings(deadline=None)
def test_claim_inventory_is_deterministic_for_arbitrary_creation_order(
    names: list[str],
) -> None:
    safe = sorted(
        {
            f"{index:03d}-{sha256(name.encode()).hexdigest()[:8]}.md"
            for index, name in enumerate(names)
        }
    )
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name in reversed(safe):
            (root / name).write_text("candidate count 33693", encoding="utf-8")
        first = MODULE.find_claim_inputs(root)
        second = MODULE.find_claim_inputs(root)
        assert first == second
        assert [row["path"] for row in first] == safe


@pytest.mark.parametrize(
    "path_parts",
    [
        ["..", "outside.txt"],
        [Path.cwd().anchor + "tmp", "outside.txt"],
        ["seeds/reviewed", "historical-work-ids-0001.txt"],
    ],
)
def test_registry_path_cannot_escape_claim_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path_parts: list[str],
) -> None:
    donor = _donor(tmp_path)
    _patch_expected_hash(monkeypatch, donor)
    target = _evidence(tmp_path)
    _public(target)
    (target / "seeds").mkdir()
    (target / "seeds/registry.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "seed_id": "historical-work-ids-0001",
                        "candidate_count": 500,
                        "path_parts": path_parts,
                        "content": {
                            "sha256": "0" * 64,
                            "line_count": 500,
                            "unique": True,
                        },
                    }
                ]
            }
        )
    )
    report, _ = MODULE.build_report(donor, target, target)
    assert report["populations"]["target_governed_reviewed_ids"]["value"] is None
    assert report["reconciliation"]["candidate_ids_outside_governed_subset"] is None


def _claim_binding_fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "claim.md"
    source.write_text("33,693 acquired\n33693 published\n", encoding="utf-8")
    analyzer_path = tmp_path / "analyzer.json"
    analyzer_path.write_text(
        json.dumps(
            {
                "inputs": [
                    {
                        "path": "claim.md",
                        "sha256": sha256(source.read_bytes()).hexdigest(),
                        "occurrences": 2,
                    }
                ]
            }
        )
    )
    claims = [
        {
            "claim_id": f"claim-{index:03d}",
            "file": "claim.md",
            "line": index,
            "text": source.read_text().splitlines()[index - 1],
            "source_sha256": sha256(source.read_bytes()).hexdigest(),
            "source_line_sha256": sha256(
                source.read_text().splitlines()[index - 1].encode()
            ).hexdigest(),
        }
        for index in (1, 2)
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "archive-govt-nz.prompt14-claim-correction-manifest/v1"
                ),
                "analyzer_claim_inputs_sha256": sha256(
                    analyzer_path.read_bytes()
                ).hexdigest(),
                "scan_contract": {"occurrence_count": 2},
                "claims": claims,
            }
        )
    )
    return manifest_path, analyzer_path


def test_claim_correction_manifest_is_bound_to_source_bytes_and_lines(
    tmp_path: Path,
) -> None:
    manifest_path, analyzer_path = _claim_binding_fixture(tmp_path)
    receipt = MODULE.validate_claim_correction_manifest(
        manifest_path, analyzer_path, tmp_path
    )
    assert receipt["status"] == "passed"
    assert receipt["claims_verified"] == 2
    assert receipt["source_files_verified"] == 1


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("analyzer_hash", "analyzer input hash"),
        ("source_hash", "source hash"),
        ("line", "text does not match"),
        ("text", "text does not match"),
        ("duplicate", "duplicate"),
        ("missing", "scan count"),
    ],
)
def test_claim_correction_manifest_rejects_unbound_entries(
    tmp_path: Path, mutation: str, message: str
) -> None:
    manifest_path, analyzer_path = _claim_binding_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    claims = manifest["claims"]
    if mutation == "analyzer_hash":
        manifest["analyzer_claim_inputs_sha256"] = "0" * 64
    elif mutation == "source_hash":
        claims[0]["source_sha256"] = "0" * 64
    elif mutation == "line":
        claims[0]["line"] = 2
    elif mutation == "text":
        claims[0]["text"] = "33,693 candidates"
    elif mutation == "duplicate":
        claims[1]["claim_id"] = claims[0]["claim_id"]
    else:
        claims.pop()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=message):
        MODULE.validate_claim_correction_manifest(
            manifest_path, analyzer_path, tmp_path
        )
