"""Canonical metadata preserves full source-token coverage and verified types."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from jsonschema import Draft202012Validator
from rdflib.namespace import DCAT, PROV, RDF
from tests.domains.health_appropriations.test_canonical_gold_queries import (
    fact_package,
    repin,
    source_row,
)
from tests.domains.health_appropriations.test_canonical_gold_verification import (
    _ready_server,
)
from tests.domains.health_appropriations.test_gold_metadata import (
    packages as legacy_packages,
)

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_queries as query,
)
from archive_govt_nz.domains.health_appropriations import gold_metadata as metadata

if TYPE_CHECKING:
    from rdflib import Graph
from tests.health_rights_review_support import RIGHTS_REVIEW

pytest_plugins = ["tests.domains.health_appropriations.test_local_rdf"]


def test_canonical_metadata_uses_full_tables_and_rebuilds_offline(
    tmp_path: Path, parse_offline: Callable[[object], Graph]
) -> None:
    root, _ = fact_package(tmp_path)
    filename, schema = query.PRODUCTS["historical"]
    rows = [source_row(schema, year) for year in range(2000, 2300)]
    pq.write_table(
        pa.Table.from_pylist(rows, schema=schema),
        root / filename,
        compression="zstd",
        use_dictionary=False,
    )
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_bytes())
    manifest["outputs"][filename]["rows"] = len(rows)
    marker.write_text(json.dumps(manifest))
    pin = repin(root)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    inputs = (metadata.GoldInput("canonical_source_separated", root, pin),)
    output, repeat = tmp_path / "metadata", tmp_path / "repeat"
    dry = metadata.export_gold_metadata(inputs, output)
    assert dry["status"] == "dry_run"
    assert not output.exists()
    first = metadata.export_gold_metadata(inputs, output, write=True)
    assert first["schema_version"] == "archive-govt-nz.health-gold-metadata/v4"
    assert first == metadata.export_gold_metadata(inputs, repeat, write=True)
    assert (
        metadata.verify_gold_metadata(inputs, output, first["manifest_sha256"])[
            "status"
        ]
        == "verified"
    )
    assert {p.name: p.read_bytes() for p in output.iterdir()} == {
        p.name: p.read_bytes() for p in repeat.iterdir()
    }
    assert (
        RIGHTS_REVIEW.review_graph_claims(
            {p.name: p.read_bytes() for p in output.iterdir()}, {}
        )["statements"]
        == []
    )
    catalogue = json.loads((output / "catalogue.json").read_bytes())
    package = catalogue["packages"][0]
    assert package["profile"] == "canonical_source_separated"
    assert package["rights"] == "not_evaluated"
    assert package["publication"] == "not_performed"
    assert len(package["tables"]) == 10
    historical = next(t for t in package["tables"] if t["path"] == filename)
    assert historical["rows"] == 300
    assert historical["observed_period_tokens"] == sorted(
        row["period_token"] for row in rows
    )
    assert historical["period_basis"] == "source_tokens_not_interpreted"
    assert historical["observed_period_end_count"] == 0
    assert historical["observed_period_end_min"] is None
    assert historical["observed_period_end_max"] is None
    for table in package["tables"]:
        if table["path"].startswith("biff8_"):
            assert (
                table["period_basis"]
                == "replayed_biff8_year_integer_rendered_as_string"
            )
        restored = pa.ipc.read_schema(
            pa.BufferReader(bytes.fromhex(table["schema_ipc_hex"]))
        )
        assert restored.equals(
            pq.read_schema(root / table["path"]), check_metadata=True
        )
    dcat = parse_offline(json.loads((output / "dcat.jsonld").read_bytes()))
    prov = parse_offline(json.loads((output / "prov.jsonld").read_bytes()))
    assert len(set(dcat.subjects(RDF.type, DCAT.Dataset))) == 10
    assert len(set(prov.subjects(RDF.type, PROV.Collection))) == 1
    for name, schema_name in (
        ("citations.json", "health-gold-citations-v4.schema.json"),
        ("changelog.json", "health-gold-changelog-v4.schema.json"),
        ("source_drillthrough.json", "health-gold-source-drillthrough-v2.schema.json"),
    ):
        definition = json.loads(
            (Path(__file__).parents[3] / "schemas" / schema_name).read_bytes()
        )
        Draft202012Validator(definition).validate(
            json.loads((output / name).read_bytes())
        )
    text = b"\n".join(p.read_bytes() for p in output.iterdir()).decode()
    assert str(tmp_path) not in text
    assert '"license"' not in text
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


@pytest.mark.parametrize("case", ["pin", "rights", "schema"])
def test_canonical_metadata_rejects_unqualified_or_changed_inputs(
    tmp_path: Path, case: str
) -> None:
    root, pin = fact_package(tmp_path)
    if case == "pin":
        pin = "0" * 64
    elif case == "rights":
        marker = root / "MANIFEST.json"
        manifest = json.loads(marker.read_bytes())
        manifest["rights_state"] = "approved"
        marker.write_text(json.dumps(manifest))
        pin = repin(root)
    else:
        pq.write_table(pa.table({"wrong": [1]}), root / query.PRODUCTS["historical"][0])
        pin = repin(root)
    with pytest.raises(
        ValueError, match=r"gold_metadata_contract|canonical_gold_query_payload_invalid"
    ):
        metadata.project_gold_metadata(
            (metadata.GoldInput("canonical_source_separated", root, pin),)
        )


def test_optional_canonical_cli_and_mcp_share_exact_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root, pin = fact_package(tmp_path)
    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    old = legacy_packages(legacy_root, monkeypatch)
    by_profile = {v.profile: v for v in old}
    output = tmp_path / "metadata"
    options = {
        "fiscal_package": str(by_profile["fiscal_analytical"].root),
        "fiscal_manifest_sha256": by_profile["fiscal_analytical"].manifest_sha256,
        "budget_package": str(by_profile["budget_comparison"].root),
        "budget_manifest_sha256": by_profile["budget_comparison"].manifest_sha256,
        "canonical_package": str(root),
        "canonical_manifest_sha256": pin,
        "output_dir": str(output),
    }
    flags = [
        value
        for key, argument in options.items()
        for value in ("--" + key.replace("_", "-"), argument)
    ]
    code = app(
        ["health-appropriations-build-gold-metadata", *flags],
        exit_on_error=False,
        result_action="return_value",
    )
    dry = json.loads(capsys.readouterr().out)
    assert code == 0
    assert dry["packages"] == 3
    assert not output.exists()
    code = app(
        ["health-appropriations-build-gold-metadata", *flags, "--write"],
        exit_on_error=False,
        result_action="return_value",
    )
    actual = json.loads(capsys.readouterr().out)
    assert code == 0
    expected = actual["verification"]
    code = app(
        [
            "health-appropriations-verify-gold-metadata",
            *flags,
            "--manifest-sha256",
            actual["manifest_sha256"],
        ],
        exit_on_error=False,
        result_action="return_value",
    )
    receipt = json.loads(capsys.readouterr().out)
    receipt.pop("command")
    assert code == 0
    assert receipt == expected
    arguments = {**options, "manifest_sha256": actual["manifest_sha256"]}
    server = _ready_server()
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "health_appropriations_verify_gold_metadata",
            "arguments": arguments,
        },
    }
    response = server.handle_request(request)
    assert response is not None
    assert response["result"]["structuredContent"] == expected
    assert response["result"]["isError"] is False
    for field in ("canonical_package", "canonical_manifest_sha256"):
        incomplete = {key: value for key, value in arguments.items() if key != field}
        response = server.handle_request(
            {
                **request,
                "id": 3,
                "params": {**request["params"], "arguments": incomplete},
            }
        )
        assert response is not None
        assert response["error"]["code"] == -32602
    index = flags.index("--canonical-manifest-sha256")
    incomplete_flags = flags[:index] + flags[index + 2 :]
    code = app(
        ["health-appropriations-build-gold-metadata", *incomplete_flags],
        exit_on_error=False,
        result_action="return_value",
    )
    failed = json.loads(capsys.readouterr().out)
    assert code == 2
    assert failed["error"] == "gold_metadata_build_failed"
