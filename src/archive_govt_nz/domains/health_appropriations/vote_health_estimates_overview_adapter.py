"""Common Bronze adapters for already reviewed Vote Health overview editions."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import partial
from io import BytesIO
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from archive_govt_nz.domains.health_appropriations import (
    modern_vote_health_overviews as modern,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_2016_17_adapter as legacy_overview,
)
from archive_govt_nz.domains.health_appropriations import vote_health_estimates_summary
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.context_dimensions import (
    context_source_dimensions,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    source_context,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
        DimensionLink,
    )
    from archive_govt_nz.domains.health_appropriations.dimension_mapping import Mapping

_MAX_BYTES = 8 * 1024 * 1024


def overview_period_dimensions(
    records: tuple[dict[str, object], ...], lineage: tuple[FieldLineage, ...]
) -> tuple[tuple[Mapping, ...], tuple[DimensionLink, ...]]:
    """Retain period tokens only when the matched source phrase contains them."""
    phrases = {
        item.record_id: item for item in lineage if item.field == "source_phrase"
    }
    period_lineage = []
    for row in records:
        record_id = row["record_id"]
        if not isinstance(record_id, str):
            continue
        source = phrases.get(record_id)
        period = row.get("reference_period")
        if not isinstance(period, str) or not period or source is None:
            continue
        if source.raw_value is None or not re.search(
            rf"(?<![0-9/]){re.escape(period)}(?![0-9/])", source.raw_value
        ):
            continue
        period_lineage.append(
            FieldLineage(
                record_id=source.record_id,
                field="reference_period",
                source_coordinate=source.source_coordinate,
                raw_value=period,
                normalized_value=period,
                rule="overview_source_period_token/v1",
            )
        )
    return context_source_dimensions(
        records, tuple(period_lineage), family="vote_overview"
    )


@dataclass(frozen=True, slots=True)
class ReviewedOverviewProfile:
    """Exact existing parser and source controls, with no inferred layout."""

    adapter_id: str
    profile: str
    transformation: str
    vintage: str
    source_sha256: str
    page_count: int
    fact_count: int
    parse_pages: Callable[[list[str]], list[dict[str, Any]]]
    quality_flags: tuple[str, ...]
    disposition_reason: str


@dataclass(frozen=True, slots=True)
class ReviewedVoteHealthOverviewAdapter:
    """Normalize one exact reviewed overview edition; retain every page."""

    profile: ReviewedOverviewProfile
    source_locator: str
    source_vintage: str
    observed_at: str

    def _rows(self, bronze: bytes) -> list[dict[str, Any]] | None:
        if (
            self.source_vintage != self.profile.vintage
            or len(bronze) > _MAX_BYTES
            or hashlib.sha256(bronze).hexdigest() != self.profile.source_sha256
        ):
            return None
        try:
            reader = PdfReader(BytesIO(bronze), strict=True)
            if reader.is_encrypted or len(reader.pages) != self.profile.page_count:
                return None
            texts = [
                reader.pages[index].extract_text(extraction_mode="plain") or ""
                for index in (1, 2)
            ]
            rows = self.profile.parse_pages(texts)
            if len(rows) != self.profile.fact_count:
                return None
            if any(int(row["source_page"]) not in {2, 3} for row in rows):
                return None
        except (
            EOFError,
            IndexError,
            KeyError,
            OSError,
            PdfReadError,
            TypeError,
            ValueError,
        ):
            return None
        else:
            return rows

    def matches_layout(self, bronze: bytes) -> bool:
        """Require the exact vintage, source fixity, page count and parser layout."""
        return self._rows(bronze) is not None

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Emit overview facts, field lineage and a disposition for all pages."""
        actual = hashlib.sha256(bronze).hexdigest()
        if actual != source_sha256:
            message = "source_hash_mismatch"
            raise ValueError(message)
        rows = self._rows(bronze)
        if rows is None:
            return preserved_only(
                source_coordinate="bronze:sha256:" + actual,
                reason="unsupported_vote_health_estimates_overview_layout",
            )

        context = source_context(
            actual, self.source_locator, self.source_vintage, self.observed_at
        )
        records: list[dict[str, object]] = []
        lineage: list[FieldLineage] = []
        normalized_pages = {int(row["source_page"]) for row in rows}
        for row in rows:
            page = int(row["source_page"])
            measure = str(row["summary_measure"])
            value = row["value"]
            record_id = identity(self.profile.transformation, actual, page, measure)
            records.append(
                {
                    **context,
                    "record_id": record_id,
                    "schema_version": "archive-govt-nz.vote-health-overview/v1",
                    "recordset": "vote_health_appropriation_overview_fact",
                    "source_page": page,
                    "summary_measure": measure,
                    "value": value,
                    "unit": row["unit"],
                    "currency_code": None,
                    "reference_period": row["reference_period"],
                    "rights_state": "not_evaluated",
                    "quality_flags": [
                        "overview_headline_only",
                        "currency_code_not_supplied",
                        *self.profile.quality_flags,
                        *(
                            ["source_qualifier_preserved_in_raw_phrase"]
                            if row.get("source_qualifier_preserved")
                            else []
                        ),
                    ],
                    "transformation_id": self.profile.transformation,
                    "lineage_id": identity(record_id, "lineage"),
                    "raw_values_json": encode_json(row),
                }
            )
            lineage.append(
                FieldLineage(
                    record_id=record_id,
                    field="value",
                    source_coordinate=f"pdf:page={page};overview:{measure}",
                    raw_value=str(row["raw_token"]),
                    normalized_value=str(value),
                    rule=self.profile.transformation,
                )
            )
            lineage.append(
                FieldLineage(
                    record_id=record_id,
                    field="source_phrase",
                    source_coordinate=f"pdf:page={page};overview:{measure}",
                    raw_value=str(row["source_phrase"]),
                    normalized_value=str(row["source_phrase"]),
                    rule="reviewed_overview_source_phrase/v1",
                )
            )
        losses = tuple(
            LossAccounting(
                source_coordinate=f"pdf:page={page}",
                disposition=(
                    "partially_normalized"
                    if page in normalized_pages
                    else "preserved_only"
                ),
                reason=(
                    self.profile.disposition_reason
                    if page in normalized_pages
                    else "not_reviewed_by_overview_profile"
                ),
            )
            for page in range(1, self.profile.page_count + 1)
        )
        dimensions, dimension_links = overview_period_dimensions(
            tuple(records), tuple(lineage)
        )
        return AdapterOutput(
            records=tuple(records),
            losses=losses,
            lineage=tuple(lineage),
            layout=self.profile.profile,
            dimensions=dimensions,
            dimension_links=dimension_links,
        )


