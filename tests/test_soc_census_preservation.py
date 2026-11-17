"""SOC01 retained source admission and content-addressed HF target controls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools import preserve_soc_census as p


def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    contents = {"census2023_general_2020": b"official-source-a", "census2023_maori_2025": b"official-source-b"}
    monkeypatch.setattr(p, "SOURCES", {
        k: {"sha256": hashlib.sha256(blob).hexdigest(), "url": "https://www3.parliament.nz/test/"+k+".xlsx"}
        for k, blob in contents.items()
    })
    rows = []
    for key, blob in contents.items():
        (tmp_path/(key+".xlsx")).write_bytes(blob)
        rows.append({"id": key, "sha256": hashlib.sha256(blob).hexdigest(),
                     "bytes": len(blob), "url": p.SOURCES[key]["url"],
                     "status": "captured", "family": "census"})
    (tmp_path/"manifest.json").write_text(json.dumps({"records": rows}))
    return tmp_path


def test_dry_run_builds_only_content_addressed_census_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture(tmp_path, monkeypatch)
    plans = p.plan_preservation(root)
    assert len(plans) == 2
    assert all("/census2023/" in x["target"] and x["target"].endswith(x["sha256"]+".xlsx") for x in plans)
    assert all(x["licence"] == "CC-BY-4.0 (Stats NZ source workbooks)" for x in plans)


def test_byte_tampering_and_source_manifest_resealing_do_not_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture(tmp_path, monkeypatch)
    source = root/"census2023_general_2020.xlsx"
    source.write_bytes(b"different-source")
    with pytest.raises(ValueError, match="pinned|hash"):
        p.plan_preservation(root)
    recorded = json.loads((root/"manifest.json").read_text())
    recorded["records"][0]["sha256"] = hashlib.sha256(b"different-source").hexdigest()
    (root/"manifest.json").write_text(json.dumps(recorded))
    with pytest.raises(ValueError, match="pinned|hash"):
        p.plan_preservation(root)


def test_extra_election_commission_workbooks_not_selected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture(tmp_path, monkeypatch)
    manifest = json.loads((root/"manifest.json").read_text())
    manifest["records"].append({"id": "turnout2023_sa2", "sha256": "b"*64,
                                "bytes": 42, "url": "https://elections.nz/x",
                                "status": "captured", "family": "turnout"})
    (root/"manifest.json").write_text(json.dumps(manifest))
    assert len(p.plan_preservation(root)) == 2


def test_duplicate_identity_or_symlink_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture(tmp_path, monkeypatch)
    manifest = json.loads((root/"manifest.json").read_text())
    manifest["records"].append(dict(manifest["records"][0]))
    (root/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="duplicate"):
        p.plan_preservation(root)
    manifest["records"].pop()
    (root/"manifest.json").write_text(json.dumps(manifest))
    target = root/"census2023_general_2020.xlsx"
    target.rename(root/"real.xlsx")
    target.symlink_to(root/"real.xlsx")
    with pytest.raises(ValueError, match="symlink"):
        p.plan_preservation(root)


def test_publish_path_requires_two_separate_approvals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture(tmp_path, monkeypatch)
    plans = p.plan_preservation(root)
    with pytest.raises(ValueError, match="approval"):
        p.publish(plans, token="not-used", approved=False)
    with pytest.raises(ValueError, match="token"):
        p.publish(plans, token="", approved=True)
