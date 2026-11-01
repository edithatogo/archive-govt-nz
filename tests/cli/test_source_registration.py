"""Public source registration command receipt and diagnostic contracts."""

import json
from typing import Literal

import pytest

from archive_govt_nz.cli import source_register


@pytest.mark.parametrize("output", ["json", "text"])
@pytest.mark.parametrize(
    "case",
    [
        ("web://agency/source", "active", "{}", "validated"),
        ("web://agency/source", "active", "{", "invalid_metadata"),
        ("web://agency/source", "absent", "{}", "invalid_status"),
        ("https://example.com", "active", "{}", "validation_failed"),
    ],
)
def test_registration_reports_validation(
    capsys: pytest.CaptureFixture[str],
    output: Literal["json", "text"],
    case: tuple[str, str, str, str],
) -> None:
    """Distinguish validation success from malformed input in both output modes."""
    uri, status, metadata, expected = case
    code = source_register(
        "sample", uri, "web", "agency", status=status, metadata=metadata, format=output
    )
    success = expected == "validated"
    assert code == (0 if success else 2)
    rendered = capsys.readouterr().out
    if output == "json":
        payload = json.loads(rendered)
        assert payload["status"] == expected
        if success:
            assert payload["manifest"]["source_uri"] == uri
        else:
            assert payload["error"]
    else:
        assert rendered.startswith("Source validated:" if success else "Error:")
