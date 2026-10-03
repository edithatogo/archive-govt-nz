"""Fail-closed headline summary extraction for exact Vote Health editions."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from pypdf import PdfReader

from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    source_context,
    verified_snapshot,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MAX_TEXT = 200_000
PROFILE = "vote-health-estimates-2002-03-overview/v1"
TRANSFORMATION = "vote-health-estimates-overview-2002-03/v1"
VINTAGE = "Treasury-Vote-Health-Estimates-2002-03"
SOURCE_SHA256 = "1170e0bf5d11e6ac93620a2d76d68004ed99b88ed45a0c6c3c48bbc38f72fafe"
PAGE_COUNT = 44
OVERVIEW_PAGE_COUNT = 2
PROFILE_2004_05 = "vote-health-estimates-2004-05-overview/v1"
TRANSFORMATION_2004_05 = "vote-health-estimates-overview-2004-05/v1"
VINTAGE_2004_05 = "Treasury-Vote-Health-Estimates-2004-05"
SOURCE_SHA256_2004_05 = (
    "6dac0aaa3fd181fffacf30cffa829b0f189e8b68ebfdbeb0dd5ef88736af96a2"
)
PAGE_COUNT_2004_05 = 48
PROFILE_2005_06 = "vote-health-estimates-2005-06-overview/v1"
TRANSFORMATION_2005_06 = "vote-health-estimates-overview-2005-06/v1"
VINTAGE_2005_06 = "Treasury-Vote-Health-Estimates-2005-06"
SOURCE_SHA256_2005_06 = (
    "9a269a87a0cef8fc998fc1b012ae9fd734fb48b111504bb7a1ca01cdcf97c2b4"
)
PAGE_COUNT_2005_06 = 50
PROFILE_2006_07 = "vote-health-estimates-2006-07-overview/v1"
TRANSFORMATION_2006_07 = "vote-health-estimates-overview-2006-07/v1"
VINTAGE_2006_07 = "Treasury-Vote-Health-Estimates-2006-07"
SOURCE_SHA256_2006_07 = (
    "866bce96ac216344c5dcdf25fee1f31548d5c32ba3cd94ef4b4977a495f509ea"
)
PAGE_COUNT_2006_07 = 41
PROFILE_2007_08 = "vote-health-estimates-2007-08-overview/v1"
TRANSFORMATION_2007_08 = "vote-health-estimates-overview-2007-08/v1"
VINTAGE_2007_08 = "Treasury-Vote-Health-Estimates-2007-08"
SOURCE_SHA256_2007_08 = (
    "fccd1fe0001e12f8238e6c4618328eac2da8d26729f997265b05688ec89a2795"
)
PAGE_COUNT_2007_08 = 53
PROFILE_2008_09 = "vote-health-estimates-2008-09-overview/v1"
TRANSFORMATION_2008_09 = "vote-health-estimates-overview-2008-09/v1"
VINTAGE_2008_09 = "Treasury-Vote-Health-Estimates-2008-09"
SOURCE_SHA256_2008_09 = (
    "2d346a460278fa278eef4fbda3f613d18bc13b486a1f2e21e503a05b5d3f9121"
)
PAGE_COUNT_2008_09 = 8
PROFILE_2009_10 = "vote-health-estimates-2009-10-overview/v1"
TRANSFORMATION_2009_10 = "vote-health-estimates-overview-2009-10/v1"
VINTAGE_2009_10 = "Treasury-Vote-Health-Estimates-2009-10"
SOURCE_SHA256_2009_10 = (
    "acd253a1d68738a06e5310c002f8051698146fe018d3d6c10fc6b5e0f6d7ac1f"
)
PAGE_COUNT_2009_10 = 8
PROFILE_2010_11 = "vote-health-estimates-2010-11-overview/v1"
TRANSFORMATION_2010_11 = "vote-health-estimates-overview-2010-11/v1"
VINTAGE_2010_11 = "Treasury-Vote-Health-Estimates-2010-11"
SOURCE_SHA256_2010_11 = (
    "5dabf866e4f60c5fdf9df88b3fcc5b0e537652d1d6817465efb46a97c0bbe497"
)
PAGE_COUNT_2010_11 = 9
PROFILE_2011_12 = "vote-health-estimates-2011-12-overview/v1"
TRANSFORMATION_2011_12 = "vote-health-estimates-overview-2011-12/v1"
VINTAGE_2011_12 = "Treasury-Vote-Health-Estimates-2011-12"
SOURCE_SHA256_2011_12 = (
    "5b56c8a0641a870d82558f2c61fc87df90bcabf318541af4c3d86ba8ce3063af"
)
PAGE_COUNT_2011_12 = 9
_PROFILE_QUALIFIER_MEASURES_2010_11 = frozenset(
    {"departmental_functions", "health_sector_risk_management"}
)
_PROFILE_QUALIFIER_MEASURES_2011_12 = frozenset(
    {
        "departmental_functions",
        "national_health_services_and_risk_management",
        "clinical_training",
    }
)
_ERROR = "vote_health_estimates_overview_contract"
_AMOUNT_TOKEN_PATTERN = r"(?P<value>[0-9][0-9,]*\.[0-9]{3})"  # noqa: S105 - regex token, not a secret
_PATTERNS = {
    "vote_total": (
        2,
        (
            rf"Appropriations sought for Vote Health in 2002/03 total "
            rf"\${_AMOUNT_TOKEN_PATTERN} million\b(?![0-9])"
        ),
        "$ million",
        "2002/03",
    ),
    "vote_increase": (
        2,
        rf"an increase of \${_AMOUNT_TOKEN_PATTERN} million\b",
        "$ million",
        "2001/02_to_2002/03",
    ),
    "departmental_total": (
        2,
        rf"Departmental appropriations total \${_AMOUNT_TOKEN_PATTERN} million",
        "$ million",
        "2002/03",
    ),
    "non_departmental_total": (
        2,
        rf"\${_AMOUNT_TOKEN_PATTERN} million \(97\.5% of the Vote\) is for the funder",
        "$ million",
        "2002/03",
    ),
    "other_services_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million "
            r"\(0\.3% of the Vote\) relates to other services"
        ),
        "$ million",
        "2002/03",
    ),
    "other_expenses_total": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million "
            r"\(0\.2% of the Vote\) relates to other expenses"
        ),
        "$ million",
        "2002/03",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN} million of Crown "
            r"revenue in 2002/03"
        ),
        "$ million",
        "2002/03",
    ),
}
_PATTERNS_2004_05 = {
    "vote_total": (
        2,
        (
            rf"Appropriations sought for Vote Health in 2004/05 total "
            rf"\${_AMOUNT_TOKEN_PATTERN} million"
        ),
        "$ million",
        "2004/05",
    ),
    "vote_increase": (
        2,
        (
            rf"an increase of \${_AMOUNT_TOKEN_PATTERN} million or 3\.47% "
            r"from 2003/04 \(Supplementary Estimates\)"
        ),
        "$ million",
        "2003/04_to_2004/05",
    ),
    "departmental_functions": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(1\.70% of the Vote\) "
            r"relates to the functions of the Ministry of Health"
        ),
        "$ million",
        "2004/05",
    ),
    "departmental_capital_contribution": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(0\.01% of the Vote\) "
            r"is a capital contribution to the Ministry of Health"
        ),
        "$ million",
        "2004/05",
    ),
    "non_departmental_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(98\.29% of the Vote\) "
            r"is for the funders of health services"
        ),
        "$ million",
        "2004/05",
    ),
    "capital_funding": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(5\.48% of the Vote\) "
            r"is to provide capital funding and loan facilities"
        ),
        "$ million",
        "2004/05",
    ),
    "other_services_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN} million \(0\.60% of the Vote\) "
            r"relates to other services"
        ),
        "$ million",
        "2004/05",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN} million of Crown "
            "Revenue and Receipts in 2004/05"
        ),
        "$ million",
        "2004/05",
    ),
}
_AMOUNT_TOKEN_PATTERN_2005_06 = r"(?P<value>[0-9][0-9,]*(?:\.[0-9]{1,3})?)"  # noqa: S105 - regex token, not a secret
_PATTERNS_2005_06 = {
    "vote_total": (
        2,
        (
            rf"Appropriations sought for Vote Health in 2005/06 total \$"
            rf"{_AMOUNT_TOKEN_PATTERN_2005_06} million \(GST exclusive\)"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "vote_increase": (
        2,
        (
            rf"an increase of \${_AMOUNT_TOKEN_PATTERN_2005_06} million or 9\.3% "
            r"from 2004/05 \(Supplementary Estimates\)"
        ),
        "$ million, GST exclusive",
        "2004/05_to_2005/06",
    ),
    "departmental_functions": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(1\.55% of the Vote\) "
            r"relates to the functions of the Ministry of Health"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "non_departmental_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(98\.45% of the Vote\) "
            r"is for non-departmental expenditure"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "service_funding_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(93\.47% of the Vote\) "
            r"is for the funders of health services"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "other_expenses_total": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(0\.18% of the Vote\) "
            r"is for other expenses\b"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "capital_funding": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2005_06} million \(4\.77% of the Vote\) "
            r"is to provide capital funding\b"
        ),
        "$ million, GST exclusive",
        "2005/06",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN_2005_06} million of Crown "
            r"Revenue and Receipts in 2005/06"
        ),
        "$ million, GST inclusive",
        "2005/06",
    ),
}
_AMOUNT_TOKEN_PATTERN_2006_07 = r"(?P<value>[0-9][0-9,]*\.[0-9]{3})"  # noqa: S105 - regex token, not a secret
_PATTERNS_2006_07 = {
    "vote_total": (
        2,
        (
            r"Appropriations sought for Vote Health in 2006/07 total "
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million"
        ),
        "$ million",
        "2006/07",
    ),
    "vote_increase": (
        2,
        (
            rf"an increase of \${_AMOUNT_TOKEN_PATTERN_2006_07} million or 8\.51% "
            r"from 2005/06"
        ),
        "$ million",
        "2005/06_to_2006/07",
    ),
    "departmental_functions": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(1\.48% of the Vote\) relates to the functions of the Ministry of Health"
        ),
        "$ million",
        "2006/07",
    ),
    "non_departmental_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(98\.52% of the Vote\) is for operating expenses incurred "
            r"on behalf of the Crown"
        ),
        "$ million",
        "2006/07",
    ),
    "service_funding_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(94\.73% of the Vote\) is for the funders of health services"
        ),
        "$ million",
        "2006/07",
    ),
    "other_expenses_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(0\.22% of the Vote\) is for other expenses"
        ),
        "$ million",
        "2006/07",
    ),
    "capital_funding": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(3\.58% of the Vote\) is to provide capital funding"
        ),
        "$ million",
        "2006/07",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN_2006_07} million of Crown "
            r"Revenue and Receipts in 2006/07"
        ),
        "$ million",
        "2006/07",
    ),
}
_PATTERNS_2007_08 = {
    "vote_total": (
        2,
        (
            rf"Appropriations sought for Vote Health in 2007/08 total "
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million"
        ),
        "$ million",
        "2007/08",
    ),
    "vote_increase": (
        2,
        (
            rf"an increase of \${_AMOUNT_TOKEN_PATTERN_2006_07} million or "
            r"14\.56% from 2006/07"
        ),
        "$ million",
        "2006/07_to_2007/08",
    ),
    "departmental_functions": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(1\.71% of the Vote\) relates to the functions of the Ministry of Health"
        ),
        "$ million",
        "2007/08",
    ),
    "non_departmental_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(98\.29% of the Vote\) is for expenses incurred on behalf of the Crown"
        ),
        "$ million",
        "2007/08",
    ),
    "service_funding_total": (
        2,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(91\.05% of the Vote\) is for funding and purchases of health services"
        ),
        "$ million",
        "2007/08",
    ),
    "other_expenses_total": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(0\.15% of the Vote\) is for other expenses"
        ),
        "$ million",
        "2007/08",
    ),
    "capital_funding": (
        3,
        (
            rf"\${_AMOUNT_TOKEN_PATTERN_2006_07} million "
            r"\(7\.09% of the Vote\) is to provide capital funding"
        ),
        "$ million",
        "2007/08",
    ),
    "crown_revenue_total": (
        3,
        (
            rf"expects to collect \${_AMOUNT_TOKEN_PATTERN_2006_07} million of "
            r"Crown Revenue and Receipts in 2007/08"
        ),
        "$ million",
        "2007/08",
    ),
}
_AMOUNT_TOKEN_PATTERN_2008_09 = r"(?P<value>[0-9][0-9,]*)"  # noqa: S105 - regex token, not a secret
_PATTERNS_2008_09 = {
    "vote_total": (
        2,
        (
            r"financial year\s+totalling just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "departmental_functions": (
        2,
        (
            r"Departmental Operating Appropriations\s+A total of just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(1\.9% of the Vote\) relates to the functions of the Ministry of Health"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "non_departmental_total": (
        2,
        (
            r"Non-Departmental Operating Appropriations\s+A total of just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(96\.1% of the Vote\) is for operating expenses to be incurred "
            r"on behalf of the Crown"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "service_funding_total": (
        2,
        (
            r"Output Expenses\s+These total just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(95\.9% of the Vote\) and are to fund the purchases of health services"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "other_expenses_total": (
        2,
        (
            r"Other Expenses Incurred by the Crown\s+A total of just over "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(0\.2% of the Vote\) is for other expenses"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
    "capital_funding": (
        2,
        (
            r"Capital Expenditure\s+A total of nearly "
            rf"\${_AMOUNT_TOKEN_PATTERN_2008_09} million "
            r"\(2\.0% of the Vote\) is to provide capital funding"
        ),
        "$ million, approximate rounded source amount",
        "2008/09",
    ),
}
_PATTERNS_2009_10 = {
    "vote_total": (
        2,
        (
            r"financial year\s+totalling just under "
            r"\$(?P<value>[0-9][0-9,]*) million"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "vote_increase": (
        2,
        (
            r"an increase of \$(?P<value>[0-9][0-9,]*) million or 7\.4% "
            r"from 2008/09 \(Supplementary Estimates\)"
        ),
        "$ million, approximate rounded source amount",
        "2008/09_to_2009/10",
    ),
    "departmental_functions": (
        2,
        (
            r"Departmental Operating Appropriations\s+A total of just over "
            r"\$(?P<value>[0-9][0-9,]*) million \(1\.7% of the Vote\) relates "
            r"to the functions of the Ministry of Health"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "non_departmental_total": (
        2,
        (
            r"Non-Departmental Operating Appropriations\s+A total of nearly "
            r"\$(?P<value>[0-9][0-9,]*) million \(95\.6% of the Vote\) is for "
            r"operating expenses to be incurred on behalf of the Crown"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "output_expenses_total": (
        2,
        (
            r"Output Expenses\s+These total just over "
            r"\$(?P<value>[0-9][0-9,]*) million \(95\.5% of the Vote\)"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "dhb_services": (
        2,
        (
            r"Nearly \$(?P<value>[0-9][0-9,]*) million \(74\.8% of the Vote\) "
            r"to fund health services from DHBs"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "national_disability_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(6\.9% of the Vote\) "
            r"to purchase national disability support services"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "public_health_services": (
        2,
        (
            r"Nearly \$(?P<value>[0-9][0-9,]*) million \(4\.0% of the Vote\) "
            r"to purchase public health services"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "national_health_services_and_training": (
        2,
        (
            r"Almost \$(?P<value>[0-9][0-9,]*) million \(6\.5% of the Vote\) "
            r"to purchas\s*e national health services and provide clinical training"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "health_sector_risk_management": (
        2,
        (
            r"Nearly \$(?P<value>[0-9][0-9,]*) million \(1\.9% of the Vote\) "
            r"to manage health sector risks"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "primary_health_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(1\.2% of the Vote\) "
            r"to purchase primary health care services"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "other_health_services": (
        2,
        (
            r"Nearly \$(?P<value>[0-9][0-9,]*) million \(0\.3% of the Vote\) "
            r"to fund other health and disability services"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "other_expenses_total": (
        2,
        (
            r"Other Expenses Incurred by the Crown\s+A total of nearly "
            r"\$(?P<value>[0-9][0-9,]*) million \(0\.2% of the Vote\) is for "
            r"other expenses"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "capital_expenditure": (
        2,
        (
            r"Capital Expenditure\s+A total of nearly "
            r"\$(?P<value>[0-9][0-9,]*) million \(2\.7% of the Vote\) is to "
            r"provide capital funding"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "dhb_and_blood_service_capital": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(2\.3 % of the Vote\) "
            r"is to prov\s*ide debt or equity for District Health Boards"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "long_term_care_interest_free_loans": (
        2,
        (
            r"\$(?P<value>[0-9][0-9,]*) million \(0\.1% of the Vote\) is to "
            r"provide intere\s*st-free loans"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
    "ministry_asset_purchases": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(0\.3% of the Vote\) "
            r"is to purchase or develop assets for use by the Ministry of Health"
        ),
        "$ million, approximate rounded source amount",
        "2009/10",
    ),
}
_PATTERNS_2010_11 = {
    "vote_total": (
        2,
        r"financial year\s+totalling just under \$(?P<value>[0-9][0-9,]*) million",
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "vote_increase": (
        2,
        (
            r"an increase of \$(?P<value>[0-9][0-9,]*) million or 6\.7% "
            r"from 2009/10 \(Supplementary Estimates\)"
        ),
        "$ million, approximate rounded source amount",
        "2009/10_to_2010/11",
    ),
    "departmental_functions": (
        2,
        (
            r"Departmental Operating Appropriations\s+A total of just over "
            r"\$(?P<value>[0-9][0-9,]*) million \(1\.6% of the Vote\) relates "
            r"to the functions of the Ministry of Health"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "non_departmental_total": (
        2,
        (
            r"Non-Departmental Operating Appropriations\s+A total of nearly "
            r"\$(?P<value>[0-9][0-9,]*) million \(94\.6% of the Vote\) is for "
            r"operating expenses to be incurred on behalf of the Crown"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "output_expenses_total": (
        2,
        (
            r"Output Expenses\s+These total nearly \$(?P<value>[0-9][0-9,]*) "
            r"million \(94\.4% of the Vote\)"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "dhb_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(74\.0% of the Vote\) "
            r"to fund health services from DHBs"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "national_disability_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(7\.1% of the Vote\) "
            r"to purchase national disability support services"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "public_health_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(3\.8% of the Vote\) "
            r"to purchase public health services"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "national_health_services_and_training": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(6\.7% of the Vote\) "
            r"to purch\s*ase national health services and provide clinical training"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "health_sector_risk_management": (
        2,
        (
            r"Nearly \$(?P<value>[0-9][0-9,]*) million \(0\.1% of the Vote\) "
            r"to manage health sector risks"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "dhb_deficit_support_provision": (
        2,
        (
            r"\$(?P<value>[0-9][0-9,]*) million \(0\.7% of the Vote\) for a "
            r"provision for DHB deficit support"
        ),
        "$ million, approximate source amount",
        "2010/11",
    ),
    "primary_health_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(1\.4% of the Vote\) "
            r"to purchase primary health care services"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "other_health_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(0\.6% of the Vote\) "
            r"to fund other health and disability services"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "other_expenses_total": (
        2,
        (
            r"Other Expenses Incurred by the Crown\s+A total of nearly "
            r"\$(?P<value>[0-9][0-9,]*) million \(0\.2% of the Vote\) is for "
            r"other expenses"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "capital_expenditure": (
        3,
        (
            r"Capital Expenditure\s+A total of nearly \$(?P<value>[0-9][0-9,]*) "
            r"million \(3\.8% of the Vote\) is to provide capital funding"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "dhb_and_agency_capital": (
        3,
        (
            r"Nearly \$(?P<value>[0-9][0-9,]*) million \(3\.5 % of the Vote\) "
            r"is to provide d\s*ebt or equity for District Health Boards"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
    "long_term_care_interest_free_loans": (
        3,
        (
            r"\$(?P<value>[0-9][0-9,]*) million \(0\.1% of the Vote\) is to "
            r"provide intere\s*st-free loans"
        ),
        "$ million, approximate source amount",
        "2010/11",
    ),
    "ministry_asset_purchases": (
        3,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(0\.1% of the Vote\) "
            r"is to purchase or develop assets for use by the Ministry of Health"
        ),
        "$ million, approximate rounded source amount",
        "2010/11",
    ),
}
_PATTERNS_2011_12 = {
    "vote_total": (
        2,
        r"financial year\s+totalling just over \$(?P<value>[0-9][0-9,]*) million",
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "departmental_functions": (
        2,
        (
            r"Departmental Operating Appropriations\s+A total of almost "
            r"\$(?P<value>[0-9][0-9,]*) million \(1\.5% of the Vote\) relates "
            r"to the functions of the Ministry of Health"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "non_departmental_total": (
        2,
        (
            r"Non-Departmental Operating Appropriations\s+A total of nearly "
            r"\$(?P<value>[0-9][0-9,]*) million \(95\.3% of the Vote\) is for "
            r"operating expenses to be incurred on behalf of the Crown"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "output_expenses_total": (
        2,
        (
            r"Output Expenses\s+These total nearly \$(?P<value>[0-9][0-9,]*) "
            r"million \(95\.1% of the Vote\)"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "dhb_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(75\.2% of the Vote\) "
            r"to fund health services from DHBs"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "national_disability_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(7\.4% of the Vote\) "
            r"to purchase national disability support services"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "public_health_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(3\.2% of the Vote\) "
            r"to purchase public health services"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "national_health_services_and_risk_management": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(5\.8% of the Vote\) "
            r"to pur\s*chase national health services and to manage health sector risks"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "clinical_training": (
        2,
        (
            r"Just under \$(?P<value>[0-9][0-9,]*) million \(1\.1% of the Vote\) "
            r"to prov\s*ide clinical training for health professionals"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "dhb_deficit_support_provision": (
        2,
        (
            r"\$(?P<value>[0-9][0-9,]*) million "
            r"\(0\.6% of the Vote\) for a provision for DHB deficit support"
        ),
        "$ million, approximate source amount",
        "2011/12",
    ),
    "primary_health_services": (
        2,
        (
            r"Nearly \$(?P<value>[0-9][0-9,]*) million \(1\.3% of the Vote\) "
            r"to purchase primary health care services"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "other_health_services": (
        2,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(0\.5% of the Vote\) "
            r"to fund other health and disability services"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "other_expenses_total": (
        2,
        (
            r"Other Expenses Incurred by the Crown\s+A total of nearly "
            r"\$(?P<value>[0-9][0-9,]*) million \(0\.2% of the Vote\) is for "
            r"other expenses"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "capital_expenditure": (
        3,
        (
            r"Capital Expenditure\s+Almost \$(?P<value>[0-9][0-9,]*) million "
            r"\(3\.3% of the Vote\) is to provide capital funding"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "dhb_and_agency_capital": (
        3,
        (
            r"Almost \$(?P<value>[0-9][0-9,]*) million \(3\.1 % of the Vote\) "
            r"is to provi\s*de debt or equity for District Health Boards"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
    "long_term_care_interest_free_loans": (
        3,
        (
            r"\$(?P<value>[0-9][0-9,]*) million \(0\.1% of the Vote\) is to provide "
            r"intere\s*st-free loans"
        ),
        "$ million, approximate source amount",
        "2011/12",
    ),
    "ministry_asset_purchases": (
        3,
        (
            r"Just over \$(?P<value>[0-9][0-9,]*) million \(0\.1% of the Vote\) "
            r"is to pur\s*chase or develop assets for use by the Ministry of Health"
        ),
        "$ million, approximate rounded source amount",
        "2011/12",
    ),
}

FACT_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("schema_version", pa.string()),
        ("recordset", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_observation_id", pa.string()),
        ("source_locator", pa.string()),
        ("source_vintage", pa.string()),
        ("observed_at", pa.timestamp("us", tz="UTC")),
        ("source_page", pa.int64()),
        ("summary_measure", pa.string()),
        ("value", pa.decimal128(20, 3)),
        ("unit", pa.string()),
        ("currency_code", pa.string()),
        ("reference_period", pa.string()),
        ("rights_state", pa.string()),
        ("quality_flags", pa.list_(pa.string())),
        ("transformation_id", pa.string()),
        ("lineage_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)
DISPOSITION_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_page", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
    ]
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def parse_overview_pages(  # noqa: PLR0913 - profile controls are explicit
    texts: list[str],
    *,
    year: str = "2002/03",
    patterns: dict[str, tuple[int, str, str, str]] | None = None,
    intro_pattern: str | None = None,
    second_page_pattern: str | None = None,
    profile_qualifier_measures: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Read only named, phrase-anchored monetary headlines from pages 2-3."""
    selected_patterns = _PATTERNS if patterns is None else patterns
    _require(
        len(texts) == OVERVIEW_PAGE_COUNT
        and all(len(text) <= MAX_TEXT for text in texts)
    )
    default_intro_pattern = (
        rf"Appropriations\s+sought\s+for\s+Vote\s+Health\s+in\s+{re.escape(year)}"
    )
    _require(re.search(intro_pattern or default_intro_pattern, texts[0]) is not None)
    _require(
        re.search(second_page_pattern or r"Crown\s+Revenue\s+and\s+Receipts", texts[1])
        is not None
    )
    facts: list[dict[str, Any]] = []
    for measure, (page, pattern, unit, period) in selected_patterns.items():
        whitespace_flexible_pattern = pattern.replace(" ", r"\s+")
        matches = list(re.finditer(whitespace_flexible_pattern, texts[page - 2]))
        _require(len(matches) == 1)
        token = matches[0].group("value")
        try:
            value = Decimal(token.replace(",", ""))
        except InvalidOperation:
            raise ValueError(_ERROR) from None
        facts.append(
            {
                "source_page": page,
                "summary_measure": measure,
                "value": value,
                "unit": unit,
                "currency_code": None,
                "reference_period": period,
                "raw_token": token,
                "source_phrase": matches[0].group(0),
                "source_qualifier_preserved": (
                    measure
                    in {
                        "vote_total",
                        "non_departmental_total",
                        "output_expenses_total",
                        "dhb_services",
                        "national_disability_services",
                        "public_health_services",
                        "national_health_services_and_training",
                        "primary_health_services",
                        "other_health_services",
                        "other_expenses_total",
                        "capital_expenditure",
                        "dhb_and_agency_capital",
                        "ministry_asset_purchases",
                    }
                    or measure in profile_qualifier_measures
                ),
            }
        )
    _require(len(facts) == len(selected_patterns))
    return facts


