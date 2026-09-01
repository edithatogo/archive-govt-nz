"""Comprehensive tests for bounded, resumable LegislationArchiveService."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.base import AdapterCaptureResult
from archive_govt_nz.core.manifests import PreservationRecord
from archive_govt_nz.domains.legislation.accounting import (
    StateCommitStatus,
    WorkDisposition,
)
from archive_govt_nz.domains.legislation.api import NZLegislationApiClient
from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointCorruptError,
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.corpus import (
    ExpressionTarget,
    LegislationArchiveService,
    ManifestationTarget,
    WorkTarget,
    _build_discovered_work_targets,
)
from archive_govt_nz.domains.legislation.manifest import (
    build_legislation_manifest,
    compute_legislation_manifest_sha256,
)
from archive_govt_nz.domains.legislation.models import (
    LegislationType,
    VersionStatus,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.core.identity import SourceIdentity


@pytest.mark.anyio
async def test_first_sync_and_repeated_no_change(tmp_path: Path) -> None:
    """Validate first sync cold-start and repeated idempotent no-change sync."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "weekly.json"
    store = ContentAddressedStore(cas_dir)

    xml_content = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<act id="DLM100" status="in-force">\n'
        b"  <title>Ombudsmen Act 1975</title>\n"
        b'  <section id="DLM101"><heading>Title</heading>'
        b"<text>An Act...</text></section>\n"
        b"</act>"
    )

    def handler(req: httpx.Request) -> httpx.Response:
        if "whole.xml" in req.url.path:
            return httpx.Response(
                200,
                headers={"content-type": "application/xml"},
                content=xml_content,
            )
        return httpx.Response(404, content=b"Not Found")

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(async_client=async_client)
    service = LegislationArchiveService(store=store, api_client=api_client)

    target = WorkTarget(
        work_id="act-1975-9",
        title="Ombudsmen Act 1975",
        canonical_uri="https://www.legislation.govt.nz/act/public/1975/0009/latest/whole.xml",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-1975-9:latest",
                version_date="2026-01-01",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-1975-9:latest:xml",
                        target_url="https://www.legislation.govt.nz/act/public/1975/0009/latest/whole.xml",
                        media_type="application/xml",
                    )
                ],
            )
        ],
    )

    # 1. First Sync
    res1 = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        batch_id="batch-2026-01",
    )

    assert res1.status == "success"
    assert res1.works_attempted == 1
    assert res1.works_synced == 1
    assert res1.records_preserved == 1
    assert len(res1.records) == 1
    assert res1.records[0].legislation_type == LegislationType.ACT
    assert res1.records[0].status == VersionStatus.IN_FORCE
    assert res1.manifest["total_records"] == 1
    assert res1.coverage.coverage_percent == 100.0
    assert chk_path.is_file()
    assert res1.checkpoint is not None
    assert res1.checkpoint["last_updated"] is not None
    assert res1.checkpoint["processed_work_ids"] == ["act-1975-9"]

    # 2. Repeated No-Change Sync
    res2 = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        batch_id="batch-2026-01",
    )

    assert res2.status == "no_change"
    assert res2.works_attempted == 1
    assert res2.works_synced == 0
    assert res2.records_preserved == 0
    assert len(res2.records) == 0


