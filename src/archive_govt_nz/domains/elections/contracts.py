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
    excluded_party_votes: dict[str, int] = Field(default_factory=dict)
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


# Beyond-Frontier Multi-Sensory, Biological, Quantum & Neuro-Symbolic Contracts


class WetwareSlimeMouldSimulation(BaseModel):
    """Synthetic biology / Physarum polycephalum bio-computing contract."""

    organism: str = "Physarum polycephalum"
    medium: str = "Nutrient agar on Aotearoa relief topography"
    duration_hours: float = 48.0
    strains: dict[str, dict[str, str]] = Field(
        default_factory=lambda: {
            "National": {"color": "#00529F", "fluorescence": "BFP", "initial_biomass": "430mg"},
            "Labour": {"color": "#D82A20", "fluorescence": "RFP", "initial_biomass": "340mg"},
            "Greens": {"color": "#098137", "fluorescence": "GFP", "initial_biomass": "180mg"},
            "ACT": {"color": "#FDE401", "fluorescence": "YFP", "initial_biomass": "140mg"},
            "NZ First": {"color": "#8b949e", "fluorescence": "CFP", "initial_biomass": "120mg"},
            "Te Pāti Māori": {"color": "#800020", "fluorescence": "mCherry", "initial_biomass": "90mg"},
            "TOP": {"color": "#32B5B5", "fluorescence": "mTurquoise", "initial_biomass": "70mg"},
        }
    )
    chemo_attractant_nodes: list[dict[str, Any]]
    vein_network_density: float = Field(ge=0.0, le=1.0)
    coalition_fusion_zones: list[str]
    starvation_desert_zones: list[str]


class PsychoacousticSonificationModel(BaseModel):
    """Spatial psychoacoustics and ultrasonic haptic turbulence contract."""

    fundamental_frequencies_hz: dict[str, float]
    chord_dissonance_score: float = Field(ge=0.0, le=1.0)
    polyrhythmic_signature: str
    ultrasonic_radiation_pressure_pa: float
    haptic_vibration_profile_hz: list[float]
    coalition_haptic_friction: dict[str, float]


class NeuralManifoldLandscape(BaseModel):
    """High-dimensional UMAP / Gaussian Splatting latent space contract."""

    embedding_algorithm: Literal["UMAP", "t-SNE", "MDS", "Isomap"]
    n_features: int = 12
    explained_variance_ratio: float = Field(ge=0.0, le=1.0)
    electorate_coordinates: list[dict[str, Any]]
    latent_canyons: list[dict[str, Any]]
    elevation_surface_grid: dict[str, Any]


class QuantumSuperpositionState(BaseModel):
    """Qubit statevector and entangled measurement contract for special votes."""

    n_qubits: int = 4
    marginal_seat_qubit_mapping: dict[int, str]
    entanglement_circuit_depth: int
    bell_state_fidelity: float = Field(ge=0.0, le=1.0)
    density_matrix_real: list[list[float]]
    density_matrix_imag: list[list[float]]
    measurement_collapse_probabilities: dict[str, float]


class AutonomousMultiAgentParliament(BaseModel):
    """Artificial life / 131-MP autonomous agent swarm contract."""

    total_agents: int = 131
    seat_distribution: dict[str, int]
    active_bills: list[str]
    majority_threshold: int = 66
    boids_flocking_parameters: dict[str, float]
    agent_whip_defiance_rates: dict[str, float]
    simulation_ticks: int = 500


# Causal Overhang Attribution & Econometric Identification Contracts


class BoothLevelSplitRecord(BaseModel):
    """Granular voting place return capturing split-ticket behavior."""

    booth_id: str
    electorate_name: str
    voting_place_address: str
    total_candidate_votes: int = Field(ge=0)
    total_party_votes: int = Field(ge=0)
    candidate_votes_by_party: dict[str, int]
    party_votes_by_party: dict[str, int]
    split_differential: dict[str, float]
    advance_voting: bool = False


class MaoriRollTransferShock(BaseModel):
    """Natural experiment shock capturing continuous roll migration under 2022 Act."""

    electorate_name: str
    electorate_type: Literal["maori", "general"]
    pre_reform_roll_2023: int = Field(ge=0)
    post_reform_roll_2026: int = Field(ge=0)
    net_transfers_onto_maori_roll: int
    pct_roll_expansion: float
    tpm_candidate_margin_shift: float
    iv_z_eligibility: float = 1.0


class OverhangDriverContribution(BaseModel):
    """Shapley additive seat contribution from a specific causal driver."""

    driver_id: Literal[
        "split_voting_decoupling",
        "minor_party_siphon_denominator",
        "maori_roll_switch_shock",
        "incumbency_candidate_brand",
        "geographic_concentration",
    ]
    driver_name: str
    methodology: Literal[
        "oaxaca_blinder_counterfactual",
        "sharp_rdd",
        "instrumental_variables_2sls",
        "shapley_additive_attribution",
    ]
    seats_attributed_national: float
    seats_attributed_tpm: float
    total_seats_attributed: float
    confidence_interval_95: list[float]
    p_value: float = Field(ge=0.0, le=1.0)
    causal_interpretation: str


