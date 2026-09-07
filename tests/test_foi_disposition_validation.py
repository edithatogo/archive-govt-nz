"""Bounded disposition evidence is not exhaustive discovery or capture proof."""

import hashlib
import json
import shutil
import socket
from pathlib import Path

import pytest

from archive_govt_nz.foi_canonical import INPUTS, build_source_index
from archive_govt_nz.foi_disposition_validation import validate_canonical_dispositions

TRACK = Path("conductor/tracks/global_foi_public_archive_20260830")
SEEDS = Path("config/foi")


@pytest.fixture(autouse=True)
def deny_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """All canonical validation, including mutations, is offline."""

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def test_actual_canonical_receipt_preserves_boundaries() -> None:
    """Only recomputed pinned metadata earns the bounded validation result."""
    result = validate_canonical_dispositions(SEEDS, TRACK)
    files = build_source_index(SEEDS, TRACK)
    registry = json.loads(files["registry.json"])
    assert result == validate_canonical_dispositions(SEEDS, TRACK)
    assert result["scope"] == "catalogue_disposition_validation"
    assert result["status"] == "passed"
    assert "phase_acceptance" not in result
    assert result["seed_provenance"] == registry["provenance"]["seeds"]
    assert (
        result["canonical_inputs"] == registry["provenance"]["canonical_join"]["inputs"]
    )
    assert (
        result["provenance_sha256"]
        == hashlib.sha256(
            json.dumps(
                registry["provenance"], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
    )
    assert len(json.dumps(result).encode()) < 20000
    assert result["coverage"] == registry["coverage"]
    assert result["coverage"]["known_sources"] == 255
    assert result["coverage"]["entities_with_explicit_dispositions"] == 251
    assert result["coverage"]["total_requests"] is None
    assert result["coverage"]["verified_complete"] == 0
    assert result["separate_gates"] == {
        "exhaustive_discovery": "not_established",
        "capture_completion": "not_validated",
        "publication": "not_validated",
        "programme_completion": "not_assessed",
        "ac04_acceptance": "parent_audit_required",
    }
    assert result["files"] == {
        name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        for name, data in sorted(files.items())
    }
    for name, data in files.items():
        assert (TRACK / "canonical-index-20260907" / name).read_bytes() == data
    assert b"robots_unsupported_rules" in files["coverage.md"]
    assert b"foi_scope_unverified" in files["sources.jsonl"]


def copied_inputs(tmp_path: Path) -> Path:
    """Copy only the pinned input set and referenced lineage receipts."""
    track = tmp_path / "track"
    track.mkdir()
    lineage = json.loads((TRACK / "rollout-reconciliation.json").read_bytes())
    names = {*INPUTS, "canonical-inputs-20260907.json"}
    names.update(row["receipt"] for row in lineage["sources"] if row["receipt"])
    for name in names:
        target = track / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TRACK / name, target)
    return track


@pytest.mark.parametrize(
    "fault",
    ["pin", "receipt", "forged_disposition", "duplicate", "cross_entity", "promotion"],
)
def test_recomputed_inputs_reject_faults(tmp_path: Path, fault: str) -> None:
    """Rehashing a forged report cannot substitute for replay or exact joins."""
    track = copied_inputs(tmp_path)
    path = track / "candidate-assessment-complete.json"
    if fault == "receipt":
        (track / "ad-transparency-discovery-20260905.json").unlink()
    elif fault == "pin":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        value = json.loads(path.read_bytes())
        row = value["sources"][0]
        if fault == "duplicate":
            value["sources"].append(row.copy())
        elif fault == "cross_entity":
            row["entity_id"] = "NZ"
        elif fault == "promotion":
            row["publication_approved"] = True
        else:
            row["foi_scope"] = "reviewed"
        path.write_text(json.dumps(value))
        pins_path = track / "canonical-inputs-20260907.json"
        pins = json.loads(pins_path.read_bytes())
        pins["files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        pins_path.write_text(json.dumps(pins))
    reason = {"pin": "canonical_input_drift", "receipt": "rollout_integrity"}.get(
        fault, "candidate_report_drift"
    )
    with pytest.raises(ValueError, match=reason):
        validate_canonical_dispositions(SEEDS, track)


@pytest.mark.parametrize("name", INPUTS)
def test_every_canonical_pin_is_enforced(tmp_path: Path, name: str) -> None:
    """Every retained input is verified even when its altered JSON still parses."""
    track = copied_inputs(tmp_path)
    path = track / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="canonical_input_drift"):
        validate_canonical_dispositions(SEEDS, track)


def test_seed_pin_is_enforced(tmp_path: Path) -> None:
    """Canonical track pins cannot replace seed provenance verification."""
    seeds = tmp_path / "seeds"
    shutil.copytree(SEEDS, seeds)
    path = seeds / "donor-instances.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="seed provenance hash mismatch"):
        validate_canonical_dispositions(seeds, TRACK)