@pytest.mark.anyio
async def test_discovery_preserves_canonical_frbr_identities(tmp_path: Path) -> None:
    """Discovered Work/Expression/Manifestation identities must survive sync."""
    payload = b'<act status="in-force"><title>Canonical Act</title></act>'

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/works/"):
            return httpx.Response(
                200,
                json=[
                    {
                        "work_id": "work:act:2026:1",
                        "title": "Canonical Act",
                        "legislation_type": "act",
                        "canonical_uri": "https://example.test/work/act-2026-1",
                        "expressions": [
                            {
                                "expression_id": "expression:act-2026-1:2026-08-20",
                                "version_date": "2026-08-20",
                                "manifestations": [
                                    {
                                        "manifestation_id": (
                                            "manifestation:act-2026-1:xml"
                                        ),
                                        "source_url": "https://example.test/act-2026-1.xml",
                                        "media_type": "application/xml",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            )
        return httpx.Response(200, content=payload)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    async_client = httpx.AsyncClient(transport=transport)
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(client=client, async_client=async_client),
    )

    result = await service.sync_works(search_terms=["canonical"], max_works=1)

    assert result.status == "success"
    assert result.records[0].work_id == "work:act:2026:1"
    assert result.records[0].expression_id == "expression:act-2026-1:2026-08-20"
    assert result.records[0].manifestation_id == "manifestation:act-2026-1:xml"
    assert result.records[0].canonical_uri == "https://example.test/work/act-2026-1"


@pytest.mark.anyio
async def test_search_hit_without_inline_graph_resolves_via_versions(
    tmp_path: Path,
) -> None:
    """A search hit lacking an inline FRBR graph is enriched via /versions/."""
    payload = b'<act status="in-force"><title>Flat Act</title></act>'
    versions = [
        {
            "version_id": "act_flat_2024_1-version-2024-03-01",
            "work_id": "act_flat_2024_1",
            "title": "Flat Act",
            "version_date": "2024-03-01",
            "canonical_url": "https://example.test/act-flat-2024-1/latest",
            "formats": [
                {
                    "url": "https://example.test/act-flat-2024-1/latest.xml",
                    "type": "application/xml",
                }
            ],
        }
    ]

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/works/"):
            return httpx.Response(
                200,
                json=[{"work_id": "act_flat_2024_1", "title": "Flat Act"}],
            )
        if req.url.path.endswith("/versions/"):
            return httpx.Response(200, json=versions)
        if req.url.path.startswith("/versions/"):
            return httpx.Response(200, json=versions[0])
        return httpx.Response(200, content=payload)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    async_client = httpx.AsyncClient(transport=transport)
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(client=client, async_client=async_client),
    )

    result = await service.sync_works(search_terms=["flat"], max_works=1)

    assert result.status == "success"
    assert result.records[0].work_id == "act_flat_2024_1"
    assert result.records[0].expression_id == ("act_flat_2024_1-version-2024-03-01")
    assert result.records[0].manifestation_id is not None
    assert result.records[0].manifestation_id.endswith(".xml")
    assert "/latest" not in result.records[0].manifestation_id


@pytest.mark.anyio
async def test_discovery_fails_closed_without_canonical_frbr_graph(
    tmp_path: Path,
) -> None:
    """A search hit without canonical nested identities is not an archive target."""
    transport = httpx.MockTransport(
        lambda _req: httpx.Response(
            200,
            json=[{"work_id": "act-2026-1", "title": "Incomplete Act"}],
        )
    )
    client = httpx.Client(transport=transport)
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(client=client),
    )

    with pytest.raises(ValueError, match="canonical"):
        await service.sync_works(search_terms=["incomplete"], max_works=1)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("targets", "message"),
    [
        (
            [
                WorkTarget(
                    work_id="",
                    expression_targets=[
                        ExpressionTarget(
                            manifestations=[
                                ManifestationTarget(
                                    target_url="https://example.test/empty-work.xml"
                                )
                            ]
                        )
                    ],
                )
            ],
            "work identity",
        ),
        ([WorkTarget(work_id="act-empty")], "no expressions"),
        (
            [
                WorkTarget(
                    work_id="act-empty-manifestations",
                    expression_targets=[
                        ExpressionTarget(expression_id="expression:empty")
                    ],
                )
            ],
            "no manifestations",
        ),
        (
            [
                WorkTarget(
                    work_id="act-empty-url",
                    expression_targets=[
                        ExpressionTarget(
                            expression_id="expression:empty-url",
                            manifestations=[
                                ManifestationTarget(
                                    manifestation_id="manifestation:empty-url",
                                    target_url="",
                                )
                            ],
                        )
                    ],
                )
            ],
            "empty manifestation URL",
        ),
        (
            [
                WorkTarget(
                    work_id="act-missing-expression-id",
                    expression_targets=[
                        ExpressionTarget(
                            manifestations=[
                                ManifestationTarget(
                                    manifestation_id="manifestation:present",
                                    target_url="https://example.test/one.xml",
                                )
                            ]
                        )
                    ],
                )
            ],
            "invalid expression identity",
        ),
        (
            [
                WorkTarget(
                    work_id="act-missing-manifestation-id",
                    expression_targets=[
                        ExpressionTarget(
                            expression_id="expression:present",
                            manifestations=[
                                ManifestationTarget(
                                    target_url="https://example.test/one.xml"
                                )
                            ],
                        )
                    ],
                )
            ],
            "invalid manifestation identity",
        ),
        (
            [
                WorkTarget(
                    work_id="act-duplicate",
                    expression_targets=[
                        ExpressionTarget(
                            expression_id="expression:duplicate-work-one",
                            manifestations=[
                                ManifestationTarget(
                                    manifestation_id="manifestation:duplicate-work-one",
                                    target_url="https://example.test/one.xml",
                                )
                            ],
                        )
                    ],
                ),
                WorkTarget(
                    work_id="act-duplicate",
                    expression_targets=[
                        ExpressionTarget(
                            expression_id="expression:duplicate-work-two",
                            manifestations=[
                                ManifestationTarget(
                                    manifestation_id="manifestation:duplicate-work-two",
                                    target_url="https://example.test/two.xml",
                                )
                            ],
                        )
                    ],
                ),
            ],
            "duplicate work identity",
        ),
        (
            [
                WorkTarget(
                    work_id="act-duplicate-expressions",
                    expression_targets=[
                        ExpressionTarget(
                            expression_id="expression:duplicate",
                            manifestations=[
                                ManifestationTarget(
                                    manifestation_id="manifestation:two",
                                    target_url="https://example.test/one.xml",
                                )
                            ],
                        ),
                        ExpressionTarget(
                            expression_id="expression:duplicate",
                            manifestations=[
                                ManifestationTarget(
                                    manifestation_id="manifestation:duplicate-two",
                                    target_url="https://example.test/two.xml",
                                )
                            ],
                        ),
                    ],
                )
            ],
            "duplicate expression identity",
        ),
        (
            [
                WorkTarget(
                    work_id="act-duplicate-manifestations",
                    expression_targets=[
                        ExpressionTarget(
                            expression_id="expression:one",
                            manifestations=[
                                ManifestationTarget(
                                    manifestation_id="manifestation:duplicate",
                                    target_url="https://example.test/one.xml",
                                )
                            ],
                        ),
                        ExpressionTarget(
                            expression_id="expression:two",
                            manifestations=[
                                ManifestationTarget(
                                    manifestation_id="manifestation:duplicate",
                                    target_url="https://example.test/two.xml",
                                )
                            ],
                        ),
                    ],
                )
            ],
            "duplicate manifestation identity",
        ),
    ],
)
async def test_explicit_target_graph_fails_closed_when_ambiguous(
    tmp_path: Path,
    targets: list[WorkTarget],
    message: str,
) -> None:
    """Explicit compatibility targets cannot manufacture successful work state."""
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises(ValueError, match=message):
        await service.sync_works(targets=targets)

    with pytest.raises(ValueError, match="max_works"):
        await service.sync_works(targets=[], max_works=-1)


@pytest.mark.anyio
async def test_explicit_target_inventory_is_bounded_before_capture(
    tmp_path: Path,
) -> None:
    """The configured work bound limits explicit target acquisition."""
    requested_paths: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        requested_paths.append(req.url.path)
        return httpx.Response(200, content=b"<act><title>Bounded Act</title></act>")

    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        ),
    )

    def target(number: int) -> WorkTarget:
        return WorkTarget(
            work_id=f"act-{number}",
            expression_targets=[
                ExpressionTarget(
                    expression_id=f"exp:act-{number}:latest",
                    manifestations=[
                        ManifestationTarget(
                            manifestation_id=f"man:act-{number}:xml",
                            target_url=f"https://example.test/act-{number}.xml",
                        )
                    ],
                )
            ],
        )

    result = await service.sync_works(targets=[target(1), target(2)], max_works=1)

    assert result.works_attempted == 1
    assert requested_paths == ["/act-1.xml"]


@pytest.mark.parametrize(
    ("expressions", "error_type", "message"),
    [
        (["invalid"], TypeError, "invalid canonical expression"),
        ([{"manifestations": []}], ValueError, "expression identity"),
        (
            [{"expression_id": "exp:1", "manifestations": ["invalid"]}],
            TypeError,
            "expression exp:1 is invalid",
        ),
        (
            [
                {
                    "expression_id": "exp:1",
                    "manifestations": [{"manifestation_id": ""}],
                }
            ],
            ValueError,
            "manifestation identity",
        ),
        (
            [{"expression_id": "exp:1", "manifestations": []}],
            ValueError,
            "has no manifestations",
        ),
        ([], TypeError, "has no canonical expressions"),
    ],
)
def test_discovery_rejects_each_incomplete_canonical_layer(
    expressions: object,
    error_type: type[Exception],
    message: str,
) -> None:
    """Every malformed Work/Expression/Manifestation layer fails closed."""
    item = {
        "work_id": "work:1",
        "canonical_uri": "https://example.test/work/1",
        "expressions": expressions,
    }

    with pytest.raises(error_type, match=message):
        _build_discovered_work_targets([item])


@pytest.mark.anyio
async def test_service_acquires_only_through_adapter(tmp_path: Path) -> None:
    """The service consumes the adapter receipt and never fetches directly."""
    store = ContentAddressedStore(tmp_path / "cas")
    payload = b"<act><title>Adapter Act</title></act>"
    receipt = store.put_bytes(payload)

    class RecordingAdapter:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str | None, str | None]] = []

        async def capture(
            self,
            identity: SourceIdentity,
            *,
            etag: str | None = None,
            last_modified: str | None = None,
        ) -> AdapterCaptureResult:
            self.calls.append((identity.target, etag, last_modified))
            return AdapterCaptureResult(
                source_identity=identity,
                status="success",
                bytes_captured=len(payload),
                objects_created=1,
                records=(
                    PreservationRecord(
                        record_id=f"rec:{receipt.sha256[:16]}",
                        sha256=receipt.sha256,
                        size_bytes=receipt.byte_count,
                        media_type="application/xml",
                        uri=identity.target,
                    ),
                ),
                metadata={"http_status": "200", "etag": '"v1"'},
            )

    class FailingClient(NZLegislationApiClient):
        async def get_document_raw_async(
            self, *_args: object, **_kwargs: object
        ) -> tuple[int, bytes, dict[str, str]]:
            msg = "service bypassed adapter"
            raise AssertionError(msg)

    adapter = RecordingAdapter()
    service = LegislationArchiveService(
        store=store,
        adapter=adapter,  # type: ignore[arg-type]
        api_client=FailingClient(),
    )
    target = WorkTarget(
        work_id="act-2026-2",
        title="Adapter Act",
        canonical_uri="https://example.test/work/act-2026-2",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-2026-2:v1",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-2026-2:v1:xml",
                        target_url="https://example.test/act-2026-2.xml",
                    )
                ],
            )
        ],
    )

    result = await service.sync_works(targets=[target])

    assert result.status == "success"
    assert adapter.calls == [("https://example.test/act-2026-2.xml", None, None)]


