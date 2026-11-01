"""Recover canonical records from a hash-pinned original packet without refetching."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from archive_govt_nz.domains.legislation.historical_packet import FORMATS, WORK
from archive_govt_nz.domains.legislation.manifest import build_legislation_manifest
from archive_govt_nz.domains.legislation.models import (
    LegislationRecord,
    LegislationType,
)
from archive_govt_nz.domains.legislation.normalise import normalise_legislation_payload
from tools.legislation_historical_packet import PacketClient, digest
from tools.legislation_parent_state import unpack
from tools.verify_final_donor_state import check_identity, manifestation_identity


def recover_records(
    packet: Path, expected_sha256: str, titles: dict[str, str]
) -> list[LegislationRecord]:
    """Bind original work, expression, format, acquisition time and byte fixity."""
    with packet.open("rb") as stream:
        if digest(stream.read()) != expected_sha256:
            message = "Original packet digest mismatch"
            raise ValueError(message)
        with ZipFile(stream) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            member_names = ["manifest.json"]
            records = []
            seen = set()
            client = PacketClient()
            for row in manifest["originals"]:
                url = row["source_url"]
                work, stamp, extension = manifestation_identity(url)
                kind = (
                    "pdf_original_scan"
                    if url.endswith("/official_scan.pdf")
                    else extension
                )
                expression = work + "_en_" + stamp
                if (
                    not WORK.fullmatch(work)
                    or work != row["work_id"]
                    or expression != row["expression_id"]
                    or kind != row["format"]
                    or url in seen
                ):
                    message = "Original packet identity mismatch"
                    raise ValueError(message)
                seen.add(url)
                name = row.get("archive_path") or manifest["file_prefix"] + row["file"]
                member_names.append(name)
                payload = archive.read(name)
                if digest(payload) != row["sha256"] or len(payload) != row.get(
                    "bytes", row.get("size_bytes")
                ):
                    message = "Original member fixity mismatch"
                    raise ValueError(message)
                timestamp = row.get("retrieval_timestamp") or row["retrieved"]
                if datetime.fromisoformat(timestamp).tzinfo is None:
                    message = "Original acquisition time lacks timezone"
                    raise ValueError(message)
                client.expected[url] = (FORMATS[kind], titles[work])
                client.check_representation(url, payload)
                record = normalise_legislation_payload(
                    payload,
                    work,
                    titles[work],
                    url,
                    retrieval_timestamp=timestamp,
                    source_media_type=FORMATS[kind],
                    legislation_type=LegislationType.ACT,
                    canonical_expression_id=expression,
                    canonical_manifestation_id=url,
                )
                check_identity(record.to_dict_v2())
                records.append(record)
            if sorted(member_names) != sorted(archive.namelist()) or len(
                set(member_names)
            ) != len(member_names):
                message = "Unexpected original packet inventory"
                raise ValueError(message)
            return records


def main() -> None:
    """Stage a cumulative manifest; the hosted workflow owns checkpoint sealing."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--parent-reference", type=Path, required=True)
    parser.add_argument(
        "--packet", nargs=2, action="append", required=True, metavar=("ZIP", "SHA256")
    )
    parser.add_argument(
        "--titles",
        type=Path,
        required=True,
        help="JSON mapping of work IDs to PCO titles",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.parent.read_bytes()
    reference = json.loads(args.parent_reference.read_bytes())["durable"]
    if digest(raw) != reference["sha256"]:
        message = "Parent archive digest mismatch"
        raise ValueError(message)
    parent = json.loads(unpack(raw)["manifest.json"])
    titles = json.loads(args.titles.read_bytes())
    records = [
        record
        for path, pin in args.packet
        for record in recover_records(Path(path), pin, titles)
    ]
    manifest = build_legislation_manifest(
        records,
        run_id="original-packet-import",
        existing_records=parent["records"],
        discovered_work_ids=parent["discovered_work_ids"],
    )
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(manifest, output, ensure_ascii=False)


if __name__ == "__main__":
    main()
