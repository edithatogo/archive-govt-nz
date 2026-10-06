"""Allowlisted local source extraction and redacted read-only preflight."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations import (
    budget_revenue,
    cpi,
    forecast,
    gdp,
    moh_indicators,
    pharmac,
    population_annual_silver,
    qes,
    vote_health,
    vote_health_estimates_summary,
    vote_health_revenue,
    vote_health_supplementary_2018_19,
    vote_health_supplementary_2019_20,
    vote_health_supplementary_2020_21,
    vote_health_supplementary_2021_22,
    vote_health_supplementary_2022_23,
    vote_health_supplementary_2023_24,
    vote_health_supplementary_2024_25,
    vote_health_supplementary_2025_26,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import source_context

MAX_CONTEXT = 2048
_INVALID_SOURCE_OPERATION = "invalid_source_operation"
PROFILES = MappingProxyType(
    {
        "cpiq-se9a/v1": (
            cpi.TRANSFORMATION,
            ("input", "selected", "numeric", "missing", "unselected"),
            "cpi_facts.parquet",
            "row_dispositions.parquet",
        ),
        "population-annual-mean-context/v1": (
            population_annual_silver.TRANSFORMATION,
            ("input", "facts", "numeric", "missing", "provisional", "lineage"),
            "population_facts.parquet",
            "row_dispositions.parquet",
        ),
        "budget-revenue-2025/v1": (
            budget_revenue.TRANSFORMATION,
            ("input", "normalized", "out_of_scope", "blank", "rejected"),
            "revenue_facts.parquet",
            "row_dispositions.parquet",
        ),
        "budget-revenue-2026/v1": (
            budget_revenue.TRANSFORMATION_2026,
            ("input", "normalized", "out_of_scope", "blank", "rejected"),
            "revenue_facts.parquet",
            "row_dispositions.parquet",
        ),
        "moh-hair2024-fig27/v1": (
            moh_indicators.TRANSFORMATION,
            ("input", "facts", "lineage"),
            "moh_indicator_facts.parquet",
            "row_dispositions.parquet",
        ),
        "moh-hair2024-fig28/v1": (
            moh_indicators.TRANSFORMATION,
            ("input", "facts", "lineage"),
            "moh_indicator_facts.parquet",
            "row_dispositions.parquet",
        ),
        "qes-june2026-table8/v1": (
            qes.TRANSFORMATION,
            ("normalized", "field_lineage", "inventoried_cells"),
            "qes_facts.parquet",
            "cell_dispositions.parquet",
        ),
        "pharmac-cpb-20260807/v1": (
            pharmac.TRANSFORMATION,
            ("facts", "lineage", "table_cells"),
            "pharmaceutical_budget_facts.parquet",
            "cell_dispositions.parquet",
        ),
        "gdp-expenditure-actual-2026q1/v1": (
            gdp.TRANSFORMATION,
            ("facts", "lineage", "dispositions"),
            "gdp_facts.parquet",
            "cell_dispositions.parquet",
        ),
        "gdp-expenditure-actual-2026q2/v1": (
            gdp.JUNE_TRANSFORMATION,
            ("facts", "lineage", "dispositions"),
            "gdp_facts.parquet",
            "cell_dispositions.parquet",
        ),
        "befu-2026/v1": (
            forecast.TRANSFORMATION,
            (
                "normalized",
                "rejected",
                "context",
                "preserved_only",
                "inventoried_cells",
            ),
            "forecast_facts.parquet",
            "cell_dispositions.parquet",
        ),
        "hyefu-2025/v1": (
            forecast.TRANSFORMATION,
            (
                "normalized",
                "rejected",
                "context",
                "preserved_only",
                "inventoried_cells",
            ),
            "forecast_facts.parquet",
            "cell_dispositions.parquet",
        ),
        "vote-health-supplementary-2003-04-summary/v1": (
            vote_health.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_summary_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_supplementary_2018_19.PROFILE: (
            vote_health_supplementary_2018_19.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_category_total_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_supplementary_2019_20.PROFILE: (
            vote_health_supplementary_2019_20.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_category_total_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_supplementary_2020_21.PROFILE: (
            vote_health_supplementary_2020_21.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_supplementary_summary_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_supplementary_2021_22.PROFILE: (
            vote_health_supplementary_2021_22.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_supplementary_summary_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_supplementary_2022_23.PROFILE: (
            vote_health_supplementary_2022_23.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_supplementary_summary_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_supplementary_2023_24.PROFILE: (
            vote_health_supplementary_2023_24.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_supplementary_summary_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_supplementary_2024_25.PROFILE: (
            vote_health_supplementary_2024_25.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_supplementary_summary_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_supplementary_2025_26.PROFILE: (
            vote_health_supplementary_2025_26.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_supplementary_summary_facts.parquet",
            "page_dispositions.parquet",
        ),
        "vote-health-supplementary-2003-04-detail/v1": (
            vote_health.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_detail_facts.parquet",
            "page_dispositions.parquet",
        ),
        "vote-health-estimates-2002-03-detail/v1": (
            vote_health.DETAIL_2002_03_TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_detail_facts.parquet",
            "page_dispositions.parquet",
        ),
        "vote-health-supplementary-2003-04-revenue/v1": (
            vote_health_revenue.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_revenue_facts.parquet",
            "page_dispositions.parquet",
        ),
        "vote-health-estimates-2002-03-revenue/v1": (
            vote_health_revenue.ESTIMATES_2002_03_TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_estimates_revenue_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE: (
            vote_health_estimates_summary.TRANSFORMATION,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2004_05: (
            vote_health_estimates_summary.TRANSFORMATION_2004_05,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2005_06: (
            vote_health_estimates_summary.TRANSFORMATION_2005_06,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2006_07: (
            vote_health_estimates_summary.TRANSFORMATION_2006_07,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2007_08: (
            vote_health_estimates_summary.TRANSFORMATION_2007_08,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2008_09: (
            vote_health_estimates_summary.TRANSFORMATION_2008_09,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2009_10: (
            vote_health_estimates_summary.TRANSFORMATION_2009_10,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2010_11: (
            vote_health_estimates_summary.TRANSFORMATION_2010_11,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2011_12: (
            vote_health_estimates_summary.TRANSFORMATION_2011_12,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2012_13: (
            vote_health_estimates_summary.TRANSFORMATION_2012_13,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2013_14: (
            vote_health_estimates_summary.TRANSFORMATION_2013_14,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2014_15: (
            vote_health_estimates_summary.TRANSFORMATION_2014_15,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2015_16: (
            vote_health_estimates_summary.TRANSFORMATION_2015_16,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2016_17: (
            vote_health_estimates_summary.TRANSFORMATION_2016_17,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
        vote_health_estimates_summary.PROFILE_2017_18: (
            vote_health_estimates_summary.TRANSFORMATION_2017_18,
            ("pages", "facts"),
            "vote_health_overview_facts.parquet",
            "page_dispositions.parquet",
        ),
    }
)
_REVENUE_VINTAGES = {
    "budget-revenue-2025/v1": "Budget-2025",
    "budget-revenue-2026/v1": "Budget-2026",
}
_GDP_VINTAGES = {
    "gdp-expenditure-actual-2026q1/v1": gdp.VINTAGE,
    "gdp-expenditure-actual-2026q2/v1": gdp.JUNE_VINTAGE,
}
_VOTE_HEALTH_DETAIL_PROFILES = {
    "vote-health-supplementary-2003-04-detail/v1": (
        vote_health.DETAIL_VINTAGE_2003_04,
        None,
    ),
    "vote-health-estimates-2002-03-detail/v1": (
        vote_health.DETAIL_VINTAGE_2002_03,
        vote_health.DETAIL_2002_03_SHA256,
    ),
}
_VOTE_HEALTH_CATEGORY_TOTAL_PROFILES = {
    vote_health_supplementary_2018_19.PROFILE: (
        vote_health_supplementary_2018_19.VINTAGE,
        vote_health_supplementary_2018_19.SOURCE_SHA256,
    ),
    vote_health_supplementary_2019_20.PROFILE: (
        vote_health_supplementary_2019_20.VINTAGE,
        vote_health_supplementary_2019_20.SOURCE_SHA256,
    ),
}
_VOTE_HEALTH_SUMMARY_PROFILES = {
    vote_health_supplementary_2020_21.PROFILE: (
        vote_health_supplementary_2020_21.VINTAGE,
        vote_health_supplementary_2020_21.SOURCE_SHA256,
    ),
    vote_health_supplementary_2021_22.PROFILE: (
        vote_health_supplementary_2021_22.VINTAGE,
        vote_health_supplementary_2021_22.SOURCE_SHA256,
    ),
    vote_health_supplementary_2022_23.PROFILE: (
        vote_health_supplementary_2022_23.VINTAGE,
        vote_health_supplementary_2022_23.SOURCE_SHA256,
    ),
    vote_health_supplementary_2023_24.PROFILE: (
        vote_health_supplementary_2023_24.VINTAGE,
        vote_health_supplementary_2023_24.SOURCE_SHA256,
    ),
    vote_health_supplementary_2024_25.PROFILE: (
        vote_health_supplementary_2024_25.VINTAGE,
        vote_health_supplementary_2024_25.SOURCE_SHA256,
    ),
    vote_health_supplementary_2025_26.PROFILE: (
        vote_health_supplementary_2025_26.VINTAGE,
        vote_health_supplementary_2025_26.SOURCE_SHA256,
    ),
}
_VOTE_HEALTH_REVENUE_PROFILES = {
    vote_health_revenue.ESTIMATES_2002_03_PROFILE: (
        vote_health_revenue.ESTIMATES_2002_03_VINTAGE,
        vote_health_revenue.ESTIMATES_2002_03_SHA256,
    ),
}
_VOTE_HEALTH_OVERVIEW_PROFILES = {
    vote_health_estimates_summary.PROFILE: (
        vote_health_estimates_summary.VINTAGE,
        vote_health_estimates_summary.SOURCE_SHA256,
    ),
    vote_health_estimates_summary.PROFILE_2004_05: (
        vote_health_estimates_summary.VINTAGE_2004_05,
        vote_health_estimates_summary.SOURCE_SHA256_2004_05,
    ),
    vote_health_estimates_summary.PROFILE_2005_06: (
        vote_health_estimates_summary.VINTAGE_2005_06,
        vote_health_estimates_summary.SOURCE_SHA256_2005_06,
    ),
    vote_health_estimates_summary.PROFILE_2006_07: (
        vote_health_estimates_summary.VINTAGE_2006_07,
        vote_health_estimates_summary.SOURCE_SHA256_2006_07,
    ),
    vote_health_estimates_summary.PROFILE_2007_08: (
        vote_health_estimates_summary.VINTAGE_2007_08,
        vote_health_estimates_summary.SOURCE_SHA256_2007_08,
    ),
    vote_health_estimates_summary.PROFILE_2008_09: (
        vote_health_estimates_summary.VINTAGE_2008_09,
        vote_health_estimates_summary.SOURCE_SHA256_2008_09,
    ),
    vote_health_estimates_summary.PROFILE_2009_10: (
        vote_health_estimates_summary.VINTAGE_2009_10,
        vote_health_estimates_summary.SOURCE_SHA256_2009_10,
    ),
    vote_health_estimates_summary.PROFILE_2010_11: (
        vote_health_estimates_summary.VINTAGE_2010_11,
        vote_health_estimates_summary.SOURCE_SHA256_2010_11,
    ),
    vote_health_estimates_summary.PROFILE_2011_12: (
        vote_health_estimates_summary.VINTAGE_2011_12,
        vote_health_estimates_summary.SOURCE_SHA256_2011_12,
    ),
    vote_health_estimates_summary.PROFILE_2012_13: (
        vote_health_estimates_summary.VINTAGE_2012_13,
        vote_health_estimates_summary.SOURCE_SHA256_2012_13,
    ),
    vote_health_estimates_summary.PROFILE_2013_14: (
        vote_health_estimates_summary.VINTAGE_2013_14,
        vote_health_estimates_summary.SOURCE_SHA256_2013_14,
    ),
    vote_health_estimates_summary.PROFILE_2014_15: (
        vote_health_estimates_summary.VINTAGE_2014_15,
        vote_health_estimates_summary.SOURCE_SHA256_2014_15,
    ),
    vote_health_estimates_summary.PROFILE_2015_16: (
        vote_health_estimates_summary.VINTAGE_2015_16,
        vote_health_estimates_summary.SOURCE_SHA256_2015_16,
    ),
    vote_health_estimates_summary.PROFILE_2016_17: (
        vote_health_estimates_summary.VINTAGE_2016_17,
        vote_health_estimates_summary.SOURCE_SHA256_2016_17,
    ),
    vote_health_estimates_summary.PROFILE_2017_18: (
        vote_health_estimates_summary.VINTAGE_2017_18,
        vote_health_estimates_summary.SOURCE_SHA256_2017_18,
    ),
}
_VOTE_HEALTH_OVERVIEW_NORMALIZERS = {
    vote_health_estimates_summary.PROFILE: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2002_03
    ),
    vote_health_estimates_summary.PROFILE_2004_05: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2004_05
    ),
    vote_health_estimates_summary.PROFILE_2005_06: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2005_06
    ),
    vote_health_estimates_summary.PROFILE_2006_07: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2006_07
    ),
    vote_health_estimates_summary.PROFILE_2007_08: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2007_08
    ),
    vote_health_estimates_summary.PROFILE_2008_09: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2008_09
    ),
    vote_health_estimates_summary.PROFILE_2009_10: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2009_10
    ),
    vote_health_estimates_summary.PROFILE_2010_11: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2010_11
    ),
    vote_health_estimates_summary.PROFILE_2011_12: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2011_12
    ),
    vote_health_estimates_summary.PROFILE_2012_13: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2012_13
    ),
    vote_health_estimates_summary.PROFILE_2013_14: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2013_14
    ),
    vote_health_estimates_summary.PROFILE_2014_15: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2014_15
    ),
    vote_health_estimates_summary.PROFILE_2015_16: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2015_16
    ),
    vote_health_estimates_summary.PROFILE_2016_17: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2016_17
    ),
    vote_health_estimates_summary.PROFILE_2017_18: (
        vote_health_estimates_summary.normalize_vote_health_estimates_overview_2017_18
    ),
}
_DUPLICATE_PROFILE = "duplicate_source_operation_profile"
if len(PROFILES) != len(set(PROFILES)):
    raise ValueError(_DUPLICATE_PROFILE)

_COMMON = {
    "schema_version": "archive-govt-nz.health-source-operation/v1",
    "verification_scope": "adapter_execution_only",
    "rights_state": "not_evaluated",
    "publication_state": "local_validation_only",
}
_DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$", "maxLength": 64}
_COUNT = {"type": "integer", "minimum": 0}
_TEXT = {"type": "string", "minLength": 1, "maxLength": MAX_CONTEXT}
SOURCE_PREFLIGHT_INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "profile": {"enum": list(PROFILES)},
        "expected_sha256": _DIGEST,
        **dict.fromkeys(
            ("source", "output_dir", "source_vintage", "source_locator", "observed_at"),
            _TEXT,
        ),
    },
    "required": [
        "profile",
        "expected_sha256",
        "source",
        "output_dir",
        "source_vintage",
        "source_locator",
        "observed_at",
    ],
}
SOURCE_OPERATION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        **{key: {"const": value} for key, value in _COMMON.items()},
        "status": {"enum": ["preflight_passed", "written_local", "failed"]},
        "error": {"const": "invalid_source_operation"},
        "profile": {"enum": list(PROFILES)},
        "source_object_sha256": _DIGEST,
        "transformation_id": {
            "enum": sorted({value[0] for value in PROFILES.values()})
        },
        "counts": {"type": "object"},
        "output_sha256": {"type": "object"},
    },
    "required": [*_COMMON, "status"],
    "oneOf": [
        {
            "properties": {"status": {"const": "failed"}},
            "required": ["error"],
            "maxProperties": len(_COMMON) + 2,
        },
        {
            "properties": {"status": {"enum": ["preflight_passed", "written_local"]}},
            "required": [
                "profile",
                "source_object_sha256",
                "transformation_id",
                "counts",
            ],
            "not": {"required": ["error"]},
            "oneOf": [
                {
                    "properties": {
                        "profile": {"const": name},
                        "transformation_id": {"const": values[0]},
                        "counts": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": dict.fromkeys(values[1], _COUNT),
                            "required": list(values[1]),
                        },
                        "output_sha256": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": dict.fromkeys(
                                (values[2], "field_lineage.parquet", values[3]), _DIGEST
                            ),
                            "required": [values[2], "field_lineage.parquet", values[3]],
                        },
                    }
                }
                for name, values in PROFILES.items()
            ],
            "allOf": [
                {
                    "if": {"properties": {"status": {"const": "written_local"}}},
                    "then": {"required": ["output_sha256"]},
                    "else": {"not": {"required": ["output_sha256"]}},
                }
            ],
        },
    ],
}


@dataclass(frozen=True, slots=True)
class SourceRequest:
    """Explicit caller context; validation is not acquisition attestation."""

    source: Path
    output_dir: Path
    profile: str
    expected_sha256: str
    source_vintage: str
    source_locator: str
    observed_at: str


def _validate(request: SourceRequest, *, dry_run: bool) -> None:
    arguments = {
        "source": str(request.source),
        "output_dir": str(request.output_dir),
        "profile": request.profile,
        "expected_sha256": request.expected_sha256,
        "source_vintage": request.source_vintage,
        "source_locator": request.source_locator,
        "observed_at": request.observed_at,
    }
    Draft202012Validator(SOURCE_PREFLIGHT_INPUT_SCHEMA).validate(arguments)
    locator = urlsplit(request.source_locator)
    if (
        not isinstance(dry_run, bool)
        or locator.scheme != "https"
        or not locator.hostname
        or locator.username is not None
        or locator.password is not None
        or locator.query
        or locator.fragment
        or any(
            not char.isprintable() or char.isspace() for char in request.source_locator
        )
        or request.source.is_symlink()
        or not request.source.is_file()
        or request.output_dir.exists()
        or request.output_dir.is_symlink()
    ):
        message = "invalid_source_operation"
        raise ValueError(message)
    source_context(
        request.expected_sha256,
        request.source_locator,
        request.source_vintage,
        request.observed_at,
    )
    if request.profile in _REVENUE_VINTAGES and (
        request.source_vintage != _REVENUE_VINTAGES[request.profile]
    ):
        raise ValueError(_INVALID_SOURCE_OPERATION)
    if request.profile in _GDP_VINTAGES and (
        request.source_vintage != _GDP_VINTAGES[request.profile]
    ):
        raise ValueError(_INVALID_SOURCE_OPERATION)
    pinned_profiles = {
        **_VOTE_HEALTH_DETAIL_PROFILES,
        **_VOTE_HEALTH_REVENUE_PROFILES,
        **_VOTE_HEALTH_CATEGORY_TOTAL_PROFILES,
        **_VOTE_HEALTH_SUMMARY_PROFILES,
        **_VOTE_HEALTH_OVERVIEW_PROFILES,
    }
    if request.profile in pinned_profiles:
        expected_vintage, expected_source_sha256 = pinned_profiles[request.profile]
        if request.source_vintage != expected_vintage or (
            expected_source_sha256 is not None
            and request.expected_sha256 != expected_source_sha256
        ):
            raise ValueError(_INVALID_SOURCE_OPERATION)


def _invoke(  # noqa: C901, PLR0911, PLR0912 - explicit allowlisted profile dispatch
    request: SourceRequest, *, dry_run: bool
) -> dict[str, Any]:
    context = {
        "expected_sha256": request.expected_sha256,
        "observed_at": request.observed_at,
        "source_vintage": request.source_vintage,
        "source_locator": request.source_locator,
    }
    if request.profile in _REVENUE_VINTAGES:
        return budget_revenue.normalize_budget_revenue(
            request.source,
            request.output_dir,
            **context,
            dry_run=dry_run,
        )
    if request.profile == "cpiq-se9a/v1":
        return cpi.normalize_cpi(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_revenue.ESTIMATES_2002_03_PROFILE:
        return vote_health_revenue.normalize_vote_health_estimates_revenue_2002_03(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile in _VOTE_HEALTH_OVERVIEW_PROFILES:
        normalizer = _VOTE_HEALTH_OVERVIEW_NORMALIZERS[request.profile]
        return normalizer(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == "population-annual-mean-context/v1":
        return population_annual_silver.normalize_population_annual(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == "qes-june2026-table8/v1":
        return qes.normalize_qes(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == "pharmac-cpb-20260807/v1":
        return pharmac.normalize_pharmac_budget(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile in _GDP_VINTAGES:
        return gdp.normalize_gdp(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile in {"befu-2026/v1", "hyefu-2025/v1"}:
        return forecast.normalize_forecast_workbook(
            request.source,
            request.output_dir,
            profile=request.profile,
            **context,
            dry_run=dry_run,
        )
    if request.profile == "vote-health-supplementary-2003-04-summary/v1":
        return vote_health.normalize_vote_health_summary(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_supplementary_2018_19.PROFILE:
        return vote_health_supplementary_2018_19.normalize(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_supplementary_2019_20.PROFILE:
        return vote_health_supplementary_2019_20.normalize(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_supplementary_2020_21.PROFILE:
        return vote_health_supplementary_2020_21.normalize(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_supplementary_2021_22.PROFILE:
        return vote_health_supplementary_2021_22.normalize(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_supplementary_2022_23.PROFILE:
        return vote_health_supplementary_2022_23.normalize(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_supplementary_2023_24.PROFILE:
        return vote_health_supplementary_2023_24.normalize(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_supplementary_2024_25.PROFILE:
        return vote_health_supplementary_2024_25.normalize(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == vote_health_supplementary_2025_26.PROFILE:
        return vote_health_supplementary_2025_26.normalize(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile in _VOTE_HEALTH_DETAIL_PROFILES:
        return vote_health.normalize_vote_health_detail(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    if request.profile == "vote-health-supplementary-2003-04-revenue/v1":
        return vote_health_revenue.normalize_vote_health_revenue(
            request.source, request.output_dir, **context, dry_run=dry_run
        )
    profile = {
        "moh-hair2024-fig27/v1": "fig27/v1",
        "moh-hair2024-fig28/v1": "fig28/v1",
    }[request.profile]
    return moh_indicators.normalize_moh_indicators(
        request.source, request.output_dir, **context, profile=profile, dry_run=dry_run
    )


def operate_source(request: SourceRequest, *, dry_run: bool = True) -> dict[str, Any]:
    """Preflight by default; only a real False enables exclusive local writing.

    No caller locator/path/context or raw rows escape in these compact receipts.
    Signed/query URLs are rejected before parsing. Expected parser/IO failures
    are redacted; interrupts propagate. Existing parser output schemas, original
    bytes, donor rebuild and archive-status semantics remain unchanged.
    """
    try:
        _validate(request, dry_run=dry_run)
        raw = _invoke(request, dry_run=dry_run)
        expected_status = (
            "passed"
            if not dry_run or request.profile == "qes-june2026-table8/v1"
            else "planned"
        )
        if raw["status"] != expected_status:
            return {**_COMMON, "status": "failed", "error": "invalid_source_operation"}
        profile = PROFILES[request.profile]
        result = {
            **_COMMON,
            "status": "preflight_passed" if dry_run else "written_local",
            "profile": request.profile,
            "source_object_sha256": request.expected_sha256,
            "transformation_id": profile[0],
            "counts": raw["counts"],
        }
        if not dry_run:
            result["output_sha256"] = raw["output_sha256"]
        Draft202012Validator(SOURCE_OPERATION_SCHEMA).validate(result)
    except Exception:  # noqa: BLE001 - never disclose parser diagnostics or user context
        return {**_COMMON, "status": "failed", "error": "invalid_source_operation"}
    return result


def preflight_source(arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate the closed MCP input shape before constructing paths; never write."""
    try:
        Draft202012Validator(SOURCE_PREFLIGHT_INPUT_SCHEMA).validate(arguments)
        request = SourceRequest(
            Path(arguments["source"]),
            Path(arguments["output_dir"]),
            arguments["profile"],
            arguments["expected_sha256"],
            arguments["source_vintage"],
            arguments["source_locator"],
            arguments["observed_at"],
        )
        return operate_source(request, dry_run=True)
    except Exception:  # noqa: BLE001 - schema errors can contain sensitive input values
        return {**_COMMON, "status": "failed", "error": "invalid_source_operation"}
