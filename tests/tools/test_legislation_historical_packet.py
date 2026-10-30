"""Historical publication is hash-bound, additive, anonymous-verified and one-send."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import io
import json
import logging
import sys
import zipfile

import httpx
import pytest

from archive_govt_nz.domains.legislation.corpus import WorkTarget
from tools import legislation_historical_packet as packet


@pytest.fixture
def publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Any]:
    """Bind the real publisher to a fictional exact-target Hub service."""
    directory = tmp_path / "capture"
    directory.mkdir()
    files = {
        "canonical-state.zip": b"canonical-fixture",
        "metadata.json": b"{}",
        "inventory.json": b"[]",
        "source-pages.json": b"[]",
    }
    for name, data in files.items():
        (directory / name).write_bytes(data)
    monkeypatch.setenv("HF_TOKEN", "synthetic-fixture-token")
    monkeypatch.setattr(
        packet,
        "validate_package",
        lambda _d, _s: (
            files["canonical-state.zip"],
            {"capture_run": 17, "records_before": 1, "records_after": 2},
        ),
    )

    class Hub:
        """Permit only an exact authorized public dataset and guarded addition."""

        def __init__(self) -> None:
            self.private: bool | None = False
            self.gated: bool | None = False
            self.existing = False
            self.corrupt = False
            self.fail = False
            self.calls = 0
            self.permissions = 0

        def dataset_info(self, repo: str, *, expand: list[str]) -> SimpleNamespace:
            assert repo == packet.REPOSITORY
            assert expand == ["sha", "private", "gated"]
            return SimpleNamespace(sha="a" * 40, private=self.private, gated=self.gated)

        def auth_check(self, repo: str, *, repo_type: str, write: bool) -> None:
            assert repo == packet.REPOSITORY
            assert repo_type == "dataset"
            assert write is True
            self.permissions += 1

        def get_paths_info(
            self, repo: str, *, paths: list[str], repo_type: str, revision: str
        ) -> list[str]:
            assert repo == packet.REPOSITORY
            assert revision == "a" * 40
            assert repo_type == "dataset"
            return paths if self.existing else []

        def create_commit(
            self,
            *,
            repo_id: str,
            repo_type: str,
            parent_commit: str,
            commit_message: str,
            operations: list[Any],
        ) -> SimpleNamespace:
            self.calls += 1
            assert repo_id == packet.REPOSITORY
            assert repo_type == "dataset"
            assert commit_message
            assert parent_commit == "a" * 40
            assert len(operations) == 4
            assert all(
                op.path_in_repo.startswith("durable-state/v1/historical-17/")
                for op in operations
            )
            if self.fail:
                message = "fixture unknown upload outcome"
                raise OSError(message)
            return SimpleNamespace(oid="b" * 40)

    hub = Hub()
    monkeypatch.setattr(packet, "HfApi", lambda **_kw: hub)

    def download(repo: str, filename: str, **kwargs: object) -> str:
        assert repo == packet.REPOSITORY
        assert kwargs["repo_type"] == "dataset"
        assert kwargs["local_dir"] == tmp_path / "publication" / "readback"
        assert kwargs["token"] is False
        assert kwargs["revision"] == ("a" * 40 if hub.existing else "b" * 40)
        target = tmp_path / ("remote-" + filename.rsplit("/", maxsplit=1)[-1])
        target.write_bytes(
            b"corrupt" if hub.corrupt else files[filename.rsplit("/", maxsplit=1)[-1]]
        )
        return str(target)

    monkeypatch.setattr(packet, "hf_hub_download", download)
    return directory, tmp_path / "publication", hub


def test_guarded_publication_verifies_every_file(
    publication: tuple[Path, Path, Any],
) -> None:
    """One commit follows explicit write qualification; every uploaded file is read."""
    directory, output, hub = publication
    result = packet.publish(directory, "d" * 64, output)
    assert result["status"] == "published_verified"
    assert len(result["verified_files"]) == 4
    assert hub.calls == 1
    assert hub.permissions == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [("private", True), ("private", None), ("gated", True), ("gated", None)],
)
def test_private_gated_or_unknown_target_never_writes(
    publication: tuple[Path, Path, Any], field: str, *, value: bool | None
) -> None:
    """An authenticated account does not substitute for verified destination access."""
    directory, output, hub = publication
    setattr(hub, field, value)
    with pytest.raises(ValueError, match="ungated public"):
        packet.publish(directory, "d" * 64, output)
    assert hub.calls == 0


def test_existing_exact_package_is_adopted_without_another_commit(
    publication: tuple[Path, Path, Any],
) -> None:
    """Unknown outcomes are resolved by readback rather than replaying mutations."""
    directory, output, hub = publication
    hub.existing = True
    result = packet.publish(directory, "d" * 64, output)
    assert result["mutation_attempts"] == 0
    assert hub.calls == 0


def test_failed_remote_integrity_cannot_report_success(
    publication: tuple[Path, Path, Any],
) -> None:
    """Retain the journal and first failure; no verified receipt or second write."""
    directory, output, hub = publication
    hub.corrupt = True
    with pytest.raises(ValueError, match="remote readback"):
        packet.publish(directory, "d" * 64, output)
    assert hub.calls == 1
    assert not (output / "receipt.json").exists()
    assert (output / "journal.json").exists()


def test_unknown_upload_outcome_is_not_retried(
    publication: tuple[Path, Path, Any],
) -> None:
    """A failed write is not a safe assertion that nothing was uploaded."""
    directory, output, hub = publication
    hub.fail = True
    with pytest.raises(OSError, match="unknown upload"):
        packet.publish(directory, "d" * 64, output)
    assert hub.calls == 1
    assert not (output / "receipt.json").exists()


def test_digest_mismatch_stops_before_native_access(tmp_path: Path) -> None:
    """An operator's exact package binding cannot be substituted."""
    (tmp_path / "canonical-state.zip").write_bytes(b"fixture")
    (tmp_path / "metadata.json").write_text('{"package_sha256":"wrong"}')
    with pytest.raises(ValueError, match="approval/digest"):
        packet.validate_package(tmp_path, "e" * 64)


