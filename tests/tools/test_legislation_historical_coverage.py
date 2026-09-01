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
from hypothesis import given
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
                "surfaces": [
                    {
                        "surface_id": "example:one",
                        "api_response_sha256": "c" * 64,
                        "published_row_count": None,
                        "file_inventory": {"total_files": 3},
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
    assert report["reconciliation"]["candidate_disposition_unknown"] == 33_193
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
    assert report["reconciliation"]["candidate_disposition_unknown"] is None


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


@given(
    st.lists(
        st.text(alphabet="abc", min_size=1, max_size=6),
        min_size=1,
        max_size=30,
        unique=True,
    )
)
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