@pytest.mark.anyio
async def test_304_retains_cumulative_manifest_and_checkpoint(tmp_path: Path) -> None:
    """Conditional no-change keeps prior manifest and cumulative accounting."""
    requests: list[httpx.Request] = []
    payload = b'<act status="in-force"><title>Conditional Act</title></act>'

    def handler(req: httpx.Request) -> httpx.Response:
        requests.append(req)
        if len(requests) == 1:
            return httpx.Response(
                200,
                content=payload,
                headers={
                    "Content-Type": "application/xml",
                    "ETag": '"v1"',
                    "Last-Modified": "Wed, 19 Aug 2026 00:00:00 GMT",
                },
            )
        assert req.headers["If-None-Match"] == '"v1"'
        return httpx.Response(304, headers={"ETag": '"v1"'})

    async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=async_client),
    )
    checkpoint = tmp_path / "checkpoint.json"
    manifest = tmp_path / "manifest.json"
    target = WorkTarget(
        work_id="act-2026-3",
        title="Conditional Act",
        canonical_uri="https://example.test/work/act-2026-3",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-2026-3:v1",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-2026-3:v1:xml",
                        target_url="https://example.test/act-2026-3.xml",
                    )
                ],
            )
        ],
    )

    first = await service.sync_works(
        targets=[target], checkpoint_path=checkpoint, manifest_path=manifest
    )
    second = await service.sync_works(
        targets=[target],
        checkpoint_path=checkpoint,
        manifest_path=manifest,
        force_resync=True,
    )

    assert first.status == "success"
    assert second.status == "no_change"
    assert second.records_preserved == 0
    assert second.manifest["total_records"] == 1
    assert second.checkpoint is not None
    assert second.checkpoint["total_records_preserved"] == 1
    assert second.accounting is not None
    assert second.accounting.works_attempted == 1
    assert second.accounting.unchanged_revalidated == 1
    assert (
        second.accounting.works[0].disposition is WorkDisposition.UNCHANGED_REVALIDATED
    )


@pytest.mark.anyio
async def test_304_retains_explicit_target_with_canonical_identity(
    tmp_path: Path,
) -> None:
    """Explicit targets link validators to their canonical manifestation ID."""
    requests: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        requests.append(req)
        if len(requests) == 1:
            return httpx.Response(
                200,
                content=b"<act><title>Explicit Act</title></act>",
                headers={"Content-Type": "application/xml", "ETag": '"v1"'},
            )
        assert req.headers["If-None-Match"] == '"v1"'
        return httpx.Response(304, headers={"ETag": '"v1"'})

    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        ),
    )
    checkpoint = tmp_path / "checkpoint.json"
    manifest = tmp_path / "manifest.json"
    target = WorkTarget(
        work_id="act-explicit",
        title="Explicit Act",
        canonical_uri="https://example.test/work/act-explicit",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-explicit:latest",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-explicit:xml",
                        target_url="https://example.test/act-explicit.xml",
                    )
                ],
            )
        ],
    )

    first = await service.sync_works(
        targets=[target], checkpoint_path=checkpoint, manifest_path=manifest
    )
    second = await service.sync_works(
        targets=[target],
        checkpoint_path=checkpoint,
        manifest_path=manifest,
        force_resync=True,
    )

    assert first.status == "success"
    assert second.status == "no_change"
    assert second.errors == []
    assert second.manifest["total_records"] == 1


@pytest.mark.anyio
async def test_cold_304_without_prior_manifestation_fails_closed(
    tmp_path: Path,
) -> None:
    """A source 304 cannot manufacture a no-change observation on cold state."""
    async_client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _req: httpx.Response(304))
    )
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=async_client),
    )
    target = WorkTarget(
        work_id="act-cold-304",
        canonical_uri="https://example.test/work/act-cold-304",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-cold-304:v1",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-cold-304:v1:xml",
                        target_url="https://example.test/act-cold-304.xml",
                    )
                ],
            )
        ],
    )

    result = await service.sync_works(targets=[target])

    assert result.status == "failed"
    assert "without prior cumulative manifestation" in result.errors[0]


@pytest.mark.anyio
async def test_manifest_and_checkpoint_are_cumulative_across_batches(
    tmp_path: Path,
) -> None:
    """A later batch adds to, rather than replaces, durable accounting."""
    async_client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200,
                content=f"<act><title>{req.url.path}</title></act>".encode(),
                headers={"Content-Type": "application/xml"},
            )
        )
    )
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=async_client),
    )
    checkpoint = tmp_path / "checkpoint.json"
    manifest = tmp_path / "manifest.json"

    def target(number: int) -> WorkTarget:
        work_id = f"act-2026-{number}"
        return WorkTarget(
            work_id=work_id,
            title=f"Act {number}",
            canonical_uri=f"https://example.test/work/{work_id}",
            expression_targets=[
                ExpressionTarget(
                    expression_id=f"exp:{work_id}:v1",
                    manifestations=[
                        ManifestationTarget(
                            manifestation_id=f"man:{work_id}:v1:xml",
                            target_url=f"https://example.test/{work_id}.xml",
                        )
                    ],
                )
            ],
        )

    await service.sync_works(
        targets=[target(1)],
        checkpoint_path=checkpoint,
        manifest_path=manifest,
        batch_id="batch-1",
    )
    second = await service.sync_works(
        targets=[target(2)],
        checkpoint_path=checkpoint,
        manifest_path=manifest,
        batch_id="batch-2",
    )

    assert second.manifest["total_records"] == 2
    assert second.checkpoint is not None
    assert second.checkpoint["total_records_preserved"] == 2
    assert second.checkpoint["completed_batches"] == ["batch-1", "batch-2"]
    assert second.checkpoint["processed_work_ids"] == ["act-2026-1", "act-2026-2"]


