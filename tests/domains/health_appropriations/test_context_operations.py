"""Context operations consume common evidence and preserve native table bytes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from dataclasses import asdict, replace
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

import pytest
from tests.domains.health_appropriations.test_cpi import HEADER, META
from tests.domains.health_appropriations.test_gdp import workbook
from tests.domains.health_appropriations.test_population_annual_export import payload
from tests.domains.health_appropriations.test_qes import fixture

from archive_govt_nz.domains.health_appropriations import (
    context_operations as operations,
)
from archive_govt_nz.domains.health_appropriations import (
    cpi,
    gdp,
    population_annual_silver,
    qes,
    source_operations,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import encode_json

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
        AdapterRegistration,
        DispatchResult,
    )

PROFILES = (
    ("cpiq-se9a/v1", "Stats-NZ-CPI-2026-Q2", cpi, "normalize_cpi"),
    (
        "population-annual-mean-context/v1",
        "2026-08-18",
        population_annual_silver,
        "normalize_population_annual",
    ),
    ("qes-june2026-table8/v1", "QES-2026-Q2", qes, "normalize_qes"),
    ("gdp-expenditure-actual-2026q1/v1", gdp.VINTAGE, gdp, "normalize_gdp"),
    ("gdp-expenditure-actual-2026q2/v1", gdp.JUNE_VINTAGE, gdp, "normalize_gdp"),
)


def _request(
    tmp_path: Path, profile: str, vintage: str
) -> source_operations.SourceRequest:
    source = tmp_path / "source"
    if profile.startswith("cpi"):
        source.write_text(
            HEADER
            + "CPIQ.SE9A,1914.06,1.25"
            + META
            + "CPIQ.SE9A,1914.09,NA"
            + META
            + "OTHER,2026.06,0"
            + META
        )
    elif profile.startswith("population"):
        source.write_bytes(payload())
    elif profile.startswith("qes"):
        fixture(source)
    else:
        workbook(source, vintage)
    return source_operations.SourceRequest(
        source,
        tmp_path / "output",
        profile,
        hashlib.sha256(source.read_bytes()).hexdigest(),
        vintage,
        "https://example.test/context",
        "2026-10-17T00:00:00Z",
    )


def _context(request: source_operations.SourceRequest) -> dict[str, Any]:
    return {
        name: getattr(request, name)
        for name in (
            "expected_sha256",
            "source_vintage",
            "source_locator",
            "observed_at",
        )
    }


def _pin(directory: Path) -> str:
    return hashlib.sha256((directory / "MANIFEST.json").read_bytes()).hexdigest()


def test_versioned_drift_manifest_preserves_v1_and_verifies_exact_evidence(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path, *PROFILES[0][:2])
    kwargs = {"profile": request.profile, **_context(request)}
    legacy = operations.normalize_context(
        request.source, request.output_dir, **kwargs, dry_run=False
    )
    assert legacy["schema_version"].endswith("/v1")
    assert "adapter_drift" not in legacy
    revised = tmp_path / "drift"
    result = operations.normalize_context(
        request.source, revised, **kwargs, dry_run=False, include_drift=True
    )
    assert result["schema_version"].endswith("/v2")
    assert result["adapter_drift"]["selection"] == result["adapter_selection"]
    repeat = tmp_path / "repeat-drift"
    assert (
        operations.normalize_context(
            request.source, repeat, **kwargs, dry_run=False, include_drift=True
        )
        == result
    )
    assert _pin(repeat) == _pin(revised)
    assert (
        operations.verify_context(
            request.source,
            revised,
            **kwargs,
            manifest_sha256=_pin(revised),
            include_drift=True,
        )
        == result
    )
    with pytest.raises(ValueError, match="source_byte_limit"):
        operations.verify_context(
            request.source, revised, **kwargs, manifest_sha256=_pin(revised)
        )
    manifest_path = revised / "MANIFEST.json"
    forged = json.loads(manifest_path.read_bytes())
    forged["adapter_drift"]["ordered_output_sha256"] = "0" * 64
    manifest_path.write_text(encode_json(forged) + "\n")
    with pytest.raises(ValueError, match="invalid_context_operation"):
        operations.verify_context(
            request.source,
            revised,
            **kwargs,
            manifest_sha256=_pin(revised),
            include_drift=True,
        )


@pytest.mark.parametrize(("profile", "vintage", "native", "method"), PROFILES)
def test_actual_common_output_native_parity_and_repeat(  # noqa: PLR0913, PLR0917 - five profile contracts
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    profile: str,
    vintage: str,
    native: ModuleType,
    method: str,
) -> None:
    request = _request(tmp_path, profile, vintage)
    reference = tmp_path / "native"
    native_receipt = getattr(native, method)(
        request.source, reference, **_context(request), dry_run=False
    )
    traced: list[DispatchResult] = []
    dispatch = operations.dispatch_bronze

    def observe(
        bronze: bytes,
        *,
        source_sha256: str,
        media_type: str,
        registrations: tuple[AdapterRegistration, ...],
    ) -> DispatchResult:
        result = dispatch(
            bronze,
            source_sha256=source_sha256,
            media_type=media_type,
            registrations=registrations,
        )
        traced.append(result)
        return result

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("filesystem native normalizer used by common operation")

    monkeypatch.setattr(operations, "dispatch_bronze", observe)
    monkeypatch.setattr(native, method, forbidden)
    assert source_operations.operate_source(request)["status"] == "preflight_passed"
    assert not request.output_dir.exists()
    receipt = source_operations.operate_source(request, dry_run=False)
    assert receipt["status"] == "written_local"
    assert receipt["counts"] == native_receipt["counts"]
    assert "manifest_sha256" not in receipt
    for path in reference.glob("*.parquet"):
        assert (request.output_dir / path.name).read_bytes() == path.read_bytes()
    manifest = operations.verify_context(
        request.source,
        request.output_dir,
        profile=profile,
        manifest_sha256=_pin(request.output_dir),
        **_context(request),
    )
    assert manifest["common_output"] == json.loads(
        encode_json(asdict(traced[-1].output))
    )
    assert manifest["adapter_selection"] == traced[-1].selection.to_receipt()
    assert manifest["common_output"]["dimensions"]
    assert all(
        item["target"] is None for item in manifest["common_output"]["dimensions"]
    )
    if profile.startswith("population"):
        assert len(manifest["common_output"]["lineage"]) == 108
        assert manifest["counts"]["lineage"] == 72
        assert manifest["common_output"]["records"][0]["denominator_selected"] is False
    if vintage == gdp.JUNE_VINTAGE:
        assert manifest["common_output"]["layout"] == gdp.TRANSFORMATION
        assert manifest["transformation_id"] == gdp.JUNE_TRANSFORMATION
    repeat = replace(request, output_dir=tmp_path / "repeat")
    assert source_operations.operate_source(repeat, dry_run=False) == receipt
    assert _pin(repeat.output_dir) == _pin(request.output_dir)


@pytest.mark.parametrize(
    "field",
    ["records", "lineage", "losses", "dimensions", "dimension_links", "selection"],
)
def test_changed_common_evidence_is_rejected_before_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    request = _request(tmp_path, *PROFILES[0][:2])
    dispatch = operations.dispatch_bronze

    def changed(
        bronze: bytes,
        *,
        source_sha256: str,
        media_type: str,
        registrations: tuple[AdapterRegistration, ...],
    ) -> DispatchResult:
        result = dispatch(
            bronze,
            source_sha256=source_sha256,
            media_type=media_type,
            registrations=registrations,
        )
        if field == "selection":
            return replace(
                result, selection=replace(result.selection, schema_version="unknown/v1")
            )
        return replace(result, output=replace(result.output, **{field: ()}))

    monkeypatch.setattr(operations, "dispatch_bronze", changed)
    assert (
        source_operations.operate_source(request, dry_run=False)["status"] == "failed"
    )
    assert not request.output_dir.exists()


@pytest.mark.parametrize(
    "mutation", ["common", "extra", "table", "missing", "pin", "duplicate"]
)
def test_independent_readback_rejects_tampering(tmp_path: Path, mutation: str) -> None:
    request = _request(tmp_path, *PROFILES[0][:2])
    assert (
        source_operations.operate_source(request, dry_run=False)["status"]
        == "written_local"
    )
    path = request.output_dir / "MANIFEST.json"
    pin = _pin(request.output_dir)
    if mutation == "common":
        value = json.loads(path.read_text())
        value["common_output"]["records"][0]["amount"] = "0"
        path.write_text(encode_json(value) + "\n")
        pin = _pin(request.output_dir)
    elif mutation == "extra":
        (request.output_dir / "unexpected").write_bytes(b"extra")
    elif mutation == "table":
        (request.output_dir / "cpi_facts.parquet").write_bytes(b"forged")
    elif mutation == "missing":
        (request.output_dir / "field_lineage.parquet").unlink()
    elif mutation == "duplicate":
        path.write_text(path.read_text().replace("{", '{"status":"passed",', 1))
        pin = _pin(request.output_dir)
    else:
        pin = "0" * 64
    with pytest.raises((ValueError, OSError)):
        operations.verify_context(
            request.source,
            request.output_dir,
            profile=request.profile,
            manifest_sha256=pin,
            **_context(request),
        )
    assert (
        source_operations.operate_source(request, dry_run=False)["status"] == "failed"
    )


def test_refuses_symlink_ancestors_and_interrupted_output(tmp_path: Path) -> None:
    request = _request(tmp_path, *PROFILES[0][:2])
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    linked = replace(request, output_dir=link / "output")
    assert source_operations.operate_source(linked, dry_run=False)["status"] == "failed"
    assert not linked.output_dir.exists()
    request.output_dir.mkdir()
    (request.output_dir / "field_lineage.parquet").write_bytes(b"interrupted")
    assert (
        source_operations.operate_source(request, dry_run=False)["status"] == "failed"
    )
    assert not (request.output_dir / "MANIFEST.json").exists()


def test_interrupted_write_is_never_repaired_or_verified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(tmp_path, *PROFILES[0][:2])

    def interrupted(
        output: Path, *_args: object, **_kwargs: object
    ) -> dict[str, object]:
        output.mkdir()
        (output / "cpi_facts.parquet").write_bytes(b"partial")
        message = "injected write interruption"
        raise OSError(message)

    monkeypatch.setattr(operations, "write_workbook_outputs", interrupted)
    assert (
        source_operations.operate_source(request, dry_run=False)["status"] == "failed"
    )
    assert not (request.output_dir / "MANIFEST.json").exists()
    with pytest.raises(
        ValueError, match=r"invalid_context_operation|source_hash_mismatch"
    ):
        operations.verify_context(
            request.source,
            request.output_dir,
            profile=request.profile,
            manifest_sha256="a" * 64,
            **_context(request),
        )
    assert (
        source_operations.operate_source(request, dry_run=False)["status"] == "failed"
    )
    assert (request.output_dir / "cpi_facts.parquet").read_bytes() == b"partial"


def test_population_boolean_is_not_an_integer_in_authenticated_metadata(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path, *PROFILES[1][:2])
    assert (
        source_operations.operate_source(request, dry_run=False)["status"]
        == "written_local"
    )
    path = request.output_dir / "MANIFEST.json"
    manifest = json.loads(path.read_text())
    manifest["common_output"]["records"][0]["denominator_selected"] = 0
    path.write_text(encode_json(manifest) + "\n")
    with pytest.raises(
        ValueError, match=r"invalid_context_operation|source_hash_mismatch"
    ):
        operations.verify_context(
            request.source,
            request.output_dir,
            profile=request.profile,
            manifest_sha256=_pin(request.output_dir),
            **_context(request),
        )


@pytest.mark.parametrize("changed", ["hash", "vintage", "profile", "observation"])
def test_readback_binds_exact_source_context(tmp_path: Path, changed: str) -> None:
    request = _request(tmp_path, *PROFILES[0][:2])
    assert (
        source_operations.operate_source(request, dry_run=False)["status"]
        == "written_local"
    )
    options = {**_context(request), "profile": request.profile}
    key, value = {
        "hash": ("expected_sha256", "a" * 64),
        "vintage": ("source_vintage", "2026-Q3"),
        "profile": ("profile", "unknown/v1"),
        "observation": ("observed_at", "2026-10-17T00:00:00+00:00"),
    }[changed]
    options[key] = value
    with pytest.raises(
        ValueError, match=r"invalid_context_operation|source_hash_mismatch"
    ):
        operations.verify_context(
            request.source,
            request.output_dir,
            manifest_sha256=_pin(request.output_dir),
            **options,
        )


def test_readback_bounds_directory_membership(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(tmp_path, *PROFILES[0][:2])
    assert (
        source_operations.operate_source(request, dry_run=False)["status"]
        == "written_local"
    )
    pin = _pin(request.output_dir)
    original = Path.iterdir

    def entries(path: Path) -> Iterator[Path]:
        yield from original(path)
        if path == request.output_dir:
            yield path / "unexpected"
            pytest.fail("operation readback scanned past the first extra entry")

    monkeypatch.setattr(Path, "iterdir", entries)
    with pytest.raises(ValueError, match="invalid_context_operation"):
        operations.verify_context(
            request.source,
            request.output_dir,
            manifest_sha256=pin,
            profile=request.profile,
            **_context(request),
        )
