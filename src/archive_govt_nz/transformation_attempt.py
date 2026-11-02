"""Pin an execution to reviewed material and preserve each attempt exactly once."""

from __future__ import annotations

import json
import os
from uuid import uuid4
lazy from pathlib import Path

from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.provenance import ProvenanceError


def check_material(expected: dict[str, object], actual: dict[str, object]) -> None:
    """Require an independent expectation for each part of the execution."""
    for field in ("operation", "config", "environment", "inputs"):
        if (
            field not in expected
            or field not in actual
            or expected[field] is None
            or expected[field] != actual[field]
        ):
            msg = f"unexpected_{field}"
            raise ProvenanceError(msg)


class TransformationAttempt:
    """Reserve the output name before launch. A crash leaves an incomplete attempt."""

    def __init__(self, location: Path, material: dict[str, object]) -> None:
        """Claim a new destination and persist the initial material snapshot."""
        self.location = location
        location.mkdir(parents=True, exist_ok=False)
        self.attempt_id = uuid4().hex
        self.store = ContentAddressedStore(location / "cas")
        self._publish("started", {"material": material})

    def _publish(self, name: str, fields: dict[str, object]) -> None:
        payload = {"attempt_id": self.attempt_id, **fields}
        raw = json.dumps(payload, sort_keys=True, allow_nan=False).encode()
        receipt = self.store.put_bytes(raw)
        os.link(self.store.verify(receipt.object_id).path, self.location / name)

    def finish(self, state: str, result: dict[str, object]) -> None:
        """Atomically publish one terminal outcome without replacing any predecessor."""
        if state not in {"succeeded", "failed", "interrupted"}:
            msg = "invalid_terminal_state"
            raise ProvenanceError(msg)
        self._publish("terminal", {"state": state, "result": result})