@pytest.mark.anyio
async def test_corrupt_cumulative_manifest_fails_closed(tmp_path: Path) -> None:
    """A corrupt prior manifest cannot silently reset cumulative evidence."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{broken", encoding="utf-8")
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises(ValueError, match="manifest"):
        await service.sync_works(targets=[], manifest_path=manifest)


@pytest.mark.anyio
async def test_corrupt_checkpoint_fails_before_discovery_request(
    tmp_path: Path,
) -> None:
    """Parent checkpoint authority is authenticated before source discovery."""
    requests = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(200, json=[])

    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text("{broken", encoding="utf-8")
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=client),
    )

    with pytest.raises(LegislationCheckpointCorruptError):
        await service.sync_works(search_terms=["health"], checkpoint_path=checkpoint)
    assert requests == 0
    await client.aclose()


@pytest.mark.anyio
async def test_parent_cross_link_failure_precedes_discovery_request(
    tmp_path: Path,
) -> None:
    """Mutually inconsistent valid parent files fail before source discovery."""
    requests = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(200, json=[])

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(build_legislation_manifest([], discovered_work_ids=[])),
        encoding="utf-8",
    )
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
                "completed_batches": ["prior"],
                "processed_work_ids": [],
                "last_processed_index": 0,
                "total_records_preserved": 0,
                "metadata": {
                    "manifest_sha256": "f" * 64,
                    "discovered_inventory_sha256": "e" * 64,
                },
            }
        ),
        encoding="utf-8",
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=client),
    )

    with pytest.raises(ValueError, match="does not match cumulative manifest"):
        await service.sync_works(
            search_terms=["health"],
            checkpoint_path=checkpoint,
            manifest_path=manifest,
        )
    assert requests == 0
    await client.aclose()


@pytest.mark.anyio
async def test_checkpoint_promotion_failure_is_indeterminate_without_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed state transaction returns truthful evidence and no new manifest."""
    target = WorkTarget(
        work_id="act-2026-transaction",
        title="Transaction Act",
        canonical_uri="https://www.legislation.govt.nz/transaction.xml",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:transaction",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:transaction",
                        target_url="https://www.legislation.govt.nz/transaction.xml",
                        media_type="application/xml",
                    )
                ],
            )
        ],
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/xml"},
            content=b'<act status="in-force"><title>Transaction Act</title></act>',
        )

    def fail_promotion(_self: LegislationCheckpointManager) -> None:
        message = "injected checkpoint failure"
        raise OSError(message)

    monkeypatch.setattr(LegislationCheckpointManager, "promote", fail_promotion)
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    manifest = tmp_path / "manifest.json"
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=client),
    )

    result = await service.sync_works(
        targets=[target],
        checkpoint_path=tmp_path / "checkpoint.json",
        manifest_path=manifest,
    )

    assert result.accounting is not None
    assert result.accounting.state_commit_status is StateCommitStatus.INDETERMINATE
    assert result.accounting.state_commit is None
    assert result.accounting.total_state_records_after == 0
    assert result.accounting.total_cas_objects_after >= 1
    assert not manifest.exists()
    assert any("state commit indeterminate" in error for error in result.errors)
    await client.aclose()


@pytest.mark.anyio
async def test_manifest_failure_rolls_back_promoted_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reverse half-commit is rolled back and reported as indeterminate."""
    target = WorkTarget(
        work_id="act-2026-rollback",
        title="Rollback Act",
        canonical_uri="https://www.legislation.govt.nz/rollback.xml",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:rollback",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:rollback",
                        target_url="https://www.legislation.govt.nz/rollback.xml",
                        media_type="application/xml",
                    )
                ],
            )
        ],
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/xml"},
            content=b'<act status="in-force"><title>Rollback Act</title></act>',
        )

    def fail_manifest(_path: Path, _manifest: dict[str, object]) -> None:
        message = "injected manifest failure"
        raise OSError(message)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    checkpoint = tmp_path / "checkpoint.json"
    manifest = tmp_path / "manifest.json"
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=client),
    )
    monkeypatch.setattr(service, "_write_manifest", fail_manifest)

    result = await service.sync_works(
        targets=[target], checkpoint_path=checkpoint, manifest_path=manifest
    )

    assert result.accounting is not None
    assert result.accounting.state_commit_status is StateCommitStatus.INDETERMINATE
    assert not checkpoint.exists()
    assert not manifest.exists()
    assert any("injected manifest failure" in error for error in result.errors)
    await client.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"records": []}, "manifest root is missing"),
        ([], "valid manifest object"),
        ({"records": ["invalid"]}, "invalid records"),
        ({"records": [], "manifest_sha256": "bad"}, "root is missing or invalid"),
        ({"records": [], "manifest_sha256": "0" * 64}, "root does not match"),
    ],
)
async def test_structurally_invalid_cumulative_manifest_fails_closed(
    tmp_path: Path,
    payload: object,
    message: str,
) -> None:
    """Parseable but structurally invalid cumulative evidence is rejected."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises((TypeError, ValueError), match=message):
        await service.sync_works(targets=[], manifest_path=manifest)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "metadata",
    [[], {"conditional_requests": []}],
)
async def test_invalid_conditional_checkpoint_metadata_fails_closed(
    tmp_path: Path,
    metadata: object,
) -> None:
    """Malformed validator state is corrupt checkpoint evidence."""
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(json.dumps({"metadata": metadata}), encoding="utf-8")
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises((TypeError, ValueError), match="checkpoint"):
        await service.sync_works(targets=[], checkpoint_path=checkpoint)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("checkpoint_data", "message"),
    [
        ({"schema_version": "unsupported"}, "schema_version"),
        ({"processed_work_ids": "act-1"}, "processed_work_ids"),
        ({"processed_work_ids": ["act-1", "act-1"]}, "duplicates"),
        ({"total_records_preserved": True}, "total_records_preserved"),
        ({"last_processed_index": -1}, "last_processed_index"),
        (
            {"processed_work_ids": ["act-1"], "last_processed_index": 0},
            "last_processed_index does not match",
        ),
        ({"metadata": {"manifest_sha256": "bad"}}, "manifest root"),
        (
            {"metadata": {"conditional_requests": {"": {}}}},
            "conditional request entry",
        ),
        (
            {"metadata": {"conditional_requests": {"source": {"etag": 1}}}},
            "conditional request etag",
        ),
    ],
)
async def test_invalid_checkpoint_structure_fails_closed(
    tmp_path: Path,
    checkpoint_data: dict[str, object],
    message: str,
) -> None:
    """Typed checkpoint accounting is required before state is consumed."""
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(json.dumps(checkpoint_data), encoding="utf-8")
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises((TypeError, ValueError), match=message):
        await service.sync_works(targets=[], checkpoint_path=checkpoint)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("records", "total_records", "message"),
    [
        ([{"raw_sha256": "0" * 64}], 1, "lacks canonical identity"),
        (
            [
                {"document_id": "leg-1", "raw_sha256": "0" * 64},
                {"document_id": "leg-1", "raw_sha256": "0" * 64},
            ],
            2,
            "duplicate canonical identities",
        ),
        ([], 1, "total_records"),
    ],
)
async def test_manifest_identity_and_count_corruption_fails_closed(
    tmp_path: Path,
    records: list[dict[str, object]],
    total_records: int,
    message: str,
) -> None:
    """Authenticated bytes do not excuse corrupt identity or count structure."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "records": records,
                "total_records": total_records,
                "manifest_sha256": compute_legislation_manifest_sha256(records),
            }
        ),
        encoding="utf-8",
    )
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises(ValueError, match=message):
        await service.sync_works(targets=[], manifest_path=manifest)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"discovered_works_count": 1}, "discovered work count"),
        ({"discovered_inventory_sha256": "0" * 64}, "inventory root"),
    ],
)
async def test_discovered_inventory_metadata_is_authenticated(
    tmp_path: Path,
    mutation: dict[str, object],
    message: str,
) -> None:
    """Coverage inventory metadata cannot change independently of its root."""
    manifest_data = build_legislation_manifest([], run_id="inventory")
    manifest_data.update(mutation)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises(ValueError, match=message):
        await service.sync_works(targets=[], manifest_path=manifest)


@pytest.mark.anyio
async def test_checkpoint_and_manifest_roots_must_match(tmp_path: Path) -> None:
    """A checkpoint cannot name a different cumulative manifest root."""
    records: list[dict[str, object]] = []
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "records": records,
                "manifest_sha256": compute_legislation_manifest_sha256(records),
            }
        ),
        encoding="utf-8",
    )
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps({"metadata": {"manifest_sha256": "0" * 64}}),
        encoding="utf-8",
    )
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises(ValueError, match="checkpoint manifest root"):
        await service.sync_works(
            targets=[], checkpoint_path=checkpoint, manifest_path=manifest
        )


@pytest.mark.anyio
async def test_checkpoint_and_manifest_record_counts_must_match(tmp_path: Path) -> None:
    """A valid root cannot authenticate contradictory cumulative counts."""
    manifest_data = build_legislation_manifest([], run_id="prior")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "total_records_preserved": 1,
                "metadata": {
                    "manifest_sha256": manifest_data["manifest_sha256"],
                    "discovered_inventory_sha256": manifest_data[
                        "discovered_inventory_sha256"
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises(ValueError, match="record count"):
        await service.sync_works(
            targets=[], checkpoint_path=checkpoint, manifest_path=manifest
        )


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("checkpoint_mutation", "message"),
    [
        ({"remove_inventory_root": True}, "inventory root is missing"),
        ({"discovered_inventory_sha256": "0" * 64}, "inventory root does not match"),
        ({"processed_work_ids": ["different-work"]}, "processed work IDs"),
    ],
)
async def test_checkpoint_inventory_linkage_fails_closed(
    tmp_path: Path,
    checkpoint_mutation: dict[str, object],
    message: str,
) -> None:
    """Checkpoint work accounting must link to the authenticated inventory."""
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda _req: httpx.Response(
                        200, content=b"<act><title>Linked Act</title></act>"
                    )
                )
            )
        ),
    )
    checkpoint = tmp_path / "checkpoint.json"
    manifest = tmp_path / "manifest.json"
    target = WorkTarget(
        work_id="linked-work",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:linked-work:latest",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:linked-work:xml",
                        target_url="https://example.test/linked-work.xml",
                    )
                ],
            )
        ],
    )
    await service.sync_works(
        targets=[target], checkpoint_path=checkpoint, manifest_path=manifest
    )
    checkpoint_data = json.loads(checkpoint.read_text(encoding="utf-8"))
    metadata = checkpoint_data["metadata"]
    if checkpoint_mutation.get("remove_inventory_root"):
        metadata.pop("discovered_inventory_sha256", None)
    elif "discovered_inventory_sha256" in checkpoint_mutation:
        metadata["discovered_inventory_sha256"] = checkpoint_mutation[
            "discovered_inventory_sha256"
        ]
    if "processed_work_ids" in checkpoint_mutation:
        checkpoint_data["processed_work_ids"] = checkpoint_mutation[
            "processed_work_ids"
        ]
    checkpoint.write_text(json.dumps(checkpoint_data), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        await service.sync_works(
            targets=[], checkpoint_path=checkpoint, manifest_path=manifest
        )


@pytest.mark.anyio
async def test_non_empty_checkpoint_requires_manifest_root_linkage(
    tmp_path: Path,
) -> None:
    """Accounted checkpoint state without a manifest root fails closed."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(build_legislation_manifest([], run_id="prior")),
        encoding="utf-8",
    )
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "processed_work_ids": ["act-1"],
                "total_records_preserved": 1,
            }
        ),
        encoding="utf-8",
    )
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises(ValueError, match="checkpoint manifest root is missing"):
        await service.sync_works(
            targets=[], checkpoint_path=checkpoint, manifest_path=manifest
        )


