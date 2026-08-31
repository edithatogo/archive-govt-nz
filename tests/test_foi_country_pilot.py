"""The bounded country pilot preserves originals without national coverage claims."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "foi_country_pilot_tool", Path(__file__).parents[1] / "tools/foi_country_pilot.py"
)
assert SPEC is not None
assert SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """Create an official-format synthetic institutional nil return."""
    path = tmp_path / "source"
    path.mkdir()
    csv = b"year,month,owner_org,owner_org_title\n2025,8,agency,Agency\n"
    metadata = {
        "success": True,
        "result": {
            "id": TOOL.DATASET,
            "license_id": "ca-ogl-lgo",
            "license_url": TOOL.LICENCE,
            "private": False,
            "state": "active",
            "resources": [
                {
                    "id": TOOL.RESOURCE,
                    "url": TOOL.RESOURCE_URL,
                    "format": "CSV",
                    "size": len(csv),
                }
            ],
        },
    }
    schema = {
        "resources": [
            {
                "resource_name": "ati-nil",
                "fields": [{"id": "year"}, {"id": "month"}],
            }
        ]
    }
    (path / "ati-nil.csv").write_bytes(csv)
    (path / "source-metadata.json").write_text(json.dumps(metadata))
    (path / "ati-schema.json").write_text(json.dumps(schema))
    return path


def test_deterministic_prepare_and_cold_restore(source: Path, tmp_path: Path) -> None:
    """Identical originals generate identical manifests and reversible metadata."""
    package = tmp_path / "package"
    digest = TOOL.prepare(source, package)
    assert TOOL.prepare(source, tmp_path / "second") == digest
    manifest = TOOL.verify(package, digest)
    assert manifest["coverage"]["enumerated"] == 1
    assert manifest["coverage"]["country_complete"] is False
    assert manifest["coverage"]["source_denominator"] is None
    restored = tmp_path / "restored"
    TOOL.restore(package, restored, digest)
    for name in TOOL.NAMES:
        assert (source / name).read_bytes() == (restored / name).read_bytes()
    with pytest.raises(ValueError, match="destination_exists"):
        TOOL.prepare(source, package)


@pytest.mark.parametrize(
    ("field", "value"), [("license_id", "unclear"), ("private", True)]
)
def test_source_binding_fails_closed(source: Path, field: str, value: object) -> None:
    """Public appearance never substitutes for explicit provider licence metadata."""
    file = source / "source-metadata.json"
    document = json.loads(file.read_bytes())
    document["result"][field] = value
    file.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="source_binding"):
        TOOL.build(source)


def test_wrong_resource_and_schema_rejected(source: Path) -> None:
    """Reject drifted resources and provider schemas."""
    file = source / "source-metadata.json"
    document = json.loads(file.read_bytes())
    document["result"]["resources"][0]["size"] += 1
    file.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="resource_binding"):
        TOOL.build(source)
    document["result"]["resources"][0]["size"] -= 1
    file.write_text(json.dumps(document))
    (source / "ati-schema.json").write_text('{"resources":[]}')
    with pytest.raises(ValueError, match="provider_schema"):
        TOOL.build(source)


@pytest.mark.parametrize(
    ("suffix", "reason"),
    [
        ("", "empty"),
        ("2025,13,agency,Agency\n", "csv_row"),
        ("2025,1,agency,Agency,extra\n", "csv_row"),
        ("2025,1,agency\n", "csv_row"),
        ("2025,1,agency,Agency\n2025,1,agency,Agency\n", "duplicate"),
    ],
)
def test_invalid_population_is_not_silently_shrunk(suffix: str, reason: str) -> None:
    """Missing, malformed and duplicate rows fail instead of improving percentages."""
    with pytest.raises(ValueError, match=reason):
        TOOL.rows(("year,month,owner_org,owner_org_title\n" + suffix).encode())
    with pytest.raises(ValueError, match="csv_schema"):
        TOOL.rows(b"unknown\nvalue\n")


def test_corruption_and_extra_objects_rejected(source: Path, tmp_path: Path) -> None:
    """Restore requires the pinned manifest and exact package population."""
    package = tmp_path / "package"
    digest = TOOL.prepare(source, package)
    with pytest.raises(ValueError, match="manifest_digest"):
        TOOL.verify(package, "0" * 64)
    extra = package / "extra"
    extra.write_bytes(b"extra")
    with pytest.raises(ValueError, match="population"):
        TOOL.verify(package, digest)
    extra.unlink()
    (package / "index.jsonl").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="integrity"):
        TOOL.verify(package, digest)


def test_source_links_and_budgets_rejected(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The offline reader rejects links and bounds bytes before parsing."""
    monkeypatch.setattr(TOOL, "LIMIT", 1)
    with pytest.raises(ValueError, match="budget"):
        TOOL.build(source)
    file = source / "ati-nil.csv"
    file.unlink()
    file.symlink_to(source / "source-metadata.json")
    with pytest.raises(ValueError, match="pilot_path"):
        TOOL.build(source)