def parse_overview_2004_05_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse only the eight explicitly observed 2004/05 overview amounts."""
    return parse_overview_pages(texts, year="2004/05", patterns=_PATTERNS_2004_05)


def parse_overview_2005_06_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse only the eight observed 2005/06 overview amounts."""
    return parse_overview_pages(texts, year="2005/06", patterns=_PATTERNS_2005_06)


def parse_overview_2006_07_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse only the eight observed 2006/07 overview amounts."""
    return parse_overview_pages(texts, year="2006/07", patterns=_PATTERNS_2006_07)


def parse_overview_2007_08_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse only the eight observed 2007/08 overview amounts."""
    return parse_overview_pages(texts, year="2007/08", patterns=_PATTERNS_2007_08)


def parse_overview_2008_09_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse six explicitly qualified, rounded 2008/09 overview amounts."""
    return parse_overview_pages(
        texts,
        year="2008/09",
        patterns=_PATTERNS_2008_09,
        intro_pattern=r"2008/09 financial year\s+totalling just over",
        second_page_pattern=r"Details of Appropriations",
    )


def parse_overview_2009_10_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse all 17 explicitly selected rounded 2009/10 overview amounts."""
    return parse_overview_pages(
        texts,
        year="2009/10",
        patterns=_PATTERNS_2009_10,
        intro_pattern=r"2009/10 financial year\s+totalling just under",
        second_page_pattern=r"Details of Appropriations",
    )


