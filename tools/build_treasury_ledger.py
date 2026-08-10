"""Build a deterministic local SQLite ledger from Treasury receipts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.ledger import Ledger
from archive_govt_nz.object_store import ContentAddressedStore

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict[str, object]:
    """Load one JSON receipt."""
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    """Materialize one non-publication operational ledger and receipt."""
    ledger_path = ROOT / "build/treasury-ledger.sqlite"
    if ledger_path.exists():
        message = "refusing to overwrite existing ledger"
        raise SystemExit(message)
    plan = _load(ROOT / "evidence/phase-6-treasury-capture-plan.json")
    capture = _load(ROOT / "build/live/capture-20260731.json")
    capture_rows: dict[str, dict[str, Any]] = {
        str(row["resource_id"]): row
        for row in cast("list[dict[str, Any]]", capture["results"])
    }
    store = ContentAddressedStore(ROOT / "build/objects")
    ledger = Ledger(ledger_path)
    try:
        for outcome in cast("list[dict[str, Any]]", plan["outcomes"]):
            resource_id = str(outcome["resource_id"])
            observation_id = f"resource:{resource_id}"
            payload: dict[str, object] = {
                "dataset_id": outcome["dataset_id"],
                "resource_id": resource_id,
                "source_url": outcome["source_url"],
                "decision": outcome["decision"],
            }
            ledger.record_observation(observation_id, payload)
            captured: dict[str, Any] | None = capture_rows.get(resource_id)
            state = "captured" if captured else str(outcome["decision"]["disposition"])
            ledger.record_attempt(
                f"attempt:{resource_id}", observation_id, state, captured or payload
            )
            ledger.record_version(
                f"version:{resource_id}",
                observation_id,
                "captured" if captured else "unavailable",
                {"state": state, "source_url": outcome["source_url"]},
            )
            if captured:
                object_id = str(captured["object_id"])
                receipt = store.verify(object_id)
                ledger.record_object(
                    object_id,
                    receipt.sha256,
                    receipt.blake3,
                    receipt.byte_count,
                    "source_resource",
                )
                ledger.record_object_source(
                    object_id,
                    resource_id,
                    "captured-from",
                    {"source_url": outcome["source_url"]},
                )
        ledger.checkpoint("treasury", "91-resources-reconciled")
        table_count_queries = {
            "observations": "SELECT count(*) FROM observations",
            "attempts": "SELECT count(*) FROM attempts",
            "objects": "SELECT count(*) FROM objects",
            "versions": "SELECT count(*) FROM versions",
        }
        counts = {
            table: int(ledger.connection.execute(statement).fetchone()[0])
            for table, statement in table_count_queries.items()
        }
    finally:
        ledger.close()
    output = ROOT / "evidence/phase-5-ledger-build.json"
    output.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.ledger-build/v1",
                "ledger": "build/treasury-ledger.sqlite",
                "counts": counts,
                "publication": "not attempted",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    main()
