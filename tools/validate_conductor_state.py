"""Validate repository-native Conductor state without rewriting historical evidence.

The project predates canonical skill labels: numbered tracks, requirements-only
specifications and unchained observation ledgers are native formats, not proof of
new completion. This reader checks their actual lifecycle and reference contracts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

CHECKBOX = re.compile(r"^\s*(?:-|\d+\.)\s*\[([ x~])\]")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
STATES = {
    "complete": "x",
    "completed": "x",
    "archived": "x",
    "new": " ",
    "pending": " ",
    "in_progress": "~",
}
GATE_STATES = {"passed", "satisfied", "pending", "blocked", "not_applicable"}


def registry_entries(registry: Path) -> list[tuple[str, str]]:
    """Read linked checkbox entries, including numbered and child tracks."""
    lines = registry.read_text(encoding="utf-8").splitlines()
    entries: list[tuple[str, str]] = []
    for index, line in enumerate(lines):
        mark = CHECKBOX.match(line)
        if not mark:
            continue
        if match := LINK.search(line):
            entries.append((mark[1], match[1]))
            continue
        for following in lines[index + 1 : index + 4]:
            if CHECKBOX.match(following):
                break
            match = LINK.search(following)
            if match:
                entries.append((mark[1], match[1]))
                break
    return entries


def _check_event(
    item: object,
    previous: str | None,
    folder: Path,
    *,
    chained: bool,
    legacy_event: bool = False,
) -> str | None:
    if not isinstance(item, dict):
        msg = "evidence must be an object"
        raise TypeError(msg)
    if legacy_event:
        datetime.fromisoformat(item["at"])
        if not all(item.get(key) for key in ("event", "actor", "summary")):
            msg = "missing legacy event fields"
            raise ValueError(msg)
        return None
    datetime.fromisoformat(item["recorded_at"])
    if not item.get("kind") or not item.get("status"):
        msg = "missing observation fields"
        raise ValueError(msg)
    if not chained:
        return None
    digest = item["entry_sha256"]
    payload = {key: value for key, value in item.items() if key != "entry_sha256"}
    actual = hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()
    if (
        digest != actual
        or item.get("previous_entry_sha256") != previous
        or item.get("track_id") != folder.name
    ):
        msg = "evidence chain mismatch"
        raise ValueError(msg)
    return str(digest)


def evidence_errors(folder: Path, metadata: dict[str, Any]) -> list[str]:
    """Validate observations and verify canonical chains when declared/present."""
    relative = Path(metadata.get("legacy_evidence_path", "evidence.jsonl"))
    path = (folder / relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(folder.resolve()):
        return ["unsafe evidence path"]
    chained = metadata.get("evidence_contract") == "chained-v1"
    if not path.exists():
        return (
            ["missing evidence"]
            if chained or metadata.get("legacy_evidence_sha256")
            else []
        )
    errors: list[str] = []
    preserved = path.read_bytes()
    if "legacy_evidence_prefix_bytes" in metadata:
        prefix = metadata["legacy_evidence_prefix_bytes"]
        if type(prefix) is not int or prefix <= 0:
            return ["invalid legacy evidence prefix length"]
        preserved = preserved[:prefix]
    if (digest := metadata.get("legacy_evidence_sha256")) and digest != hashlib.sha256(
        preserved
    ).hexdigest():
        errors.append("legacy evidence bytes changed")
    previous: str | None = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            chained = chained or (isinstance(item, dict) and "entry_sha256" in item)
            previous = _check_event(
                item,
                previous,
                folder,
                chained=chained,
                legacy_event=metadata.get("evidence_schema") == "legacy-event-v1",
            )
        except KeyError, TypeError, ValueError:
            errors.append(f"invalid evidence line {number}")
    if chained and previous is None:
        errors.append("empty chained evidence")
    return errors


def _plan_errors(folder: Path, state: str, metadata: dict[str, Any]) -> list[str]:
    plan_path = folder / "plan.md"
    plan = re.sub(
        r"```.*?```", "", plan_path.read_text(encoding="utf-8"), flags=re.DOTALL
    )
    tasks = [match[1] for line in plan.splitlines() if (match := CHECKBOX.match(line))]
    if digest := metadata.get("original_plan_sha256"):
        original = folder / "plan.original.md"
        if (
            not original.is_file()
            or hashlib.sha256(original.read_bytes()).hexdigest() != digest
        ):
            return ["historical plan bytes changed or missing"]
    if not tasks:
        return ["plan contains no task checkboxes"]
    if state == "x" and any(task != "x" for task in tasks):
        return ["completed track has incomplete plan"]
    if state == " " and any(task != " " for task in tasks):
        return ["pending track has started plan"]
    if state == "~" and all(task == "x" for task in tasks):
        return ["in-progress track has completed plan"]
    return []


def _metadata_errors(folder: Path, state: str, metadata: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    identity = metadata.get("track_id", metadata.get("id", folder.name))
    if identity != folder.name:
        errors.append("metadata identity mismatch")
    if STATES.get(str(metadata.get("status"))) != state:
        errors.append("metadata status mismatch")
    gates = metadata.get("gates", [])
    if not isinstance(gates, list):
        errors.append("invalid gates container")
        gates = []
    errors.extend(
        "invalid gate"
        for gate in gates
        if not isinstance(gate, dict)
        or not gate.get("id")
        or not gate.get("kind")
        or str(gate.get("status")) not in GATE_STATES
    )
    for name in ("created_at", "updated_at"):
        if value := metadata.get(name):
            try:
                datetime.fromisoformat(str(value))
            except ValueError:
                errors.append(f"invalid {name}")
    return errors


def track_errors(folder: Path, state: str) -> list[str]:
    """Check authoritative plan/metadata agreement and evidence structure."""
    errors = [
        f"missing {name}"
        for name in ("index.md", "plan.md", "metadata.json")
        if not (folder / name).is_file()
        or not (folder / name).read_text(encoding="utf-8").strip()
    ]
    if errors:
        return errors
    try:
        metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    except ValueError:
        return ["invalid metadata.json"]
    if not isinstance(metadata, dict):
        return ["invalid metadata.json"]
    errors.extend(_metadata_errors(folder, state, metadata))
    errors.extend(_plan_errors(folder, state, metadata))
    if not any((folder / name).is_file() for name in ("spec.md", "requirements.md")):
        errors.append("missing specification or requirements")
    errors.extend(evidence_errors(folder, metadata))
    return errors


def _unregistered(conductor: Path, seen: set[Path]) -> list[str]:
    errors: list[str] = []
    for section in ("tracks", "archive"):
        base = conductor / section
        if not base.is_dir():
            continue
        for folder in base.iterdir():
            # Imported donor snapshots have their own immutable lineage contracts.
            if folder.name == "imported" and section == "archive":
                continue
            if folder.is_dir() and folder not in seen:
                errors.append(f"unregistered track: {folder.name}")
    return errors


def validate(root: Path) -> dict[str, Any]:
    """Validate all local tracks; imported immutable donor trees are containers."""
    root = root.resolve()
    conductor = root / "conductor"
    registry = conductor / "tracks.md"
    errors: list[str] = []
    seen: set[Path] = set()
    if not registry.is_file():
        return {"errors": ["missing registry"], "track_count": 0}
    for state, target in registry_entries(registry):
        path = (conductor / target).resolve()
        if not path.is_relative_to(conductor) or Path(target).is_absolute():
            errors.append(f"unsafe registry target: {target}")
            continue
        folder = path.parent if path.name == "index.md" else path
        if folder.parent not in {conductor / "tracks", conductor / "archive"}:
            errors.append(f"unsafe track location: {target}")
            continue
        if folder in seen:
            errors.append(f"duplicate track: {folder.name}")
            continue
        seen.add(folder)
        errors.extend(
            f"{folder.name}: {error}" for error in track_errors(folder, state)
        )
        if folder.parent.name == "archive" and state != "x":
            errors.append(f"{folder.name}: archived track is not complete")
    errors.extend(_unregistered(conductor, seen))
    return {"errors": errors, "track_count": len(seen)}


def main() -> int:
    """Print a machine-readable validation result and fail on lifecycle drift."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    result = validate(parser.parse_args().root)
    print(json.dumps(result, indent=2))
    return int(bool(result["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