def parse_overview_2010_11_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse 18 selected, qualified 2010/11 statements on pages 2-3."""
    return parse_overview_pages(
        texts,
        year="2010/11",
        patterns=_PATTERNS_2010_11,
        intro_pattern=r"2010/11 financial year\s+totalling just under",
        second_page_pattern=r"Capital Expenditure",
        profile_qualifier_measures=_PROFILE_QUALIFIER_MEASURES_2010_11,
    )


def parse_overview_2011_12_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse 17 selected, phrase-anchored 2011/12 overview statements."""
    return parse_overview_pages(
        texts,
        year="2011/12",
        patterns=_PATTERNS_2011_12,
        intro_pattern=r"2011/12 financial year\s+totalling just over",
        second_page_pattern=r"Capital Expenditure",
        profile_qualifier_measures=_PROFILE_QUALIFIER_MEASURES_2011_12,
    )


def _normalize_overview(  # noqa: PLR0913 - profile/provenance are explicit
    source: Path,
    output_dir: Path,
    *,
    profile: str,
    transformation: str,
    expected_vintage: str,
    expected_source_sha256: str,
    expected_page_count: int,
    year: str,
    patterns: dict[str, tuple[int, str, str, str]],
    disposition_reason: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    intro_pattern: str | None = None,
    second_page_pattern: str | None = None,
    additional_quality_flags: tuple[str, ...] = (),
    profile_qualifier_measures: frozenset[str] = frozenset(),
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize a pinned edition's exact overview headlines into local Silver."""
    _require(
        source_vintage == expected_vintage and expected_sha256 == expected_source_sha256
    )
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    _require(not reader.is_encrypted and len(reader.pages) == expected_page_count)
    texts = [
        reader.pages[index].extract_text(extraction_mode="plain") or ""
        for index in (1, 2)
    ]
    rows = parse_overview_pages(
        texts,
        year=year,
        patterns=patterns,
        intro_pattern=intro_pattern,
        second_page_pattern=second_page_pattern,
        profile_qualifier_measures=profile_qualifier_measures,
    )
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    facts: list[dict[str, object]] = []
    lineage: list[dict[str, object]] = []
    for row in rows:
        page = int(row["source_page"])
        measure = str(row["summary_measure"])
        record_id = identity(transformation, expected_sha256, page, measure)
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.vote-health-overview/v1",
                "recordset": "vote_health_appropriation_overview_fact",
                "source_page": page,
                "summary_measure": measure,
                "value": row["value"],
                "unit": row["unit"],
                "currency_code": None,
                "reference_period": row["reference_period"],
                "rights_state": "not_evaluated",
                "quality_flags": [
                    "overview_headline_only",
                    "currency_code_not_supplied",
                    *additional_quality_flags,
                    *(
                        ("source_qualifier_preserved_in_raw_phrase",)
                        if row.get("source_qualifier_preserved")
                        else ()
                    ),
                ],
                "transformation_id": transformation,
                "lineage_id": identity(record_id, "lineage"),
                "raw_values_json": encode_json(row),
            }
        )
        lineage.append(
            {
                "lineage_id": identity(record_id, "value"),
                "record_id": record_id,
                "field": "value",
                "source_object_sha256": expected_sha256,
                "source_locator": source_locator,
                "source_coordinate": f"pdf:page={page};overview:{measure}",
                "raw_value": str(row["raw_token"]),
                "normalized_value": str(row["value"]),
                "rule": transformation,
            }
        )
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.vote-health-overview-extraction/v1",
        "status": "planned" if dry_run else "passed",
        "profile": profile,
        "source_object_sha256": expected_sha256,
        "counts": {
            "pages": len({int(row["source_page"]) for row in rows}),
            "facts": len(facts),
        },
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "vote_health_overview_facts.parquet": pa.Table.from_pylist(
                facts, FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(lineage, LINEAGE_SCHEMA),
            "page_dispositions.parquet": pa.Table.from_pylist(
                [
                    {
                        "source_object_sha256": expected_sha256,
                        "source_locator": source_locator,
                        "source_page": page,
                        "disposition": "partially_normalized"
                        if any(int(row["source_page"]) == page for row in rows)
                        else "preserved_unreviewed",
                        "reason": disposition_reason
                        if any(int(row["source_page"]) == page for row in rows)
                        else "not_reviewed_by_overview_profile",
                    }
                    for page in range(1, expected_page_count + 1)
                ],
                DISPOSITION_SCHEMA,
            ),
        },
        receipt,
    )


