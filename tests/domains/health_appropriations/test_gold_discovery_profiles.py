"""Discovery candidates preserve exact Gold identity and disclose standards gaps."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from rdflib import Graph, Namespace, URIRef
from tests.domains.health_appropriations.test_gold_metadata import packages

from archive_govt_nz.domains.health_appropriations import (
    gold_discovery_profiles as profiles,
)

pytest_plugins = ["tests.domains.health_appropriations.test_local_rdf"]


def test_pinned_candidates_replay_and_reject_unsupported_claims(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = packages(tmp_path, monkeypatch)
    first, second = tmp_path / "first", tmp_path / "second"
    dry = profiles.export_profiles(values, first)
    assert dry["status"] == "dry_run"
    assert not first.exists()
    written = profiles.export_profiles(values, first, write=True)
    assert written == profiles.export_profiles(
        tuple(reversed(values)), second, write=True
    )
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    console = Path(sys.executable).parent / (
        "archive-govt-nz.exe" if sys.platform == "win32" else "archive-govt-nz"
    )
    by_profile = {v.profile: v for v in values}
    args = [
        str(console),
        "health-appropriations-build-gold-discovery-candidates",
        "--fiscal-package",
        str(by_profile["fiscal_analytical"].root),
        "--fiscal-manifest-sha256",
        by_profile["fiscal_analytical"].manifest_sha256,
        "--budget-package",
        str(by_profile["budget_comparison"].root),
        "--budget-manifest-sha256",
        by_profile["budget_comparison"].manifest_sha256,
        "--output-dir",
        str(tmp_path / "console"),
    ]
    dry_cli = subprocess.run(
        args, capture_output=True, text=True, check=True, timeout=30
    )
    assert json.loads(dry_cli.stdout)["status"] == "dry_run"
    assert not (tmp_path / "console").exists()
    built_cli = subprocess.run(
        [*args, "--write"], capture_output=True, text=True, check=True, timeout=30
    )
    assert json.loads(built_cli.stdout)["manifest_sha256"] == written["manifest_sha256"]
    assert (
        json.loads(built_cli.stdout)["verification"]["status"]
        == "verified_local_candidates"
    )
    failed_cli = subprocess.run(
        [*args, "--write"], capture_output=True, text=True, check=False, timeout=30
    )
    assert failed_cli.returncode == 2
    assert json.loads(failed_cli.stdout)["error"] == "gold_discovery_build_failed"
    receipt = profiles.verify_profiles(values, first, written["manifest_sha256"])
    assert receipt["status"] == "verified_local_candidates"
    report = json.loads((first / "profile-validation.json").read_bytes())
    assert report["full_conformance"] == "not_asserted"
    assert report["release_readiness"] == "blocked"
    assert report["croissant"]["missing_dataset_properties"] == [
        "creator",
        "datePublished",
        "dct:conformsTo",
        "license",
        "url",
    ]
    assert report["croissant"]["missing_content_urls"] == 10
    assert report["ro_crate"]["missing_root_properties"] == ["datePublished", "license"]
    assert report["fields"] > 0
    croissant = json.loads((first / "croissant.json").read_bytes())
    crate = json.loads((first / "ro-crate-metadata.json").read_bytes())
    assert len(croissant["distribution"]) == 10
    assert len(croissant["cr:recordSet"]) == 5
    assert len(crate["@graph"]) == 12
    assert str(tmp_path) not in json.dumps(croissant)
    assert '"license"' not in json.dumps(crate)
    assert '"datePublished"' not in json.dumps(croissant)
    croissant["license"] = "https://creativecommons.org/publicdomain/zero/1.0/"
    with pytest.raises(ValueError, match="gold_discovery_profile_contract"):
        profiles.validate_documents(values, croissant, crate)
    with pytest.raises(FileExistsError):
        profiles.export_profiles(values, first, write=True)
    with pytest.raises(ValueError, match="gold_discovery_profile_contract"):
        profiles.export_profiles(values, values[0].root, write=True)
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        profiles.verify_profiles(values, first, "0" * 64)
    (first / "profile-validation.json").write_text("changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        profiles.verify_profiles(values, first, written["manifest_sha256"])


def test_offline_candidates_have_exact_files_columns_and_type_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parse_offline: Callable[[object], Graph],
) -> None:
    values = packages(tmp_path, monkeypatch)
    croissant, crate, report = profiles.project_profiles(values)
    cr = parse_offline(croissant)
    ro = parse_offline(crate)
    schema = Namespace("http://schema.org/")
    croissant_ns = Namespace("http://mlcommons.org/croissant/")
    rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    assert len(list(cr.subjects(rdf.type, croissant_ns.FileObject))) == 10
    assert len(list(cr.subjects(rdf.type, croissant_ns.RecordSet))) == 5
    assert len(list(cr.subjects(rdf.type, croissant_ns.Field))) == report["fields"]
    assert len(list(ro.subjects(rdf.type, schema.MediaObject))) == 10
    for record in croissant["cr:recordSet"]:
        for field in record["cr:field"]:
            assert (
                URIRef(field["@id"]),
                croissant_ns.dataType,
                URIRef(field["cr:dataType"]["@id"]),
            ) in cr
            assert field["cr:source"]["cr:extract"]["cr:column"] == field["name"]
    assert profiles.validate_documents(values, croissant, crate) == report
    root = next(n for n in crate["@graph"] if n["@id"] == "./")
    assert len(root["hasPart"]) == 10
    assert {m["@id"] for m in root["hasPart"]} == {
        d["@id"] for d in croissant["distribution"]
    }

    croissant["@context"]["@vocab"] = "https://unsupported.example/"
    with pytest.raises(ValueError, match="gold_discovery_profile_contract"):
        profiles.validate_documents(values, croissant, crate)
