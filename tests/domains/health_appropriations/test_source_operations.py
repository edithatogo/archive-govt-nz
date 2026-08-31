"""Source operations expose metadata, not rows, secrets or publication approval."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import textwrap
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator, ValidationError
from tests.domains.health_appropriations.test_cpi import HEADER, META
from tests.domains.health_appropriations.test_pharmac import (
    fixture_source as pharmac_fixture,
)
from tests.domains.health_appropriations.test_qes import fixture as qes_fixture

from archive_govt_nz import cli, mcp_server
from archive_govt_nz.cli import app, health_appropriations_extract_source
from archive_govt_nz.domains.health_appropriations import (
    moh_indicators,
    pharmac,
    source_operations,
)
from archive_govt_nz.mcp_server import Server, call_tool, list_tools


@pytest.fixture(
    params=[
        "cpiq-se9a/v1",
        "moh-hair2024-fig27/v1",
        "moh-hair2024-fig28/v1",
        "qes-june2026-table8/v1",
        "pharmac-cpb-20260807/v1",
    ]
)
def request_source(
    tmp_path: Path, request: pytest.FixtureRequest
) -> source_operations.SourceRequest:
    profile = request.param
    source = tmp_path / "source"
    if profile == "cpiq-se9a/v1":
        source.write_bytes(
            (
                HEADER + "CPIQ.SE9A,1914.06,1.25" + META + "CPIQ.SE9A,1914.09,NA" + META
            ).encode()
        )
        vintage = "2026-Q2"
    elif profile.startswith("moh"):
        headers = moh_indicators.PROFILES[
            "fig27/v1" if "fig27" in profile else "fig28/v1"
        ]

        content = io.StringIO(newline="")
        writer = csv.writer(content)
        writer.writerow(headers)
        writer.writerows(
            (year, "1.25", "2.5") for year in sorted(moh_indicators.PERIODS)
        )
        source.write_bytes(content.getvalue().encode())
        vintage = "MoH-HAIR-2024"
    elif profile == "pharmac-cpb-20260807/v1":
        source, _ = pharmac_fixture(tmp_path)
        vintage = "Pharmac-CPB-2026-08-07"
    else:
        qes_fixture(source)
        vintage = "QES-2026-Q2"
    return source_operations.SourceRequest(
        source,
        tmp_path / "output",
        profile,
        hashlib.sha256(source.read_bytes()).hexdigest(),
        vintage,
        "https://example.invalid/source",
        "2026-08-31T00:00:00Z",
    )


def test_preflight_and_explicit_local_write(
    request_source: source_operations.SourceRequest,
) -> None:
    before = request_source.source.read_bytes()
    result = source_operations.operate_source(request_source)
    assert result["status"] == "preflight_passed"
    assert result["profile"] == request_source.profile
    assert "source_locator" not in result
    assert "source_vintage" not in result
    assert not request_source.output_dir.exists()
    written = source_operations.operate_source(request_source, dry_run=False)
    assert written["status"] == "written_local"
    assert written["rights_state"] == "not_evaluated"
    assert written["publication_state"] == "local_validation_only"
    assert len(written["output_sha256"]) == 3
    assert request_source.source.read_bytes() == before


def test_pharmac_dispatch_preserves_source_specific_package(tmp_path: Path) -> None:
    source, pin = pharmac_fixture(tmp_path)
    before = source.read_bytes()
    context = {
        "expected_sha256": pin,
        "source_vintage": "Pharmac-CPB-2026-08-07",
        "source_locator": "https://example.invalid/source",
        "observed_at": "2026-08-31T00:00:00Z",
    }
    direct = tmp_path / "direct"
    raw = pharmac.normalize_pharmac_budget(source, direct, **context, dry_run=False)
    destination = tmp_path / "dispatch"
    request = source_operations.SourceRequest(
        source, destination, "pharmac-cpb-20260807/v1", **context
    )
    result = source_operations.operate_source(request, dry_run=False)
    assert result["status"] == "written_local"
    assert result["counts"] == raw["counts"]
    assert {p.name: p.read_bytes() for p in destination.iterdir()} == {
        p.name: p.read_bytes() for p in direct.iterdir()
    }
    assert source.read_bytes() == before


@pytest.mark.parametrize("flag", [None, 0, 1, "", "false", [], {}])
def test_non_boolean_flags_fail_closed(
    request_source: source_operations.SourceRequest, flag: object
) -> None:
    result = source_operations.operate_source(
        request_source, dry_run=cast("bool", flag)
    )
    assert result["status"] == "failed"
    assert not request_source.output_dir.exists()


@pytest.mark.parametrize(
    "locator",
    [
        "https://example.invalid/x?secret=private",
        "https://" + ":".join(("user", "private")) + "@example.invalid/x",  # noqa: FLY002 - synthetic rejected userinfo, not literal credentials
        "https://example.invalid/x#private",
    ],
)
def test_sensitive_locator_redacted(
    request_source: source_operations.SourceRequest, locator: str
) -> None:
    result = source_operations.operate_source(
        replace(request_source, source_locator=locator), dry_run=False
    )
    assert result["status"] == "failed"
    assert "private" not in json.dumps(result)
    assert not request_source.output_dir.exists()


def test_cli_mcp_preflight_parity(
    request_source: source_operations.SourceRequest, capsys: pytest.CaptureFixture[str]
) -> None:
    arguments = {
        key: getattr(request_source, key) for key in request_source.__dataclass_fields__
    }
    assert health_appropriations_extract_source(**arguments) == 0
    cli = json.loads(capsys.readouterr().out)
    assert cli.pop("command") == "health-appropriations-extract-source"
    args = {key: str(value) for key, value in arguments.items()}
    assert call_tool("health_appropriations_preflight_source", args) == cli
    tool = next(
        tool
        for tool in list_tools()
        if tool["name"] == "health_appropriations_preflight_source"
    )
    assert tool["annotations"]["readOnlyHint"] is True
    assert "dry_run" not in tool["inputSchema"]["properties"]
    assert not request_source.output_dir.exists()


@pytest.mark.parametrize("malformed", [False, True])
def test_mcp_sensitive_failures_are_redacted(
    request_source: source_operations.SourceRequest, *, malformed: bool
) -> None:
    args = {
        key: str(getattr(request_source, key))
        for key in request_source.__dataclass_fields__
    }
    args["source_locator"] = (
        "https://example.invalid/private-secret?signature=private-secret"
    )
    if malformed:
        args["source_locator"] += "x" * 3000
    server = Server()
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        }
    )
    server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
    result = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "health_appropriations_preflight_source",
                "arguments": args,
            },
        }
    )
    assert "private-secret" not in json.dumps(result)
    assert not request_source.output_dir.exists()


def test_false_mcp_write_flag_rejected(
    request_source: source_operations.SourceRequest,
) -> None:
    args: dict[str, Any] = {
        key: str(getattr(request_source, key))
        for key in request_source.__dataclass_fields__
    }
    args["dry_run"] = False
    result = source_operations.preflight_source(args)
    assert result["status"] == "failed"
    assert not request_source.output_dir.exists()


def test_failed_adapter_result_is_not_success(
    request_source: source_operations.SourceRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    counts = dict.fromkeys(source_operations.PROFILES[request_source.profile][1], 0)
    monkeypatch.setattr(
        source_operations,
        "_invoke",
        lambda *_args, **_kwargs: {"status": "failed", "counts": counts},
    )
    assert source_operations.operate_source(request_source)["status"] == "failed"
    assert not request_source.output_dir.exists()


@pytest.mark.parametrize(
    "case",
    [
        "profile",
        "digest",
        "timestamp",
        "vintage",
        "locator",
        "missing",
        "source-link",
        "output-link",
        "existing",
    ],
)
def test_invalid_request_creates_no_state(
    request_source: source_operations.SourceRequest, case: str
) -> None:
    changed = request_source
    if case in ("profile", "vintage", "locator"):
        name = case if case == "profile" else "source_" + case
        changed = replace(
            changed, **{name: "private-value" if case != "vintage" else " "}
        )
    elif case == "digest":
        changed = replace(changed, expected_sha256="0" * 64)
    elif case == "timestamp":
        changed = replace(changed, observed_at="2026-08-31T00:00:00")
    elif case == "missing":
        changed = replace(changed, source=changed.source.parent / "missing")
    elif case == "source-link":
        link = changed.source.parent / "source-link"
        link.symlink_to(changed.source)
        changed = replace(changed, source=link)
    elif case == "output-link":
        changed.output_dir.symlink_to(
            changed.source.parent / "absent", target_is_directory=True
        )
    else:
        changed.output_dir.mkdir()
    before = {
        p: p.read_bytes()
        for p in changed.source.parent.rglob("*")
        if p.is_file() and not p.is_symlink()
    }
    result = source_operations.operate_source(changed, dry_run=False)
    assert result["status"] == "failed"
    assert "private-value" not in json.dumps(result)
    assert before == {
        p: p.read_bytes()
        for p in changed.source.parent.rglob("*")
        if p.is_file() and not p.is_symlink()
    }


@pytest.mark.parametrize("interrupt", [False, True])
def test_parser_failure_and_interrupt(
    request_source: source_operations.SourceRequest,
    monkeypatch: pytest.MonkeyPatch,
    *,
    interrupt: bool,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        message = "private parser token"
        if interrupt:
            raise KeyboardInterrupt(message)
        raise RuntimeError(message)

    monkeypatch.setattr(source_operations, "_invoke", fail)
    if interrupt:
        with pytest.raises(KeyboardInterrupt):
            source_operations.operate_source(request_source)
    else:
        result = source_operations.operate_source(request_source)
        assert result["status"] == "failed"
        assert "private" not in json.dumps(result)
    assert not request_source.output_dir.exists()


@pytest.mark.parametrize("write", [False, True])
def test_cli_arguments(
    request_source: source_operations.SourceRequest,
    capsys: pytest.CaptureFixture[str],
    *,
    write: bool,
) -> None:
    args = ["health-appropriations-extract-source"]
    for key in request_source.__dataclass_fields__:
        args.extend(["--" + key.replace("_", "-"), str(getattr(request_source, key))])
    if write:
        args.append("--no-dry-run")
    with pytest.raises(SystemExit) as exc:
        app(args, exit_on_error=False)
    assert exc.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == (
        "written_local" if write else "preflight_passed"
    )
    assert request_source.output_dir.exists() is write


@pytest.mark.parametrize("bad", [{}, {"secret": 1}, {"input": True}])
def test_malformed_backend_receipt_redacted(
    request_source: source_operations.SourceRequest,
    monkeypatch: pytest.MonkeyPatch,
    bad: dict[str, Any],
) -> None:
    monkeypatch.setattr(
        source_operations,
        "_invoke",
        lambda *_a, **_k: {
            "status": "passed",
            "counts": bad,
            "output_sha256": {"private": "secret"},
        },
    )
    result = source_operations.operate_source(request_source, dry_run=False)
    assert result["status"] == "failed"
    assert "secret" not in json.dumps(result)


def test_partial_failure_is_preserved(
    request_source: source_operations.SourceRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        request_source.output_dir.mkdir()
        (request_source.output_dir / "partial").write_bytes(b"partial evidence")
        message = "private diagnostic"
        raise OSError(message)

    monkeypatch.setattr(source_operations, "_invoke", fail)
    result = source_operations.operate_source(request_source, dry_run=False)
    assert result["status"] == "failed"
    assert (request_source.output_dir / "partial").read_bytes() == b"partial evidence"
    assert not (request_source.output_dir / "MANIFEST.json").exists()


@given(
    st.sampled_from(tuple(source_operations.PROFILES)),
    st.integers(min_value=0, max_value=10**9),
)
def test_receipt_schema_count_property(profile: str, count: int) -> None:
    contract = source_operations.PROFILES[profile]
    receipt = {
        "schema_version": "archive-govt-nz.health-source-operation/v1",
        "verification_scope": "adapter_execution_only",
        "rights_state": "not_evaluated",
        "publication_state": "local_validation_only",
        "status": "preflight_passed",
        "profile": profile,
        "source_object_sha256": "a" * 64,
        "transformation_id": contract[0],
        "counts": dict.fromkeys(contract[1], count),
    }
    validator = Draft202012Validator(source_operations.SOURCE_OPERATION_SCHEMA)
    validator.validate(receipt)
    receipt["rights_state"] = "cleared"
    with pytest.raises(ValidationError):
        validator.validate(receipt)


def test_committed_receipt_schema() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "schemas/health-source-operation-v1.schema.json"
    )
    assert json.loads(path.read_text()) == source_operations.SOURCE_OPERATION_SCHEMA


@pytest.mark.parametrize(
    "field", ["source", "output_dir", "source_vintage", "source_locator", "observed_at"]
)
def test_input_schema_exact_length_boundary(field: str) -> None:
    args = {
        "source": "source",
        "output_dir": "output",
        "profile": "cpiq-se9a/v1",
        "expected_sha256": "a" * 64,
        "source_vintage": "vintage",
        "source_locator": "https://example.invalid/x",
        "observed_at": "2026-08-31T00:00:00Z",
    }
    validator = Draft202012Validator(source_operations.SOURCE_PREFLIGHT_INPUT_SCHEMA)
    args[field] = "x" * 2048
    validator.validate(args)
    args[field] += "x"
    with pytest.raises(ValidationError):
        validator.validate(args)


def _seeded_function(
    function: Callable[..., Any], namespace: dict[str, Any], before: str, after: str
) -> Callable[..., Any]:
    """Compile only trusted local function text, without decorators or IO."""
    source = textwrap.dedent(inspect.getsource(function))
    assert source.count(before) == 1
    tree = ast.parse(source.replace(before, after))
    node = tree.body[0]
    assert isinstance(node, ast.FunctionDef)
    node.decorator_list = []
    exec(compile(tree, "<trusted-wiring-counterexample>", "exec"), namespace)  # noqa: S102
    return namespace[function.__name__]


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("dry_run: bool = True", "dry_run: bool = False"),
        ("dry_run=dry_run", "dry_run=True"),
        ('return 2 if result["status"] == "failed" else 0', "return 0"),
    ],
)
def test_cli_seeded_wiring_counterexamples(before: str, after: str) -> None:
    def oracle(function: Callable[..., Any]) -> None:
        arguments = {
            "source": Path("source"),
            "output_dir": Path("output"),
            "profile": "cpiq-se9a/v1",
            "expected_sha256": "a" * 64,
            "source_vintage": "vintage",
            "source_locator": "https://example.invalid/x",
            "observed_at": "2026-08-31T00:00:00Z",
        }
        assert function(**arguments) == 2
        assert seen[-1] is True
        assert function(**arguments, dry_run=False) == 2
        assert seen[-1] is False

    seen: list[bool] = []

    def invoke(_request: object, *, dry_run: bool) -> dict[str, str]:
        seen.append(dry_run)
        return {"status": "failed"}

    namespace = {
        **vars(cli),
        "operate_source": invoke,
        "_emit_json": lambda _result: None,
    }
    baseline = _seeded_function(
        health_appropriations_extract_source, namespace.copy(), before, before
    )
    oracle(baseline)
    mutant = _seeded_function(
        health_appropriations_extract_source, namespace.copy(), before, after
    )
    with pytest.raises(AssertionError):
        oracle(mutant)


def test_mcp_seeded_redaction_counterexample() -> None:
    args = {
        "source": "source",
        "output_dir": "output",
        "profile": "cpiq-se9a/v1",
        "expected_sha256": "a" * 64,
        "source_vintage": "vintage",
        "source_locator": "https://example.invalid/private-secret" + "x" * 3000,
        "observed_at": "2026-08-31T00:00:00Z",
    }
    params = {"name": "health_appropriations_preflight_source", "arguments": args}

    def oracle(function: Callable[..., Any]) -> None:
        assert "private-secret" not in json.dumps(function(Server(), 1, params))

    before = '"Invalid source operation arguments"'
    baseline = _seeded_function(
        Server._call_tool,  # noqa: SLF001 - exact protocol boundary
        vars(mcp_server).copy(),
        before,
        before,
    )
    oracle(baseline)
    mutant = _seeded_function(
        Server._call_tool,  # noqa: SLF001 - exact protocol boundary
        vars(mcp_server).copy(),
        before,
        "errors[0].message",
    )
    with pytest.raises(AssertionError):
        oracle(mutant)