def normalize_vote_health_estimates_overview_2002_03(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize the exact 2002/03 overview headlines into a local product."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE,
        transformation=TRANSFORMATION,
        expected_vintage=VINTAGE,
        expected_source_sha256=SOURCE_SHA256,
        expected_page_count=PAGE_COUNT,
        year="2002/03",
        patterns=_PATTERNS,
        disposition_reason="seven_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2004_05(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize eight observed 2004/05 overview amounts, without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2004_05,
        transformation=TRANSFORMATION_2004_05,
        expected_vintage=VINTAGE_2004_05,
        expected_source_sha256=SOURCE_SHA256_2004_05,
        expected_page_count=PAGE_COUNT_2004_05,
        year="2004/05",
        patterns=_PATTERNS_2004_05,
        disposition_reason="eight_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2005_06(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize eight observed 2005/06 overview amounts, without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2005_06,
        transformation=TRANSFORMATION_2005_06,
        expected_vintage=VINTAGE_2005_06,
        expected_source_sha256=SOURCE_SHA256_2005_06,
        expected_page_count=PAGE_COUNT_2005_06,
        year="2005/06",
        patterns=_PATTERNS_2005_06,
        disposition_reason="eight_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2006_07(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize eight observed 2006/07 overview amounts, without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2006_07,
        transformation=TRANSFORMATION_2006_07,
        expected_vintage=VINTAGE_2006_07,
        expected_source_sha256=SOURCE_SHA256_2006_07,
        expected_page_count=PAGE_COUNT_2006_07,
        year="2006/07",
        patterns=_PATTERNS_2006_07,
        disposition_reason="eight_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2007_08(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize eight observed 2007/08 overview amounts, without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2007_08,
        transformation=TRANSFORMATION_2007_08,
        expected_vintage=VINTAGE_2007_08,
        expected_source_sha256=SOURCE_SHA256_2007_08,
        expected_page_count=PAGE_COUNT_2007_08,
        year="2007/08",
        patterns=_PATTERNS_2007_08,
        disposition_reason="eight_reviewed_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2008_09(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize six rounded/qualified 2008/09 amounts without implying precision."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2008_09,
        transformation=TRANSFORMATION_2008_09,
        expected_vintage=VINTAGE_2008_09,
        expected_source_sha256=SOURCE_SHA256_2008_09,
        expected_page_count=PAGE_COUNT_2008_09,
        year="2008/09",
        patterns=_PATTERNS_2008_09,
        disposition_reason="six_approximate_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        intro_pattern=r"2008/09 financial year\s+totalling just over",
        second_page_pattern=r"Details of Appropriations",
        additional_quality_flags=(
            "source_value_rounded_to_whole_million",
            "source_amount_is_not_exact",
        ),
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2009_10(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize 17 reviewed 2009/10 overview amounts without summing."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2009_10,
        transformation=TRANSFORMATION_2009_10,
        expected_vintage=VINTAGE_2009_10,
        expected_source_sha256=SOURCE_SHA256_2009_10,
        expected_page_count=PAGE_COUNT_2009_10,
        year="2009/10",
        patterns=_PATTERNS_2009_10,
        disposition_reason="seventeen_approximate_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        intro_pattern=r"2009/10 financial year\s+totalling just under",
        second_page_pattern=r"Details of Appropriations",
        additional_quality_flags=(
            "source_value_rounded_to_whole_million",
            "source_amount_is_not_exact",
        ),
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2010_11(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize 18 selected rounded/qualified 2010/11 overview statements."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2010_11,
        transformation=TRANSFORMATION_2010_11,
        expected_vintage=VINTAGE_2010_11,
        expected_source_sha256=SOURCE_SHA256_2010_11,
        expected_page_count=PAGE_COUNT_2010_11,
        year="2010/11",
        patterns=_PATTERNS_2010_11,
        disposition_reason="eighteen_approximate_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        intro_pattern=r"2010/11 financial year\s+totalling just under",
        second_page_pattern=r"Capital Expenditure",
        profile_qualifier_measures=_PROFILE_QUALIFIER_MEASURES_2010_11,
        additional_quality_flags=(
            "source_value_rounded_to_whole_million",
            "source_amount_is_not_exact",
        ),
        dry_run=dry_run,
    )


def normalize_vote_health_estimates_overview_2011_12(  # noqa: PLR0913 - explicit pinned profile
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize 17 selected rounded/qualified 2011/12 overview statements."""
    return _normalize_overview(
        source,
        output_dir,
        profile=PROFILE_2011_12,
        transformation=TRANSFORMATION_2011_12,
        expected_vintage=VINTAGE_2011_12,
        expected_source_sha256=SOURCE_SHA256_2011_12,
        expected_page_count=PAGE_COUNT_2011_12,
        year="2011/12",
        patterns=_PATTERNS_2011_12,
        disposition_reason="seventeen_selected_2011_12_overview_headlines_only",
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
        intro_pattern=r"2011/12 financial year\s+totalling just over",
        second_page_pattern=r"Capital Expenditure",
        profile_qualifier_measures=_PROFILE_QUALIFIER_MEASURES_2011_12,
        additional_quality_flags=(
            "source_value_rounded_to_whole_million",
            "source_amount_is_not_exact",
        ),
        dry_run=dry_run,
    )
