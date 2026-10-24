"""Actual common overview output and externally pinned readback contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import pytest
from jsonschema import ValidationError
from tests.domains.health_appropriations.test_reviewed_overview_adapters import (
    OBSERVED_AT,
    _adapter_fixture,
)

from archive_govt_nz.domains.health_appropriations import (
    overview_operations as operations,
)
from archive_govt_nz.domains.health_appropriations import (
    source_operations,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_overview_adapter as adapters,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    DispatchResult,
    dispatch_bronze,
)


@pytest.fixture
def fixture_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> source_operations.SourceRequest:
    adapter, payload = _adapter_fixture(monkeypatch)
    adapter = replace(adapter, source_locator="https://example.test/source.pdf")
    registration = adapters.vote_health_estimates_overview_registration(
        source_locator=adapter.source_locator,
        source_vintage=adapter.source_vintage,
        observed_at=adapter.observed_at,
    )
    registration = replace(
        registration, adapter=adapter, layout_probe=adapter.matches_layout
    )
    monkeypatch.setattr(
        adapters, "reviewed_overview_profile", lambda _vintage: adapter.profile
    )
    monkeypatch.setattr(
        adapters,
        "vote_health_estimates_overview_registration",
        lambda **_kwargs: registration,
    )
    monkeypatch.setitem(
        source_operations._VOTE_HEALTH_OVERVIEW_PROFILES,  # noqa: SLF001
        adapter.profile.profile,
        (adapter.profile.vintage, adapter.profile.source_sha256),
    )
    source = tmp_path / "source.pdf"
    source.write_bytes(payload)
    return source_operations.SourceRequest(
        source,
        tmp_path / "output",
        adapter.profile.profile,
        adapter.profile.source_sha256,
        adapter.source_vintage,
        "https://example.test/source.pdf",
        OBSERVED_AT,
    )


def _run(
    request: source_operations.SourceRequest, *, dry_run: bool = False
) -> dict[str, Any]:
    return operations.normalize_overview(
        request.source,
        request.output_dir,
        profile=request.profile,
        expected_sha256=request.expected_sha256,
        source_vintage=request.source_vintage,
        source_locator=request.source_locator,
        observed_at=request.observed_at,
        dry_run=dry_run,
    )


def _verify(request: source_operations.SourceRequest, pin: str) -> dict[str, Any]:
    return operations.verify_overview(
        request.source,
        request.output_dir,
        manifest_sha256=pin,
        profile=request.profile,
        expected_sha256=request.expected_sha256,
        source_vintage=request.source_vintage,
        source_locator=request.source_locator,
        observed_at=request.observed_at,
    )


def _pin(request: source_operations.SourceRequest) -> str:
    return hashlib.sha256(
        (request.output_dir / "MANIFEST.json").read_bytes()
    ).hexdigest()


def test_operation_consumes_common_output_and_preserves_public_receipt(
    fixture_request: source_operations.SourceRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = fixture_request

    # The common adapter result is the only extraction route.
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("direct normalizer used instead of common dispatch output")

    monkeypatch.setattr(
        source_operations.vote_health_estimates_summary,
        "_normalize_overview",
        forbidden,
    )
    observed: list[DispatchResult] = []

    def traced(
        bronze: bytes,
        *,
        source_sha256: str,
        media_type: str,
        registrations: tuple[AdapterRegistration, ...],
    ) -> DispatchResult:
        result = dispatch_bronze(
            bronze,
            source_sha256=source_sha256,
            media_type=media_type,
            registrations=registrations,
        )
        observed.append(result)
        return result

    monkeypatch.setattr(operations, "dispatch_bronze", traced)
    receipt = source_operations.operate_source(request, dry_run=True)
    assert receipt["status"] == "preflight_passed"
    assert not request.output_dir.exists()
    receipt = source_operations.operate_source(request, dry_run=False)
    assert receipt["status"] == "written_local"
    assert set(receipt["output_sha256"]) == {
        "vote_health_overview_facts.parquet",
        "field_lineage.parquet",
        "page_dispositions.parquet",
    }
    assert "adapter_selection" not in receipt
    assert "manifest_sha256" not in receipt
    assert observed
    facts = pq.read_table(
        request.output_dir / "vote_health_overview_facts.parquet"
    ).to_pylist()
    assert facts == list(observed[-1].output.records)
    manifest = _verify(request, _pin(request))
    assert manifest["adapter_selection"] == observed[-1].selection.to_receipt()
    assert manifest["common_losses"][0]["disposition"] == "preserved_only"
    assert (
        pq.read_table(request.output_dir / "page_dispositions.parquet")["disposition"][
            0
        ].as_py()
        == "preserved_unreviewed"
    )
    assert request.source.read_bytes().startswith(b"%PDF-")


@pytest.mark.parametrize(
    "mutation",
    [
        "selection",
        "selection_digest",
        "loss",
        "schema",
        "extra",
        "output",
        "forged_output",
        "missing",
        "context",
        "pin",
    ],
)
def test_readback_rejects_tampering_and_partial_outputs(  # noqa: C901 - explicit tamper cases
    fixture_request: source_operations.SourceRequest, mutation: str
) -> None:
    request = fixture_request
    _run(request)
    pin = _pin(request)
    manifest_path = request.output_dir / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_bytes())
    if mutation == "selection":
        manifest["adapter_selection"]["adapter"]["version"] = "unsupported"
    elif mutation == "selection_digest":
        manifest["adapter_selection"]["receipt_sha256"] = "0" * 64
    elif mutation == "loss":
        manifest["common_losses"][0]["reason"] = "silently changed"
    elif mutation == "forged_output":
        payload = b"wrong bytes with a matching manifest digest"
        (request.output_dir / "field_lineage.parquet").write_bytes(payload)
        manifest["output_sha256"]["field_lineage.parquet"] = hashlib.sha256(
            payload
        ).hexdigest()
    elif mutation == "schema":
        manifest["schema_version"] = "unknown/v2"
    elif mutation == "extra":
        (request.output_dir / "unbound.json").write_text("{}")
    elif mutation == "output":
        (request.output_dir / "field_lineage.parquet").write_bytes(b"tampered")
    elif mutation == "missing":
        manifest_path.unlink()
    elif mutation == "context":
        request = replace(request, source_locator="https://example.test/wrong.pdf")
    else:
        pin = "0" * 64
    if mutation in {"selection", "selection_digest", "loss", "forged_output", "schema"}:
        # A caller who re-pins malformed metadata still cannot evade semantics.
        manifest_path.write_text(json.dumps(manifest))
        pin = _pin(request)
    with pytest.raises((ValueError, OSError, ValidationError)):
        _verify(request, pin)


def test_interrupted_write_is_not_reusable_or_overwritten(
    fixture_request: source_operations.SourceRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = fixture_request
    original = operations.write_workbook_outputs

    def interrupt(output: Path, _tables: object, _receipt: object) -> None:
        output.mkdir()
        (output / "field_lineage.parquet").write_bytes(b"partial")
        raise KeyboardInterrupt

    monkeypatch.setattr(operations, "write_workbook_outputs", interrupt)
    with pytest.raises(KeyboardInterrupt):
        _run(request)
    assert not (request.output_dir / "MANIFEST.json").exists()
    with pytest.raises(FileNotFoundError):
        _verify(request, "0" * 64)
    monkeypatch.setattr(operations, "write_workbook_outputs", original)
    with pytest.raises(ValueError, match="invalid_overview_operation"):
        _run(request)
    assert (request.output_dir / "field_lineage.parquet").read_bytes() == b"partial"


def test_symlinked_output_parent_is_rejected_before_any_write(
    fixture_request: source_operations.SourceRequest, tmp_path: Path
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlinks unavailable: {error}")
    request = replace(fixture_request, output_dir=alias / "output")
    with pytest.raises(ValueError, match="invalid_overview_operation"):
        _run(request)
    assert list(target.iterdir()) == []
