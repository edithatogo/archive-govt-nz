"""Reject lifecycle drift while reading both historical and current track formats."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from tools.validate_conductor_state import validate


def make_track(root: Path, *, number: str = " 14", state: str = "completed") -> Path:
    """Create a small historical track with numbered registry syntax."""
    folder = root / "conductor/tracks/example"
    folder.mkdir(parents=True)
    (folder.parent.parent / "tracks.md").write_text(
        f"- [x] **Track{number}: Example**\n"
        "  *Link: [track](./tracks/example/index.md)*\n",
    )
    (folder / "index.md").write_text("# Example\n")
    (folder / "requirements.md").write_text("# Must\nPreserve bytes.\n")
    (folder / "plan.md").write_text("- [x] Preserve bytes.\n")
    (folder / "metadata.json").write_text(
        json.dumps({"id": "example", "status": state})
    )
    return folder


@pytest.mark.parametrize("state", ["complete", "completed"])
def test_reads_numbered_legacy_tracks(tmp_path: Path, state: str) -> None:
    """Historical spellings do not hide registered tracks."""
    make_track(tmp_path, state=state)
    assert validate(tmp_path)["errors"] == []


def test_rejects_pending_task_in_completed_track(tmp_path: Path) -> None:
    """Legacy compatibility never turns pending implementation into completion."""
    folder = make_track(tmp_path)
    (folder / "plan.md").write_text("- [ ] Not done.\n")
    assert any("incomplete plan" in e for e in validate(tmp_path)["errors"])


def test_rejects_missing_and_duplicate_registration(tmp_path: Path) -> None:
    """Directory existence and registration are distinct obligations."""
    make_track(tmp_path)
    registry = tmp_path / "conductor/tracks.md"
    text = registry.read_text()
    registry.write_text(text + text)
    assert any("duplicate" in e for e in validate(tmp_path)["errors"])
    registry.write_text("")
    assert any("unregistered" in e for e in validate(tmp_path)["errors"])


def test_rejects_path_escape(tmp_path: Path) -> None:
    """Registry targets cannot escape the Conductor directories."""
    make_track(tmp_path)
    registry = tmp_path / "conductor/tracks.md"
    registry.write_text("- [x] **Track: Bad**\n[bad](../../outside/index.md)\n")
    assert any("unsafe" in e for e in validate(tmp_path)["errors"])


def test_rejects_identity_and_status_drift(tmp_path: Path) -> None:
    """Unrecognized states and mismatched IDs fail closed."""
    folder = make_track(tmp_path)
    (folder / "metadata.json").write_text('{"track_id":"wrong","status":"green"}')
    errors = validate(tmp_path)["errors"]
    assert any("identity" in e for e in errors)
    assert any("status" in e for e in errors)


def test_rejects_corrupt_chained_evidence(tmp_path: Path) -> None:
    """Canonical evidence cannot be weakened to legacy mode by deleting a hash."""
    folder = make_track(tmp_path, number="")
    (folder / "metadata.json").write_text(
        '{"track_id":"example","status":"completed","evidence_contract":"chained-v1"}',
    )
    (folder / "evidence.jsonl").write_text('{"kind":"review","status":"passed"}\n')
    assert any("evidence" in e for e in validate(tmp_path)["errors"])


def test_legacy_evidence_requires_structured_observation(tmp_path: Path) -> None:
    """Pre-chain evidence is validated as such, not retrospectively signed."""
    folder = make_track(tmp_path)
    (folder / "evidence.jsonl").write_text(
        '{"schema_version":"1.0","status":"passed"}\n'
    )
    assert any("evidence" in e for e in validate(tmp_path)["errors"])


@pytest.mark.parametrize("event", ['"bad"', "[]", "null"])
def test_malformed_evidence_is_reported(tmp_path: Path, event: str) -> None:
    """Corrupt JSON values return a diagnostic instead of crashing validation."""
    folder = make_track(tmp_path)
    (folder / "evidence.jsonl").write_text(event + "\n")
    assert any("evidence" in e for e in validate(tmp_path)["errors"])


def test_malformed_gates_are_reported(tmp_path: Path) -> None:
    """A non-list gate container cannot be treated as valid evidence."""
    folder = make_track(tmp_path)
    (folder / "metadata.json").write_text(
        '{"id":"example","status":"completed","gates":null}'
    )
    assert any("gate" in e for e in validate(tmp_path)["errors"])


def test_inline_registration_is_checked(tmp_path: Path) -> None:
    """An inline link has the same lifecycle checks as a following-line link."""
    make_track(tmp_path)
    (tmp_path / "conductor/tracks.md").write_text(
        "- [x] [Example](./tracks/example/index.md)\n"
    )
    assert validate(tmp_path)["errors"] == []


def test_reconciled_legacy_evidence_remains_byte_pinned(tmp_path: Path) -> None:
    """Correcting a legacy format label must not hide edits to old observations."""
    folder = make_track(tmp_path)
    original = (
        '{"recorded_at":"2026-08-30T00:00:00Z","kind":"review","status":"passed"}\n'
    )
    (folder / "evidence.jsonl").write_text(original)
    metadata = json.loads((folder / "metadata.json").read_text())
    metadata["legacy_evidence_sha256"] = hashlib.sha256(original.encode()).hexdigest()
    (folder / "metadata.json").write_text(json.dumps(metadata))
    assert validate(tmp_path)["errors"] == []
    (folder / "evidence.jsonl").write_text(original.replace("passed", "failed"))
    assert any("legacy evidence" in e for e in validate(tmp_path)["errors"])


def test_preserved_original_plan_cannot_be_changed(tmp_path: Path) -> None:
    """The completed preservation step requires the exact original plan bytes."""
    folder = make_track(tmp_path)
    original = folder / "plan.original.md"
    original.write_text("Historical prose without individual task states.\n")
    metadata = json.loads((folder / "metadata.json").read_text())
    metadata["original_plan_sha256"] = hashlib.sha256(original.read_bytes()).hexdigest()
    (folder / "metadata.json").write_text(json.dumps(metadata))
    assert validate(tmp_path)["errors"] == []
    original.write_text("Changed historical claim.\n")
    assert any("historical plan" in e for e in validate(tmp_path)["errors"])
    original.unlink()
    assert any("historical plan" in e for e in validate(tmp_path)["errors"])


def test_nested_legacy_event_is_checked_without_rewriting(tmp_path: Path) -> None:
    """Legacy event/at ledgers remain checked at their original nested paths."""
    folder = make_track(tmp_path)
    original = folder / "evidence/evidence.jsonl"
    original.parent.mkdir()
    original.write_text(
        json.dumps(
            {
                "at": "2026-08-30T00:00:00Z",
                "event": "recorded",
                "actor": "maintainer",
                "summary": "Original record",
            }
        )
    )
    metadata = json.loads((folder / "metadata.json").read_text())
    metadata.update(
        evidence_schema="legacy-event-v1",
        legacy_evidence_path="evidence/evidence.jsonl",
        legacy_evidence_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
    )
    (folder / "metadata.json").write_text(json.dumps(metadata))
    assert validate(tmp_path)["errors"] == []
    original.unlink()
    assert any("missing evidence" in e for e in validate(tmp_path)["errors"])


def test_legacy_prefix_allows_valid_appends_but_never_rewrites(tmp_path: Path) -> None:
    """An active legacy ledger can grow while its baseline remains immutable."""
    folder = make_track(tmp_path)
    original = (
        b'{"recorded_at":"2026-08-30T00:00:00Z","kind":"review","status":"passed"}\n'
    )
    ledger = folder / "evidence.jsonl"
    metadata = json.loads((folder / "metadata.json").read_text())
    metadata.update(
        legacy_evidence_sha256=hashlib.sha256(original).hexdigest(),
        legacy_evidence_prefix_bytes=len(original),
    )
    (folder / "metadata.json").write_text(json.dumps(metadata))
    ledger.write_bytes(original + original)
    assert validate(tmp_path)["errors"] == []
    ledger.write_bytes(original + b"{}\n")
    assert any("invalid evidence line 2" in e for e in validate(tmp_path)["errors"])
    ledger.write_bytes(original.replace(b"passed", b"failed") + original)
    assert any("legacy evidence bytes" in e for e in validate(tmp_path)["errors"])
    ledger.write_bytes(original[:-1])
    assert any("legacy evidence bytes" in e for e in validate(tmp_path)["errors"])
    for invalid in (True, 0, -1, "100"):
        metadata["legacy_evidence_prefix_bytes"] = invalid
        (folder / "metadata.json").write_text(json.dumps(metadata))
        assert any(
            "invalid legacy evidence prefix" in e for e in validate(tmp_path)["errors"]
        )
