"""CKAN Action API envelope and transport classification contracts."""

import pytest
from archive_govt_nz.ckan.envelope import (
    CkanActionError,
    CkanProtocolError,
    CkanTransportError,
    classify_transport_failure,
    interpret_action_response,
)


def test_success_envelope_is_independent_of_http_transport_metadata() -> None:
    """A valid successful Action envelope exposes its result and status."""
    response = interpret_action_response(
        200,
        {"success": True, "result": {"ckan_version": "2.10.9"}},
    )

    assert response.status_code == 200
    assert response.result == {"ckan_version": "2.10.9"}


def test_error_envelope_on_http_200_is_an_action_failure() -> None:
    """CKAN's success flag remains authoritative inside a successful HTTP response."""
    with pytest.raises(CkanActionError) as raised:
        interpret_action_response(
            200,
            {
                "success": False,
                "error": {"__type": "Validation Error", "name": ["Missing value"]},
            },
        )

    assert raised.value.retryable is False
    assert raised.value.error_type == "Validation Error"


@pytest.mark.parametrize("status_code", [429, 500, 502, 503, 504])
def test_retryable_http_status_preserves_ckan_envelope(status_code: int) -> None:
    """Transient transport status wins while retaining parsed CKAN evidence."""
    document = {
        "success": False,
        "error": {"__type": "Service Error", "message": "bounded failure"},
    }

    with pytest.raises(CkanTransportError) as raised:
        interpret_action_response(status_code, document)

    assert raised.value.retryable is True
    assert raised.value.status_code == status_code
    assert raised.value.response_document == document


def test_terminal_non_200_is_not_silently_retried() -> None:
    """A terminal transport response has an explicit non-retryable outcome."""
    with pytest.raises(CkanTransportError) as raised:
        interpret_action_response(
            404,
            {"success": False, "error": {"__type": "Not Found Error"}},
        )

    assert raised.value.retryable is False


@pytest.mark.parametrize(
    "document",
    [
        None,
        [],
        {},
        {"success": "yes", "result": {}},
        {"success": True},
        {"success": False},
    ],
)
def test_malformed_envelopes_fail_as_protocol_errors(document: object) -> None:
    """Malformed or incomplete Action documents never become successful results."""
    with pytest.raises(CkanProtocolError):
        interpret_action_response(200, document)


def test_timeout_is_classified_as_retryable_without_exposing_payload() -> None:
    """A bounded timeout maps to a stable retryable diagnostic."""
    failure = classify_transport_failure(TimeoutError("private upstream detail"))

    assert failure.error_class == "timeout"
    assert failure.retryable is True
    assert "private upstream detail" not in str(failure)


def test_unclassified_transport_failure_is_terminal() -> None:
    """Unknown failures default closed rather than entering an unsafe retry loop."""
    failure = classify_transport_failure(RuntimeError("private detail"))

    assert failure.error_class == "transport_failure"
    assert failure.retryable is False
    assert "private detail" not in str(failure)
