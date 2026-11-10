"""Pydantic data contracts for New Zealand General Election analytics.

Implements strict validation matching JSON Schemas in ``schemas/election/``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PartyVoteRow(BaseModel):
    """Normalized party vote record."""

    party_name: str
    party_votes: int = Field(ge=0)
    party_vote_percentage: float = Field(ge=0.0, le=100.0)
    electorate_seats_won: int = Field(ge=0, default=0)


class ElectorateResultRow(BaseModel):
    """Winning and runner-up candidate returns for an electorate."""

    electorate_name: str
    type: Literal["general", "maori"]
    winning_candidate: str
    winning_party: str
    margin: int = Field(ge=0)
    runner_up_candidate: str = ""
    runner_up_party: str = ""
    total_valid_votes: int = Field(ge=0, default=0)


class RawElectionResults(BaseModel):
    """Raw election result payload (Bronze/Silver border)."""

    election_year: int = Field(ge=1996, le=2030)
    vintage: Literal["preliminary", "official"]
    captured_at: datetime
    total_votes_cast: int = Field(ge=0)
    special_votes_estimated: int = Field(ge=0, default=0)
    special_votes_counted: bool = False
    parties: list[PartyVoteRow]
    electorates: list[ElectorateResultRow]


class PartyAllocation(BaseModel):
    """Sainte-Laguë allocation for a qualifying party."""

    party_name: str
    qualification_reason: Literal["threshold_5_percent", "electorate_seat", "both"]
    party_vote: int = Field(ge=0)
    proportional_entitlement: int = Field(ge=0)
    electorate_seats: int = Field(ge=0)
    list_seats: int = Field(ge=0)
    total_seats: int = Field(ge=0)


class SainteLagueResult(BaseModel):
    """Statutory Sainte-Laguë seat allocation receipt."""

    election_year: int
    vintage: Literal["preliminary", "official"]
    nominal_seats: int = 120
    qualifying_parties: list[str]
    excluded_parties: list[str]
    allocations: list[PartyAllocation]


class PartyOverhangDetail(BaseModel):
    """Overhang metrics per party."""

    party_name: str
    proportional_entitlement: int
    electorate_seats_won: int
    overhang_seats: int = Field(ge=0)
    seat_share_percentage: float
    vote_share_percentage: float


class DisproportionalityIndices(BaseModel):
    """Standard electoral disproportionality metrics."""

    gallagher_index: float = Field(ge=0.0)
    loosemore_hanby_index: float = Field(ge=0.0)


class OverhangAnalysis(BaseModel):
    """Overhang analysis and expanded House sizing."""

    election_year: int
    vintage: Literal["preliminary", "official"]
    nominal_seats: int = 120
    total_house_seats: int = Field(ge=120)
    overhang_seats_total: int = Field(ge=0)
    majority_threshold: int = Field(ge=61)
    overhang_details: list[PartyOverhangDetail]
    disproportionality_indices: DisproportionalityIndices


class VulnerableElectorate(BaseModel):
    """Marginal electorate at risk of flipping under special votes."""

    electorate_name: str
    preliminary_winner: str
    preliminary_runner_up: str
    preliminary_margin: int
    flip_probability: float = Field(ge=0.0, le=1.0)


class SpecialVotesSensitivity(BaseModel):
    """Sensitivity analysis over uncounted special votes."""

    election_year: int
    preliminary_capture_date: str
    estimated_special_votes: int
    simulation_runs: int = 10000
    vulnerable_electorates: list[VulnerableElectorate]
    overhang_probability_distribution: dict[str, float]
    majority_bloc_probabilities: dict[str, float]


class PartyFinanceRecord(BaseModel):
    """Financial returns for a party."""

    party_name: str
    total_donations: float = Field(ge=0.0)
    total_expenses: float = Field(ge=0.0)
    cost_per_party_vote: float = Field(ge=0.0)
    seats_won: int = Field(ge=0, default=0)
    cost_per_elected_seat: float = Field(ge=0.0, default=0.0)
    donor_gini_coefficient: float = Field(ge=0.0, le=1.0)


class ElectorateFinanceRecord(BaseModel):
    """Candidate spending returns in an electorate."""

    electorate_name: str
    winning_candidate_spend: float = Field(ge=0.0)
    runner_up_spend: float = Field(ge=0.0)
    third_party_promoter_spend: float = Field(ge=0.0, default=0.0)
    spend_margin_ratio: float = 0.0


class CampaignFinanceAttribution(BaseModel):
    """Econometric spend attribution and causal models."""

    election_year: int
    parties_finance: list[PartyFinanceRecord]
    electorates_finance: list[ElectorateFinanceRecord]
    causal_models: dict[str, Any]


class MultivariateDrivers(BaseModel):
    """Multivariate feature matrix and attribution."""

    election_year: int
    feature_matrix_variables: list[str]
    pca_decomposition: dict[str, Any]
    shap_attribution: dict[str, Any]
    elastic_net_drivers: dict[str, float]



# --- Longitudinal & Expanded Funding / Predictive Contracts ---


class LongitudinalPartySummary(BaseModel):
    """Historical election party performance record."""

    party_name: str
    party_vote_share: float = Field(ge=0.0, le=100.0)
    electorate_seats: int = Field(ge=0)
    list_seats: int = Field(ge=0)
    total_seats: int = Field(ge=0)
    overhang_seats: int = Field(ge=0, default=0)
    cost_per_vote_real: float = Field(ge=0.0)
    cost_per_elected_mp_real: float = Field(ge=0.0)


class LongitudinalElectionRecord(BaseModel):
    """Historical longitudinal election record across 10 MMP cycles (1996-2026)."""

    election_year: int = Field(ge=1996, le=2035)
    total_registered_electors: int = Field(ge=1000000)
    total_votes_cast: int = Field(ge=1000000)
    turnout_percentage: float = Field(ge=50.0, le=100.0)
    nominal_seats: int = 120
    overhang_seats: int = Field(ge=0)
    total_house_seats: int = Field(ge=120)
    majority_threshold: int = Field(ge=61)
    total_campaign_spend_nominal: float = Field(ge=0.0)
    total_campaign_spend_cpi_adjusted_2026: float = Field(ge=0.0)
    mean_cost_per_vote_cpi_adjusted: float = Field(ge=0.0)
    mean_cost_per_mp_cpi_adjusted: float = Field(ge=0.0)
    party_summaries: list[LongitudinalPartySummary]


class MajorDonorDisclosure(BaseModel):
    """Individual or institutional major political donor disclosure (> $5,000)."""

    donor_name: str
    recipient_party: str
    amount: float = Field(ge=5000.0)
    category: Literal[
        "individual_hnwi",
        "corporate_business",
        "trade_union",
        "trust_foundation",
        "bequest",
        "other",
    ]
    disclosure_year: int


class LocalCandidateSpendingRecord(BaseModel):
    """Candidate-level local electorate expenditure and win rate."""

    electorate_name: str
    party_name: str
    candidate_name: str
    candidate_expenditure: float = Field(ge=0.0)
    electorate_won: bool
    statutory_limit: float = 32600.0


class PartyDetailedFunding(BaseModel):
    """Party financial breakdown with cost per vote, elected MP, and local candidate MP."""

    party_name: str
    total_donations: float = Field(ge=0.0)
    total_party_expenses: float = Field(ge=0.0)
    total_candidate_expenses: float = Field(ge=0.0)
    party_votes: int = Field(ge=0)
    electorates_won: int = Field(ge=0)
    total_seats_won: int = Field(ge=0)
    cost_per_party_vote: float = Field(ge=0.0)
    cost_per_elected_mp: float = Field(ge=0.0)
    cost_per_local_electorate_mp: float | None = None
    donation_gini: float = Field(ge=0.0, le=1.0)


class CampaignFundingDonorsAnalysis(BaseModel):
    """Full campaign funding, donor concentration, and local member cost contract."""

    election_year: int
    filing_vintage: Literal["annual_return", "10_day_major_disclosure", "consolidated_archive"]
    parties: list[PartyDetailedFunding]
    major_donors: list[MajorDonorDisclosure]
    local_candidate_metrics: list[LocalCandidateSpendingRecord]


class MacroeconomicFundamentals(BaseModel):
    """Macroeconomic voting indicators influencing incumbent government durability."""

    real_gdp_growth_pct: float
    cpi_inflation_pct: float
    two_year_mortgage_rate_pct: float
    unemployment_rate_pct: float
    incumbent_term_count: int = Field(ge=1)
    official_cash_rate_pct: float = Field(default=4.75, description="RBNZ Official Cash Rate")
    terms_of_trade_index: float = Field(default=124.5, description="Stats NZ Terms of Trade Index")
    household_debt_to_income_ratio: float = Field(default=5.8, description="Macroprudential DTI ratio")
    real_wage_growth_gap_pct: float = Field(default=-0.6, description="Real wage growth minus CPI inflation")
    consumer_confidence_index: float = Field(default=91.2, description="Westpac-McDermott Miller Consumer Confidence")


class DynamicEngineProvenance(BaseModel):
    """Cryptographic provenance and runtime versioning for all analytical outputs."""

    engine_version: str = "v2.4.0-frontier"
    input_fingerprint_sha256: str
    calculation_timestamp: datetime
    random_seed: int = 42
    cas_merkle_root: str
    active_economic_indicators_count: int = 10
    models_invoked: list[str] = Field(
        default_factory=lambda: [
            "sainte_lague_odd_divisor",
            "overhang_131_seat_expansion",
            "xgboost_electorate_flip_classifier",
            "sharp_rdd_2sls_late",
            "hibbs_stokes_macroeconomic_2029",
            "boids_swarm_caucus_flocking",
        ]
    )


class SocioeconomicIndicators(BaseModel):
    """Census deprivation and household cost pressure metrics."""

    nzdep_median_decile: float = Field(ge=1.0, le=10.0)
    housing_affordability_ratio: float
    food_cost_annual_change_pct: float


class ClimateEnvironmentalIndicators(BaseModel):
    """Environmental and primary industry weather anomaly metrics."""

    drought_soil_moisture_deficit_anomaly: float
    severe_flood_cyclone_disaster_events: int = Field(ge=0)


class ElectorateFlipForecast(BaseModel):
    """Machine learning (XGBoost) prediction for an electorate contest."""

    electorate_name: str
    incumbent_party: str
    challenger_party: str
    flip_probability_xgboost: float = Field(ge=0.0, le=1.0)
    predicted_margin: float


class GoldElectionForecast(BaseModel):
    """Synthesized predictive forecast model for subsequent general elections."""

    target_election_year: int = Field(ge=2026, le=2035)
    forecast_generated_at: datetime
    methodology_stack: list[
        Literal[
            "xgboost_classifier",
            "linear_macro_fundamentals",
            "socioeconomic_nzdep_elastic_net",
            "bayesian_poll_aggregation",
        ]
    ]
    macroeconomic_fundamentals: MacroeconomicFundamentals
    socioeconomic_indicators: SocioeconomicIndicators
    climate_environmental_indicators: ClimateEnvironmentalIndicators
    electorate_flip_forecasts: list[ElectorateFlipForecast]
    parliamentary_seat_projections: dict[str, dict[str, Any]]
    coalition_formation_probabilities: dict[str, float]
    provenance: DynamicEngineProvenance | None = None
