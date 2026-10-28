# SPDX-License-Identifier: Apache-2.0
"""Read-only reconstruction rejects self-rehashed metadata claims."""

import hashlib
import json
from typing import TYPE_CHECKING, Any

import pytest
from tests.domains.health_appropriations import test_partner_snapshots as peer
from tests.domains.health_appropriations import (
    test_qualified_overview_metadata as shared,
)

from archive_govt_nz.domains.health_appropriations import (
    qualified_overview_metadata as metadata,
)

if TYPE_CHECKING:
    from pathlib import Path

qualified_inputs = shared.qualified_inputs
metadata_input = shared.metadata_input
reviewed_inputs = peer.reviewed_inputs


@pytest.mark.parametrize("discovery", [False, True])
def test_read_only_verifier_reconstructs_existing_versions(
    metadata_input: metadata.QualifiedOverviewInput, tmp_path: Path, *, discovery: bool
) -> None:
    output = tmp_path / "metadata"
    metadata.export_qualified_overview_metadata(
        (metadata_input,), output, include_discovery=discovery
    )
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    pin = hashlib.sha256(before["MANIFEST.json"]).hexdigest()
    receipt = metadata.verify_qualified_overview_metadata(
        (metadata_input,), output, manifest_sha256=pin, include_discovery=discovery
    )
    assert receipt["status"] == "verified_reconstruction"
    assert receipt["files"] == len(before)
    assert receipt["publication"] == "not_performed"
    assert receipt["release_readiness"] == "not_assessed"
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_rehashed_blanket_licence_is_not_an_authority_record(
    metadata_input: metadata.QualifiedOverviewInput, tmp_path: Path
) -> None:
    output = tmp_path / "metadata"
    metadata.export_qualified_overview_metadata((metadata_input,), output)
    document = json.loads((output / "croissant.json").read_bytes())
    document["license"] = "CC0-1.0"
    changed = (json.dumps(document, sort_keys=True, indent=2) + "\n").encode()
    (output / "croissant.json").write_bytes(changed)
    manifest = json.loads((output / "MANIFEST.json").read_bytes())
    manifest["output_sha256"]["croissant.json"] = hashlib.sha256(changed).hexdigest()
    changed_manifest = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output / "MANIFEST.json").write_bytes(changed_manifest)
    with pytest.raises(ValueError, match="qualified_overview_metadata_contract"):
        metadata.verify_qualified_overview_metadata(
            (metadata_input,),
            output,
            manifest_sha256=hashlib.sha256(changed_manifest).hexdigest(),
        )


def test_unknown_metadata_member_is_rejected(
    metadata_input: metadata.QualifiedOverviewInput, tmp_path: Path
) -> None:
    output = tmp_path / "metadata"
    metadata.export_qualified_overview_metadata((metadata_input,), output)
    pin = hashlib.sha256((output / "MANIFEST.json").read_bytes()).hexdigest()
    (output / "unreviewed.json").write_text("{}")
    with pytest.raises(ValueError, match="qualified_overview_metadata_contract"):
        metadata.verify_qualified_overview_metadata(
            (metadata_input,), output, manifest_sha256=pin
        )


def test_partner_packet_reconstruction_rejects_rehashed_positive_links(
    metadata_input: metadata.QualifiedOverviewInput,
    reviewed_inputs: tuple[bytes, tuple[metadata.PartnerSnapshot, ...], dict[str, Any]],
    tmp_path: Path,
) -> None:
    _, snapshots, ledger = reviewed_inputs
    baseline = metadata.project_qualified_overview_discovery((metadata_input,))
    ledger["source_readiness_sha256"] = hashlib.sha256(
        baseline["federation_readiness.json"]
    ).hexdigest()
    output = tmp_path / "metadata"
    metadata.export_qualified_overview_metadata(
        (metadata_input,), output, include_discovery=True, partner_snapshots=snapshots
    )
    pin = hashlib.sha256((output / "MANIFEST.json").read_bytes()).hexdigest()
    receipt = metadata.verify_qualified_overview_metadata(
        (metadata_input,),
        output,
        manifest_sha256=pin,
        include_discovery=True,
        partner_snapshots=snapshots,
    )
    assert receipt["partner_snapshots"] == len(snapshots)
    assert receipt["publisher_checksum_mismatches"] == 0
    report = json.loads((output / "federation_readiness.json").read_bytes())
    report["approved_links"] = [{"unreviewed_target": "clinical-product"}]
    body = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    (output / "federation_readiness.json").write_bytes(body)
    manifest = json.loads((output / "MANIFEST.json").read_bytes())
    manifest["output_sha256"]["federation_readiness.json"] = hashlib.sha256(
        body
    ).hexdigest()
    body = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output / "MANIFEST.json").write_bytes(body)
    with pytest.raises(ValueError, match="qualified_overview_metadata_contract"):
        metadata.verify_qualified_overview_metadata(
            (metadata_input,),
            output,
            manifest_sha256=hashlib.sha256(body).hexdigest(),
            include_discovery=True,
            partner_snapshots=snapshots,
        )