def test_api_catalogue_path_and_response_are_qualified() -> None:
    """Use the selected header credential only on the official JSON endpoint."""
    calls = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.headers["X-Api-Key"] == "synthetic-key"
        assert "synthetic-key" not in str(request.url)
        return httpx.Response(
            200, json={"results": [], "page": 1, "per_page": 100, "total": 0}
        )

    client = httpx.Client(transport=httpx.MockTransport(respond))
    api = packet.NZLegislationApiClient(
        client=client, api_key="synthetic-key", min_interval_seconds=0
    )
    assert api.get_catalogue_page("works/", {"page": 1})["total"] == 0
    with pytest.raises(ValueError, match="unsupported"):
        api.get_catalogue_page("https://outside.invalid/", {})
    assert len(calls) == 1


@pytest.mark.anyio
@pytest.mark.parametrize("limited", [False, True])
async def test_original_stream_has_hard_budget_and_no_key_transfer(
    monkeypatch: pytest.MonkeyPatch, *, limited: bool
) -> None:
    """A source body cannot exceed its cap or receive the API credential."""
    body = b"%PDF-1.7 fixture"
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert "X-Api-Key" not in request.headers
        return httpx.Response(
            200, content=body, headers={"content-type": "application/pdf"}
        )

    original = httpx.AsyncClient
    monkeypatch.setattr(
        packet.httpx,
        "AsyncClient",
        lambda **_kw: original(transport=httpx.MockTransport(respond)),
    )
    monkeypatch.setattr(packet, "MAX_FILE", 4 if limited else 100)
    client = packet.PacketClient()
    client.min_interval_seconds = 0
    client.api_key = "synthetic-key"
    if limited:
        with pytest.raises(ValueError, match="byte budget"):
            await client.get_document_raw_async(
                "https://www.legislation.govt.nz/act/public/1841/1/en/1841-01-01.pdf"
            )
    else:
        status, content, headers = await client.get_document_raw_async(
            "https://www.legislation.govt.nz/act/public/1841/1/en/1841-01-01.pdf"
        )
        assert status == 200
        assert content == body
        assert headers["content-type"] == "application/pdf"
    assert len(requests) == 1


