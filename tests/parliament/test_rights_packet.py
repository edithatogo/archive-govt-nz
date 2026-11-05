"""A metadata-only decision must never carry bytes into the public archive."""

import hashlib
import json
import sys
from zipfile import ZipFile
lazy from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.verify_rights_packet import verify_packet


def test_cleared_item_and_held_control(tmp_path: Path) -> None:
    """Adding a held original to an otherwise valid packet must fail."""
    packet = tmp_path / "packet.zip"
    body = b"licensed work"
    digest = hashlib.sha256(body).hexdigest()
    member = f"payloads/{digest}.txt"
    cleared = {
        "id": "one",
        "status": "cleared",
        "source": "fixture",
        "licence": "CC BY 4.0",
        "attribution": "Author",
        "source_sha256": digest,
        "changes": "plain text",
        "permission_evidence": "item notice",
        "payload": member,
        "sha256": digest,
    }
    with ZipFile(packet, "w") as archive:
        archive.writestr(member, body)
        archive.writestr(
            "ledger.json",
            json.dumps(
                {
                    "destination": "dataset",
                    "items": [
                        cleared,
                        {
                            "id": "two",
                            "status": "held",
                            "reason": "Third-party quotation",
                        },
                    ],
                }
            ),
        )
    verify_packet(packet, "dataset")
    with ZipFile(packet, "a") as archive:
        archive.writestr("payloads/two.pdf", b"held")
    with pytest.raises(ValueError, match="members differ"):
        verify_packet(packet, "dataset")
