"""Tests for the Econometric Causal Attribution of the 2026 MMP Overhang."""

from pathlib import Path

import pandas as pd

from archive_govt_nz.domains.elections.contracts import CausalOverhangAttribution
from archive_govt_nz.domains.elections.overhang_causal_attribution import (
    compute_oaxaca_blinder_overhang_decomposition,
    compute_shapley_overhang_seat_attribution,
    estimate_incumbency_rdd_treatment_on_split,
    estimate_maori_roll_switch_iv_effect,
    materialize_causal_overhang_parquet,
    synthesize_causal_overhang_attribution,
)


def test_oaxaca_blinder_decomposition():
    """Verify Oaxaca-Blinder counterfactual decomposition structure and values."""
    decomp = compute_oaxaca_blinder_overhang_decomposition()
    assert isinstance(decomp, dict)
    assert "left_plurality_fragmentation" in decomp
    assert "minor_party_siphon_denominator" in decomp
    assert "maori_roll_switch_shock" in decomp
    assert "inter_electorate_quotient_spillover" in decomp
    # Sum of components minus residual should account for 11 overhang seats
    assert (
        round(sum(decomp.values()), 1) == 10.0 or round(sum(decomp.values()), 1) == 11.0
    )


def test_rdd_incumbency_estimation():
    """Verify Sharp RDD local polynomial treatment estimation on ticket-splitting."""
    rdd = estimate_incumbency_rdd_treatment_on_split()
    assert rdd["running_variable"] == "margin_of_victory_2023"
    assert rdd["cutoff"] == 0.0
    assert rdd["late_estimate"] > 0.0
    assert rdd["p_value"] < 0.05
    assert len(rdd["confidence_interval_95"]) == 2
    assert (
        rdd["confidence_interval_95"][0]
        < rdd["late_estimate"]
        < rdd["confidence_interval_95"][1]
    )


def test_iv_maori_roll_switch_estimation():
    """Verify 2SLS IV regression of continuous roll switch shock on candidate margin."""
    iv = estimate_maori_roll_switch_iv_effect()
    assert iv["first_stage_f_statistic"] > 10.0  # Weak instrument threshold
    assert iv["iv_beta"] > 0.0
    assert iv["p_value"] < 0.01
    assert iv["sargan_hansen_p_value"] > 0.05  # Passes exogeneity test


def test_shapley_overhang_seat_attribution():
    """Verify Shapley additive seat attributions sum exactly to 11.0 overhang seats."""
    contributions = compute_shapley_overhang_seat_attribution()
    assert len(contributions) == 5

    total_nat = sum(c.seats_attributed_national for c in contributions)
    total_tpm = sum(c.seats_attributed_tpm for c in contributions)
    total_all = sum(c.total_seats_attributed for c in contributions)

    assert round(total_nat, 2) == 7.00
    assert round(total_tpm, 2) == 4.00
    assert round(total_all, 2) == 11.00

    for c in contributions:
        assert c.p_value <= 0.05
        assert len(c.confidence_interval_95) == 2
        assert c.causal_interpretation


def test_synthesize_causal_overhang_attribution():
    """Verify synthesis produces a compliant, complete CausalOverhangAttribution instance."""
    attr = synthesize_causal_overhang_attribution()
    assert isinstance(attr, CausalOverhangAttribution)
    assert attr.total_overhang_seats == 11
    assert attr.national_overhang_seats == 7
    assert attr.tpm_overhang_seats == 4
    assert attr.total_attributed_sum == 11.00
    assert attr.unexplained_residual_seats == 0.00
    assert "reform_option" in attr.counterfactual_review_2012
    assert attr.provenance is not None


def test_materialize_causal_overhang_parquet(tmp_path: Path) -> None:
    """Verify Parquet export executes correctly with proper schema."""
    output_path = materialize_causal_overhang_parquet(output_dir=tmp_path)
    assert output_path.exists()
    assert output_path.name == "gold_causal_overhang_attribution.parquet"

    df = pd.read_parquet(output_path)
    assert len(df) == 5
    assert set(df.columns) >= {
        "driver_id",
        "driver_name",
        "methodology",
        "seats_attributed_national",
        "seats_attributed_tpm",
        "total_seats_attributed",
        "ci_95_lower",
        "ci_95_upper",
        "p_value",
        "causal_interpretation",
    }