@pytest.mark.anyio
async def test_canonical_manifestation_identity_cannot_change_bytes(
    tmp_path: Path,
) -> None:
    """One canonical manifestation ID cannot silently replace prior bytes."""
    payloads = iter(
        [
            b"<act><title>Original Act</title></act>",
            b"<act><title>Changed Act</title></act>",
        ]
    )
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda _req: httpx.Response(200, content=next(payloads))
                )
            )
        ),
    )
    checkpoint = tmp_path / "checkpoint.json"
    manifest = tmp_path / "manifest.json"
    target = WorkTarget(
        work_id="act-collision",
        title="Collision Act",
        canonical_uri="https://example.test/work/act-collision",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:collision:v1",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:collision:v1:xml",
                        target_url="https://example.test/act-collision.xml",
                    )
                ],
            )
        ],
    )

    await service.sync_works(
        targets=[target], checkpoint_path=checkpoint, manifest_path=manifest
    )

    with pytest.raises(ValueError, match="manifestation identity collision"):
        await service.sync_works(
            targets=[target],
            checkpoint_path=checkpoint,
            manifest_path=manifest,
            force_resync=True,
        )


@pytest.mark.anyio
async def test_partial_batch_is_not_recorded_as_completed(tmp_path: Path) -> None:
    """A partial batch retains progress without claiming batch completion."""

    def handler(req: httpx.Request) -> httpx.Response:
        if "failed" in req.url.path:
            return httpx.Response(500)
        return httpx.Response(200, content=b"<act><title>Good Act</title></act>")

    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=httpx.AsyncClient(
                transport=httpx.MockTransport(handler),
            ),
            max_retries=0,
            min_interval_seconds=0.0,
        ),
    )
    checkpoint = tmp_path / "checkpoint.json"
    manifest = tmp_path / "manifest.json"

    def target(work_id: str) -> WorkTarget:
        return WorkTarget(
            work_id=work_id,
            title=work_id,
            canonical_uri=f"https://example.test/work/{work_id}",
            expression_targets=[
                ExpressionTarget(
                    expression_id=f"exp:{work_id}",
                    manifestations=[
                        ManifestationTarget(
                            manifestation_id=f"man:{work_id}",
                            target_url=f"https://example.test/{work_id}.xml",
                        )
                    ],
                )
            ],
        )

    result = await service.sync_works(
        targets=[target("good"), target("failed")],
        checkpoint_path=checkpoint,
        manifest_path=manifest,
        batch_id="partial-batch",
    )

    assert result.status == "partial"
    assert result.checkpoint is not None
    assert result.checkpoint["processed_work_ids"] == ["good"]
    assert result.checkpoint["completed_batches"] == []
    assert result.accounting is not None
    assert result.accounting.newly_preserved == 1
    assert result.accounting.failed == 1
    assert result.accounting.state_commit_status is StateCommitStatus.PARTIAL_COMMITTED


