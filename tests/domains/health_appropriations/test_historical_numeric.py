"""Inert OOXML lexical parsing and exact decimal boundaries."""

from decimal import Decimal
from io import BytesIO
from typing import Any
from zipfile import ZipFile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations.historical import (
    _exact_amount,
    _number_tokens,
)


def _package(  # noqa: PLR0913 - independent XML attack fixture dimensions
    *,
    target: str = "worksheets/sheet1.xml",
    mode: str = "",
    cells: str = '<c r="A1"><v>605.70000000000005</v></c>',
    sheets: str = '<sheet name="Spending" r:id="rId1"/>',
    duplicate: bool = False,
    dtd: bool = False,
) -> bytes:
    relation = f'<Relationship Id="rId1" Target="{target}" {mode}/>'
    workbook = f'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>{sheets}</sheets></workbook>'
    if dtd:
        workbook = '<!DOCTYPE workbook [<!ENTITY x "expanded">]>' + workbook
    output = BytesIO()
    with ZipFile(output, "w") as package:
        package.writestr(
            "xl/_rels/workbook.xml.rels",
            f"<Relationships>{relation}{relation if duplicate else ''}</Relationships>",
        )
        package.writestr(
            "xl/workbook.xml", workbook.encode("utf-16") if dtd else workbook.encode()
        )
        package.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row>{cells}</row></sheetData></worksheet>',
        )
    return output.getvalue()


@pytest.mark.parametrize(
    "target", ["worksheets/sheet1.xml", "/xl/worksheets/sheet1.xml"]
)
def test_literal_tokens_and_inert_formula_caches(target: str) -> None:
    cells = '<c r="A1"><v>605.70000000000005</v></c><c r="B1"><f>1+1</f><v>2</v></c><c r="C1"><v/></c><c r="D1"/><c r="E1" t="b"><v>1</v></c>'
    assert _number_tokens(_package(target=target, cells=cells)) == {
        "Spending": {"A1": "605.70000000000005"}
    }


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"duplicate": True}, "duplicate_sheet_relationship"),
        ({"mode": 'TargetMode="External"'}, "unsupported_sheet_relationship"),
        ({"target": "../outside.xml"}, "unsupported_sheet_relationship"),
        ({"cells": '<c r="A1"/><c r="A1"/>'}, "ambiguous_source_cell"),
        ({"cells": '<c r="a1"/>'}, "ambiguous_source_cell"),
        ({"cells": '<c r="A1"><v>1</v><v>2</v></c>'}, "ambiguous_source_value"),
        ({"sheets": '<sheet name="" r:id="rId1"/>'}, "ambiguous_sheet_name"),
        (
            {"sheets": '<sheet name="A" r:id="rId1"/><sheet name="A" r:id="rId1"/>'},
            "ambiguous_sheet_name",
        ),
        ({"dtd": True}, "xml_doctype_forbidden"),
    ],
)
def test_ambiguous_and_active_xml_rejected(kwargs: dict[str, Any], reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        _number_tokens(_package(**kwargs))


@pytest.mark.parametrize(
    "value", ["x", "NaN", "Infinity", "1e21", "1e-18", "9" * 129, "1e" + "9" * 40]
)
def test_unrepresentable_numbers_are_not_rounded(value: str) -> None:
    assert _exact_amount(value) is None


@pytest.mark.parametrize(
    "value", ["0", "-0", "-1.25", "1e-17", "999999999999999999999.99999999999999999"]
)
def test_exact_decimal_boundaries(value: str) -> None:
    assert _exact_amount(value) == Decimal(value)


@given(
    st.integers(min_value=-(10**10), max_value=10**10),
    st.integers(min_value=0, max_value=10**17 - 1),
)
@settings(max_examples=40, deadline=None)
def test_generated_exact_decimal_values(whole: int, fraction: int) -> None:
    literal = f"{whole}.{fraction:017d}"
    assert _exact_amount(literal) == Decimal(literal)
