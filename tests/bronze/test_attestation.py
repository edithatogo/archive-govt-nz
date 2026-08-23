"""Unit tests for Bronze Ed25519 manifest sealing and cryptographic attestation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from archive_govt_nz.bronze.adapter import BronzeDomainIngestor
from archive_govt_nz.bronze.attestation import (
    Ed25519Signer,
    Ed25519Verifier,
    seal_manifest,
    verify_manifest_seal,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def test_ed25519_rfc8032_vector_1() -> None:
    """Matches RFC 8032 test vector 1 for Ed25519 key derivation and signing."""
    sk_hex = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
    expected_pk = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    expected_sig = (
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
    )

    signer = Ed25519Signer.from_hex(sk_hex)
    assert signer.public_key_hex == expected_pk

    sig_hex = signer.sign_hex(b"")
    assert sig_hex == expected_sig

    verifier = Ed25519Verifier.from_hex(expected_pk)
    assert verifier.verify_hex(b"", expected_sig) is True


def test_ed25519_signing_and_tampering_detection() -> None:
    """Ed25519Verifier detects tampered messages and corrupted signatures."""
    signer = Ed25519Signer.generate()
    verifier = Ed25519Verifier(signer.public_key_bytes)

    message = b"Canonical Bronze manifest payload integrity attestation"
    sig_bytes = signer.sign(message)

    assert verifier.verify(message, sig_bytes) is True
    # Tampered message fails
    assert verifier.verify(message + b"!", sig_bytes) is False
    # Corrupted signature fails
    corrupted_sig = bytearray(sig_bytes)
    corrupted_sig[0] ^= 0xFF
    assert verifier.verify(message, bytes(corrupted_sig)) is False


def test_seal_and_verify_manifest(tmp_path: Path) -> None:
    """seal_manifest produces detached signature verified by verify_manifest_seal."""
    manifest_file = tmp_path / "manifest-batch-001.json"
    manifest_data = {
        "manifest_id": "manifest-001",
        "batch_id": "batch-001",
        "domain": "legislation",
        "records": [],
    }
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    signer = Ed25519Signer.generate()
    sig_file = tmp_path / "manifest-batch-001.sig"

    attestation = seal_manifest(manifest_file, signer, output_sig_path=sig_file)

    assert attestation.manifest_id == "manifest-001"
    assert sig_file.is_file()
    assert verify_manifest_seal(manifest_file, sig_file) is True

    # Tampering manifest breaks signature
    manifest_file.write_text(
        json.dumps({**manifest_data, "domain": "tampered"}, indent=2),
        encoding="utf-8",
    )
    assert verify_manifest_seal(manifest_file, sig_file) is False


def test_bronze_ingestor_sealing_flow(tmp_path: Path) -> None:
    """BronzeDomainIngestor finalizes batch with attached Ed25519 signature."""
    store = ContentAddressedStore(tmp_path / "cas")
    out_dir = tmp_path / "bronze_signed"
    ingestor = BronzeDomainIngestor(store=store, domain="gazette", base_dir=out_dir)

    rec = ingestor.ingest_payload(
        record_id="not-001",
        payload_bytes=b"Notice content 001",
        source_url="https://gazette.govt.nz/notice/001",
        media_type="text/plain",
    )

    signer = Ed25519Signer.generate()
    res = ingestor.finalize_batch(
        batch_id="batch-001",
        manifest_id="man-001",
        records=[rec],
        signer=signer,
    )

    assert res.status == "success"
    assert res.signature_path is not None
    sig_path = tmp_path / "bronze_signed" / "manifest-man-001.sig"
    manifest_path = tmp_path / "bronze_signed" / "manifest-man-001.json"

    assert sig_path.is_file()
    assert manifest_path.is_file()
    assert verify_manifest_seal(manifest_path, sig_path) is True
