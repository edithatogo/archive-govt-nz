"""Catalogue lineage must not turn rollout candidates into reviewed coverage."""

import hashlib
import json
import runpy
import sys
from pathlib import Path

import pytest

from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_reconciliation import (
    main,
    reconcile_rollout,
    reconciliation_files,
)
from archive_govt_nz.foi_rollout import build_rollout

ROOT = Path(__file__).parents[1]
TRACK = ROOT / "conductor/tracks/global_foi_public_archive_20260830"
ROLLOUT = TRACK / "country-rollout-20260831.json"
SEEDS = ROOT / "config/foi"


def test_materialized_rollout_is_an_extension_not_reviewed_coverage() -> None:
    """Reproduce the real 30 versus 255 gap with immutable input bindings."""
    report = reconcile_rollout(SEEDS, ROLLOUT, TRACK)
    assert report["summary"] == {
        "entities": 251,
        "catalogue_sources": 30,
        "rollout_sources": 255,
        "additional_candidates": 225,
        "sources_with_receipt": 228,
        "sources_without_receipt": 27,
    }
    assert report["coverage_credit_granted"] is False
    assert report["total_requests"] is None
    rows = {row["source_id"]: row for row in report["sources"]}
    assert (
        rows["kw-open-data"]["lineage"] == "additional_candidate_not_catalogue_reviewed"
    )
    assert rows["kw-open-data"]["receipt_kind"] == "discovery_metadata_only"
    assert rows["ar-derechoaldato"]["receipt_sha256"] is None
    assert rows["ar-derechoaldato"]["lineage"] == "pinned_catalogue"
    assert all(row["review_credit_granted"] is False for row in rows.values())
    assert reconciliation_files(report) == reconciliation_files(
        reconcile_rollout(SEEDS, ROLLOUT, TRACK)
    )


@pytest.mark.parametrize("mode", ["pin", "missing", "entity", "duplicate", "receipt"])
def test_reconciliation_rejects_drift(tmp_path: Path, mode: str) -> None:
    """Internally consistent subsets and cross-country moves still fail lineage."""
    rollout = json.loads(ROLLOUT.read_bytes())
    if mode == "pin":
        rollout["catalogue_sha256"] = "0" * 64
    elif mode == "missing":
        rollout["sources"] = [
            s for s in rollout["sources"] if s["source_id"] != "ar-derechoaldato"
        ]
        next(e for e in rollout["entities"] if e["entity_id"] == "AR")[
            "source_ids"
        ].remove("ar-derechoaldato")
        rollout["summary"]["sources"] -= 1
    elif mode == "entity":
        for source in rollout["sources"]:
            if source["entity_id"] == "AR":
                source["entity_id"] = "UNKNOWN"
        next(e for e in rollout["entities"] if e["entity_id"] == "AR")["entity_id"] = (
            "UNKNOWN"
        )
    elif mode == "duplicate":
        rollout["sources"].append(rollout["sources"][0])
    else:
        rollout["sources"][0]["capture_evidence"] = "../outside.json"
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    with pytest.raises(ValueError, match=r"catalogue_|rollout_integrity"):
        reconcile_rollout(SEEDS, path, TRACK)


