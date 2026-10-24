"""Source-native Budget Silver with exact BIFF8 stored-integer evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from openpyxl.utils.cell import get_column_letter

from archive_govt_nz.domains.health_appropriations import (
    biff8_projection,
    biff8_records,
    budget_expenditure_2020,
    budget_expenditure_2024,
    budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    exact_number,
    identity,
    source_context,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

SCHEMA_VERSION = "archive-govt-nz.health-budget-biff8-extraction/v1"
MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 16384
_DEFINITION_COLUMN = 2
_SOURCE_QUALIFIER_EDITION = 2014
_UNLABELLED_COLUMN_EDITION = 2011
_UNLABELLED_COLUMN_COUNT = 13
_UNSCALED_EDITIONS = (2007, 2008, 2009)
_SOURCE_PARENT_IDENTIFIER_EDITION = 2010
_NO_SCOPE_EXPENDITURE_EDITIONS = (2010, 2011)
_REVENUE_DEPENDENT_EDITIONS = (2010, 2011)
_LEGACY_DIMENSION_EDITIONS = (2010, 2011, 2012, 2013)
PERIOD_TYPES = {
    2015: "Actuals",
    2016: "Actuals",
    2017: "Actuals",
    2018: "Actuals",
    2019: "Estimated Actual",
    2020: "Main Estimates",
}
BASIS = biff8_projection.VALUE_BASIS


@dataclass(frozen=True, slots=True)
class BiffBudgetProfile:
    """Closed source observation and independently reviewed physical columns."""

    kind: str
    source_sha256: str
    source_locator: str
    max_rows: int
    fields: tuple[tuple[str, str], ...]
    numeric_columns: tuple[tuple[str, int], ...]
    definitions: tuple[tuple[int, str], ...]
    definition_links: tuple[tuple[str, int], ...]
    edition: int = 2019
    group_types: tuple[str, ...] = ("Single", "MCA")
    period_types: tuple[tuple[int, str], ...] = tuple(PERIOD_TYPES.items())
    absent_fields: tuple[str, ...] = ()
    unit: str | None = "$000"

    @property
    def profile_id(self) -> str:
        """Identify the separately versioned stored-integer interpretation."""
        return f"budget-{self.kind}-{self.edition}-biff8/v1"

    @property
    def transformation(self) -> str:
        """Keep source-native output identity separate from literal XLSX facts."""
        return f"budget-{self.edition}-health-{self.kind}-biff8/v1"

    @property
    def source_vintage(self) -> str:
        """Retain the edition explicitly declared by the closed source profile."""
        return f"Budget-{self.edition}"

    @property
    def fact_schema(self) -> pa.Schema:
        """Retain source dimensions while excluding the lexical-token class."""
        base = (
            budget_expenditure_2024.FACT_SCHEMA
            if self.kind == "expenditure"
            else budget_revenue.FACT_SCHEMA
        )
        return pa.schema(
            [
                f
                for f in base
                if f.name not in {"source_number_token", "raw_values_json"}
            ]
            + [
                pa.field("value_basis", pa.string()),
                pa.field("canonical_stored_integer", pa.string()),
                pa.field("numeric_evidence_id", pa.string()),
                pa.field("decoded_values_json", pa.string()),
            ]
            + (
                [
                    pa.field(
                        "is_mca" if self.kind == "expenditure" else "periodicity",
                        pa.string(),
                    )
                ]
                if self.edition == _SOURCE_QUALIFIER_EDITION
                else []
            )
            + (
                [
                    pa.field(
                        "parent_appropriation_id"
                        if self.edition == _SOURCE_PARENT_IDENTIFIER_EDITION
                        and self.kind == "revenue"
                        else "mcoa_id",
                        pa.int64(),
                    )
                ]
                + (
                    [pa.field("output_expense_type", pa.string())]
                    if self.kind == "expenditure"
                    else [
                        pa.field("functional_classification", pa.string()),
                        pa.field("periodicity", pa.string()),
                    ]
                )
                if self.edition in _LEGACY_DIMENSION_EDITIONS
                else (
                    [
                        pa.field("mcoa_id", pa.int64()),
                        pa.field("output_expense_type", pa.string()),
                    ]
                    if self.kind == "expenditure"
                    else [
                        pa.field("functional_classification", pa.string()),
                        pa.field("periodicity", pa.string()),
                    ]
                )
                if self.edition in _UNSCALED_EDITIONS
                else []
            )
            + (
                [pa.field("source_unlabelled_m", pa.string())]
                if self.edition == _UNLABELLED_COLUMN_EDITION
                and self.kind == "expenditure"
                else []
            )
        )


PROFILES = {
    "expenditure": BiffBudgetProfile(
        "expenditure",
        "30602fd66ec1f4fb7d0b47f2766f6560c4d22e90c11e994fba3e404e29ceab48",
        "https://www.treasury.govt.nz/sites/default/files/2019-"
        "05/b19-expenditure-data.xls",
        6288,
        tuple(budget_expenditure_2024.FIELDS.items()),
        (
            ("app_id", 3),
            ("parent_id", 4),
            ("amount", 11),
            ("year", 12),
            ("m_number", 16),
        ),
        tuple(
            (int(coordinate[1:]), text)
            for coordinate, text in {
                **budget_expenditure_2020.DEFINITIONS,
                "B3": (
                    "This Expense workbook contains details of actual government "
                    "expenditure for the years ended 30 June 2015, 2016, 2017 and "
                    "2018; estimated actual government expenditure for the year "
                    "ending 30\xa0June 2019 and budgeted government expenditure for "
                    "the year ending 30 June 2020 as published in Budget 2019."
                ),
            }.items()
        ),
        (
            *(
                (field, int(coordinate[1:]))
                for field, coordinate in budget_expenditure_2020.DEFINITION_COORDINATES
            ),
            ("source_vintage", 3),
            ("amount_type", 3),
        ),
    ),
    "revenue": BiffBudgetProfile(
        "revenue",
        "d927995dd91eda6fdfb4020eb2a3e91871a24d5144e837e7801b6725e5f33df8",
        "https://www.treasury.govt.nz/sites/default/files/2019-05/b19-revenue-data.xls",
        1020,
        tuple(budget_revenue.FIELDS.items()),
        (("app_id", 3), ("amount", 6), ("year", 7)),
        tuple(
            (int(coordinate[1:]), text)
            for coordinate, text in {
                **budget_revenue.DEFINITIONS_2020,
                "B4": (
                    "The Revenue workbook contains details of  actual government "
                    "Crown revenue and capital receipts for the years ended 30 June "
                    "2015, 2016, 2017 and 2018; estimated actual government Crown "
                    "revenue and capital receipts for the year ending 30 June 2019 "
                    "and budgeted government Crown revenue and capital receipts for "
                    "the year ending 30 June 2020 as published in Budget 2019."
                ),
            }.items()
        ),
        (
            ("unit", 36),
            ("valid_time_end", 37),
            ("amount_type", 38),
            ("app_id", 42),
            ("source_vintage", 4),
            ("amount_type", 4),
        ),
    ),
}

# Exact changed definition cells from the pinned Budget2018 Explanation sheets.
_EXPENDITURE_DEFINITIONS_2018 = {
    47: (
        "App ID: Number used to uniquely identify each appropriation; "
        "category of an MCA; or output class of an MCOA. This is "
        "particularly useful where an MYA is superceded by another MYA with"
        " the same name."
    ),
    48: (
        "Parent ID: Number used to group categories or output classes "
        "belonging to an MCA or an MCOA."
    ),
    49: (
        'Group Type: "Single" if Appropriation contains a single category, '
        '"MCA" or "MCOA" if the line is part of a multi-line Appropriation.'
    ),
    3: (
        "This Expense workbook contains details of actual government "
        "expenditure for the years ended 30 June 2014, 2015, 2016 and 2017;"
        " estimated actual government expenditure for the year ending "
        "30\xa0June 2018 and budgeted government expenditure for the year "
        "ending 30 June 2019 as published in Budget 2018."
    ),
}
_REVENUE_DEFINITIONS_2018 = {
    4: (
        "The Revenue workbook contains details of  actual government Crown "
        "revenue and capital receipts for the years ended 30 June 2014, "
        "2015, 2016 and 2017; estimated actual government Crown revenue and"
        " capital receipts for the year ending 30 June 2018 and budgeted "
        "government Crown revenue and capital receipts for the year ending "
        "30 June 2019 as published in Budget 2018."
    ),
}

PROFILES_2018 = {
    "expenditure": replace(
        PROFILES["expenditure"],
        source_sha256="fecd70019054313f3a11cbb370be684d8bea0eea8cb3623b69a9e193ac085c24",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-05/b18-expenditure-data.xls",
        max_rows=6167,
        edition=2018,
        group_types=("Single", "MCA", "MCOA"),
        period_types=(
            (2014, "Actuals"),
            (2015, "Actuals"),
            (2016, "Actuals"),
            (2017, "Actuals"),
            (2018, "Estimated Actual"),
            (2019, "Main Estimates"),
        ),
        definitions=tuple(
            (row, _EXPENDITURE_DEFINITIONS_2018.get(row, text))
            for row, text in PROFILES["expenditure"].definitions
        ),
    ),
    "revenue": replace(
        PROFILES["revenue"],
        source_sha256="4db87e7eddd7a76b5b7523db5a01952d15e7f47b88d03ef9878d37cd077f937f",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-05/b18-revenue-data.xls",
        max_rows=1011,
        edition=2018,
        period_types=(
            (2014, "Actuals"),
            (2015, "Actuals"),
            (2016, "Actuals"),
            (2017, "Actuals"),
            (2018, "Estimated Actual"),
            (2019, "Main Estimates"),
        ),
        definitions=tuple(
            (row, _REVENUE_DEFINITIONS_2018.get(row, text))
            for row, text in PROFILES["revenue"].definitions
        ),
    ),
}


# Exact changed edition statements from both pinned Budget2017 originals.
_EXPENDITURE_DEFINITIONS_2017 = {
    3: (
        "This Expense workbook contains details of actual government expen"
        "diture for the years ended 30 June 2013, 2014, 2015 and 2016; est"
        "imated actual government expenditure for the year ending 30\xa0June "
        "2017 and budgeted government expenditure for the year ending 30 J"
        "une 2018 as published in Budget 2017."
    )
}
_REVENUE_DEFINITIONS_2017 = {
    4: (
        "The Revenue workbook contains details of  actual government Crown"
        " revenue and capital receipts for the years ended 30 June 2013, 2"
        "014, 2015 and 2016; estimated actual government Crown revenue and"
        " capital receipts for the year ending 30 June 2017 and budgeted g"
        "overnment Crown revenue and capital receipts for the year ending "
        "30 June 2018 as published in Budget 2017."
    )
}

_PERIOD_TYPES_2017 = (
    (2013, "Actuals"),
    (2014, "Actuals"),
    (2015, "Actuals"),
    (2016, "Actuals"),
    (2017, "Estimated Actual"),
    (2018, "Main Estimates"),
)

PROFILES_2017 = {
    "expenditure": replace(
        PROFILES_2018["expenditure"],
        source_sha256="7e0cc535eb9feb7e82b1a998dd40b7b318e5593e13589aa48ef4a3b5508708fc",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b17-expenditure-data.xls",
        max_rows=6079,
        edition=2017,
        period_types=_PERIOD_TYPES_2017,
        definitions=tuple(
            (row, _EXPENDITURE_DEFINITIONS_2017.get(row, text))
            for row, text in PROFILES_2018["expenditure"].definitions
        ),
    ),
    "revenue": replace(
        PROFILES_2018["revenue"],
        source_sha256="e49a706c4a5ac889e8b9e68165dbfd704a9f05b0300bef7f69abf5f5620b7adf",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b17-revenue-data.xls",
        max_rows=1026,
        edition=2017,
        period_types=_PERIOD_TYPES_2017,
        definitions=tuple(
            (row, _REVENUE_DEFINITIONS_2017.get(row, text))
            for row, text in PROFILES_2018["revenue"].definitions
        ),
    ),
}


# Exact2016 definition cells; revenue definitions moved three rows earlier.
_EXPENDITURE_DEFINITIONS_2016 = {
    3: (
        "This Expense workbook contains details of actual government "
        "expenditure for the years ended 30 June 2012, 2013, 2014 and "
        "2015; estimated actual government expenditure for the year "
        "ending 30\xa0June 2016 and budgeted government expenditure for the "
        "year ending 30 June 2017 as published in Budget 2016."
    ),
}
_REVENUE_DEFINITIONS_2016 = {
    4: (
        "The Revenue workbook contains details of  actual government "
        "Crown revenue and capital receipts for the years ended 30 June "
        "2012, 2013, 2014 and 2015; estimated actual government Crown "
        "revenue and capital receipts for the year ending 30 June 2016 "
        "and budgeted government Crown revenue and capital receipts for "
        "the year ending 30 June 2017 as published in Budget 2016."
    ),
    33: (
        "Amount $000: Amount (in thousands) for the Year as reported in "
        "the Main Estimates."
    ),
    34: (
        "Year: Year ending that the Amount relates to (at 30 June) as "
        "reported in the Main Estimates."
    ),
    35: (
        'Amount Type: "Actuals" - as audited for prior Years, "Estimated '
        'Actual" - for the Year immediately prior to the current Main '
        'Estimates, "Main Estimates" - for the Main Estimates Year.'
    ),
    39: (
        "App ID: Number used to uniquely identify each Crown revenue or "
        "capital receipt line."
    ),
}

_PERIOD_TYPES_2016 = (
    (2012, "Actuals"),
    (2013, "Actuals"),
    (2014, "Actuals"),
    (2015, "Actuals"),
    (2016, "Estimated Actual"),
    (2017, "Main Estimates"),
)

PROFILES_2016 = {
    "expenditure": replace(
        PROFILES_2017["expenditure"],
        source_sha256="bce6d2e55c15c1249881bac9d2a1afdf111cd9d1c258c20913bd4b39300f0f5a",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b16-expenditure-data.xls",
        max_rows=5972,
        edition=2016,
        period_types=_PERIOD_TYPES_2016,
        definitions=tuple(
            (row, _EXPENDITURE_DEFINITIONS_2016.get(row, text))
            for row, text in PROFILES_2017["expenditure"].definitions
        ),
    ),
    "revenue": replace(
        PROFILES_2017["revenue"],
        source_sha256="df34849f2ef7ce1903469edb315047afc8ae716574d163f59691a654c51b957f",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b16-revenue-data.xls",
        max_rows=1011,
        edition=2016,
        period_types=_PERIOD_TYPES_2016,
        definitions=tuple(_REVENUE_DEFINITIONS_2016.items()),
        definition_links=(
            ("unit", 33),
            ("valid_time_end", 34),
            ("amount_type", 35),
            ("app_id", 39),
            ("source_vintage", 4),
            ("amount_type", 4),
        ),
    ),
}


# The pinned2015 expenditure source has no minister/portfolio columns.
_ABSENT_EXPENDITURE_FIELDS_2015 = ("m_number", "portfolio_name")
_EXPENDITURE_DEFINITIONS_2015 = {
    3: (
        "This Expense workbook contains details of actual government expend"
        "iture for the years ended 30 June 2011, 2012, 2013 and 2014; estim"
        "ated actual government expenditure for the year ending 30\xa0June 201"
        "5 and budgeted government expenditure for the year ending 30 June "
        "2016 as published in Budget 2015."
    ),
    38: (
        "Periodicity: As per the arrangement of appropriations at the begin"
        'ning of each vote chapter in the Main Estimates: "A" refers to an '
        "Annual appropriation or to a Permanent Legislative Authority appro"
        'priation. "M" refers to a multi-year appropriation.'
    ),
    39: (
        "Amount $000: Amount (in thousands) for the Year as reported in the"
        " Main Estimates."
    ),
    40: (
        "Year: Year ending that the Amount relates to (at 30 June) as repor"
        "ted in the Main Estimates."
    ),
    41: (
        'Amount Type: "Actuals" - as audited for prior Years, "Estimated Ac'
        'tual" - for the Year immediately prior to the current Main Estimat'
        'es, "Main Estimates" - for the Main Estimates Year.'
    ),
    46: (
        "App ID: Number used to uniquely identify each appropriation; categ"
        "ory of an MCA; or output class of an MCOA. This is particularly us"
        "eful where an MYA is superceded by another MYA with the same name."
    ),
    47: (
        "Parent ID: Number used to group categories or output classes belon"
        "ging to an MCA or an MCOA."
    ),
    48: (
        'Group Type: "Single" if Appropriation contains a single category, '
        '"MCA" or "MCOA" if the line is part of a multi-line Appropriation.'
    ),
    49: (
        "Functional Classification: Groups expenses into broad objectives o"
        "f the government (based on OECD classification) \u2013 e.g. Health, Edu"
        "cation, Defence, etc. This classification is not included in the M"
        "ain Estimates."
    ),
}

_REVENUE_DEFINITIONS_2015 = {
    4: (
        "The Revenue workbook contains details of  actual government Crown "
        "revenue and capital receipts for the years ended 30 June 2011, 201"
        "2, 2013 and 2014; estimated actual government Crown revenue and ca"
        "pital receipts for the year ending 30 June 2015 and budgeted gover"
        "nment Crown revenue and capital receipts for the year ending 30 Ju"
        "ne 2016 as published in Budget 2015."
    ),
    34: (
        "Amount $000: Amount (in thousands) for the Year as reported in the"
        " Main Estimates."
    ),
    35: (
        "Year: Year ending that the Amount relates to (at 30 June) as repor"
        "ted in the Main Estimates."
    ),
    36: (
        'Amount Type: "Actuals" - as audited for prior Years, "Estimated Ac'
        'tual" - for the Year immediately prior to the current Main Estimat'
        'es, "Main Estimates" - for the Main Estimates Year.'
    ),
    40: (
        "App ID: Number used to uniquely identify each Crown revenue or cap"
        "ital receipt line."
    ),
}

_PERIOD_TYPES_2015 = (
    (2011, "Actuals"),
    (2012, "Actuals"),
    (2013, "Actuals"),
    (2014, "Actuals"),
    (2015, "Estimated Actual"),
    (2016, "Main Estimates"),
)

PROFILES_2015 = {
    "expenditure": replace(
        PROFILES_2016["expenditure"],
        source_sha256="4dbabc88f1e0756e0f651ef261b3408b262a10f0b1cdb51977844c97841b9325",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2015-05/b15-expenditure-data.xls",
        max_rows=5977,
        edition=2015,
        fields=PROFILES_2016["expenditure"].fields[:15],
        numeric_columns=PROFILES_2016["expenditure"].numeric_columns[:4],
        absent_fields=_ABSENT_EXPENDITURE_FIELDS_2015,
        period_types=_PERIOD_TYPES_2015,
        definitions=tuple(_EXPENDITURE_DEFINITIONS_2015.items()),
        definition_links=(
            ("periodicity", 38),
            ("unit", 39),
            ("valid_time_end", 40),
            ("amount_type", 41),
            ("app_id", 46),
            ("parent_id", 47),
            ("group_type", 48),
            ("functional_classification", 49),
            ("source_vintage", 3),
            ("amount_type", 3),
        ),
    ),
    "revenue": replace(
        PROFILES_2016["revenue"],
        source_sha256="481b971d4569cbadbf48440fa1d66f82d8d42942fd855e95e5bfd1ea95e70171",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2015-05/b15-revenue-data.xls",
        max_rows=1006,
        edition=2015,
        period_types=_PERIOD_TYPES_2015,
        definitions=tuple(_REVENUE_DEFINITIONS_2015.items()),
        definition_links=(
            ("unit", 34),
            ("valid_time_end", 35),
            ("amount_type", 36),
            ("app_id", 40),
            ("source_vintage", 4),
            ("amount_type", 4),
        ),
    ),
}


# Pinned2014 source context resolves the retained revenue B10 edition conflict.
_EXPENDITURE_DEFINITIONS_2014 = {
    1: "Budget 2014 Data from the Estimates of Appropriations 2014/15",
    4: "Published 15 May 2014",
    9: "This Expense workbook contains details of actual government expenditure for "
    "the years' ended 30 June 2010, 2011, 2012 and 2013; estimated actual "
    "government expenditure for the year ending 30\xa0June 2014 and budgeted "
    "government expenditure for the year ending 30 June 2015 as published in Budget "
    "2014.",
    24: "This workbook is based on the data contained in the Crown's Financial and "
    "Information System, which is used to collect and compile the raw data for the "
    "2014/15 Estimates.  They do not include data from the 2013/14 Supplementary "
    "Estimates. ",
    26: "Data relating to the 2014/15 fiscal year should match the 2014/15 Estimates "
    "exactly.",
    39: "Appropriation Type: Indicates the nature of the expenditure that can be "
    "incurred under the appropriation as appearing in the current Main Estimates "
    "(e.g. whether capital expenditure or the nature of expenses incurred). Refer "
    "to the Main Estimates: Introduction to the Estimates: Types of Appropriation.",
    41: "Periodicity: As per the arrangement of appropriations at the beginning of "
    'each vote chapter in the Main Estimates: "A" refers to an Annual '
    'appropriation or to a Permanent Legislative Authority appropriation. "M" '
    "refers to a multi-year appropriation.",
    42: "Amount ($000): Amount (in thousands) for the Year as reported in the Main "
    "Estimates.",
    43: "Year: Year ending that the Amount relates to (at 30 June) as reported in the "
    "Main Estimates.",
    44: 'Amount Type: "Actuals" - as audited for prior Years, "Estimated Actual" - for '
    'the Year immediately prior to the current Main Estimates, "Main Estimates" - '
    "for the Main Estimates Year.",
    49: "App ID: Number used to uniquely identify each appropriation; category of an "
    "MCA; or output class of an MCOA.",
    50: "Parent ID: Number used to group categories or output classes belonging to an "
    "MCA or an MCOA.",
    51: 'Group Type: "Single" if Appropriation contains a single category, "MCA" or '
    '"MCOA" if the line is part of a multi-line Appropriation.',
    52: 'IsMCA: "Yes" when the line is part of a MCA, "No" when the line is not part '
    "of a MCA.",
    53: "Functional Classification: Groups expenses into broad objectives of the "
    "government (based on OECD classification) \u2013 e.g. Health, Education, Defence, "
    "etc. This classification is not included in the Main Estimates.",
}

_REVENUE_DEFINITIONS_2014 = {
    1: "Budget 2014 Data from the Estimates of Appropriations 2014/15",
    4: "Published 15 May 2014",
    10: "The Revenue workbook contains details of  actual government Crown revenue and "
    "capital receipts for the years' ended 30 June 2010, 2011, 2012 and 2013; "
    "estimated actual government Crown revenue and capital receipts for the year "
    "ending 30 June 2014 and budgeted government Crown revenue and capital "
    "receipts for the year ending 30 June 2015 as published in Budget 2015.",
    24: "This workbook is based on the data contained in the Crown's Financial and "
    "Information System, which is used to collect and compile the raw data for the "
    "2014/15 Estimates.  They do not include data from the 2013/14 Supplementary "
    "Estimates. ",
    26: "Data relating to the 2014/15 fiscal year should match the 2014/15 Estimates "
    "exactly.",
    29: "Amounts are in thousands of dollars.",
    34: "Data sourced from the 2014/15 Main Estimates:",
    40: 'Periodicity: "A" refers to Annual.',
    41: "Amount ($000): Amount (in thousands) for the Year as reported in the Main "
    "Estimates.",
    42: "Year: Year ending that the Amount relates to (at 30 June) as reported in the "
    "Main Estimates.",
    43: 'Amount Type: "Actuals" - as audited for prior Years, "Estimated Actual" - for '
    'the Year immediately prior to the current Main Estimates, "Main Estimates" - '
    "for the Main Estimates Year.",
    46: "App ID: Number used to uniquely identify each Crown revenue or capital "
    "receipt line.",
}

_PERIOD_TYPES_2014 = (
    *((year, "Actuals") for year in range(2010, 2014)),
    (2014, "Estimated Actual"),
    (2015, "Main Estimates"),
)
PROFILES_2014 = {
    "expenditure": replace(
        PROFILES_2015["expenditure"],
        source_sha256="7194eebe691ff57378168439d7ba5a785dfa408bc3c836f2a7cfe50519af5169",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b14-expenditure-data.xls",
        max_rows=5912,
        edition=2014,
        period_types=_PERIOD_TYPES_2014,
        fields=tuple(
            (
                header.replace("Amount $000", "Amount ($000)").replace(
                    "Appropriation or Category Type", "Appropriation Type"
                ),
                field,
            )
            for header, field in (
                *PROFILES_2015["expenditure"].fields[:7],
                ("IsMCA", "is_mca"),
                *PROFILES_2015["expenditure"].fields[7:],
            )
        ),
        numeric_columns=(("app_id", 3), ("parent_id", 4), ("amount", 12), ("year", 13)),
        definitions=tuple(_EXPENDITURE_DEFINITIONS_2014.items()),
        definition_links=(
            ("source_vintage", 1),
            ("source_vintage", 4),
            ("source_vintage", 9),
            ("source_vintage", 24),
            ("source_vintage", 26),
            ("appropriation_or_category_type", 39),
            ("periodicity", 41),
            ("unit", 42),
            ("valid_time_end", 43),
            ("amount_type", 44),
            ("app_id", 49),
            ("parent_id", 50),
            ("group_type", 51),
            ("is_mca", 52),
            ("functional_classification", 53),
        ),
    ),
    "revenue": replace(
        PROFILES_2015["revenue"],
        source_sha256="ba1798c82e556afe98188ea58651759cb6fa1f52a461e4529bc664af424db91b",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b14-revenue-data.xls",
        max_rows=1009,
        edition=2014,
        period_types=_PERIOD_TYPES_2014,
        fields=(
            *(
                (h.replace("Amount $000", "Amount ($000)"), f)
                for h, f in PROFILES_2015["revenue"].fields
            ),
            ("Periodicity", "periodicity"),
        ),
        definitions=tuple(_REVENUE_DEFINITIONS_2014.items()),
        definition_links=(
            ("source_vintage", 1),
            ("source_vintage", 4),
            ("amount_type", 10),
            ("source_vintage", 24),
            ("source_vintage", 26),
            ("unit", 29),
            ("source_vintage", 34),
            ("periodicity", 40),
            ("unit", 41),
            ("valid_time_end", 42),
            ("amount_type", 43),
            ("app_id", 46),
        ),
    ),
}


# Budget2013 has MCOA identifiers, not the later ParentID/group/category fields.
_ABSENT_FIELDS_2013 = {
    "expenditure": (
        "parent_id",
        "category_name",
        "group_type",
        "restriction_type",
        "m_number",
        "portfolio_name",
    ),
    "revenue": (),
}
PROFILES_2013 = {
    "expenditure": replace(
        PROFILES_2014["expenditure"],
        source_sha256="c5b7f6916b89a9ea0fd14caf73a979c730116d517d78ffe777d36c5966626140",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b13-expenditure-data.xls",
        max_rows=5848,
        edition=2013,
        fields=(
            ("Department", "department"),
            ("Vote", "vote"),
            ("App ID", "app_id"),
            ("MCOA ID", "mcoa_id"),
            ("Description", "appropriation_name"),
            ("Appropriation Type", "appropriation_or_category_type"),
            ("Output Expense Type", "output_expense_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount ($000)", "amount"),
            ("Year", "year"),
            ("Amount_Type_Desc", "amount_type"),
            ("Periodicity", "periodicity"),
            ("Current Scope", "current_scope"),
        ),
        numeric_columns=(("app_id", 3), ("mcoa_id", 4), ("amount", 9), ("year", 10)),
        definitions=(
            (1, "Expenditure Data - Estimates of Appropriations 2013/14"),
            (
                2,
                (
                    "Published 16 May 2013 at www.treasury.govt.nz/budget/2013/da"
                    "ta and www.budget.govt.nz/budget/2013/data\nand on the Budget"
                    " USBs."
                ),
            ),
            (5, "Definitions and Explanations"),
            (7, "Overview"),
            (
                8,
                (
                    "This Expense workbook contains details of actual government "
                    "expenditure for the years' ended 30 June 2009, 2010, 2011 an"
                    "d 2012; estimated actual government expenditure for the year"
                    " ending 30\u00a0June 2013 and budgeted government expenditure for"
                    " the year ending 30 June 2014 as published in Budget 2013."
                ),
            ),
            (
                10,
                (
                    "Raw data has been included in this workbook to allow anyone "
                    "to filter, sort and manipulate the data for their own purpos"
                    "es.  Some examples in the form of pivot tables and charts ar"
                    "e also provided."
                ),
            ),
            (
                12,
                (
                    "More assistance on the use of pivot tables and charts can be"
                    " obtained from the Microsoft Excel help system."
                ),
            ),
            (14, "Definitions"),
            (15, "All amounts are in thousands of dollars ($000)."),
            (
                17,
                (
                    "Definitions of appropriation types can be found in the Intro"
                    "duction chapter of The Estimates of Appropriations for the N"
                    "ew Zealand Government."
                ),
            ),
            (
                19,
                (
                    "The appropriation name and scope is as published in the 2013"
                    "/14 Estimates - the same name and scope is applied to all ye"
                    "ars where the appropriation ID is the same."
                ),
            ),
            (21, "Disclaimer"),
            (
                22,
                (
                    "This workbook is based on the data contained in the Crown's "
                    "Financial and Information System, which is used to collect a"
                    "nd compile the raw data for the 2013/14 Estimates.  They do "
                    "not include data from the 2012/13 Supplementary Estimates. "
                ),
            ),
            (
                24,
                (
                    "Data relating to the 2013/14 fiscal year should match the 20"
                    "13/14 Estimates exactly."
                ),
            ),
            (
                26,
                (
                    "This workbook supports, but does not form part of, the offic"
                    "ial Budget documents.  The printed copies of the Estimates a"
                    "nd Supplementary Estimates, as tabled by the Minister of Fin"
                    "ance on each Budget day, are the official sources for data c"
                    "ontained in these workbooks."
                ),
            ),
            (
                28,
                (
                    "The Treasury has generated this workbook as a resource for i"
                    "nterested persons and has taken all care to ensure the data "
                    "are correct, but does not take responsibility for any errors"
                    " or conclusions drawn from this data."
                ),
            ),
            (
                30,
                (
                    "The Treasury does not provide technical support on the use o"
                    "f Microsoft Excel workbooks."
                ),
            ),
        ),
        definition_links=(
            ("source_vintage", 1),
            ("source_vintage", 2),
            ("source_vintage", 8),
            ("amount_type", 8),
            ("valid_time_end", 8),
            ("unit", 15),
        ),
        absent_fields=_ABSENT_FIELDS_2013["expenditure"],
        period_types=(
            (2009, "Actuals"),
            (2010, "Actuals"),
            (2011, "Actuals"),
            (2012, "Actuals"),
            (2013, "Estimated Actual"),
            (2014, "Main Estimates"),
        ),
    ),
    "revenue": replace(
        PROFILES_2014["revenue"],
        source_sha256="69e9d3d10c72bd01c661ca02633d48404f7add6f5e4fda02017ab5649fa27869",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b13-revenue-data.xls",
        max_rows=995,
        edition=2013,
        fields=(
            ("Department", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("MCOA id", "mcoa_id"),
            ("Description", "description"),
            ("Revenue Type", "revenue_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount ($000)", "amount"),
            ("Year", "year"),
            ("Amount_Type_Desc", "amount_type"),
            ("Periodicity", "periodicity"),
        ),
        numeric_columns=(("app_id", 3), ("mcoa_id", 4), ("amount", 8), ("year", 9)),
        definitions=(
            (1, "Revenue Data - Estimates of Appropriations 2013/14"),
            (
                2,
                (
                    "Published 16 May 2013 at www.treasury.govt.nz/budget/2013/da"
                    "ta and www.budget.govt.nz/budget/2013/data\nand on the Budget"
                    " USBs."
                ),
            ),
            (4, "Definitions and Explanations"),
            (6, "Overview"),
            (
                8,
                (
                    "The Revenue workbook contains details of  actual government "
                    "Crown revenue and capital receipts for the years' ended 30 J"
                    "une 2009, 2010, 2011 and 2012; estimated actual government C"
                    "rown revenue and capital receipts for the year ending 30 Jun"
                    "e 2013 and budgeted government Crown revenue and capital rec"
                    "eipts for the year ending 30 June 2014 as published in Budge"
                    "t 2013."
                ),
            ),
            (
                10,
                (
                    "Raw data has been made available to allow anyone to filter, "
                    "sort and manipulate the data for their own purposes.  Some e"
                    "xamples in the form of pivot tables and charts are also prov"
                    "ided."
                ),
            ),
            (
                12,
                (
                    "More assistance on the use of pivot tables and charts can be"
                    " obtained from the Microsoft Excel help system."
                ),
            ),
            (14, "Definitions"),
            (16, "Amounts are in thousands of dollars."),
            (
                18,
                (
                    "Definitions of Crown revenue and capital receipts can be fou"
                    "nd in the Introduction chapter of The Estimates of Appropria"
                    "tions for the Government of New Zealand."
                ),
            ),
            (20, "Disclaimer"),
            (
                22,
                (
                    "This workbook is based on the data contained in the Crown's "
                    "Financial and Information System, which was used to collect "
                    "and compile the raw data for the 2013/14 Estimates.  They do"
                    " not include data from the 2012/13 Supplementary Estimates. "
                ),
            ),
            (
                24,
                (
                    "Data relating to the 2013/14 fiscal year should match the 20"
                    "13/14 Estimates exactly."
                ),
            ),
            (
                26,
                (
                    "This workbook supports, but does not form part of, the offic"
                    "ial Budget documents.  The printed copies of the Estimates a"
                    "nd Supplementary Estimates, as tabled by the Minister of Fin"
                    "ance on each Budget day, are the official sources for data c"
                    "ontained in these workbooks."
                ),
            ),
            (
                28,
                (
                    "The Treasury has generated this workbook as a resource for i"
                    "nterested persons and has taken all care to ensure the data "
                    "are correct, but does not take responsibility for any errors"
                    " or conclusions drawn from this data."
                ),
            ),
            (
                30,
                (
                    "The Treasury does not provide technical support on the use o"
                    "f Microsoft Excel workbooks."
                ),
            ),
        ),
        definition_links=(
            ("source_vintage", 1),
            ("source_vintage", 2),
            ("source_vintage", 8),
            ("amount_type", 8),
            ("valid_time_end", 8),
            ("unit", 16),
        ),
        absent_fields=_ABSENT_FIELDS_2013["revenue"],
        period_types=(
            (2009, "Actuals"),
            (2010, "Actuals"),
            (2011, "Actuals"),
            (2012, "Actuals"),
            (2013, "Estimated Actual"),
            (2014, "Main Estimates"),
        ),
    ),
}


# Independently pinned Budget2012 columns and definition cells.
PROFILES_2012 = {
    "expenditure": replace(
        PROFILES_2013["expenditure"],
        source_sha256="81429ccc5da52cdba73bb6276bba7d1c55a301dc996a447909fc8fc82ca1af12",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b12-expenditure-data.xls",
        max_rows=5789,
        edition=2012,
        definitions=(
            (1, dict(PROFILES_2013["expenditure"].definitions)[5]),
            (3, dict(PROFILES_2013["expenditure"].definitions)[7]),
            (
                4,
                (
                    "This Expense workbook contains details of actual "
                    "government expenditure for the years' ended 30 June 2008, "
                    "2009, 2010 and 2011; estimated actual government "
                    "expenditure for the year ending 30\u00a0June 2012 and budgeted "
                    "government expenditure for the year ending 30 June 2013 as"
                    " published in Budget 2012."
                ),
            ),
            (6, dict(PROFILES_2013["expenditure"].definitions)[10]),
            (8, dict(PROFILES_2013["expenditure"].definitions)[12]),
            (10, dict(PROFILES_2013["expenditure"].definitions)[14]),
            (11, dict(PROFILES_2013["expenditure"].definitions)[15]),
            (13, dict(PROFILES_2013["expenditure"].definitions)[17]),
            (
                15,
                (
                    "The appropriation name and scope is as published in the "
                    "2012/13 Estimates - the same name and scope is applied to "
                    "all years where the appropriation ID is the same."
                ),
            ),
            (17, dict(PROFILES_2013["expenditure"].definitions)[21]),
            (
                18,
                (
                    "This workbook is based on the data contained in the "
                    "Crown's Financial and Information System, which is used to"
                    " collect and compile the raw data for the 2012/13 "
                    "Estimates.  They do not include data from the 2011/12 "
                    "Supplementary Estimates. "
                ),
            ),
            (
                20,
                (
                    "Data relating to the 2012/13 fiscal year should match the "
                    "2012/13 Estimates exactly."
                ),
            ),
            (22, dict(PROFILES_2013["expenditure"].definitions)[26]),
            (24, dict(PROFILES_2013["expenditure"].definitions)[28]),
            (26, dict(PROFILES_2013["expenditure"].definitions)[30]),
        ),
        definition_links=(
            ("source_vintage", 4),
            ("amount_type", 4),
            ("valid_time_end", 4),
            ("unit", 11),
        ),
        period_types=(
            (2008, "Actuals"),
            (2009, "Actuals"),
            (2010, "Actuals"),
            (2011, "Actuals"),
            (2012, "Estimated Actual"),
            (2013, "Main Estimates"),
        ),
    ),
    "revenue": replace(
        PROFILES_2013["revenue"],
        source_sha256="643fad503424ee6b3aa060a2ff2107fc69d9326bb51446d6fa41755a32d038cb",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2018-04/b12-revenue-data.xls",
        max_rows=993,
        edition=2012,
        fields=tuple(
            ("vote" if h == "Vote" else h, f)
            for h, f in PROFILES_2013["revenue"].fields
        ),
        definitions=(
            (1, dict(PROFILES_2013["revenue"].definitions)[4]),
            (3, dict(PROFILES_2013["revenue"].definitions)[6]),
            (
                5,
                (
                    "The Revenue workbook contains details of  actual "
                    "government Crown revenue and capital receipts for the "
                    "years' ended 30 June 2008, 2009, 2010 and 2011; estimated "
                    "actual government Crown revenue and capital receipts for "
                    "the year ending 30 June 2012 and budgeted government Crown"
                    " revenue and capital receipts for the year ending 30 June "
                    "2013 as published in Budget 2012."
                ),
            ),
            (7, dict(PROFILES_2013["revenue"].definitions)[10]),
            (9, dict(PROFILES_2013["revenue"].definitions)[12]),
            (11, dict(PROFILES_2013["revenue"].definitions)[14]),
            (13, dict(PROFILES_2013["revenue"].definitions)[16]),
            (15, dict(PROFILES_2013["revenue"].definitions)[18]),
            (17, dict(PROFILES_2013["revenue"].definitions)[20]),
            (
                19,
                (
                    "This workbook is based on the data contained in the "
                    "Crown's Financial and Information System, which was used "
                    "to collect and compile the raw data for the 2012/13 "
                    "Estimates.  They do not include data from the 2011/12 "
                    "Supplementary Estimates. "
                ),
            ),
            (
                21,
                (
                    "Data relating to the 2012/13 fiscal year should match the "
                    "2012/13 Estimates exactly."
                ),
            ),
            (23, dict(PROFILES_2013["revenue"].definitions)[26]),
            (25, dict(PROFILES_2013["revenue"].definitions)[28]),
            (27, dict(PROFILES_2013["revenue"].definitions)[30]),
        ),
        definition_links=(
            ("source_vintage", 5),
            ("amount_type", 5),
            ("valid_time_end", 5),
            ("unit", 13),
        ),
        period_types=(
            (2008, "Actuals"),
            (2009, "Actuals"),
            (2010, "Actuals"),
            (2011, "Actuals"),
            (2012, "Estimated Actual"),
            (2013, "Main Estimates"),
        ),
    ),
}


# Budget2011 blank column M is structural only, never Current Scope.
PROFILES_2011 = {
    "expenditure": replace(
        PROFILES_2012["expenditure"],
        source_sha256="8712d27f2da918d1cc8376a8f15e24cafb6b608a3be0cc19da226768a8f69ba0",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2011-05/b11-expense-data.xls",
        max_rows=5658,
        edition=2011,
        absent_fields=(*_ABSENT_FIELDS_2013["expenditure"], "current_scope"),
        fields=(
            ("Department", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("MCOA id", "mcoa_id"),
            ("Description", "appropriation_name"),
            ("Appropriation Type", "appropriation_or_category_type"),
            ("Output Expense Type", "output_expense_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount ($000)", "amount"),
            ("Year", "year"),
            ("Amount_Type_Desc", "amount_type"),
            ("Periodicity", "periodicity"),
            ("", "source_unlabelled_m"),
        ),
        definitions=(
            (1, "Definitions and Explanations"),
            (3, "Overview"),
            (
                4,
                (
                    "This Expense workbook contains details of actual "
                    "government expenditure for the years' ended 30 June "
                    "2007, 2008, 2009 and 2010; estimated actual government "
                    "expenditure for the year ending 30\xa0June 2011 and "
                    "budgeted government expenditure for the year ending 30 "
                    "June 2012 as published in Budget 2011."
                ),
            ),
            (
                6,
                (
                    "Raw data has been included in this workbook to allow "
                    "anyone to filter, sort and manipulate the data for "
                    "their own purposes.  Some examples in the form of pivot"
                    " tables and charts are also provided."
                ),
            ),
            (
                8,
                (
                    "More assistance on the use of pivot tables and charts "
                    "can be obtained from the Microsoft Excel help system."
                ),
            ),
            (10, "Definitions"),
            (11, "Amounts are in thousands of dollars."),
            (
                12,
                (
                    "Definitions of appropriation types can be found in the "
                    "Introduction chapter of The Estimates of Appropriations"
                    " for the New Zealand Government."
                ),
            ),
            (14, "Disclaimer"),
            (
                15,
                (
                    "These spreadsheets are based on the data contained in "
                    "the Crown Financial Information System, which is used "
                    "to collect and compile the raw data for the 2011/12 "
                    "Estimates.  They do not include data from the 2010/11 "
                    "Supplementary Estimates. "
                ),
            ),
            (
                17,
                (
                    "Data relating to the 2011/12 fiscal year should match "
                    "the 2011/12 Estimates exactly."
                ),
            ),
            (
                19,
                (
                    "This workbook supports, but does not form part of, the "
                    "official Budget documents.  The printed copies of the "
                    "Estimates and Supplementary Estimates, as tabled by the"
                    " Minister of Finance on each Budget day, are the "
                    "official sources for data contained in these workbooks."
                ),
            ),
            (
                21,
                (
                    "The Treasury has generated this workbook as a resource "
                    "for interested persons and has taken all care to ensure"
                    " the data are correct, but does not take responsibility"
                    " for any errors or conclusions drawn from this data."
                ),
            ),
            (
                23,
                (
                    "The Treasury does not provide technical support on the "
                    "use of Microsoft Excel workbooks."
                ),
            ),
        ),
        period_types=(
            (2007, "Actuals"),
            (2008, "Actuals"),
            (2009, "Actuals"),
            (2010, "Actuals"),
            (2011, "Estimated Actual"),
            (2012, "Main Estimates"),
        ),
    ),
    "revenue": replace(
        PROFILES_2012["revenue"],
        source_sha256="bd902503455cebe5cc455031bbd2b07f325cce57027c8391c9bec476ad77f073",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2011-05/b11-revenue-data.xls",
        max_rows=990,
        edition=2011,
        fields=(
            ("Department", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("MCOA id", "mcoa_id"),
            ("Description", "description"),
            ("Revenue Type", "revenue_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount ($000)", "amount"),
            ("Year", "year"),
            ("Amount_Type_Desc", "amount_type"),
            ("Periodicity", "periodicity"),
        ),
        definitions=(
            (1, "Definitions and Explanations"),
            (3, "Overview"),
            (
                5,
                (
                    "The Revenue workbook contains details of  actual "
                    "government Crown revenue and capital receipts for the "
                    "years' ended 30 June 2007, 2008, 2009 and 2010; "
                    "estimated actual government Crown revenue and capital "
                    "receipts for the year ending 30 June 2011 and budgeted "
                    "government Crown revenue and capital receipts for the "
                    "year ending 30 June 2012 as published in Budget 2011."
                ),
            ),
            (
                7,
                (
                    "Raw data has been made available to allow anyone to "
                    "filter, sort and manipulate the data for their own "
                    "purposes.  Some examples in the form of pivot tables "
                    "and charts are also provided."
                ),
            ),
            (
                9,
                (
                    "More assistance on the use of pivot tables and charts "
                    "can be obtained from the Microsoft Excel help system."
                ),
            ),
            (11, "Definitions"),
            (13, "Amounts are in thousands of dollars."),
            (
                14,
                (
                    "Definitions of Crown revenue and capital receipts can "
                    "be found in the Introduction chapter of The Estimates "
                    "of Appropriations for the Government of New Zealand."
                ),
            ),
            (16, "Disclaimer"),
            (
                18,
                (
                    "These spreadsheets are based on the data contained in "
                    "the Crown Financial Information System, which was used "
                    "to collect and compile the raw data for the 2011/12 "
                    "Estimates.  They do not include data from the 2010/11 "
                    "Supplementary Estimates. "
                ),
            ),
            (
                20,
                (
                    "Data relating to the 2011/12 fiscal year should match "
                    "the 2011/12 Estimates exactly."
                ),
            ),
            (
                22,
                (
                    "This workbook supports, but does not form part of, the "
                    "official Budget documents.  The printed copies of the "
                    "Estimates and Supplementary Estimates, as tabled by the"
                    " Minister of Finance on each Budget day, are the "
                    "official sources for data contained in these workbooks."
                ),
            ),
            (
                24,
                (
                    "The Treasury has generated this workbook as a resource "
                    "for interested persons and has taken all care to ensure"
                    " the data are correct, but does not take responsibility"
                    " for any errors or conclusions drawn from this data."
                ),
            ),
            (
                26,
                (
                    "The Treasury does not provide technical support on the "
                    "use of Microsoft Excel workbooks."
                ),
            ),
        ),
        period_types=(
            (2007, "Actuals"),
            (2008, "Actuals"),
            (2009, "Actuals"),
            (2010, "Actuals"),
            (2011, "Estimated Actual"),
            (2012, "Main Estimates"),
        ),
    ),
}


# Budget2010 source-stated ParentAppropriationID is distinct from expenditure MCOA.
PROFILES_2010 = {
    "expenditure": replace(
        PROFILES_2011["expenditure"],
        source_sha256="7e26853cbed914ef19bc6dc426d24708dbf19487ce0a9dbc15db4d32d3d00a4f",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2010-05/b10-expense-data.xls",
        max_rows=5513,
        edition=2010,
        fields=(
            ("Department", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("MCOA id", "mcoa_id"),
            ("Description", "appropriation_name"),
            ("Appropriation Type", "appropriation_or_category_type"),
            ("Output Expense Type", "output_expense_type"),
            ("FunctionalClassification", "functional_classification"),
            ("Amount ($000)", "amount"),
            ("Year", "year"),
            ("Amount_Type_Desc", "amount_type"),
            ("Periodicity", "periodicity"),
        ),
        numeric_columns=(("app_id", 3), ("mcoa_id", 4), ("amount", 9), ("year", 10)),
        definitions=(
            (1, dict(PROFILES_2011["expenditure"].definitions)[1]),
            (3, dict(PROFILES_2011["expenditure"].definitions)[3]),
            (
                4,
                (
                    "This Expense workbook contains details of actual "
                    "government expenditure for the years' ended 30 June "
                    "2006, 2007, 2008 and 2009; estimated actual "
                    "government expenditure for the year ending 30\xa0June "
                    "2010 and budgeted government expenditure for the "
                    "year ending 30 June 2011 as published in Budget "
                    "2010."
                ),
            ),
            (6, dict(PROFILES_2011["expenditure"].definitions)[6]),
            (8, dict(PROFILES_2011["expenditure"].definitions)[8]),
            (10, dict(PROFILES_2011["expenditure"].definitions)[10]),
            (11, dict(PROFILES_2011["expenditure"].definitions)[11]),
            (12, dict(PROFILES_2011["expenditure"].definitions)[12]),
            (14, dict(PROFILES_2011["expenditure"].definitions)[14]),
            (
                15,
                (
                    "These spreadsheets are based on the data contained "
                    "in the Crown Financial Information System, which is "
                    "used to collect and compile the raw data for the "
                    "2010/11 Estimates.  They do not include data from "
                    "the 2009/10 Supplementary Estimates. "
                ),
            ),
            (
                17,
                (
                    "Data relating to the 2010/11 fiscal year should "
                    "match the 2010/11 Estimates exactly."
                ),
            ),
            (19, dict(PROFILES_2011["expenditure"].definitions)[19]),
            (21, dict(PROFILES_2011["expenditure"].definitions)[21]),
            (23, dict(PROFILES_2011["expenditure"].definitions)[23]),
        ),
        period_types=(
            (2006, "Actuals"),
            (2007, "Actuals"),
            (2008, "Actuals"),
            (2009, "Actuals"),
            (2010, "Estimated Actual"),
            (2011, "Main Estimates"),
        ),
    ),
    "revenue": replace(
        PROFILES_2011["revenue"],
        source_sha256="d6f63516ef967abec18f09cbe347c02a648a53ef04ce382aa8511c7280f08e15",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2010-05/b10-revenue-data.xls",
        max_rows=983,
        edition=2010,
        fields=(
            ("UnitName", "department"),
            ("VoteName", "vote"),
            ("AppropriationID", "app_id"),
            ("ParentAppropriationID", "parent_appropriation_id"),
            ("Description", "description"),
            ("Revenue Type", "revenue_type"),
            ("FunctionalClassification", "functional_classification"),
            ("Amount $(000)", "amount"),
            ("Year", "year"),
            ("AmountType", "amount_type"),
            ("Periodicity", "periodicity"),
        ),
        numeric_columns=(
            ("app_id", 3),
            ("parent_appropriation_id", 4),
            ("amount", 8),
            ("year", 9),
        ),
        definitions=(
            (1, dict(PROFILES_2011["revenue"].definitions)[1]),
            (3, dict(PROFILES_2011["revenue"].definitions)[3]),
            (
                5,
                (
                    "The Revenue workbook contains details of  actual "
                    "government Crown revenue and capital receipts for "
                    "the years' ended 30 June 2006, 2007 2008 and 2009; "
                    "estimated actual government Crown revenue and "
                    "capital receipts for the year ending 30 June 2010 "
                    "and budgeted government Crown revenue and capital "
                    "receipts for the year ending 30 June 2011 as "
                    "published in Budget 2010."
                ),
            ),
            (7, dict(PROFILES_2011["revenue"].definitions)[7]),
            (9, dict(PROFILES_2011["revenue"].definitions)[9]),
            (11, dict(PROFILES_2011["revenue"].definitions)[11]),
            (13, dict(PROFILES_2011["revenue"].definitions)[13]),
            (14, dict(PROFILES_2011["revenue"].definitions)[14]),
            (16, dict(PROFILES_2011["revenue"].definitions)[16]),
            (
                18,
                (
                    "These spreadsheets are based on the data contained "
                    "in the Crown Financial Information System, which was"
                    " used to collect and compile the raw data for the "
                    "2010/11 Estimates.  They do not include data from "
                    "the 2009/10 Supplementary Estimates. "
                ),
            ),
            (
                20,
                (
                    "Data relating to the 2010/11 fiscal year should "
                    "match the 2010/11 Estimates exactly."
                ),
            ),
            (22, dict(PROFILES_2011["revenue"].definitions)[22]),
            (24, dict(PROFILES_2011["revenue"].definitions)[24]),
            (26, dict(PROFILES_2011["revenue"].definitions)[26]),
        ),
        period_types=(
            (2006, "Actuals"),
            (2007, "Actuals"),
            (2008, "Actuals"),
            (2009, "Actuals"),
            (2010, "Estimated Actual"),
            (2011, "Main Estimates"),
        ),
    ),
}


# Budget2009 has no amount-scale statement or later source qualifiers.
_ABSENT_FIELDS_2009 = {
    "expenditure": (
        *_ABSENT_FIELDS_2013["expenditure"],
        "current_scope",
        "periodicity",
        "output_expense_type",
    ),
    "revenue": ("periodicity",),
}
PROFILES_2009 = {
    "expenditure": replace(
        PROFILES_2010["expenditure"],
        source_sha256="c1177036dd97da6f0e63fb2c91f878a5ec0f98111f62dd881a0e70b536b0bebc",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2009-05/b09-expense-data.xls",
        max_rows=4573,
        edition=2009,
        unit=None,
        absent_fields=_ABSENT_FIELDS_2009["expenditure"],
        fields=(
            ("Unit", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("MCOA id", "mcoa_id"),
            ("Description", "appropriation_name"),
            ("Expense Type", "appropriation_or_category_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount", "amount"),
            ("Year", "year"),
            ("Type", "amount_type"),
        ),
        numeric_columns=(("app_id", 3), ("mcoa_id", 4), ("amount", 8), ("year", 9)),
        definitions=(
            (
                1,
                ("Definitions and Explanations"),
            ),
            (
                3,
                ("Overview"),
            ),
            (
                4,
                (
                    "This Expense workbook contains details of actual "
                    "government expenditure for the years' ended 30 June "
                    "2006, 2007 and 2008; estimated actual government "
                    "expenditure for the year ending 30\xa0June 2009 and "
                    "budgeted government expenditure for the year ending "
                    "30 June 2010 as published in Budget 2009."
                ),
            ),
            (
                6,
                (
                    "Raw data has been included in this workbook to allow"
                    " anyone to filter, sort and manipulate the data for "
                    "their own purposes.  Some examples in the form of "
                    "pivot tables and charts are also provided."
                ),
            ),
            (
                8,
                (
                    "More assistance on the use of pivot tables and "
                    "charts can be obtained from the Microsoft Excel help"
                    " system."
                ),
            ),
            (
                10,
                ("Definitions"),
            ),
            (
                11,
                (
                    "Definitions relating to classifications used in the "
                    "filters can be found by clicking on The Estimates of"
                    " Appropriations then Introduction."
                ),
            ),
            (
                13,
                ("Disclaimer"),
            ),
            (
                14,
                (
                    "These spreadsheets are based on the data contained "
                    "in the Crown Financial Information System, which is "
                    "used to collect and compile the raw data for the "
                    "2009/10 Estimates.  They do not include data from "
                    "the 2008/09 Supplementary Estimates. "
                ),
            ),
            (
                16,
                (
                    "Data relating to the 2009/10 fiscal year should "
                    "match the 2009/10 Estimates exactly."
                ),
            ),
            (
                18,
                (
                    "This workbook supports, but does not form part of, "
                    "the official Budget documents.  The printed copies "
                    "of the Estimates and Supplementary Estimates, as "
                    "tabled by the Minister of Finance on each Budget "
                    "day, are the official sources for data contained in "
                    "these workbooks."
                ),
            ),
            (
                20,
                (
                    "The Treasury has generated this workbook as a "
                    "resource for interested persons and has taken all "
                    "care to ensure the data are correct, but does not "
                    "take responsibility for any errors or conclusions "
                    "drawn from this data."
                ),
            ),
            (
                22,
                (
                    "The Treasury does not provide technical support on "
                    "the use of Microsoft Excel workbooks."
                ),
            ),
        ),
        definition_links=(
            ("source_vintage", 4),
            ("valid_time_end", 4),
            ("amount_type", 4),
        ),
        period_types=(
            (2006, "Actuals"),
            (2007, "Actuals"),
            (2008, "Actuals"),
            (2009, "Estimated Actual"),
            (2010, "Main Estimates"),
        ),
    ),
    "revenue": replace(
        PROFILES_2010["revenue"],
        source_sha256="dc5ce0e7faf9302cdca3bf9e0af5f423e0cac851cb1bdf031508b732f0ae383d",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2009-05/b09-revenue-data.xls",
        max_rows=823,
        edition=2009,
        unit=None,
        absent_fields=_ABSENT_FIELDS_2009["revenue"],
        fields=(
            ("Unit", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("Description", "description"),
            ("Revenue Type", "revenue_type"),
            ("FunctionalClassification", "functional_classification"),
            ("Amount", "amount"),
            ("Year", "year"),
            ("Type", "amount_type"),
        ),
        numeric_columns=(("app_id", 3), ("amount", 7), ("year", 8)),
        definitions=(
            (
                1,
                ("Definitions and Explanations"),
            ),
            (
                3,
                ("Overview"),
            ),
            (
                5,
                (
                    "The Revenue workbook contains details of  actual "
                    "government Crown revenue and capital receipts for "
                    "the years' ended 30 June 2006, 2007 and 2008; "
                    "estimated actual government Crown revenue and "
                    "capital receipts for the year ending 30 June 2009 "
                    "and budgeted government Crown revenue and capital "
                    "receipts for the year ending 30 June 2010 as "
                    "published in Budget 2009."
                ),
            ),
            (
                7,
                (
                    "Raw data has been made available to allow anyone to "
                    "filter, sort and manipulate the data for their own "
                    "purposes.  Some examples in the form of pivot tables"
                    " and charts are also provided."
                ),
            ),
            (
                9,
                (
                    "More assistance on the use of pivot tables and "
                    "charts can be obtained from the Microsoft Excel help"
                    " system."
                ),
            ),
            (
                11,
                ("Definitions"),
            ),
            (
                13,
                (
                    "Definitions relating to classifications used in the "
                    "filters can be found by clicking on The Estimates of"
                    " Appropriations then Introduction."
                ),
            ),
            (
                15,
                ("Disclaimer"),
            ),
            (
                17,
                (
                    "These spreadsheets are based on the data contained "
                    "in the Crown Financial Information System, which was"
                    " used to collect and compile the raw data for the "
                    "2009/10 Estimates.  They do not include data from "
                    "the 2008/09 Supplementary Estimates. "
                ),
            ),
            (
                19,
                (
                    "Data relating to the 2009/10 fiscal year should "
                    "match the 2009/10 Estimates exactly."
                ),
            ),
            (
                21,
                (
                    "This workbook supports, but does not form part of, "
                    "the official Budget documents.  The printed copies "
                    "of the Estimates and Supplementary Estimates, as "
                    "tabled by the Minister of Finance on each Budget "
                    "day, are the official sources for data contained in "
                    "these workbooks."
                ),
            ),
            (
                23,
                (
                    "The Treasury has generated this workbook as a "
                    "resource for interested persons and has taken all "
                    "care to ensure the data are correct, but does not "
                    "take responsibility for any errors or conclusions "
                    "drawn from this data."
                ),
            ),
            (
                25,
                (
                    "The Treasury does not provide technical support on "
                    "the use of Microsoft Excel workbooks."
                ),
            ),
        ),
        definition_links=(
            ("source_vintage", 5),
            ("valid_time_end", 5),
            ("amount_type", 5),
        ),
        period_types=(
            (2006, "Actuals"),
            (2007, "Actuals"),
            (2008, "Actuals"),
            (2009, "Estimated Actual"),
            (2010, "Main Estimates"),
        ),
    ),
}


# Independently pinned2007/2008 profiles preserve the older unscaled layout.
PROFILES_2008 = {
    "expenditure": replace(
        PROFILES_2009["expenditure"],
        source_sha256="62283a0454233bfeec9ce75bdbc822dcf59326cc2aecf5ea33581a4e1355c51b",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2008-05/b08-expense-data.xls",
        max_rows=3557,
        edition=2008,
        fields=(
            ("Unit", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("MCOA id", "mcoa_id"),
            ("Description", "appropriation_name"),
            ("Expense Type", "appropriation_or_category_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount", "amount"),
            ("Year", "year"),
            ("Type", "amount_type"),
        ),
        definitions=(
            (
                1,
                ("Definitions and Explanations"),
            ),
            (
                3,
                ("Overview"),
            ),
            (
                4,
                (
                    "This Expense workbook contains details of actual "
                    "government expenditure for the year ended 30 June "
                    "2006 and 30 June 2007, estimated actual government "
                    "expenditure for the year ending 30\xa0June 2008 and "
                    "budgeted government expenditure for the year ending "
                    "30 June 2009 as published in Budget 2008."
                ),
            ),
            (
                6,
                (
                    "Raw data has been included in this workbook to allow"
                    " anyone to filter, sort and manipulate the data for "
                    "their own purposes.  Some examples in the form of "
                    "pivot tables and charts are also provided."
                ),
            ),
            (
                8,
                ("Definitions"),
            ),
            (
                9,
                (
                    "Definitions relating to classifications used in the "
                    "filters can be found by clicking on The Estimates of"
                    " Appropriations then Introduction."
                ),
            ),
            (
                11,
                ("Using the workbook"),
            ),
            (
                12,
                ("Filtering raw data"),
            ),
            (
                13,
                (
                    "Filters have been applied by using the "
                    "Data/Filter/AutoFilter option on the Excel menu bar."
                    "  Filters can be selected by clicking on the arrows "
                    "to the right of each header cell and selecting the "
                    "filter value.  Custom filters can be selected by "
                    'using the "(Custom)" option in the filter drop-down '
                    "list.  Filter criteria can be removed by clicking on"
                    " the arrow to the right of the header cell and "
                    'selecting the "(All)" option.'
                ),
            ),
            (
                14,
                ("Pivot table tips"),
            ),
            (
                15,
                (
                    "Pivot tables settings can be changed by right-"
                    'clicking on the pivot table and selecting "Wizard".'
                ),
            ),
            (
                16,
                (
                    "Column and row filters can be selected by clicking "
                    "on the arrows to the right of header cells."
                ),
            ),
            (
                17,
                (
                    "Note: any changes to the pivot tables will change "
                    "the associated pivot charts."
                ),
            ),
            (
                18,
                ("Pivot chart line/bar graph tips"),
            ),
            (
                19,
                (
                    "Data series can be hidden and displayed by clicking "
                    "on the arrow to the right of the legend header."
                ),
            ),
            (
                20,
                (
                    "Hover the mouse over a data series to see the name "
                    "and range of the data."
                ),
            ),
            (
                21,
                ("Pivot chart pie graph tips"),
            ),
            (
                22,
                (
                    "Use arrows at the right of grey boxes to change "
                    "parameters for the graph (ie year or output type)."
                ),
            ),
            (
                23,
                (
                    "Hover the mouse over a data series to see the name "
                    "and range of the data."
                ),
            ),
            (
                25,
                (
                    "More assistance on the use of pivot tables and "
                    "charts can be obtained from the Microsoft Excel help"
                    " system."
                ),
            ),
            (
                27,
                ("Disclaimer"),
            ),
            (
                28,
                (
                    "These spreadsheets are based on the data contained "
                    "in the Crown Financial Information System, which is "
                    "used to collect and compile the raw data for the "
                    "2008/09 Estimates.  They do not include data from "
                    "the 2007/08 Supplementary Estimates. "
                ),
            ),
            (
                30,
                (
                    "Data relating to the 2008/09 fiscal year will match "
                    "the 2008/09 Estimates exactly."
                ),
            ),
            (
                32,
                (
                    "This workbook supports, but does not form part of, "
                    "the official Budget documents.  The printed copies "
                    "of the Estimates and Supplementary Estimates, as "
                    "tabled by the Minister of Finance on each Budget "
                    "day, are the official sources for data contained in "
                    "these workbooks."
                ),
            ),
            (
                34,
                (
                    "The Treasury has generated this workbook as a "
                    "resource for interested persons and has taken all "
                    "care to ensure the data are correct, but does not "
                    "take responsibility for any errors or conclusions "
                    "drawn from this data."
                ),
            ),
            (
                36,
                (
                    "The Treasury does not provide technical support on "
                    "the use of Microsoft Excel workbooks."
                ),
            ),
        ),
        definition_links=(
            ("source_vintage", 4),
            ("valid_time_end", 4),
            ("amount_type", 4),
        ),
        period_types=(
            (2006, "Actuals"),
            (2007, "Actuals"),
            (2008, "Estimated Actual"),
            (2009, "Main Estimates"),
        ),
    ),
    "revenue": replace(
        PROFILES_2009["revenue"],
        source_sha256="c261fb95965f8dc1c0d649000e5bf46012c6e5c37385c050c370de07a580e94a",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2008-05/b08-revenue-data.xls",
        max_rows=651,
        edition=2008,
        fields=(
            ("Unit", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("Description", "description"),
            ("Revenue Type", "revenue_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount", "amount"),
            ("Year", "year"),
            ("Type", "amount_type"),
        ),
        definitions=(
            (
                1,
                ("Definitions and Explanations"),
            ),
            (
                3,
                ("Overview"),
            ),
            (
                4,
                (
                    "The Revenue workbook contains details of  actual "
                    "government revenue and receipts for the year ended "
                    "30 June 2006 and 30 June 2007, estimated actual "
                    "government revenue and receipts for the year ending "
                    "30 June 2008 and budgeted government revenue and "
                    "receipts for the year ending 30 June 2009 as "
                    "published in Budget 2008."
                ),
            ),
            (
                6,
                (
                    "Raw data has been made available to allow anyone to "
                    "filter, sort and manipulate the data for their own "
                    "purposes.  Some examples in the form of pivot tables"
                    " and charts are also provided."
                ),
            ),
            (
                8,
                ("Definitions"),
            ),
            (
                9,
                (
                    "Definitions relating to classifications used in the "
                    "filters can be found by clicking on The Estimates of"
                    " Appropriations then Introduction."
                ),
            ),
            (
                11,
                ("Using the workbook"),
            ),
            (
                12,
                ("Filtering raw data"),
            ),
            (
                13,
                (
                    "Filters have been applied by using the "
                    "Data/Filter/AutoFilter option on the Excel menu bar."
                    "  Filters can be selected by clicking on the arrows "
                    "to the right of each header cell and selecting the "
                    "filter value.  Custom filters can be selected by "
                    'using the "(Custom)" option in the filter drop-down '
                    "list.  Filter criteria can be removed by clicking on"
                    " the arrow to the right of the header cell and "
                    'selecting the "(All)" option.'
                ),
            ),
            (
                14,
                ("Pivot table tips"),
            ),
            (
                15,
                (
                    "Pivot table settings can be changed by right-"
                    'clicking on the pivot table and selecting "Wizard".'
                ),
            ),
            (
                16,
                (
                    "Column and row filters can be selected by clicking "
                    "on the arrows to the right of header cells."
                ),
            ),
            (
                17,
                (
                    "Note: any changes to the pivot tables will change "
                    "the associated pivot charts."
                ),
            ),
            (
                18,
                ("Pivot chart line/bar graph tips"),
            ),
            (
                19,
                (
                    "Data series can be hidden and displayed by clicking "
                    "on the arrow to the right of the legend header."
                ),
            ),
            (
                20,
                (
                    "Hover the mouse over a data series to see the name "
                    "and range of the data."
                ),
            ),
            (
                21,
                ("Pivot chart pie graph tips"),
            ),
            (
                22,
                (
                    "Use arrows at the right of grey boxes to change "
                    "parameters for the graph (ie year or output type)."
                ),
            ),
            (
                23,
                (
                    "Hover the mouse over a data series to see the name "
                    "and range of the data."
                ),
            ),
            (
                25,
                (
                    "More assistance on the use of pivot tables and "
                    "charts can be obtained from the Microsoft Excel help"
                    " system."
                ),
            ),
            (
                27,
                ("Disclaimer"),
            ),
            (
                28,
                (
                    "These spreadsheets are based on the data contained "
                    "in the Crown Financial Information System, which was"
                    " used to collect and compile the raw data for the "
                    "2008/09 Estimates.  They do not include data from "
                    "the 2007/08 Supplementary Estimates. "
                ),
            ),
            (
                30,
                (
                    "Data relating to the 2008/09 fiscal year will match "
                    "the 2008/09 Estimates exactly."
                ),
            ),
            (
                32,
                (
                    "This workbook supports, but does not form part of, "
                    "the official Budget documents.  The printed copies "
                    "of the Estimates and Supplementary Estimates, as "
                    "tabled by the Minister of Finance on each Budget "
                    "day, are the official sources for data contained in "
                    "these workbooks."
                ),
            ),
            (
                34,
                (
                    "The Treasury has generated this workbook as a "
                    "resource for interested persons and has taken all "
                    "care to ensure the data are correct, but does not "
                    "take responsibility for any errors or conclusions "
                    "drawn from this data."
                ),
            ),
            (
                36,
                (
                    "The Treasury does not provide technical support on "
                    "the use of Microsoft Excel workbooks."
                ),
            ),
        ),
        definition_links=(
            ("source_vintage", 4),
            ("valid_time_end", 4),
            ("amount_type", 4),
        ),
        period_types=(
            (2006, "Actuals"),
            (2007, "Actuals"),
            (2008, "Estimated Actual"),
            (2009, "Main Estimates"),
        ),
    ),
}

PROFILES_2007 = {
    "expenditure": replace(
        PROFILES_2009["expenditure"],
        source_sha256="803822e4b27c1bda6c7c3bbe95c8bc025e1ef67ded6beca55473011d8b62ba21",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2007-11/b07-data-expenses.xls",
        max_rows=2566,
        edition=2007,
        fields=(
            ("Unit", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("MCOA id", "mcoa_id"),
            ("Description", "appropriation_name"),
            ("Expense Type", "appropriation_or_category_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount", "amount"),
            ("Year", "year"),
            ("Type", "amount_type"),
        ),
        definitions=(
            (1, dict(PROFILES_2008["expenditure"].definitions)[1]),
            (3, dict(PROFILES_2008["expenditure"].definitions)[3]),
            (
                4,
                (
                    "This Expense workbook contains details of actual "
                    "government expenditure for the year ended 30 June "
                    "2006, estimated actual government expenditure for "
                    "the year ending 30\xa0June 2007 and budgeted government"
                    " expenditure for the year ending 30 June 2008 as "
                    "published in the 2007 Budget."
                ),
            ),
            (6, dict(PROFILES_2008["expenditure"].definitions)[6]),
            (8, dict(PROFILES_2008["expenditure"].definitions)[8]),
            (
                9,
                (
                    "Definitions relating to classifications used in the "
                    "filters can be found in the Introduction chapter of "
                    "the Estimates of Appropriations document on the "
                    "Budget 2007 CD-Rom or the Treasury website."
                ),
            ),
            (11, dict(PROFILES_2008["expenditure"].definitions)[11]),
            (12, dict(PROFILES_2008["expenditure"].definitions)[12]),
            (13, dict(PROFILES_2008["expenditure"].definitions)[13]),
            (14, dict(PROFILES_2008["expenditure"].definitions)[14]),
            (15, dict(PROFILES_2008["expenditure"].definitions)[15]),
            (16, dict(PROFILES_2008["expenditure"].definitions)[16]),
            (17, dict(PROFILES_2008["expenditure"].definitions)[17]),
            (18, dict(PROFILES_2008["expenditure"].definitions)[18]),
            (19, dict(PROFILES_2008["expenditure"].definitions)[19]),
            (20, dict(PROFILES_2008["expenditure"].definitions)[20]),
            (21, dict(PROFILES_2008["expenditure"].definitions)[21]),
            (22, dict(PROFILES_2008["expenditure"].definitions)[22]),
            (23, dict(PROFILES_2008["expenditure"].definitions)[23]),
            (25, dict(PROFILES_2008["expenditure"].definitions)[25]),
            (27, dict(PROFILES_2008["expenditure"].definitions)[27]),
            (
                28,
                (
                    "These spreadsheets are based on the data contained "
                    "in the Crown Financial Information System, which is "
                    "used to collect and compile the raw data for the "
                    "Estimates 2007/08.  They do not include data from "
                    "the Supplementary Estimates 2006/07. "
                ),
            ),
            (
                30,
                (
                    "Data relating to the 2007/08 fiscal year will match "
                    "the Estimates 2007/08 exactly."
                ),
            ),
            (32, dict(PROFILES_2008["expenditure"].definitions)[32]),
            (34, dict(PROFILES_2008["expenditure"].definitions)[34]),
            (36, dict(PROFILES_2008["expenditure"].definitions)[36]),
        ),
        definition_links=(
            ("source_vintage", 4),
            ("valid_time_end", 4),
            ("amount_type", 4),
        ),
        period_types=(
            (2006, "Actuals"),
            (2007, "Estimated Actual"),
            (2008, "Main Estimates"),
        ),
    ),
    "revenue": replace(
        PROFILES_2009["revenue"],
        source_sha256="bbb62b2d4fb16a35315854adc81899bb416a0cebc3f84f4a971158626b8be3e4",
        source_locator="https://www.treasury.govt.nz/sites/default/files/2007-11/b07-data-revenue.xls",
        max_rows=480,
        edition=2007,
        fields=(
            ("Unit", "department"),
            ("Vote", "vote"),
            ("App id", "app_id"),
            ("Description", "description"),
            ("Revenue Type", "revenue_type"),
            ("Functional Classification", "functional_classification"),
            ("Amount", "amount"),
            ("Year", "year"),
            ("Type", "amount_type"),
        ),
        definitions=(
            (1, dict(PROFILES_2008["revenue"].definitions)[1]),
            (3, dict(PROFILES_2008["revenue"].definitions)[3]),
            (
                4,
                (
                    "The Revenue workbook contains details of  actual "
                    "government revenue and receipts for the year ended "
                    "30 June 2006, estimated actual government revenue "
                    "and receipts for the year ending 30 June 2007 and "
                    "budgeted government revenue and receipts for the "
                    "year ending 30 June 2008 as published in the 2007 "
                    "Budget."
                ),
            ),
            (6, dict(PROFILES_2008["revenue"].definitions)[6]),
            (8, dict(PROFILES_2008["revenue"].definitions)[8]),
            (
                9,
                (
                    "Definitions relating to classifications used in the "
                    "filters can be found in the Introduction chapter of "
                    "the Estimates of Appropriations document on the "
                    "Budget 2007 CD-Rom or the Treasury website."
                ),
            ),
            (11, dict(PROFILES_2008["revenue"].definitions)[11]),
            (12, dict(PROFILES_2008["revenue"].definitions)[12]),
            (13, dict(PROFILES_2008["revenue"].definitions)[13]),
            (14, dict(PROFILES_2008["revenue"].definitions)[14]),
            (15, dict(PROFILES_2008["revenue"].definitions)[15]),
            (16, dict(PROFILES_2008["revenue"].definitions)[16]),
            (17, dict(PROFILES_2008["revenue"].definitions)[17]),
            (18, dict(PROFILES_2008["revenue"].definitions)[18]),
            (19, dict(PROFILES_2008["revenue"].definitions)[19]),
            (20, dict(PROFILES_2008["revenue"].definitions)[20]),
            (21, dict(PROFILES_2008["revenue"].definitions)[21]),
            (22, dict(PROFILES_2008["revenue"].definitions)[22]),
            (23, dict(PROFILES_2008["revenue"].definitions)[23]),
            (25, dict(PROFILES_2008["revenue"].definitions)[25]),
            (27, dict(PROFILES_2008["revenue"].definitions)[27]),
            (
                28,
                (
                    "These spreadsheets are based on the data contained "
                    "in the Crown Financial Information System, which was"
                    " used to collect and compile the raw data for the "
                    "Estimates 2007/08.  They do not include data from "
                    "the Supplementary Estimates 2006/07. "
                ),
            ),
            (
                30,
                (
                    "Data relating to the 2007/08 fiscal year will match "
                    "the Estimates 2007/08 exactly."
                ),
            ),
            (32, dict(PROFILES_2008["revenue"].definitions)[32]),
            (34, dict(PROFILES_2008["revenue"].definitions)[34]),
            (36, dict(PROFILES_2008["revenue"].definitions)[36]),
        ),
        definition_links=(
            ("source_vintage", 4),
            ("valid_time_end", 4),
            ("amount_type", 4),
        ),
        period_types=(
            (2006, "Actuals"),
            (2007, "Estimated Actual"),
            (2008, "Main Estimates"),
        ),
    ),
}


def declared_profiles() -> tuple[BiffBudgetProfile, ...]:
    """Expose only the twenty-six independently pinned source-edition profiles."""
    return (
        *PROFILES.values(),
        *PROFILES_2018.values(),
        *PROFILES_2017.values(),
        *PROFILES_2016.values(),
        *PROFILES_2015.values(),
        *PROFILES_2014.values(),
        *PROFILES_2013.values(),
        *PROFILES_2012.values(),
        *PROFILES_2011.values(),
        *PROFILES_2010.values(),
        *PROFILES_2009.values(),
        *PROFILES_2008.values(),
        *PROFILES_2007.values(),
    )


NUMERIC_SCHEMA = pa.schema(
    [pa.field("source_object_sha256", pa.string()), *biff8_projection.NUMERIC_SCHEMA]
)
LINEAGE_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("lineage_id", pa.string()),
        ("field", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_coordinate", pa.string()),
        ("source_row", pa.int64()),
        ("source_column", pa.int64()),
        ("raw_value", pa.string()),
        ("normalized_value", pa.string()),
        ("value_basis", pa.string()),
        ("numeric_evidence_id", pa.string()),
        ("rule", pa.string()),
    ]
)
DISPOSITION_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("sheet", pa.string()),
        ("source_row", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
        ("record_id", pa.string()),
        ("decoded_values_json", pa.string()),
    ]
)


@dataclass(frozen=True, slots=True)
class BiffBudgetSnapshot:
    """All companion tables and bounded source observations for one interpretation."""

    tables: Mapping[str, pa.Table]
    metadata: Mapping[str, Any]


def _require(condition: object) -> None:
    if not condition:
        message = "budget_biff8_contract"
        raise ValueError(message)


def _definitions(payload: bytes, profile: BiffBudgetProfile) -> biff8_records.BiffSheet:
    sheet = biff8_records.read_sheet(
        payload, profile.source_sha256, sheet="Explanation"
    )
    for row, expected in profile.definitions:
        _require(
            row not in sheet.formula_rows
            and row not in sheet.error_rows
            and 1 <= row <= len(sheet.values)
            and len(sheet.values[row - 1]) >= _DEFINITION_COLUMN
            and type(sheet.values[row - 1][1]) is str
            and sheet.values[row - 1][1] == expected
        )
    return sheet


def _selected_reason(values: dict[str, Any], profile: BiffBudgetProfile) -> str | None:
    required = (
        (
            "department",
            "appropriation_name",
            "category_name",
            "appropriation_or_category_type",
            "functional_classification",
            "portfolio_name",
        )
        if profile.kind == "expenditure"
        else ("department", "description", "revenue_type")
    )
    period_types = dict(profile.period_types)
    checks = [
        (
            any(
                type(values[field]) is not str or not values[field].strip()
                for field in required
                if field not in profile.absent_fields
            ),
            "missing_label",
        ),
        (
            any(
                values[field] <= 0
                for field, _ in profile.numeric_columns
                if field not in {"amount", "year"}
            ),
            "invalid_source_id",
        ),
        (
            values["year"] not in period_types
            or values["amount_type"] != period_types.get(values["year"]),
            "invalid_period_type",
        ),
        (exact_number(values["amount"]) is None, "invalid_amount_range"),
    ]
    if profile.kind == "revenue":
        checks.append(
            (
                values["revenue_type"] not in {"Non-Tax Revenue", "Capital Receipts"},
                "invalid_revenue_type",
            )
        )
    else:
        checks.extend(
            [
                (
                    any(
                        values[field] is not None and type(values[field]) is not str
                        for field in ("restriction_type", "current_scope")
                        if field not in profile.absent_fields
                    ),
                    "invalid_optional_label",
                ),
                (
                    "group_type" not in profile.absent_fields
                    and values["group_type"] not in profile.group_types,
                    "invalid_group_type",
                ),
                (
                    "periodicity" not in profile.absent_fields
                    and values["periodicity"] not in {"A", "M"},
                    "invalid_periodicity",
                ),
            ]
        )
    if profile.edition in _LEGACY_DIMENSION_EDITIONS:
        checks.append((values["periodicity"] != "A", "invalid_source_qualifier"))
        if profile.kind == "expenditure":
            checks.append(
                (
                    values["output_expense_type"]
                    not in (
                        {None, "Permanent Legislative Authority", "Revenue Dependent"}
                        if profile.edition in _REVENUE_DEPENDENT_EDITIONS
                        else {None, "Permanent Legislative Authority"}
                    ),
                    "invalid_source_qualifier",
                )
            )
    if profile.edition == _SOURCE_QUALIFIER_EDITION:
        checks.append(
            (
                (values["is_mca"] != ("Yes" if values["group_type"] == "MCA" else "No"))
                if profile.kind == "expenditure"
                else values["periodicity"] != "A",
                "invalid_source_qualifier",
            )
        )
    return next((reason for invalid, reason in checks if invalid), None)


def _scope(
    raw: biff8_records.BiffSheet, row: int, values: dict[str, Any]
) -> tuple[str, str] | None:
    if all(value is None for value in values.values()):
        return "blank", "empty_row"
    if type(values["vote"]) is not str or not values["vote"].strip():
        return "rejected", "invalid_vote"
    if values["vote"] != "Health":
        return "out_of_scope", "non_health_vote"
    if row in raw.formula_rows:
        return "rejected", "formula_not_evaluated"
    if row in raw.error_rows:
        return "rejected", "spreadsheet_error"
    return None


def _classify(
    raw: biff8_records.BiffSheet,
    row: int,
    profile: BiffBudgetProfile,
) -> tuple[str, str, dict[str, Any], list[biff8_records.NumericWitness]]:
    values = dict(
        zip((field for _, field in profile.fields), raw.values[row - 1], strict=True)
    )
    scope = _scope(raw, row, values)
    if scope is not None:
        return *scope, values, []
    witnesses = []
    try:
        for field, column in profile.numeric_columns:
            witness = raw.integer_cell(row, column)
            values[field] = raw.verify_integer(witness, row=row, column=column)
            witnesses.append(witness)
    except ValueError as error:
        return "rejected", str(error), values, []
    reason = _selected_reason(values, profile)
    if reason:
        return "rejected", reason, values, []
    return "normalized", "named_biff8_columns", values, witnesses


def _fact(
    context: dict[str, Any],
    profile: BiffBudgetProfile,
    row: int,
    values: dict[str, Any],
    witnesses: list[biff8_records.NumericWitness],
) -> dict[str, Any]:
    record_id = identity(profile.transformation, profile.source_sha256, "Raw Data", row)
    by_field = dict(
        zip((field for field, _ in profile.numeric_columns), witnesses, strict=True)
    )
    return {
        **context,
        **dict.fromkeys(profile.absent_fields),
        **values,
        "record_id": record_id,
        "schema_version": f"archive-govt-nz.health-budget-biff8-{profile.kind}-fact/v1",
        "recordset": f"budget_{profile.kind}_fact",
        "source_row": row,
        "amount": exact_number(values["amount"]),
        "value_basis": BASIS,
        "canonical_stored_integer": by_field["amount"].canonical_stored_integer,
        "numeric_evidence_id": by_field["amount"].numeric_evidence_id,
        "unit": profile.unit,
        "currency": None,
        "valid_time_start": None,
        "valid_time_end": date(values["year"], 6, 30),
        "rights_state": "not_evaluated",
        "quality_flags": [
            "iso_currency_not_verified",
            "period_start_not_asserted",
            *(["amount_scale_not_verified"] if profile.unit is None else []),
            "no_parent_category_aggregation",
            "source_classification_unmapped",
            *("source_field_absent_" + field for field in profile.absent_fields),
            *(
                ["source_parent_relationship_not_asserted"]
                if profile.edition == _SOURCE_PARENT_IDENTIFIER_EDITION
                and profile.kind == "revenue"
                else []
            ),
            *(
                ["source_edition_conflict_resolved_by_title_and_estimates_context"]
                if profile.edition == _SOURCE_QUALIFIER_EDITION
                and profile.kind == "revenue"
                else []
            ),
        ],
        "transformation_id": profile.transformation,
        "lineage_id": identity(record_id, "lineage"),
    }


def _lineage(
    profile: BiffBudgetProfile,
    fact: dict[str, Any],
    values: dict[str, Any],
    witnesses: list[biff8_records.NumericWitness],
) -> list[dict[str, Any]]:
    by_field = dict(
        zip((field for field, _ in profile.numeric_columns), witnesses, strict=True)
    )
    result = []
    for column, (_, field) in enumerate(profile.fields, 1):
        witness = by_field.get(field)
        result.append(
            {
                "record_id": fact["record_id"],
                "lineage_id": fact["lineage_id"],
                "field": field,
                "source_object_sha256": profile.source_sha256,
                "source_locator": profile.source_locator,
                "source_coordinate": (
                    f"'Raw Data'!{get_column_letter(column)}{fact['source_row']}"
                ),
                "source_row": fact["source_row"],
                "source_column": column,
                "raw_value": None if witness else values[field],
                "normalized_value": None if fact[field] is None else str(fact[field]),
                "value_basis": BASIS if witness else "source_text/v1",
                "numeric_evidence_id": witness.numeric_evidence_id if witness else None,
                "rule": profile.transformation,
            }
        )
    definitions = dict(profile.definitions)
    for field, row in profile.definition_links:
        result.append(
            {
                "record_id": fact["record_id"],
                "lineage_id": fact["lineage_id"],
                "field": field,
                "source_object_sha256": profile.source_sha256,
                "source_locator": profile.source_locator,
                "source_coordinate": f"'Explanation'!B{row}",
                "source_row": row,
                "source_column": 2,
                "raw_value": definitions[row],
                "normalized_value": str(fact[field]),
                "value_basis": "source_text/v1",
                "numeric_evidence_id": None,
                "rule": profile.transformation,
            }
        )
    return result


def parse_snapshot(
    payload: bytes, *, profile: BiffBudgetProfile, observed_at: str
) -> BiffBudgetSnapshot:
    """Interpret one hash-pinned source without writing or granting source rights."""
    _require(
        profile.kind in {"expenditure", "revenue"}
        and type(profile.edition) is int
        and profile.edition
        in {
            2007,
            2008,
            2009,
            2010,
            2011,
            2012,
            2013,
            2014,
            2015,
            2016,
            2017,
            2018,
            2019,
        }
    )
    _require(
        profile.unit == (None if profile.edition in _UNSCALED_EDITIONS else "$000")
        and profile.absent_fields
        == (
            _ABSENT_FIELDS_2009[profile.kind]
            if profile.edition in _UNSCALED_EDITIONS
            else (*_ABSENT_FIELDS_2013["expenditure"], "current_scope")
            if profile.edition in _NO_SCOPE_EXPENDITURE_EDITIONS
            and profile.kind == "expenditure"
            else _ABSENT_FIELDS_2013[profile.kind]
            if profile.edition in _LEGACY_DIMENSION_EDITIONS
            else _ABSENT_EXPENDITURE_FIELDS_2015
            if profile.kind == "expenditure" and profile.edition in {2014, 2015}
            else ()
        )
        and not set(profile.absent_fields) & {field for _, field in profile.fields}
    )
    context = source_context(
        profile.source_sha256,
        profile.source_locator,
        profile.source_vintage,
        observed_at,
    )
    raw = biff8_records.read_sheet(payload, profile.source_sha256, sheet="Raw Data")
    _definitions(payload, profile)
    _require(
        1 < len(raw.values) <= profile.max_rows + 1
        and (
            (*raw.values[0][:12], "")
            if profile.edition == _UNLABELLED_COLUMN_EDITION
            and profile.kind == "expenditure"
            and len(raw.values[0]) == _UNLABELLED_COLUMN_COUNT
            and raw.values[0][12] is None
            else raw.values[0]
        )
        == tuple(header for header, _ in profile.fields)
        and 1 not in raw.formula_rows
        and 1 not in raw.error_rows
    )
    if profile.edition == _UNLABELLED_COLUMN_EDITION and profile.kind == "expenditure":
        _require(
            all(
                len(row) == _UNLABELLED_COLUMN_COUNT and row[12] is None
                for row in raw.values[1:]
            )
        )
    facts, lineage, dispositions, numeric = [], [], [], []
    for row in range(2, len(raw.values) + 1):
        _require(len(raw.values[row - 1]) == len(profile.fields))
        _require(all(len(str(value)) <= MAX_TEXT for value in raw.values[row - 1]))
        decoded_json = encode_json(
            dict(
                zip(
                    (header for header, _ in profile.fields),
                    raw.values[row - 1],
                    strict=True,
                )
            )
        )
        state, reason, values, witnesses = _classify(raw, row, profile)
        fact = (
            _fact(context, profile, row, values, witnesses)
            if state == "normalized"
            else None
        )
        dispositions.append(
            {
                "source_object_sha256": profile.source_sha256,
                "source_locator": profile.source_locator,
                "sheet": "Raw Data",
                "source_row": row,
                "disposition": state,
                "reason": reason,
                "record_id": fact["record_id"] if fact else None,
                "decoded_values_json": decoded_json,
            }
        )
        if fact is None:
            continue
        fact["decoded_values_json"] = decoded_json
        _require(set(fact) == set(profile.fact_schema.names))
        links = _lineage(profile, fact, values, witnesses)
        biff8_projection.replay_projection(
            raw,
            fact,
            [w.to_record() for w in witnesses],
            [link for link in links if link["numeric_evidence_id"] is not None],
            columns=dict(profile.numeric_columns),
        )
        facts.append(fact)
        lineage.extend(links)
        numeric.extend(
            {"source_object_sha256": profile.source_sha256, **w.to_record()}
            for w in witnesses
        )
    tables = {
        "budget_facts.parquet": pa.Table.from_pylist(facts, schema=profile.fact_schema),
        "field_lineage.parquet": pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA),
        "row_dispositions.parquet": pa.Table.from_pylist(
            dispositions, schema=DISPOSITION_SCHEMA
        ),
        "numeric_evidence.parquet": pa.Table.from_pylist(
            numeric, schema=NUMERIC_SCHEMA
        ),
    }
    counts = {
        state: sum(row["disposition"] == state for row in dispositions)
        for state in ("normalized", "out_of_scope", "blank", "rejected")
    }
    counts["input"] = len(dispositions)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "profile": profile.profile_id,
        "transformation_id": profile.transformation,
        "source_object_sha256": profile.source_sha256,
        "source_locator": profile.source_locator,
        "source_vintage": profile.source_vintage,
        "observed_at": context["observed_at"].isoformat(),
        "rights_state": "not_evaluated",
        "value_basis": BASIS,
        "status": "partial" if counts["rejected"] else "passed" if facts else "empty",
        "counts": counts,
        "workbook_inventory": raw.inventory,
        "decoded_values_semantics": "reader_values_only_not_source_decimal_tokens",
        "excluded_sheets": [
            {
                "sheet": b.name,
                "reason": "preserved_context_sheet_inventoried_only",
            }
            for b in raw.bindings
            if b.name != "Raw Data"
        ],
        "definitions": [
            {
                "source_coordinate": f"'Explanation'!B{row}",
                "text_sha256": identity(text),
            }
            for row, text in profile.definitions
        ],
    }
    if profile.edition == _SOURCE_QUALIFIER_EDITION and profile.kind == "revenue":
        metadata["edition_resolution"] = {
            "status": "resolved_from_independent_source_context",
            "conflicting_coordinate": "'Explanation'!B10",
            "conflicting_text_retained": True,
            "authoritative_coordinates": [
                "'Explanation'!B" + str(n) for n in (1, 4, 24, 26, 34)
            ],
            "publisher_locator": "https://www.treasury.govt.nz/publications/data/budget-2014-data-estimates-appropriations-2014-15",
            "publisher_correction_claimed": False,
        }
    return BiffBudgetSnapshot(tables, metadata)
