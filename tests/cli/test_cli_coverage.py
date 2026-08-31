"""Coverage of CLI error and text-output branches."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import archive_govt_nz.cli as cli_module
from archive_govt_nz.distribution import publisher
from archive_govt_nz.gold import analytics, search
from archive_govt_nz.schemas import medallion

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_archive_manifest_text_and_verify_provenance_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise archive manifest text and provenance failure reporting."""
    warc = tmp_path / "sample.warc.gz"
    warc.write_bytes(b"WARC/1.0")
    assert (
        cli_module.archive(action="manifest", output_dir=str(tmp_path), format="text")
        == 0
    )
    assert "status=manifest_written" in capsys.readouterr().out

    monkeypatch.setattr(
        cli_module,
        "load_and_validate_provenance",
        lambda _path: (_ for _ in ()).throw(ValueError("bad provenance")),
    )
    assert (
        cli_module.verify(
            cas_dir=str(tmp_path / "cas"),
            schemas_dir=str(tmp_path),
            provenance_path=str(tmp_path / "bad"),
            format="json",
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["provenance_integrity"]["status"] == "failed"


def test_search_and_publish_corrupt_inputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise fail-closed search and publication preparation branches."""
    monkeypatch.setattr(
        cli_module,
        "search_scope_manifest",
        lambda *_args: (_ for _ in ()).throw(ValueError("corrupt index")),
    )
    assert cli_module.search("term", index_dir=str(tmp_path), format="json") == 1
    assert json.loads(capsys.readouterr().out)["status"] == "corrupt"

    monkeypatch.setattr(
        cli_module,
        "load_publication_package",
        lambda *_args: (_ for _ in ()).throw(ValueError("corrupt package")),
    )
    status, error, code, package = cli_module._evaluate_publish_request(  # noqa: SLF001
        "dry-run", str(tmp_path), ""
    )
    assert (status, code, package) == ("failed", 1, None)
    assert error == "corrupt package"


def test_legislation_manifest_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the human-readable legislation manifest branch."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        cli_module,
        "load_authenticated_manifest",
        lambda _path: {"total_records": 2, "manifest_sha256": "a" * 64},
    )
    assert cli_module._handle_leg_manifest(str(manifest), "text") == 0  # noqa: SLF001
    assert "Legislation manifest: status=ready" in capsys.readouterr().out


def test_query_metadata_and_text_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise Croissant, Hugging Face, SQL, semantic, and graph query paths."""
    monkeypatch.setattr(
        medallion,
        "generate_domain_croissant_descriptor",
        lambda _domain: {"domain": "x"},
    )
    monkeypatch.setattr(publisher, "build_hf_dataset_card", lambda _domain: "# card")
    assert cli_module.query_command(croissant_domain="health") == 0
    capsys.readouterr()
    assert cli_module.query_command(hf_card_domain="health") == 0
    capsys.readouterr()

    class FakeResult:
        def __init__(self) -> None:
            self.row_count = 1
            self.column_names = ["value"]

        def to_pylist(self) -> list[dict[str, int]]:
            return [{"value": 1}]

    class FakeAnalytics:
        def __init__(self, silver_base_dir: Path) -> None:
            self.silver_base_dir = silver_base_dir

        def query(self, _sql: str) -> FakeResult:
            return FakeResult()

        def close(self) -> None:
            return None

    monkeypatch.setattr(analytics, "GoldAnalyticsEngine", FakeAnalytics)
    assert (
        cli_module.query_command(sql="select 1", format="text", silver_dir=tmp_path)
        == 0
    )
    capsys.readouterr()

    class FakeSearch:
        def __init__(self) -> None:
            pass

        def search(self, *_args: object, **_kwargs: object) -> list[object]:
            return []

        def index_parquet_corpus(self, _path: Path) -> int:
            return 0

    monkeypatch.setattr(search, "GoldHybridSearchEngine", FakeSearch)
    assert (
        cli_module.query_command(semantic="term", format="text", silver_dir=tmp_path)
        == 0
    )
    capsys.readouterr()
    assert cli_module.query_command(graph_uri="urn:example", format="text") == 0
    capsys.readouterr()