def test_sealed_package_binding_and_lineage_are_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A matching outer hash cannot hide a changed scope inventory or seal."""
    raw = b"fixture-zip"
    inventory = b"{}"
    pages = b"[]"
    roots = {"manifest_sha256": "d" * 64}
    context = {"run_id": 17, "software_commit": "a" * 40}
    lineage = packet.encoded({"context": context})
    seal = {
        "status": "complete",
        "roots": roots,
        "parent_lineage_sha256": packet.digest(lineage),
        "context": context,
    }
    files = {packet.parent.LINEAGE: lineage, packet.parent.SEAL: packet.encoded(seal)}
    metadata = {
        "package_sha256": packet.digest(raw),
        "repository": packet.REPOSITORY,
        "authority": {"id": packet.AUTHORITY},
        "inventory_sha256": packet.digest(inventory),
        "source_pages_sha256": packet.digest(pages),
        "roots": roots,
        "capture_run": 17,
        "software_commit": "a" * 40,
    }
    for name, content in [
        ("canonical-state.zip", raw),
        ("inventory.json", inventory),
        ("source-pages.json", pages),
        ("metadata.json", packet.encoded(metadata)),
    ]:
        (tmp_path / name).write_bytes(content)
    monkeypatch.setattr(packet.parent, "unpack", lambda _raw: files)
    monkeypatch.setattr(packet.parent, "state_roots", lambda _files: roots)
    monkeypatch.setattr(packet.parent, "schema", lambda *_args: None)
    monkeypatch.setattr(packet.parent, "check_lineage", lambda *_args: None)
    data, actual = packet.validate_package(tmp_path, packet.digest(raw))
    assert data == raw
    assert actual == metadata
    bad = {**seal, "parent_lineage_sha256": "b" * 64}
    files[packet.parent.SEAL] = packet.encoded(bad)
    with pytest.raises(ValueError, match="lineage provenance"):
        packet.validate_package(tmp_path, packet.digest(raw))
    files[packet.parent.SEAL] = packet.encoded(seal)
    (tmp_path / "inventory.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="inventory digest"):
        packet.validate_package(tmp_path, packet.digest(raw))


def test_capture_orchestration_keeps_parent_and_binds_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The service output must retain every original record before it can seal."""
    before = {
        "records": [{"manifestation_id": "original", "raw_sha256": "a" * 64}],
        "discovered_work_ids": ["original-work"],
    }
    after = {
        "records": before["records"] + [{"manifestation_id": "addition"}],
        "discovered_work_ids": ["original-work", "new-work"],
    }
    roots = {"manifest_sha256": "d" * 64}

    class Service:
        """Reuse the canonical service boundary with deterministic fictional output."""

        def __init__(self, *_args: object, **_kwargs: object) -> None:
            """Accept the real isolated store and API configuration."""

        def load_manifest(self, _path: Path) -> dict[str, Any]:
            return before

        async def sync_works(self, **kwargs: object) -> SimpleNamespace:
            assert kwargs["force_resync"] is True
            assert kwargs["fail_fast"] is True
            return SimpleNamespace(
                status="success",
                manifest=after,
                accounting=SimpleNamespace(
                    failed=0, partial=0, to_receipt=lambda: {"fixture": True}
                ),
            )

    monkeypatch.setenv("GITHUB_RUN_ID", "17")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_WORKFLOW", "Fixture capture")
    monkeypatch.setattr(packet, "LegislationArchiveService", Service)
    monkeypatch.setattr(
        packet,
        "missing_targets",
        lambda *_args: (
            [
                WorkTarget(
                    "new-work",
                    "Fixture",
                    "https://www.legislation.govt.nz/act/public/1841/1/en/1841-01-01.xml",
                )
            ],
            {"selected": []},
        ),
    )
    monkeypatch.setattr(packet.parent, "seal", lambda *_args: None)
    monkeypatch.setattr(packet.parent, "context_from_environment", dict)
    monkeypatch.setattr(packet.parent, "read_state", lambda _p: {})
    monkeypatch.setattr(packet.parent, "state_roots", lambda _f: roots)
    monkeypatch.setattr(packet.parent, "unpack", lambda _raw: {})
    monkeypatch.setattr(packet, "package_bytes", lambda _f: b"fixture-zip")
    metadata = packet.capture(tmp_path / "state", tmp_path / "output", packet.Bounds())
    assert metadata["records_before"] == 1
    assert metadata["records_after"] == 2
    assert metadata["new_records"] == 1
    assert metadata["default_parent_promoted"] is False
    assert (tmp_path / "output/canonical-state.zip").read_bytes() == b"fixture-zip"
    assert json.loads((tmp_path / "state/receipts/harvest.json").read_bytes()) == {
        "fixture": True
    }


