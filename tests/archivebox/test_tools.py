"""ArchiveBox pilot command integration contracts."""

import json
import subprocess
from pathlib import Path


def test_prepare_and_inventory_commands_emit_paired_receipts(tmp_path: Path) -> None:
    """The hosted command sequence produces deterministic machine evidence."""
    root = Path(__file__).parents[2]
    prepared = tmp_path / "prepared"
    prepare = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/prepare_archivebox_pilot.py",
            "--config",
            "config/archivebox-pilot.json",
            "--output-dir",
            str(prepared),
            "--prepared-at",
            "2026-08-11T00:00:00Z",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(prepare.stdout)["state"] == "prepared"
    assert len((prepared / "urls.txt").read_text(encoding="utf-8").splitlines()) == 3

    archive = prepared / "archive"
    archive.mkdir()
    (archive / "index.html").write_text("fixture", encoding="utf-8")
    urls = (prepared / "urls.txt").read_text(encoding="utf-8").splitlines()
    for index, url in enumerate(urls):
        snapshot = archive / "archive" / str(index)
        snapshot.mkdir(parents=True)
        (snapshot / "index.json").write_text(
            json.dumps({"url": url, "history": {"wget": []}}), encoding="utf-8"
        )
    receipt_json = prepared / "receipt.json"
    receipt_markdown = prepared / "receipt.md"
    inventory = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/inventory_archivebox_pilot.py",
            "--manifest",
            str(prepared / "input-manifest.json"),
            "--archive-root",
            str(archive),
            "--output-json",
            str(receipt_json),
            "--output-markdown",
            str(receipt_markdown),
            "--observed-at",
            "2026-08-11T01:00:00Z",
            "--max-total-bytes",
            "1024",
            "--max-files",
            "10",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(inventory.stdout)["state"] == "outputs-inventoried-and-hashed"
    receipt = json.loads(receipt_json.read_text(encoding="utf-8"))
    assert receipt["admission_state"] == "not-admitted"
    assert receipt["files"][0]["authoritative_original"] is False
    assert receipt_markdown.read_text(encoding="utf-8").startswith(
        "# ArchiveBox pilot receipt"
    )