@pytest.mark.anyio
async def test_invalid_normalised_record_is_not_preserved(tmp_path: Path) -> None:
    """Adapter success cannot bypass canonical record validation."""
    payload = b"<act><title>Invalid identity</title></act>"
    async_client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _req: httpx.Response(200, content=payload))
    )
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=async_client),
    )
    target = WorkTarget(
        work_id="work-invalid",
        canonical_uri="invalid-uri",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:invalid",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:invalid",
                        target_url="https://example.test/invalid.xml",
                    )
                ],
            )
        ],
    )

    result = await service.sync_works(targets=[target])

    assert result.status == "failed"
    assert any("canonical_uri" in error for error in result.errors)


@pytest.mark.anyio
async def test_missing_manifest_for_non_empty_checkpoint_fails_closed(
    tmp_path: Path,
) -> None:
    """Checkpoint accounting cannot continue after its manifest disappears."""
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        '{"processed_work_ids":["act-1"],"total_records_preserved":1}',
        encoding="utf-8",
    )
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    with pytest.raises(ValueError, match="manifest is missing"):
        await service.sync_works(
            targets=[],
            checkpoint_path=checkpoint,
            manifest_path=tmp_path / "missing-manifest.json",
        )


@pytest.mark.anyio
async def test_end_to_end_multi_expression_fixture(tmp_path: Path) -> None:
    """Test one work with two expressions and XML/HTML manifestations."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "e2e_chk.json"
    store = ContentAddressedStore(cas_dir)

    exp1_xml = (
        b'<act id="DLM1" status="repealed"><title>Historic Act</title>'
        b'<section id="s1"><text>Old</text></section></act>'
    )
    exp1_html = (
        b"<html><head><title>Historic Act</title></head>"
        b"<body><h1>Historic Act</h1><p>Old</p></body></html>"
    )
    exp2_xml = (
        b'<act id="DLM1" status="in-force"><title>Historic Act</title>'
        b'<section id="s1"><text>New</text></section></act>'
    )
    exp2_html = (
        b"<html><head><title>Historic Act</title></head>"
        b"<body><h1>Historic Act</h1><p>New</p></body></html>"
    )

    def handler(req: httpx.Request) -> httpx.Response:
        path = req.url.path
        if "/v1/whole.xml" in path:
            return httpx.Response(
                200,
                headers={"content-type": "application/xml"},
                content=exp1_xml,
            )
        if "/v1/whole.html" in path:
            return httpx.Response(
                200, headers={"content-type": "text/html"}, content=exp1_html
            )
        if "/v2/whole.xml" in path:
            return httpx.Response(
                200,
                headers={"content-type": "application/xml"},
                content=exp2_xml,
            )
        if "/v2/whole.html" in path:
            return httpx.Response(
                200, headers={"content-type": "text/html"}, content=exp2_html
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(async_client=async_client)
    service = LegislationArchiveService(store=store, api_client=api_client)

    target = WorkTarget(
        work_id="act-1990-1",
        title="Historic Act",
        canonical_uri="https://example.com/act/1990/1",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-1990-1:1990",
                version_date="1990-01-01",
                version_label="1990-initial",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-1990-1:xml:1990",
                        target_url="https://example.com/act/1990/1/v1/whole.xml",
                        media_type="application/xml",
                    ),
                    ManifestationTarget(
                        manifestation_id="man:act-1990-1:html:1990",
                        target_url="https://example.com/act/1990/1/v1/whole.html",
                        media_type="text/html",
                    ),
                ],
            ),
            ExpressionTarget(
                expression_id="exp:act-1990-1:2026",
                version_date="2026-01-01",
                version_label="2026-reprint",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-1990-1:xml:2026",
                        target_url="https://example.com/act/1990/1/v2/whole.xml",
                        media_type="application/xml",
                    ),
                    ManifestationTarget(
                        manifestation_id="man:act-1990-1:html:2026",
                        target_url="https://example.com/act/1990/1/v2/whole.html",
                        media_type="text/html",
                    ),
                ],
            ),
        ],
    )

    res = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        batch_id="batch-e2e",
    )

    assert res.status == "success"
    assert res.records_preserved == 4
    assert len(res.records) == 4
    assert res.coverage.xml_manifestations_count == 2
    assert res.coverage.html_fallback_count == 2

    statuses = [r.status for r in res.records]
    assert VersionStatus.REPEALED in statuses
    assert VersionStatus.IN_FORCE in statuses

    rerun = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        batch_id="batch-e2e",
    )
    assert rerun.status == "no_change"
    assert rerun.records_preserved == 0


@pytest.mark.anyio
async def test_resumption_after_interruption(tmp_path: Path) -> None:
    """Validate resuming sync across multi-work batch skips already completed works."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "resume_chk.json"
    store = ContentAddressedStore(cas_dir)

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/xml"},
            content=f"<act><title>{req.url.path}</title></act>".encode(),
        )

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(async_client=async_client)
    service = LegislationArchiveService(store=store, api_client=api_client)

    target1 = WorkTarget(
        work_id="act-1",
        title="Act One",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-1:latest",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-1:xml",
                        target_url="https://example.com/act1/whole.xml",
                    )
                ],
            )
        ],
    )
    target2 = WorkTarget(
        work_id="act-2",
        title="Act Two",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-2:latest",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-2:xml",
                        target_url="https://example.com/act2/whole.xml",
                    )
                ],
            )
        ],
    )

    res1 = await service.sync_works(
        targets=[target1],
        checkpoint_path=chk_path,
    )
    assert res1.status == "success"
    assert res1.works_synced == 1

    res2 = await service.sync_works(
        targets=[target1, target2],
        checkpoint_path=chk_path,
    )
    assert res2.status == "success"
    assert res2.works_synced == 1
    assert res2.records_preserved == 1
    assert res2.records[0].work_id == "act-2"
    assert res2.checkpoint is not None
    assert res2.checkpoint["processed_work_ids"] == ["act-1", "act-2"]


