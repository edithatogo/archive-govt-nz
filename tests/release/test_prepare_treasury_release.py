"""Treasury release-candidate preparation contracts."""

import hashlib
import json
import subprocess
import tarfile
from pathlib import Path


def prepare_workspace(workspace: Path) -> tuple[Path, Path, Path, Path]:
    """Create a minimal complete preservation workspace without ignored fixtures."""
    evidence_files = (
        "phase-2-live-observation.json",
        "phase-6-pre-capture-reconciliation.json",
        "phase-6-treasury-capture-plan.json",
        "archive-evidence-ledger.json",
        "release-attestation.json",
        "preservation-packaging-evaluation.json",
        "phase-6-capture-summary.json",
        "phase-6-rights-classification.json",
        "phase-8-hf-derivative-viewer-diagnosis.json",
        "phase-8-hf-csv-viewer-diagnosis.json",
    )
    evidence = workspace / "evidence"
    evidence.mkdir(parents=True)
    for name in evidence_files:
        (evidence / name).write_text("{}\n", encoding="utf-8")
    (evidence / "phase-8-hf-publication-verification.json").write_text(
        json.dumps(
            {
                "repository": "example/treasury",
                "revision": "fixture-revision",
                "publication_state": "uploaded-remotely-verified",
            }
        ),
        encoding="utf-8",
    )
    metadata = evidence / "publication-metadata"
    metadata.mkdir()
    (metadata / "README.md").write_text("fixture\n", encoding="utf-8")
    for name in ("zenodo.json", "taxonomy.json", "hf-estate-observation.json"):
        (metadata / name).write_text("{}\n", encoding="utf-8")
    docs = workspace / "docs"
    docs.mkdir()
    (docs / "archive-system-architecture.md").write_text(
        "# Architecture\n", encoding="utf-8"
    )
    (docs / "archive-system-architecture.mmd").write_text(
        "flowchart LR\n  A --> B\n", encoding="utf-8"
    )
    (docs / "archive-system-architecture.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"/>\n', encoding="utf-8"
    )
    build = workspace / "build"
    build.mkdir()
    (build / "sbom.cdx.json").write_text("{}\n", encoding="utf-8")
    raw = build / "raw"
    raw.mkdir()
    for index in range(2):
        (raw / f"package_search-{index:08d}.json").write_text("{}\n")
    objects = build / "objects"
    results: list[dict[str, str]] = []
    for payload in (b"first", b"second"):
        digest = hashlib.sha256(payload).hexdigest()
        path = objects / "sha256" / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        results.append({"state": "captured", "object_id": f"sha256:{digest}"})
    derivatives = build / "derivatives"
    derivatives.mkdir()
    (derivatives / "datasets.parquet").write_bytes(b"fixture")
    receipt = build / "capture.json"
    receipt.write_text(json.dumps({"results": results}), encoding="utf-8")
    return raw, objects, derivatives, receipt


def test_treasury_candidate_is_checksum_pinned_and_not_published(
    tmp_path: Path,
) -> None:
    """Candidate preparation excludes claims of complete payload capture."""
    root = Path(__file__).parents[2]
    workspace = tmp_path / "workspace"
    raw, objects, derivatives, receipt = prepare_workspace(workspace)
    output = workspace / "output"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            str(root / "tools/prepare_treasury_release.py"),
            "--output-dir",
            str(output),
            "--raw-dir",
            str(raw),
            "--object-root",
            str(objects),
            "--derivatives-dir",
            str(derivatives),
            "--capture-receipt",
            str(receipt),
        ],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "prepared-not-published" in result.stdout
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["publication_authorized"] is False
    assert "payload_capture_not_complete" in manifest["limitations"]
    assert len(manifest["file_checksums"]) > 20
    assert manifest["huggingface"]["revision"] == "fixture-revision"
    with tarfile.open(output / "treasury-release-candidate.tar") as archive:
        names = set(archive.getnames())
    assert any(name.startswith("build/objects/sha256/") for name in names)
    assert any(name.endswith("raw/package_search-00000000.json") for name in names)
    assert "build/derivatives/datasets.parquet" in names
    assert "build/capture.json" in names
    assert "docs/archive-system-architecture.md" in names
    assert "docs/archive-system-architecture.mmd" in names
    assert "docs/archive-system-architecture.svg" in names
    assert manifest["layer_counts"]["captured_objects"] == 2
    assert manifest["layer_counts"]["raw_ckan_responses"] == 2