def test_cli_does_not_print_private_sdk_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failed native operation exposes only its stable exception class."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["packet", "publish"])

    def fail(*_args: object) -> dict[str, object]:
        message = "fixture-private-url-must-not-appear"
        raise OSError(message)

    monkeypatch.setattr(packet, "publish", fail)
    previous_logging_disable = logging.root.manager.disable
    assert packet.main() == 1
    assert logging.root.manager.disable == previous_logging_disable
    output = capsys.readouterr().out
    assert "fixture-private-url" not in output
    assert json.loads(output)["publication_retried"] is False


@pytest.mark.parametrize(
    ("mime", "content"),
    [
        ("application/pdf", b"<html>Challenge</html>"),
        ("application/xml", b"<html>Challenge</html>"),
        ("text/html", b"<html>Challenge</html>"),
    ],
)
def test_offered_formats_reject_challenges_before_custody(
    mime: str, content: bytes
) -> None:
    """HTTP success and content-type alone do not prove an offered representation."""
    client = packet.PacketClient()
    url = "https://www.legislation.govt.nz/act/public/1841/1/en/1841-01-01/"
    client.expected[url] = (mime, "Fixture Act 1841")
    with pytest.raises(ValueError, match="historical"):
        client.check_representation(url, content)


def test_offered_xml_and_html_admission() -> None:
    """Accept the actual Act structure/title while leaving original bytes intact."""
    client = packet.PacketClient()
    url = "https://www.legislation.govt.nz/act/public/1841/1/en/1841-01-01/"
    client.expected[url] = ("application/xml", "Fixture Act 1841")
    client.check_representation(url, b"<act><title>Fixture Act 1841</title></act>")
    client.expected[url] = ("text/html", "Fixture Act 1841")
    client.check_representation(
        url, b"<html><body><h1>Fixture Act 1841</h1></body></html>"
    )


def test_canonical_compression_keeps_exact_bytes_and_reproducible_headers() -> None:
    """Parent contents must not expand beyond a supported container-size profile."""
    files = {
        "manifest.json": b"{}",
        "cas/sha256/aa/" + "a" * 64: b"fixture-source" * 100,
    }
    first = packet.package_bytes(files)
    assert first == packet.package_bytes(files)
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert {name: archive.read(name) for name in archive.namelist()} == files
        assert all(
            info.compress_type == zipfile.ZIP_DEFLATED for info in archive.infolist()
        )