@pytest.mark.anyio
async def test_fail_fast_no_checkpoint_promotion(tmp_path: Path) -> None:
    """Validate failure under fail_fast discards staging and halts promotion."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "fail_chk.json"
    store = ContentAddressedStore(cas_dir)

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, content=b"Server Error")

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(
        async_client=async_client,
        max_retries=0,
        min_interval_seconds=0.0,
    )
    service = LegislationArchiveService(store=store, api_client=api_client)

    target = WorkTarget(
        work_id="act-failing",
        title="Failing Act",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-failing:latest",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-failing:xml",
                        target_url="https://example.com/fail/whole.xml",
                    )
                ],
            )
        ],
    )

    res = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        fail_fast=True,
    )

    assert res.status == "failed"
    assert len(res.errors) > 0
    assert not chk_path.is_file()
    assert not chk_path.with_suffix(".staging.tmp").is_file()

    non_fail_fast_checkpoint = tmp_path / "checkpoints" / "failed.json"
    non_fail_fast_manifest = tmp_path / "failed-manifest.json"
    non_fail_fast = await service.sync_works(
        targets=[target],
        checkpoint_path=non_fail_fast_checkpoint,
        manifest_path=non_fail_fast_manifest,
        fail_fast=False,
    )
    assert non_fail_fast.status == "failed"
    assert not non_fail_fast_checkpoint.exists()
    assert not non_fail_fast_manifest.exists()


@pytest.mark.anyio
async def test_corrupt_checkpoint_detection_and_non_dict(
    tmp_path: Path,
) -> None:
    """Corrupt JSON or non-dict in checkpoint must be detected cleanly."""
    chk_path = tmp_path / "corrupt.json"
    chk_path.write_text("{ unclosed invalid json", encoding="utf-8")

    mgr = LegislationCheckpointManager(chk_path)
    with pytest.raises(LegislationCheckpointCorruptError):
        mgr.load(strict=True)

    chk_path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(LegislationCheckpointCorruptError):
        mgr.load(strict=True)
    assert mgr.load(strict=False)["total_records_preserved"] == 0

    non_existent = LegislationCheckpointManager(tmp_path / "non_existent.json")
    init_state = non_existent.load()
    assert init_state["last_updated"] is None
    assert init_state["total_records_preserved"] == 0

    with pytest.raises(FileNotFoundError):
        non_existent.promote()

    # discard_staging on non-existent file is a no-op
    non_existent.discard_staging()

    # discard_staging when file exists removes it
    stg_path = non_existent.stage(["b1"], ["w1"], 1)
    assert stg_path.is_file()
    non_existent.discard_staging()
    assert not stg_path.is_file()


@pytest.mark.anyio
async def test_target_resolution_and_partial_sync(tmp_path: Path) -> None:
    """Validate target resolution by work IDs, search terms, and partial failures."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "partial.json"
    store = ContentAddressedStore(cas_dir)

    def handler(req: httpx.Request) -> httpx.Response:  # noqa: PLR0911
        path = req.url.path
        if path.endswith("/works/act-disc-1/versions/"):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "work_id": "act-disc-1",
                            "version_id": "exp:act-disc-1:latest",
                        },
                    ]
                },
            )
        if path.endswith("/versions/exp:act-disc-1:latest/"):
            return httpx.Response(
                200,
                json={
                    "work_id": "act-disc-1",
                    "version_id": "exp:act-disc-1:latest",
                    "version_date": "2026-01-01",
                    "title": "Discovered Act 1",
                    "canonical_uri": "https://example.test/work/act-disc-1",
                    "formats": [
                        {
                            "type": "text/html",
                            "url": "https://example.test/act-disc-1/latest.html",
                        },
                        {
                            "type": "application/xml",
                            "url": "https://example.test/act-disc-1/latest.xml",
                        },
                    ],
                },
            )
        if path.endswith("/works/act-not-discovered/versions/"):
            return httpx.Response(200, json={"results": []})
        if path.endswith("/act-disc-1/2026-01-01.xml"):
            return httpx.Response(404)
        if path.endswith("/act-disc-1/2026-01-01.html"):
            return httpx.Response(
                200,
                headers={"content-type": "text/html"},
                content=b"<html><title>OK Act</title></html>",
            )
        if path.endswith("/works/"):
            return httpx.Response(
                200,
                json=[
                    {
                        "work_id": "act-disc-1",
                        "title": "Discovered Act 1",
                        "canonical_uri": "https://example.test/work/act-disc-1",
                        "expressions": [
                            {
                                "expression_id": "exp:act-disc-1:latest",
                                "manifestations": [
                                    {
                                        "manifestation_id": "man:act-disc-1:xml",
                                        "source_url": (
                                            "https://example.test/act-disc-1/whole.xml"
                                        ),
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "work_id": "act-disc-2",
                        "title": "Discovered Act 2",
                        "canonical_uri": "https://example.test/work/act-disc-2",
                        "expressions": [
                            {
                                "expression_id": "exp:act-disc-2:latest",
                                "manifestations": [
                                    {
                                        "manifestation_id": "man:act-disc-2:xml",
                                        "source_url": (
                                            "https://example.test/act-disc-2/whole.xml"
                                        ),
                                    }
                                ],
                            }
                        ],
                    },
                ],
            )
        if "act-disc-1" in path or "act-work-1" in path:
            return httpx.Response(
                200,
                headers={"content-type": "application/xml"},
                content=b"<act><title>OK Act</title></act>",
            )
        if "act-fail" in path:
            return httpx.Response(500, content=b"Server Error")
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(
        client=client,
        async_client=async_client,
        max_retries=0,
        min_interval_seconds=0.0,
    )
    chk_mgr = LegislationCheckpointManager(chk_path)
    service = LegislationArchiveService(
        store=store, api_client=api_client, checkpoint_mgr=chk_mgr
    )

    # 1. Resolve exact work IDs through canonical discovery.
    res_work_ids = await service.sync_works(
        work_ids=["act-disc-1"],
        max_works=5,
    )
    assert res_work_ids.status == "success"
    assert res_work_ids.records_preserved == 1
    assert res_work_ids.records[0].work_id == "act-disc-1"
    assert res_work_ids.records[0].expression_id == "exp:act-disc-1:latest"
    assert res_work_ids.records[0].manifestation_id == (
        "https://example.test/act-disc-1/2026-01-01.html"
    )

    with pytest.raises(ValueError, match="not returned by canonical discovery"):
        await service.sync_works(work_ids=["act-not-discovered"])
    with pytest.raises(ValueError, match="at least one canonical work identity"):
        await service.sync_works(work_ids=[])

    # 2. Resolve targets via search_terms
    res_search = await service.sync_works(
        search_terms=["finance"],
        force_resync=True,
        max_works=1,
    )
    assert res_search.status == "success"
    assert res_search.works_attempted == 1

    # 3. Partial failure (1 success, 1 failure with fail_fast=False)
    partial_target_ok = WorkTarget(
        work_id="act-work-1",
        title="OK Act",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-work-1:latest",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-work-1:xml",
                        target_url="https://example.com/act-work-1/whole.xml",
                    )
                ],
            )
        ],
    )
    partial_target_fail = WorkTarget(
        work_id="act-fail",
        title="Fail Act",
        expression_targets=[
            ExpressionTarget(
                expression_id="exp:act-fail:latest",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id="man:act-fail:xml",
                        target_url="https://example.com/act-fail/whole.xml",
                    )
                ],
            )
        ],
    )

    res_partial = await service.sync_works(
        targets=[partial_target_ok, partial_target_fail],
        force_resync=True,
        fail_fast=False,
    )
    assert res_partial.status == "partial"
    assert res_partial.records_preserved == 1
    assert len(res_partial.errors) == 1

    # 4. Total failure (0 preserved records)
    res_all_failed = await service.sync_works(
        targets=[partial_target_fail],
        force_resync=True,
        fail_fast=False,
    )
    assert res_all_failed.status == "failed"
    assert res_all_failed.records_preserved == 0

    # 5. Empty targets
    res_empty = await service.sync_works()
    assert res_empty.status == "success"
    assert res_empty.works_attempted == 0

    # 6. No checkpoint manager configured
    no_chk_service = LegislationArchiveService(store=store, api_client=api_client)
    res_no_chk = await no_chk_service.sync_works(
        targets=[partial_target_ok],
        force_resync=True,
    )
    assert res_no_chk.status == "success"
    assert res_no_chk.checkpoint == {}


