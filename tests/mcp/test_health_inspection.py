"""Read-only workbook inspection has explicit previews and redacted failures."""

import hashlib
import json
from pathlib import Path

import pytest
from openpyxl import Workbook

from archive_govt_nz import mcp_health_inspection
from archive_govt_nz import mcp_server as mcp
from archive_govt_nz.cli import health_appropriations_inspect_workbook

NAME = "health_appropriations_inspect_workbook"


def source(tmp_path: Path) -> dict:
    """Create a synthetic workbook; never read a real source in this suite."""
    path = tmp_path / "source.xlsx"
    book = Workbook()
    sheet = book.active
    assert sheet is not None
    sheet.title = "Data"
    sheet.append(["Synthetic", "=1+1"])
    book.save(path)
    book.close()
    return {
        "source": str(path),
        "expected_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def rpc(arguments: object) -> dict:
    """Exercise initialized protocol dispatch, including argument rejection."""
    server = mcp.Server()
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": mcp.PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "fixture", "version": "1"},
            },
        }
    )
    server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
    result = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": NAME, "arguments": arguments},
        }
    )
    assert result is not None
    return result


def test_default_listing_and_cli_parity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Inventory-only MCP and CLI serialize identical receipts without writes."""
    args = source(tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = rpc(args)["result"]
    assert result["isError"] is False
    receipt = result["structuredContent"]
    assert receipt["previews"] == []
    assert receipt["inventory"]["sheets"][0]["title"] == "Data"
    assert (
        health_appropriations_inspect_workbook(
            Path(args["source"]), args["expected_sha256"], rows=0
        )
        == 0
    )
    cli = json.loads(capsys.readouterr().out)
    cli.pop("command")
    assert cli == receipt
    assert json.loads(result["content"][0]["text"]) == receipt
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


def test_explicit_preview_preserves_formula(tmp_path: Path) -> None:
    """Explicit preview exposes literal formula text, not an evaluated value."""
    args = {**source(tmp_path), "rows": 1, "columns": 2, "sheet": "Data"}
    result = mcp.call_tool(NAME, args)
    assert result["value_semantics"] == "decoded_preview_not_canonical_facts"
    assert result["previews"][0]["cells"][1]["decoded_value_json"] == '"=1+1"'


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("rows", True),
        ("rows", -1),
        ("rows", 21),
        ("rows", 1.0),
        ("columns", 0),
        ("columns", 51),
        ("columns", False),
        ("source", ""),
        ("expected_sha256", "private-invalid"),
        ("sheet", ""),
        ("dry_run", False),
        ("source", None),
    ],
)
def test_invalid_inputs_redacted_before_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str, value: object
) -> None:
    """Both direct and protocol paths reject invalid caller arguments."""
    args = {**source(tmp_path), key: value}

    def forbidden(*_args: object, **_kwargs: object) -> dict:
        pytest.fail("invalid arguments reached the inspector")

    monkeypatch.setattr(mcp_health_inspection, "inspect_workbook", forbidden)
    result = rpc(args)
    assert result["error"]["code"] == -32602
    assert result["error"]["message"] == "Invalid workbook inspection arguments"
    with pytest.raises(ValueError, match=r"^invalid_workbook_inspection_arguments$"):
        mcp.call_tool(NAME, args)


@pytest.mark.parametrize("key", ["source", "expected_sha256"])
def test_required_identity(tmp_path: Path, key: str) -> None:
    """Neither source location nor fixity can be inferred by the tool."""
    args = source(tmp_path)
    del args[key]
    assert rpc(args)["error"]["code"] == -32602


@pytest.mark.parametrize("fault", ["digest", "missing", "corrupt", "sheet"])
def test_read_failures_are_redacted_and_do_not_write(
    tmp_path: Path, fault: str
) -> None:
    """Source failures expose only redacted classes and retain existing bytes."""
    args = source(tmp_path)
    if fault == "digest":
        args["expected_sha256"] = "0" * 64
    elif fault == "missing":
        args["source"] = str(tmp_path / "private-missing.xlsx")
    elif fault == "corrupt":
        Path(args["source"]).write_bytes(b"private-corrupt")
        args["expected_sha256"] = hashlib.sha256(b"private-corrupt").hexdigest()
    else:
        args["sheet"] = "private-unknown-sheet"
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = rpc(args)["result"]
    assert result["isError"] is True
    assert "private" not in json.dumps(result)
    assert str(tmp_path) not in json.dumps(result)
    assert result["content"][0]["text"].startswith("workbook_inspection_failed:")
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


def test_registration_reuses_canonical_output_schema() -> None:
    """The installed runtime mirror matches the canonical inspector schema."""
    definition = next(t for t in mcp.list_tools() if t["name"] == NAME)
    canonical = json.loads(
        Path("schemas/health-workbook-inspection-v1.schema.json").read_bytes()
    )
    assert definition["outputSchema"] == canonical
    assert definition["inputSchema"]["properties"]["rows"]["default"] == 0
    assert definition["annotations"]["readOnlyHint"] is True
    assert definition["annotations"]["destructiveHint"] is False
    assert definition["annotations"]["openWorldHint"] is False


def test_exact_preview_bounds(tmp_path: Path) -> None:
    """Maximum accepted limits still delegate to bounded source inspection."""
    args = {**source(tmp_path), "rows": 20, "columns": 50}
    result = mcp.call_tool(NAME, args)
    assert len(result["previews"][0]["cells"]) == 2
    assert result["previews"][0]["row_truncated"] is False
