"""Fail-closed selection contracts for immutable Health Bronze payloads."""

import hashlib
from io import BytesIO

import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    LossAccounting,
)

PDF = "application/pdf"
CSV = "text/csv"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SQLITE = "application/vnd.sqlite3"


class RecordingAdapter:
    """Tiny adapter fake that proves invocation and input identity."""

    def __init__(self) -> None:
        """Initialize the captured invocation list."""
        self.calls: list[tuple[bytes, str]] = []

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Record the exact supplied bytes and return an empty fixture result."""
        self.calls.append((bronze, source_sha256))
        return AdapterOutput((), (), (), "fixture/v1")


@pytest.mark.parametrize(
    ("media_type", "payload"),
    [
        (PDF, b"%PDF-1.7\n"),
        (XLSX, b"PK\x03\x04fixture"),
        (SQLITE, b"SQLite format 3\x00fixture"),
        (CSV, b"column\r\nvalue\r\n"),
    ],
)
def test_dispatch_binds_explicit_adapter_to_exact_bronze_bytes(
    media_type: str, payload: bytes
) -> None:
    if media_type == XLSX:
        workbook = Workbook()
        stream = BytesIO()
        workbook.save(stream)
        workbook.close()
        payload = stream.getvalue()
    adapter = RecordingAdapter()
    digest = hashlib.sha256(payload).hexdigest()
    result = dispatch_bronze(
        payload,
        source_sha256=digest,
        media_type=media_type,
        registrations=(AdapterRegistration("fixture", "v1", media_type, adapter),),
    )
    assert result.selection.status == "selected"
    assert result.selection.source_sha256 == digest
    assert result.selection.detected_media_type == media_type
    assert result.selection.adapter_id == "fixture"
    assert adapter.calls == [(payload, digest)]
    assert result.output.layout == "fixture/v1"


@pytest.mark.parametrize(
    ("media_type", "payload", "expected_reason"),
    [
        (PDF, b"not a pdf", "unrecognized_or_invalid_payload"),
        (PDF, b"SQLite format 3\x00fixture", "declared_media_type_mismatch"),
        (XLSX, b"PK\x03\x04not an xlsx", "unrecognized_or_invalid_payload"),
        ("application/octet-stream", b"opaque", "unrecognized_or_invalid_payload"),
        (CSV, b"\xff\xfe\x00", "unrecognized_or_invalid_payload"),
        (CSV, b"column\x00,value", "unrecognized_or_invalid_payload"),
    ],
)
def test_unknown_mismatch_and_invalid_payloads_are_preserved_only(
    media_type: str, payload: bytes, expected_reason: str
) -> None:
    adapter = RecordingAdapter()
    registrations = (
        ()
        if media_type not in {PDF, CSV, XLSX, SQLITE}
        else (AdapterRegistration("fixture", "v1", media_type, adapter),)
    )
    result = dispatch_bronze(
        payload,
        source_sha256=hashlib.sha256(payload).hexdigest(),
        media_type=media_type,
        registrations=registrations,
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.reason == expected_reason
    assert result.selection.adapter_id is None
    assert result.output.records == ()
    assert result.output.lineage == ()
    assert result.output.losses == (
        LossAccounting(
            "bronze:sha256:" + hashlib.sha256(payload).hexdigest(),
            "preserved_only",
            expected_reason,
        ),
    )
    assert adapter.calls == []


def test_missing_or_ambiguous_selection_never_chooses_by_registration_order() -> None:
    payload = b"%PDF-1.7\n"
    digest = hashlib.sha256(payload).hexdigest()
    first = RecordingAdapter()
    second = RecordingAdapter()
    for rows in (
        (),
        (
            AdapterRegistration("first", "v1", PDF, first),
            AdapterRegistration("second", "v1", PDF, second),
        ),
    ):
        result = dispatch_bronze(
            payload, source_sha256=digest, media_type=PDF, registrations=rows
        )
        assert result.selection.status == "preserved_only"
        assert result.selection.reason in {
            "no_registered_adapter",
            "adapter_selection_ambiguous",
        }
    assert first.calls == []
    assert second.calls == []


def test_multiple_layouts_require_probes_and_select_exactly_one_match() -> None:
    payload = b"%PDF-1.7\nlayout-a"
    digest = hashlib.sha256(payload).hexdigest()
    first = RecordingAdapter()
    second = RecordingAdapter()
    rows = (
        AdapterRegistration(
            "first", "v1", PDF, first, layout_probe=lambda data: b"layout-a" in data
        ),
        AdapterRegistration(
            "second", "v1", PDF, second, layout_probe=lambda data: b"layout-b" in data
        ),
    )

    result = dispatch_bronze(
        payload, source_sha256=digest, media_type=PDF, registrations=rows
    )

    assert result.selection.status == "selected"
    assert result.selection.adapter_id == "first"
    assert result.selection.considered_adapter_ids == ("first", "second")
    assert result.selection.matched_adapter_ids == ("first",)
    assert first.calls == [(payload, digest)]
    assert second.calls == []


def test_single_layout_probe_is_recorded_in_selection() -> None:
    payload = b"%PDF-1.7\nknown"
    digest = hashlib.sha256(payload).hexdigest()
    adapter = RecordingAdapter()
    result = dispatch_bronze(
        payload,
        source_sha256=digest,
        media_type=PDF,
        registrations=(
            AdapterRegistration(
                "known",
                "v1",
                PDF,
                adapter,
                layout_probe=lambda data: b"known" in data,
            ),
        ),
    )
    assert result.selection.adapter_id == "known"
    assert result.selection.considered_adapter_ids == ("known",)
    assert result.selection.matched_adapter_ids == ("known",)


def test_layout_probe_must_return_a_real_boolean() -> None:
    payload = b"%PDF-1.7\nknown"
    with pytest.raises(TypeError, match="invalid_layout_probe_result"):
        dispatch_bronze(
            payload,
            source_sha256=hashlib.sha256(payload).hexdigest(),
            media_type=PDF,
            registrations=(
                AdapterRegistration(
                    "known",
                    "v1",
                    PDF,
                    RecordingAdapter(),
                    layout_probe=lambda _data: 1,  # type: ignore[return-value]
                ),
            ),
        )


@pytest.mark.parametrize(
    ("payload", "expected_reason", "matches"),
    [
        (b"%PDF-1.7\nunknown", "no_matching_layout", ()),
        (b"%PDF-1.7\nambiguous", "adapter_selection_ambiguous", ("first", "second")),
    ],
)
def test_multiple_layout_probes_fail_closed(
    payload: bytes, expected_reason: str, matches: tuple[str, ...]
) -> None:
    first = RecordingAdapter()
    second = RecordingAdapter()
    rows = (
        AdapterRegistration(
            "first",
            "v1",
            PDF,
            first,
            layout_probe=lambda data: b"unknown" not in data or b"ambiguous" in data,
        ),
        AdapterRegistration(
            "second",
            "v1",
            PDF,
            second,
            layout_probe=lambda data: b"ambiguous" in data,
        ),
    )
    result = dispatch_bronze(
        payload,
        source_sha256=hashlib.sha256(payload).hexdigest(),
        media_type=PDF,
        registrations=rows,
    )
    assert result.selection.status == "preserved_only"
    assert result.selection.reason == expected_reason
    assert result.selection.matched_adapter_ids == matches
    assert first.calls == []
    assert second.calls == []


def test_payload_fixity_is_checked_before_adapter_runs() -> None:
    adapter = RecordingAdapter()
    with pytest.raises(ValueError, match=r"^source_hash_mismatch$"):
        dispatch_bronze(
            b"%PDF-1.7\n",
            source_sha256="0" * 64,
            media_type=PDF,
            registrations=(AdapterRegistration("pdf", "v1", PDF, adapter),),
        )
    assert adapter.calls == []


def test_duplicate_registration_identity_is_rejected() -> None:
    payload = b"%PDF-1.7\n"
    adapter = RecordingAdapter()
    row = AdapterRegistration("pdf", "v1", PDF, adapter)
    with pytest.raises(ValueError, match=r"^invalid_adapter_registration$"):
        dispatch_bronze(
            payload,
            source_sha256=hashlib.sha256(payload).hexdigest(),
            media_type=PDF,
            registrations=(row, row),
        )


@pytest.mark.parametrize(
    ("bronze", "source_sha256", "registrations", "error"),
    [
        (b"x", "invalid", (), "invalid_source_sha256"),
        (b"x", hashlib.sha256(b"x").hexdigest(), [], "registrations_tuple_required"),
        (
            b"x",
            hashlib.sha256(b"x").hexdigest(),
            (object(),),
            "invalid_adapter_registration",
        ),
    ],
)
def test_invalid_dispatch_inputs_fail_before_selection(
    bronze: bytes,
    source_sha256: str,
    registrations: object,
    error: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=f"^{error}$"):
        dispatch_bronze(
            bronze,
            source_sha256=source_sha256,
            media_type=PDF,
            registrations=registrations,  # type: ignore[arg-type]
        )


def test_non_bytes_payload_is_rejected() -> None:
    with pytest.raises(TypeError, match=r"^bronze_bytes_required$"):
        dispatch_bronze(
            None,  # type: ignore[arg-type]
            source_sha256="0" * 64,
            media_type=PDF,
            registrations=(),
        )


def test_adapter_must_return_typed_output() -> None:
    class InvalidAdapter:
        """A malformed adapter return for output-boundary coverage."""

        def extract(self, bronze: bytes, *, source_sha256: str) -> object:
            """Return an invalid object deliberately."""
            _ = bronze, source_sha256
            return object()

    payload = b"%PDF-1.7\n"
    with pytest.raises(TypeError, match=r"^invalid_adapter_output$"):
        dispatch_bronze(
            payload,
            source_sha256=hashlib.sha256(payload).hexdigest(),
            media_type=PDF,
            registrations=(AdapterRegistration("pdf", "v1", PDF, InvalidAdapter()),),  # type: ignore[arg-type]
        )