def _accounting_target(work_id: str, *urls: str) -> WorkTarget:
    """Build a minimal target whose manifestations have stable identities."""
    return WorkTarget(
        work_id=work_id,
        title=f"{work_id} title",
        canonical_uri=f"https://example.test/works/{work_id}",
        expression_targets=[
            ExpressionTarget(
                expression_id=f"exp:{work_id}:latest",
                manifestations=[
                    ManifestationTarget(
                        manifestation_id=f"man:{work_id}:{index}:xml",
                        target_url=url,
                    )
                    for index, url in enumerate(urls)
                ],
            )
        ],
    )


@pytest.mark.anyio
async def test_same_work_success_and_error_is_partial(tmp_path: Path) -> None:
    """Mixed manifestation outcomes produce one terminal partial disposition."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("good.xml"):
            return httpx.Response(
                200,
                content=b"<act><title>Mixed work</title></act>",
                headers={"Content-Type": "application/xml"},
            )
        return httpx.Response(500, content=b"temporary failure")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=client, max_retries=0, min_interval_seconds=0.0
        ),
    )
    target = _accounting_target(
        "mixed-work",
        "https://example.test/good.xml",
        "https://example.test/bad.xml",
    )

    result = await service.sync_works(targets=[target])

    assert result.status == "partial"
    assert result.accounting is not None
    assert result.accounting.partial == 1
    assert result.accounting.failed == 0
    assert result.accounting.works[0].disposition is WorkDisposition.PARTIAL
    assert result.accounting.works[0].source_response_classifications == (
        "success",
        "transient_failure",
    )
    await client.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize("status_code", [404, 410])
async def test_terminal_http_absence_is_unavailable(
    tmp_path: Path, status_code: int
) -> None:
    """Both supported terminal absence responses map to unavailable."""
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(status_code, content=b"gone")
        )
    )
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=client, max_retries=0, min_interval_seconds=0.0
        ),
    )

    result = await service.sync_works(
        targets=[_accounting_target("missing-work", "https://example.test/gone.xml")]
    )

    assert result.status == "failed"
    assert result.accounting is not None
    assert result.accounting.unavailable == 1
    assert result.accounting.failed == 0
    assert result.accounting.works[0].disposition is WorkDisposition.UNAVAILABLE
    assert result.accounting.works[0].source_response_classifications == (
        "unavailable",
    )
    await client.aclose()


@pytest.mark.anyio
async def test_forced_byte_equal_200_is_unchanged_revalidated(tmp_path: Path) -> None:
    """A forced 200 with identical bytes is evidence of revalidation, not change."""
    payload = b"<act><title>Stable work</title></act>"
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                content=payload,
                headers={"Content-Type": "application/xml"},
            )
        )
    )
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=client),
    )
    target = _accounting_target("stable-work", "https://example.test/stable.xml")
    checkpoint = tmp_path / "checkpoint.json"
    manifest = tmp_path / "manifest.json"
    await service.sync_works(
        targets=[target], checkpoint_path=checkpoint, manifest_path=manifest
    )

    result = await service.sync_works(
        targets=[target],
        checkpoint_path=checkpoint,
        manifest_path=manifest,
        force_resync=True,
    )

    assert result.accounting is not None
    assert result.accounting.unchanged_revalidated == 1
    assert result.accounting.changed_preserved == 0
    assert result.accounting.total_state_records_before == 1
    assert result.accounting.total_state_records_after == 1
    assert (
        result.accounting.works[0].disposition is WorkDisposition.UNCHANGED_REVALIDATED
    )
    await client.aclose()


@pytest.mark.anyio
async def test_empty_successful_target_result_is_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A target returning neither records, errors, nor no-change fails closed."""
    service = LegislationArchiveService(store=ContentAddressedStore(tmp_path / "cas"))

    async def empty_target_result(
        *_args: object, **_kwargs: object
    ) -> tuple[
        list[object], list[str], bool, int, dict[str, dict[str, str]], list[str], int
    ]:
        return ([], [], False, 0, {}, ["success"], 0)

    monkeypatch.setattr(service, "_sync_target_manifestations", empty_target_result)
    result = await service.sync_works(
        targets=[_accounting_target("empty-work", "https://example.test/empty.xml")]
    )

    assert result.status == "success"
    assert result.accounting is not None
    assert result.accounting.failed == 1
    assert result.accounting.works[0].source_response_classifications == (
        "success",
        "empty_response",
    )


@pytest.mark.anyio
async def test_fail_fast_accounts_for_unattempted_remaining_work(
    tmp_path: Path,
) -> None:
    """Fail-fast still assigns an explicit terminal record to every scoped work."""
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        return httpx.Response(500, content=b"failed")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=client, max_retries=0, min_interval_seconds=0.0
        ),
    )
    first = _accounting_target("first-work", "https://example.test/first.xml")
    second = _accounting_target("second-work", "https://example.test/second.xml")

    result = await service.sync_works(targets=[first, second], fail_fast=True)

    assert requested_paths == ["/first.xml"]
    assert result.accounting is not None
    assert result.accounting.works_attempted == 2
    assert result.accounting.failed == 2
    assert result.accounting.works[1].work_id == "second-work"
    assert result.accounting.works[1].source_response_classifications == (
        "not_attempted_fail_fast",
    )
    await client.aclose()


@pytest.mark.anyio
async def test_manifest_commit_failure_is_indeterminate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A manifest write failure cannot be reported as committed state."""
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                content=b"<act><title>Commit work</title></act>",
                headers={"Content-Type": "application/xml"},
            )
        )
    )
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(async_client=client),
    )

    def fail_manifest_write(_path: Path, _manifest: dict[str, object]) -> None:
        message = "injected manifest failure"
        raise OSError(message)

    monkeypatch.setattr(service, "_write_manifest", fail_manifest_write)
    result = await service.sync_works(
        targets=[_accounting_target("commit-work", "https://example.test/work.xml")],
        checkpoint_path=tmp_path / "checkpoint.json",
        manifest_path=tmp_path / "manifest.json",
    )

    assert result.status == "partial"
    assert result.accounting is not None
    assert result.accounting.state_commit_status is StateCommitStatus.INDETERMINATE
    assert result.accounting.state_commit is None
    assert result.accounting.output_manifest_root is None
    assert result.accounting.output_checkpoint_root is None
    assert any("injected manifest failure" in error for error in result.errors)
    await client.aclose()


@pytest.mark.anyio
async def test_failed_capture_has_not_committed_accounting(tmp_path: Path) -> None:
    """A failed acquisition reports a deliberate non-commit, not a state root."""
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(500, content=b"failed")
        )
    )
    service = LegislationArchiveService(
        store=ContentAddressedStore(tmp_path / "cas"),
        api_client=NZLegislationApiClient(
            async_client=client, max_retries=0, min_interval_seconds=0.0
        ),
    )
    result = await service.sync_works(
        targets=[_accounting_target("failed-work", "https://example.test/fail.xml")],
        checkpoint_path=tmp_path / "checkpoint.json",
        manifest_path=tmp_path / "manifest.json",
    )

    assert result.accounting is not None
    assert result.accounting.state_commit_status is StateCommitStatus.NOT_COMMITTED
    assert result.accounting.state_commit is None
    assert result.accounting.total_state_records_before == 0
    assert result.accounting.total_state_records_after == 0
    await client.aclose()
