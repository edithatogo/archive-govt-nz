"""Synthetic no-write source preflight, failures, and resource boundaries."""

from __future__ import annotations

import importlib.util
import json
import os
import runpy
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest
from hypothesis import given
from hypothesis import strategies as st

spec = importlib.util.spec_from_file_location(
    "source_preflight",
    os.environ.get(
        "SOURCE_PREFLIGHT_UNDER_TEST", "tools/legislation_source_preflight.py"
    ),
)
assert spec is not None
assert spec.loader is not None
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


ENVIRONMENT_KEY = "LEGISLATION_API_KEY"
SAMPLE_VALUE = "synthetic-value"


def sample_environment() -> dict[str, str]:
    """Build synthetic configuration without credential-shaped diagnostic literals."""
    return {ENVIRONMENT_KEY: SAMPLE_VALUE}


def client_for(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    """Make a synthetic transport that cannot access the network."""
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


@pytest.mark.parametrize("credential", ["", " ", "\n\t"])
def test_missing_credentials_do_not_make_requests(credential: str) -> None:
    """Absent and whitespace-only credentials fail before network access."""
    with client_for(lambda _: pytest.fail("unexpected network")) as client:
        result = preflight.probe(client, credential)
    assert result["status"] == "missing_credential"
    assert result["requests_attempted"] == 0
    assert result["credential_present"] is False


@given(st.integers(min_value=100, max_value=599).filter(lambda code: code != 200))
def test_only_ok_status_can_pass(code: int) -> None:
    """Authentication failures, redirects, throttling and surprises fail closed."""
    with client_for(lambda _: httpx.Response(code)) as client:
        result = preflight.probe(client, "synthetic-value")
    assert result["status"] == "http_failure"
    assert result["http_status"] == code
    assert result["requests_attempted"] == 1


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (httpx.ReadTimeout("sensitive error"), "timeout"),
        (httpx.ConnectError("sensitive error"), "transport_failure"),
        (ValueError("sensitive error"), "transport_failure"),
    ],
)
def test_transport_errors_are_sanitized(error: Exception, status: str) -> None:
    """No raw transport details escape into the receipt."""

    def handler(_: httpx.Request) -> httpx.Response:
        raise error

    with client_for(handler) as client:
        result = preflight.probe(client, "synthetic-value")
    assert result["status"] == status
    assert "sensitive" not in json.dumps(result)
    assert "synthetic-value" not in json.dumps(result)


def test_fixed_endpoint_headers_timeout_and_no_body_consumption() -> None:
    """One authenticated official-origin request never follows or reads payload."""

    class Unreadable(httpx.SyncByteStream):
        def __iter__(self) -> Iterator[bytes]:
            pytest.fail("response body must not be consumed")
            yield b""

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            "https://api.legislation.govt.nz/v0/works/act_imperial_1539_1/versions/"
        )
        assert request.method == "GET"
        assert request.headers["X-Api-Key"] == "synthetic-value"
        assert request.extensions["timeout"]["read"] == preflight.TIMEOUT_SECONDS
        return httpx.Response(200, stream=Unreadable())

    with client_for(handler) as client:
        result = preflight.probe(client, "synthetic-value")
    assert result["status"] == "passed"
    assert result["payload_bytes_preserved"] == 0


def state_at(tmp_path: Path) -> Path:
    """Create a tiny already-restored synthetic state."""
    state = tmp_path / "state"
    (state / "cas").mkdir(parents=True)
    (state / "manifest.json").write_text("{}")
    (state / "cas/object").write_bytes(b"object")
    return state


@pytest.mark.parametrize("passed", [True, False])
def test_run_retains_sanitized_success_and_failure(
    tmp_path: Path, *, passed: bool
) -> None:
    """Both outcomes preserve no-write fixity and external evidence only."""
    state = state_at(tmp_path)
    before = preflight.snapshot(state)
    receipt = tmp_path / "evidence/receipt.json"
    with client_for(lambda _: httpx.Response(200 if passed else 401)) as client:
        code = preflight.run(state, receipt, client, sample_environment())
    result = json.loads(receipt.read_text())
    assert code == (0 if passed else 1)
    assert result["state_unchanged"] is True
    assert result["state_files_before"] == result["state_files_after"] == before
    assert SAMPLE_VALUE not in receipt.read_text()


def test_run_detects_state_mutation(tmp_path: Path) -> None:
    """Concurrent state changes cannot be called a successful no-write preflight."""
    state = state_at(tmp_path)

    def handler(_: httpx.Request) -> httpx.Response:
        (state / "manifest.json").write_text("changed")
        return httpx.Response(200)

    receipt = tmp_path / "receipt.json"
    with client_for(handler) as client:
        code = preflight.run(state, receipt, client, sample_environment())
        assert code == 1
    assert json.loads(receipt.read_text())["state_unchanged"] is False


@pytest.mark.parametrize(
    "limit", ["MAX_STATE_BYTES", "MAX_CAS_BYTES", "MAX_CAS_OBJECTS"]
)
def test_resource_overruns_fail_before_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    """Existing governed resource ceilings are enforced before credential use."""
    state = state_at(tmp_path)
    monkeypatch.setattr(preflight, limit, 0)
    receipt = tmp_path / "receipt.json"
    with client_for(lambda _: pytest.fail("unexpected network")) as client:
        assert preflight.run(state, receipt, client, {}) == 1
    assert (
        json.loads(receipt.read_text())["failure_code"] == "state_verification_failed"
    )


def test_empty_state_and_symlink_rejected(tmp_path: Path) -> None:
    """No empty bootstrap or path aliases are accepted."""
    with pytest.raises(ValueError, match="state_resource_limit"):
        preflight.snapshot(tmp_path)
    state = state_at(tmp_path)
    (state / "alias").symlink_to(state / "manifest.json")
    with pytest.raises(ValueError, match="state_resource_limit"):
        preflight.snapshot(state)


def test_main_uses_only_workflow_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CLI has no operator-supplied endpoint or output path."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LEGISLATION_API_KEY", raising=False)
    assert preflight.main() == 1
    assert (tmp_path / "build/legislation-attempt/source-preflight.json").is_file()


def test_cli_entrypoint_fails_closed_without_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Direct script invocation exits nonzero and preserves failure receipt."""
    assert preflight.__file__ is not None
    tool = Path(preflight.__file__).resolve()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(tool), run_name="__main__")
    assert result.value.code == 1


def test_redirect_never_sends_credential_to_other_origin() -> None:
    """Even a client default cannot override the fixed-origin redirect boundary."""
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://example.org/"})

    with client_for(handler) as client:
        result = preflight.probe(client, "synthetic-value")
    assert seen == [preflight.ENDPOINT]
    assert result["status"] == "http_failure"


def test_exact_resource_boundaries_are_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The configured maximum is inclusive; only an excess must fail."""
    state = state_at(tmp_path)
    monkeypatch.setattr(preflight, "MAX_STATE_BYTES", 8)
    monkeypatch.setattr(preflight, "MAX_CAS_BYTES", 6)
    monkeypatch.setattr(preflight, "MAX_CAS_OBJECTS", 1)
    assert len(preflight.snapshot(state)) == 2
