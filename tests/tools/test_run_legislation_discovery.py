"""Verify discovery authenticates without leaking its credential into receipts."""

import json
from pathlib import Path

import httpx
import pytest

from tools import run_legislation_discovery as runner


def test_authenticated_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the real request builder and ensure the secret stays in a header."""
    credential = "synthetic-discovery-key"
    monkeypatch.setenv("LEGISLATION_API_KEY", credential)
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Api-Key"] == credential
        assert credential not in str(request.url)
        requests.append(request)
        return httpx.Response(200, json={"results": []})

    client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(runner.httpx, "Client", lambda **_kwargs: client)
    output = tmp_path / "candidates.json"
    runner.run(Path("config/legislation/discovery-scope-v1.json"), output)
    assert requests
    assert json.loads(output.read_text())["candidate_count"] == 0
    assert credential not in output.read_text()


def test_missing_key_stops_before_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing configuration has a useful error and makes no unauthenticated call."""
    monkeypatch.delenv("LEGISLATION_API_KEY", raising=False)
    with pytest.raises(ValueError, match="LEGISLATION_API_KEY is required"):
        runner.run(
            Path("config/legislation/discovery-scope-v1.json"), tmp_path / "unused.json"
        )
    assert not (tmp_path / "unused.json").exists()