class CausalOverhangAttribution(BaseModel):
    """Complete econometric causal attribution payload for the 11-seat overhang."""

    analysis_timestamp: datetime
    total_overhang_seats: int = 11
    national_overhang_seats: int = 7
    tpm_overhang_seats: int = 4
    oaxaca_blinder_decomposition: dict[str, float]
    rdd_incumbency_lates: dict[str, Any]
    iv_maori_roll_estimates: dict[str, Any]
    shapley_seat_attributions: list[OverhangDriverContribution]
    total_attributed_sum: float
    unexplained_residual_seats: float
    counterfactual_review_2012: dict[str, Any]
    provenance: DynamicEngineProvenance | None = None


# Māori Electorate Vote-Splitting & Upstream Transfer Contracts


class MaoriSeatReturnRecord(BaseModel):
    """Electorate-level return for one of the 7 Māori electorates."""

    electorate_name: str
    total_valid_party_votes: int = Field(ge=0)
    total_valid_candidate_votes: int = Field(ge=0)
    party_votes: dict[str, int]
    party_percentages: dict[str, float]
    candidate_votes: dict[str, int]
    candidate_percentages: dict[str, float]
    vote_splitting_indices: dict[str, float]


class PartyExcessPVRecord(BaseModel):
    """Quantification of excess party vote derived from Māori electorates."""

    party_name: str
    general_electorates_pv: int = Field(ge=0)
    general_electorates_pv_pct: float
    maori_electorates_actual_pv: int = Field(ge=0)
    maori_electorates_actual_pv_pct: float
    maori_electorates_baseline_pv: int = Field(ge=0)
    excess_party_votes: int
    national_actual_pv: int = Field(ge=0)
    national_counterfactual_pv: int = Field(ge=0)
    national_actual_pv_pct: float
    national_counterfactual_pv_pct: float
    percentage_point_boost: float


class CounterfactualSeatRow(BaseModel):
    """Comparative seat outcome under actual vs counterfactual Sainte-Laguë."""

    party_name: str
    actual_entitlement: int = Field(ge=0)
    actual_electorates: int = Field(ge=0)
    actual_list_seats: int = Field(ge=0)
    actual_total_seats: int = Field(ge=0)
    actual_overhang: int = Field(ge=0)
    counterfactual_entitlement: int = Field(ge=0)
    counterfactual_list_seats: int = Field(ge=0)
    counterfactual_total_seats: int = Field(ge=0)
    counterfactual_overhang: int = Field(ge=0)
    delta_list_seats: int
    delta_total_seats: int


class MaoriVoteSplittingAnalysis(BaseModel):
    """Comprehensive secondary effects analysis of Māori electorate vote-splitting."""

    analysis_timestamp: datetime
    election_year: int = 2026
    vintage: Literal["preliminary", "official"] = "preliminary"
    total_valid_pv_national: int
    total_valid_pv_general: int
    total_valid_pv_maori: int
    maori_electorate_returns: list[MaoriSeatReturnRecord]
    excess_pv_by_party: list[PartyExcessPVRecord]
    seat_comparison_by_party: list[CounterfactualSeatRow]
    actual_house_size: int = 131
    counterfactual_house_size: int = 129
    house_size_reduction: int = 2
    green_excess_pv: int
    green_list_seat_impact: int = -3
    labour_excess_pv: int
    labour_list_seat_impact: int = 1
    national_overhang_reduction: int = -2
    data_sources_and_approximations: list[str]


# System-Wide All-Seat Vote-Splitting & Caucus Crowding-Out Contracts


class GeneralSeatSplitRecord(BaseModel):
    """Electorate split dynamics across general seats capturing plurality splits."""

    electorate_name: str
    electorate_type: Literal["general", "maori"]
    winning_party: str
    winning_margin: int
    candidate_shares: dict[str, float]
    party_vote_shares: dict[str, float]
    is_plurality_split_win: bool
    split_index_by_party: dict[str, float]


class CaucusCrowdingOutRecord(BaseModel):
    """Quantification of list-seat displacement and caucus crowding-out."""

    party_name: str
    proportional_entitlement: int = Field(ge=0)
    electorates_won: int = Field(ge=0)
    list_seats_allocated: int = Field(ge=0)
    total_seats: int = Field(ge=0)
    overhang_seats: int = Field(ge=0)
    list_seat_share_pct: float
    crowding_out_status: Literal[
        "complete_extinction",
        "severe_compression",
        "balanced",
        "list_dominant",
    ]
    institutional_consequence: str


class SystemWideVoteSplittingAnalysis(BaseModel):
    """Full-system secondary effects analysis across all 71 electorates."""

    analysis_timestamp: datetime
    total_electorates: int = 71
    general_electorates_count: int = 64
    maori_electorates_count: int = 7
    total_house_seats: int = 131
    overhang_seats_total: int = 11
    plurality_split_general_seats_count: int = 14
    plurality_split_electorates: list[str]
    caucus_crowding_out_by_party: list[CaucusCrowdingOutRecord]
    general_seat_sample_splits: list[GeneralSeatSplitRecord]
    coalition_threshold_actual: int = 66
    coalition_threshold_nominal: int = 61
    coalition_arithmetic_impact: str



