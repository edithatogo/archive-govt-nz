"""Tests for the unified archive-govt-nz query CLI command."""

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA, NormalizedSilverRecord


def test_query_cli_sql_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    silver_dir = tmp_path / "silver"
    leg_dir = silver_dir / "legislation"
    leg_dir.mkdir(parents=True)

    rec = NormalizedSilverRecord(
        nz_source_record_id="act-001",
        nz_acquisition_id="b-001",
        nz_content_id="c-001",
        nz_observed_at="2026-08-23T00:00:00Z",
        nz_schema_fingerprint="fp-001",
        domain="legislation",
        entity_type="act",
        canonical_uri="nzlc:act/001",
        title="Public Records Act 2005",
        body_text="Preservation text",
        body_format="text",
        valid_from="2005-04-21",
        valid_to=None,
        source_observed_at="2026-08-23T00:00:00Z",
        is_current=True,
        source_url="https://legislation.govt.nz",
        cas_path="cas/1",
        sha256_payload="1",
        blake3_payload="2",
        byte_size=100,
    )
    pydict = {field.name: [rec.to_dict()[field.name]] for field in SILVER_ARROW_SCHEMA}
    table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(table, leg_dir / "corpus.parquet")

    # Run CLI query command with --sql
    with pytest.raises(SystemExit) as exc_info:
        app(
            [
                "query",
                "--sql",
                "SELECT title, domain FROM silver_legislation",
                "--silver-dir",
                str(silver_dir),
            ]
        )
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["query_type"] == "sql"
    assert data["row_count"] == 1
    assert data["rows"][0]["title"] == "Public Records Act 2005"


def test_query_cli_semantic_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    silver_dir = tmp_path / "silver"
    leg_dir = silver_dir / "legislation"
    leg_dir.mkdir(parents=True)

    rec = NormalizedSilverRecord(
        nz_source_record_id="act-001",
        nz_acquisition_id="b-001",
        nz_content_id="c-001",
        nz_observed_at="2026-08-23T00:00:00Z",
        nz_schema_fingerprint="fp-001",
        domain="legislation",
        entity_type="act",
        canonical_uri="nzlc:act/001",
        title="Public Records Act 2005",
        body_text="Preservation text",
        body_format="text",
        valid_from="2005-04-21",
        valid_to=None,
        source_observed_at="2026-08-23T00:00:00Z",
        is_current=True,
        source_url="https://legislation.govt.nz",
        cas_path="cas/1",
        sha256_payload="1",
        blake3_payload="2",
        byte_size=100,
    )
    pydict = {field.name: [rec.to_dict()[field.name]] for field in SILVER_ARROW_SCHEMA}
    table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(table, leg_dir / "corpus.parquet")

    # Run CLI query command with --semantic
    with pytest.raises(SystemExit) as exc_info:
        app(
            [
                "query",
                "--semantic",
                "Public Records",
                "--silver-dir",
                str(silver_dir),
            ]
        )
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["query_type"] == "semantic"
    assert data["results_count"] == 1
    assert data["results"][0]["canonical_uri"] == "nzlc:act/001"


def test_query_cli_missing_args(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        app(["query"])
    assert exc_info.value.code == 2
