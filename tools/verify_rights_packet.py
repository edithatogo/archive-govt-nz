"""Check an exact-destination rights ledger before admitting packet members."""

from __future__ import annotations

import hashlib
import json
from zipfile import ZipFile
lazy from pathlib import Path


def verify_packet(packet: Path, destination: str) -> None:
    """Reject unlisted bytes, duplicate IDs and bodies without a bound decision."""
    with ZipFile(packet) as archive:
        expected = {"ledger.json"}
        ids = set()
        ledger = json.loads(archive.read("ledger.json"))
        if ledger["destination"] != destination:
            msg = "Rights review is for a different destination"
            raise ValueError(msg)
        for item in ledger["items"]:
            if item["id"] in ids:
                msg = "Duplicate rights decision"
                raise ValueError(msg)
            ids.add(item["id"])
            if (
                item["status"] == "held"
                and item.get("payload") is None
                and item["reason"]
            ):
                continue
            if item["status"] != "cleared" or not all(
                item.get(key)
                for key in (
                    "source",
                    "licence",
                    "attribution",
                    "source_sha256",
                    "changes",
                    "permission_evidence",
                )
            ):
                msg = "Missing item-specific clearance"
                raise ValueError(msg)
            member = "payloads/" + item["sha256"] + ".txt"
            if (
                item["payload"] != member
                or hashlib.sha256(archive.read(member)).hexdigest() != item["sha256"]
            ):
                msg = "Payload differs from reviewed bytes"
                raise ValueError(msg)
            expected.add(member)
        if sorted(archive.namelist()) != sorted(expected):
            msg = "Packet members differ from rights ledger"
            raise ValueError(msg)
