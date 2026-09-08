"""Contract tests for the shared health adapter boundary."""

import pytest

from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    FieldLineage,
    HealthAdapter,
    LossAccounting,
    preserved_only,
)


def test_preserved_only_is_empty_and_explicit() -> None:
    result = preserved_only(
        source_coordinate="sheet:Unknown!A1", reason="unknown_layout"
    )
    assert result.records == ()
    assert result.layout == "unknown"
    assert result.losses == (
        LossAccounting("sheet:Unknown!A1", "preserved_only", "unknown_layout"),
    )
    assert result.lineage == ()


def test_lineage_is_structured_and_adapter_protocol_is_runtime_checkable_by_shape() -> (
    None
):
    lineage = FieldLineage("record:1", "amount", "A1", "1.00", "1.00", "decimal/v1")
    assert lineage.field == "amount"
    assert hasattr(HealthAdapter, "extract")


@pytest.mark.parametrize(("coordinate", "reason"), [("", "unknown"), ("A1", "")])
def test_preserved_only_rejects_unlocated_or_unexplained_loss(
    coordinate: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=r"^invalid_preserved_only_loss$"):
        preserved_only(source_coordinate=coordinate, reason=reason)