_PROFILES = MappingProxyType(
    {
        **{
            item.vintage: ReviewedOverviewProfile(
                adapter_id=f"nz-treasury-{item.profile.removesuffix('/v1')}",
                profile=item.profile,
                transformation=item.transformation,
                vintage=item.vintage,
                source_sha256=item.source_sha256,
                page_count=item.page_count,
                fact_count=1,
                parse_pages=partial(modern.parse_pages, profile=item),
                quality_flags=(
                    "source_reported_in_whole_millions",
                    "headline_only_not_component_sum",
                    "health_reform_scope_not_restated",
                    "cross_year_comparability_not_qualified",
                    *(
                        ("capital_charge_change_not_adjusted",)
                        if item.period == "2026/27"
                        else ()
                    ),
                ),
                disposition_reason="one_published_vote_total_headline_only",
            )
            for item in modern.PROFILES.values()
        },
        vote_health_estimates_summary.VINTAGE: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2002-03-overview",
            profile=vote_health_estimates_summary.PROFILE,
            transformation=vote_health_estimates_summary.TRANSFORMATION,
            vintage=vote_health_estimates_summary.VINTAGE,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256,
            page_count=vote_health_estimates_summary.PAGE_COUNT,
            fact_count=7,
            parse_pages=vote_health_estimates_summary.parse_overview_pages,
            quality_flags=(),
            disposition_reason="seven_reviewed_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2004_05: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2004-05-overview",
            profile=vote_health_estimates_summary.PROFILE_2004_05,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2004_05,
            vintage=vote_health_estimates_summary.VINTAGE_2004_05,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2004_05,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2004_05,
            fact_count=8,
            parse_pages=vote_health_estimates_summary.parse_overview_2004_05_pages,
            quality_flags=(),
            disposition_reason="eight_reviewed_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2005_06: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2005-06-overview",
            profile=vote_health_estimates_summary.PROFILE_2005_06,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2005_06,
            vintage=vote_health_estimates_summary.VINTAGE_2005_06,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2005_06,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2005_06,
            fact_count=8,
            parse_pages=vote_health_estimates_summary.parse_overview_2005_06_pages,
            quality_flags=(),
            disposition_reason="eight_reviewed_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2006_07: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2006-07-overview",
            profile=vote_health_estimates_summary.PROFILE_2006_07,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2006_07,
            vintage=vote_health_estimates_summary.VINTAGE_2006_07,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2006_07,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2006_07,
            fact_count=8,
            parse_pages=vote_health_estimates_summary.parse_overview_2006_07_pages,
            quality_flags=(),
            disposition_reason="eight_reviewed_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2007_08: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2007-08-overview",
            profile=vote_health_estimates_summary.PROFILE_2007_08,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2007_08,
            vintage=vote_health_estimates_summary.VINTAGE_2007_08,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2007_08,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2007_08,
            fact_count=8,
            parse_pages=vote_health_estimates_summary.parse_overview_2007_08_pages,
            quality_flags=(),
            disposition_reason="eight_reviewed_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2008_09: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2008-09-overview",
            profile=vote_health_estimates_summary.PROFILE_2008_09,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2008_09,
            vintage=vote_health_estimates_summary.VINTAGE_2008_09,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2008_09,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2008_09,
            fact_count=6,
            parse_pages=vote_health_estimates_summary.parse_overview_2008_09_pages,
            quality_flags=(
                "source_value_rounded_to_whole_million",
                "source_amount_is_not_exact",
            ),
            disposition_reason="six_approximate_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2009_10: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2009-10-overview",
            profile=vote_health_estimates_summary.PROFILE_2009_10,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2009_10,
            vintage=vote_health_estimates_summary.VINTAGE_2009_10,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2009_10,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2009_10,
            fact_count=17,
            parse_pages=vote_health_estimates_summary.parse_overview_2009_10_pages,
            quality_flags=(
                "source_value_rounded_to_whole_million",
                "source_amount_is_not_exact",
            ),
            disposition_reason="seventeen_approximate_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2010_11: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2010-11-overview",
            profile=vote_health_estimates_summary.PROFILE_2010_11,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2010_11,
            vintage=vote_health_estimates_summary.VINTAGE_2010_11,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2010_11,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2010_11,
            fact_count=18,
            parse_pages=vote_health_estimates_summary.parse_overview_2010_11_pages,
            quality_flags=(
                "source_value_rounded_to_whole_million",
                "source_amount_is_not_exact",
            ),
            disposition_reason="eighteen_approximate_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2011_12: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2011-12-overview",
            profile=vote_health_estimates_summary.PROFILE_2011_12,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2011_12,
            vintage=vote_health_estimates_summary.VINTAGE_2011_12,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2011_12,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2011_12,
            fact_count=17,
            parse_pages=vote_health_estimates_summary.parse_overview_2011_12_pages,
            quality_flags=(
                "source_value_rounded_to_whole_million",
                "source_amount_is_not_exact",
            ),
            disposition_reason="seventeen_selected_2011_12_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2012_13: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2012-13-overview",
            profile=vote_health_estimates_summary.PROFILE_2012_13,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2012_13,
            vintage=vote_health_estimates_summary.VINTAGE_2012_13,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2012_13,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2012_13,
            fact_count=18,
            parse_pages=vote_health_estimates_summary.parse_overview_2012_13_pages,
            quality_flags=(
                "source_value_rounded_to_whole_million",
                "source_amount_is_not_exact",
            ),
            disposition_reason="eighteen_approximate_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2013_14: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2013-14-overview",
            profile=vote_health_estimates_summary.PROFILE_2013_14,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2013_14,
            vintage=vote_health_estimates_summary.VINTAGE_2013_14,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2013_14,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2013_14,
            fact_count=17,
            parse_pages=vote_health_estimates_summary.parse_overview_2013_14_pages,
            quality_flags=(
                "source_value_rounded_to_whole_million",
                "source_amount_is_not_exact",
            ),
            disposition_reason="seventeen_selected_2013_14_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2014_15: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2014-15-overview",
            profile=vote_health_estimates_summary.PROFILE_2014_15,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2014_15,
            vintage=vote_health_estimates_summary.VINTAGE_2014_15,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2014_15,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2014_15,
            fact_count=18,
            parse_pages=vote_health_estimates_summary.parse_overview_2014_15_pages,
            quality_flags=(
                "source_value_rounded_to_whole_million",
                "source_amount_is_not_exact",
            ),
            disposition_reason="eighteen_selected_2014_15_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2015_16: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2015-16-overview",
            profile=vote_health_estimates_summary.PROFILE_2015_16,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2015_16,
            vintage=vote_health_estimates_summary.VINTAGE_2015_16,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2015_16,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2015_16,
            fact_count=17,
            parse_pages=vote_health_estimates_summary.parse_overview_2015_16_pages,
            quality_flags=(
                "source_value_rounded_to_whole_million",
                "source_amount_is_not_exact",
            ),
            disposition_reason="seventeen_selected_2015_16_overview_headlines_only",
        ),
        vote_health_estimates_summary.VINTAGE_2017_18: ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2017-18-overview",
            profile=vote_health_estimates_summary.PROFILE_2017_18,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2017_18,
            vintage=vote_health_estimates_summary.VINTAGE_2017_18,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2017_18,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2017_18,
            fact_count=25,
            parse_pages=vote_health_estimates_summary.parse_overview_2017_18_pages,
            quality_flags=("source_reported_in_whole_millions",),
            disposition_reason="twenty_five_selected_2017_18_overview_statements_only",
        ),
    }
)