def test_receipt_assertions_never_grant_review_credit(tmp_path: Path) -> None:
    """Even an approval claim in a candidate receipt cannot admit a source."""
    rollout = build_rollout(build_reviewed_catalogue(SEEDS))
    source = dict(rollout["sources"][0])
    source.update(source_id="candidate", capture_evidence="receipt.json")
    rollout["sources"].append(source)
    next(e for e in rollout["entities"] if e["entity_id"] == source["entity_id"])[
        "source_ids"
    ].append("candidate")
    rollout["summary"]["sources"] += 1
    receipt = {
        "source_id": "candidate",
        "entity_id": source["entity_id"],
        "schema_version": "archive-govt-nz.source-discovery/v1",
        "reviewed": True,
        "publication_approved": True,
        "country_complete": True,
        "private_content": "do not copy this field",
    }
    payload = json.dumps(receipt).encode()
    (tmp_path / "receipt.json").write_bytes(payload)
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    report = reconcile_rollout(SEEDS, path, tmp_path)
    row = next(r for r in report["sources"] if r["source_id"] == "candidate")
    assert row["receipt_sha256"] == hashlib.sha256(payload).hexdigest()
    assert row["review_credit_granted"] is False
    assert row["lineage"] == "additional_candidate_not_catalogue_reviewed"
    assert report["summary"]["catalogue_sources"] == 30
    assert "do not copy" not in json.dumps(report)
    assert report["rollout_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_retained_source_cannot_move_between_existing_entities(tmp_path: Path) -> None:
    """Internal source links can be consistent while contradicting the catalogue."""
    rollout = build_rollout(build_reviewed_catalogue(SEEDS))
    source = rollout["sources"][0]
    original = next(
        e for e in rollout["entities"] if e["entity_id"] == source["entity_id"]
    )
    target = next(e for e in rollout["entities"] if e["entity_id"] == "US")
    original["source_ids"].remove(source["source_id"])
    target["source_ids"].append(source["source_id"])
    source["entity_id"] = "US"
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    with pytest.raises(ValueError, match="catalogue_source_mismatch"):
        reconcile_rollout(SEEDS, path, tmp_path)


@pytest.mark.parametrize("field", ["schema_version", "scope"])
def test_foreign_rollout_contract_is_rejected(tmp_path: Path, field: str) -> None:
    """An internally consistent ledger must still use the expected contract."""
    rollout = json.loads(ROLLOUT.read_bytes())
    rollout[field] = "unsupported"
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    with pytest.raises(ValueError, match="rollout_contract_mismatch"):
        reconcile_rollout(SEEDS, path, TRACK)


@pytest.mark.parametrize("kind", ["rollout", "receipt"])
def test_input_change_during_validation_is_rejected(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Hashes must describe the same rollout and receipt identities checked."""
    read = Path.read_bytes
    calls = 0

    def changed(path: Path) -> bytes:
        nonlocal calls
        payload = read(path)
        if kind == "rollout" and path == ROLLOUT:
            calls += 1
            if calls == 2:
                return payload + b" "
        if kind == "receipt" and path.name == "ad-transparency-discovery-20260905.json":
            calls += 1
            if calls == 2:
                return b'{"source_id": "wrong"}'
        return payload

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValueError, match="changed"):
        reconcile_rollout(SEEDS, ROLLOUT, TRACK)


@pytest.mark.parametrize("output_format", ["json", "md"])
def test_cli_emits_deterministic_report(
    capsys: pytest.CaptureFixture[str], output_format: str
) -> None:
    """The command only emits the requested local report, without diagnostics."""
    assert (
        main(
            [
                "--seeds",
                str(SEEDS),
                "--rollout",
                str(ROLLOUT),
                "--evidence-dir",
                str(TRACK),
                "--format",
                output_format,
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    expected = reconciliation_files(reconcile_rollout(SEEDS, ROLLOUT, TRACK))
    assert captured.out.encode() == expected[f"rollout-reconciliation.{output_format}"]
    assert captured.err == ""


def test_cli_failure_has_no_report_or_input_details(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unavailable inputs fail without emitting a success report or local paths."""
    assert (
        main(
            [
                "--seeds",
                str(SEEDS),
                "--rollout",
                str(tmp_path / "absent"),
                "--evidence-dir",
                str(TRACK),
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err == "FOI reconciliation rejected invalid or unavailable inputs.\n"
    )


def test_module_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Module execution returns the command's explicit failure exit status."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "foi_reconciliation",
            "--seeds",
            str(SEEDS),
            "--rollout",
            "absent",
            "--evidence-dir",
            str(TRACK),
        ],
    )
    with pytest.raises(SystemExit) as result:
        runpy.run_path(
            str(ROOT / "src/archive_govt_nz/foi_reconciliation.py"), run_name="__main__"
        )
    assert result.value.code == 2


def test_reordering_changes_byte_pin_but_not_lineage(tmp_path: Path) -> None:
    """Input order is immaterial to accounting; exact bytes remain distinguishable."""
    original = reconcile_rollout(SEEDS, ROLLOUT, TRACK)
    rollout = json.loads(ROLLOUT.read_bytes())
    rollout["sources"].reverse()
    rollout["entities"].reverse()
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(rollout), encoding="utf-8")
    reordered = reconcile_rollout(SEEDS, path, TRACK)
    assert reordered["rollout_sha256"] != original["rollout_sha256"]
    reordered["rollout_sha256"] = original["rollout_sha256"]
    assert reordered == original


def test_checked_in_reports_reproduce_without_mutating_inputs() -> None:
    """The paired track artefacts are derived from the exact retained inputs."""
    paths = [ROLLOUT, *SEEDS.glob("*.json")]
    before = {path: path.read_bytes() for path in paths}
    files = reconciliation_files(reconcile_rollout(SEEDS, ROLLOUT, TRACK))
    for name, payload in files.items():
        assert (TRACK / name).read_bytes() == payload
    assert {path: path.read_bytes() for path in paths} == before