def test_cli_prepare_verify_restore(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CLI has no network or publication action."""
    package = tmp_path / "package"
    monkeypatch.setattr(
        sys,
        "argv",
        ["pilot", "prepare", "--source", str(source), "--output", str(package)],
    )
    assert TOOL.main() == 0
    digest = hashlib.sha256((package / "manifest.json").read_bytes()).hexdigest()
    for action in ["verify", "restore"]:
        args = ["pilot", action, "--source", str(package), "--manifest-sha256", digest]
        if action == "restore":
            args += ["--output", str(tmp_path / "restored")]
        monkeypatch.setattr(sys, "argv", args)
        assert TOOL.main() == 0
    monkeypatch.setattr(
        sys,
        "argv",
        ["pilot", "verify", "--source", str(package), "--manifest-sha256", "wrong"],
    )
    assert TOOL.main() == 1


def test_generated_index_budget_fails_before_output(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Metadata expansion must not create an oversized unverifiable package."""
    monkeypatch.setattr(TOOL, "LIMIT", 2048)
    monkeypatch.setattr(TOOL, "rows", lambda _data: [{"value": "x" * 4096}])
    output = tmp_path / "oversized"
    with pytest.raises(ValueError, match="pilot_budget"):
        TOOL.prepare(source, output)
    assert not output.exists()


@pytest.mark.parametrize("flag", [False, None, 1, "true"])
def test_failed_ckan_envelope_is_not_source_evidence(
    source: Path, flag: object
) -> None:
    """A response result is not valid evidence when its provider envelope failed."""
    file = source / "source-metadata.json"
    document = json.loads(file.read_bytes())
    document["success"] = flag
    file.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="pilot_source_binding"):
        TOOL.build(source)


@pytest.mark.parametrize("action", ["prepare", "verify", "restore"])
def test_cli_requires_explicit_destination_or_digest(
    source: Path, monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    """Missing operational arguments fail before a package can be modified."""
    args = ["pilot", action, "--source", str(source)]
    if action == "restore":
        args += ["--manifest-sha256", "a" * 64]
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit):
        TOOL.main()


def test_symlink_destination_parent_is_rejected(source: Path, tmp_path: Path) -> None:
    """A new output path must not redirect through another directory."""
    link = tmp_path / "link"
    link.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="pilot_path"):
        TOOL.prepare(source, link / "package")


def test_restore_rechecks_originals_after_copy(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Injected same-length corruption during restore cannot pass rebuilt fixity."""
    package = tmp_path / "package"
    digest = TOOL.prepare(source, package)
    restored = tmp_path / "restored"
    build = TOOL.build

    def corrupt_then_build(folder: Path) -> dict:
        if folder == restored:
            file = folder / "ati-nil.csv"
            file.write_bytes(file.read_bytes().replace(b"2025", b"2024"))
        return build(folder)

    monkeypatch.setattr(TOOL, "build", corrupt_then_build)
    with pytest.raises(ValueError, match="restore_integrity"):
        TOOL.restore(package, restored, digest)


def test_output_preflight_checks_package_total(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Even generated content is bounded before creating the output directory."""
    monkeypatch.setattr(TOOL, "LIMIT", 1)
    monkeypatch.setattr(TOOL, "build", lambda _source: {str(i): b"x" for i in range(6)})
    with pytest.raises(ValueError, match="pilot_budget"):
        TOOL.prepare(source, tmp_path / "oversized")


def test_row_count_cap_fails_without_truncation(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An oversized population cannot turn into an apparently complete prefix."""
    monkeypatch.setattr(TOOL, "MAX_ROWS", 0)
    with pytest.raises(ValueError, match="pilot_budget"):
        TOOL.build(source)
