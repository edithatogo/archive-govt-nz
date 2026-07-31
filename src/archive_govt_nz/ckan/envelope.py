"""CKAN Action envelope and transport failure semantics."""

from dataclasses import dataclass
from typing import cast

type JsonObject = dict[str, object]

RETRYABLE_HTTP_STATUSES = frozenset({429, 500, 502, 503, 504})
HTTP_SUCCESS_MINIMUM = 200
HTTP_SUCCESS_MAXIMUM_EXCLUSIVE = 300


class CkanError(Exception):
    """Base class for bounded CKAN failures."""

    def __init__(self, error_class: str, *, retryable: bool) -> None:
        """Create a diagnostic that never retains private exception text."""
        self.error_class = error_class
        self.retryable = retryable
        super().__init__(f"CKAN request failed: {error_class}")


class CkanProtocolError(CkanError):
    """The response is not a complete CKAN Action envelope."""

    def __init__(self) -> None:
        """Create a terminal protocol error."""
        super().__init__("protocol_error", retryable=False)


class CkanActionError(CkanError):
    """CKAN returned a complete error envelope."""

    def __init__(self, error: JsonObject) -> None:
        """Create a terminal error from a validated CKAN error object."""
        self.error = error
        error_type = error.get("__type")
        self.error_type = error_type if isinstance(error_type, str) else "CKAN Error"
        super().__init__("action_error", retryable=False)


class CkanTransportError(CkanError):
    """HTTP transport status prevents accepting an Action envelope."""

    def __init__(self, status_code: int, response_document: JsonObject) -> None:
        """Create an HTTP-status failure with preserved bounded evidence."""
        self.status_code = status_code
        self.response_document = response_document
        super().__init__(
            "http_status",
            retryable=status_code in RETRYABLE_HTTP_STATUSES,
        )


class TransportFailureError(CkanError):
    """A failure raised before a complete HTTP response exists."""


@dataclass(frozen=True, slots=True)
class ActionResponse:
    """A validated successful CKAN Action response."""

    status_code: int
    result: JsonObject
    response_document: JsonObject


def interpret_action_response(
    status_code: int,
    document: object,
) -> ActionResponse:
    """Validate and classify HTTP and CKAN envelope state independently."""
    if not isinstance(document, dict):
        raise CkanProtocolError
    response_document = cast("JsonObject", document)
    success = response_document.get("success")
    if not isinstance(success, bool):
        raise CkanProtocolError

    if success:
        result = response_document.get("result")
        if not isinstance(result, dict):
            raise CkanProtocolError
        typed_result = cast("JsonObject", result)
        if not HTTP_SUCCESS_MINIMUM <= status_code < HTTP_SUCCESS_MAXIMUM_EXCLUSIVE:
            raise CkanTransportError(status_code, response_document)
        return ActionResponse(
            status_code=status_code,
            result=typed_result,
            response_document=response_document,
        )

    error = response_document.get("error")
    if not isinstance(error, dict):
        raise CkanProtocolError
    typed_error = cast("JsonObject", error)
    if not HTTP_SUCCESS_MINIMUM <= status_code < HTTP_SUCCESS_MAXIMUM_EXCLUSIVE:
        raise CkanTransportError(status_code, response_document)
    raise CkanActionError(typed_error)


def classify_transport_failure(error: BaseException) -> TransportFailureError:
    """Map an exception to a bounded diagnostic without retaining its text."""
    if isinstance(error, TimeoutError):
        return TransportFailureError("timeout", retryable=True)
    return TransportFailureError("transport_failure", retryable=False)