def reviewed_overview_profile(source_vintage: str) -> ReviewedOverviewProfile:
    """Return exact operational controls without changing legacy registration."""
    if source_vintage == vote_health_estimates_summary.VINTAGE_2016_17:
        return ReviewedOverviewProfile(
            adapter_id="nz-treasury-vote-health-estimates-2016-17-overview",
            profile=vote_health_estimates_summary.PROFILE_2016_17,
            transformation=vote_health_estimates_summary.TRANSFORMATION_2016_17,
            vintage=vote_health_estimates_summary.VINTAGE_2016_17,
            source_sha256=vote_health_estimates_summary.SOURCE_SHA256_2016_17,
            page_count=vote_health_estimates_summary.PAGE_COUNT_2016_17,
            fact_count=24,
            parse_pages=vote_health_estimates_summary.parse_overview_2016_17_pages,
            quality_flags=("source_reported_in_whole_millions",),
            disposition_reason="twenty_four_selected_2016_17_overview_statements_only",
        )
    profile = _PROFILES.get(source_vintage)
    if profile is None:
        message = "unsupported reviewed overview vintage"
        raise ValueError(message)
    return profile


def reviewed_overview_profiles() -> tuple[ReviewedOverviewProfile, ...]:
    """Enumerate exact reviewed controls, including the retained legacy boundary."""
    vintages = {*_PROFILES, vote_health_estimates_summary.VINTAGE_2016_17}
    return tuple(reviewed_overview_profile(vintage) for vintage in sorted(vintages))


def vote_health_estimates_overview_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register only an existing reviewed vintage; keep the 2016/17 API intact."""
    if source_vintage == vote_health_estimates_summary.VINTAGE_2016_17:
        return legacy_overview.vote_health_estimates_2016_17_registration(
            source_locator=source_locator,
            source_vintage=source_vintage,
            observed_at=observed_at,
        )
    profile = _PROFILES.get(source_vintage)
    if profile is None:
        message = "unsupported reviewed overview vintage"
        raise ValueError(message)
    adapter = ReviewedVoteHealthOverviewAdapter(
        profile, source_locator, source_vintage, observed_at
    )
    return AdapterRegistration(
        adapter_id=profile.adapter_id,
        version="1",
        media_type="application/pdf",
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
