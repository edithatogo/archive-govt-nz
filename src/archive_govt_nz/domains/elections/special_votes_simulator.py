"""Monte Carlo simulation engine for uncounted special votes.

Simulates partisan swings and seat-flip probabilities across knife-edge electorates.
"""

from __future__ import annotations

import random
from typing import Any

from archive_govt_nz.domains.elections.contracts import (
    SpecialVotesSensitivity,
    VulnerableElectorate,
)


def simulate_special_votes(
    electorates: list[dict[str, Any]],
    estimated_special_votes: int = 400000,
    historical_left_drift_mean: float = 1.65,
    historical_left_drift_std: float = 0.4,
    iterations: int = 10000,
    seed: int = 42,
) -> SpecialVotesSensitivity:
    """Run Monte Carlo simulation of special vote outcomes on marginal electorates.

    Parameters
    ----------
    electorates : list[dict[str, Any]]
        List of electorates with 'electorate_name', 'winner', 'runner_up', 'margin', 'total_votes'.
    estimated_special_votes : int
        Estimated total special votes remaining (default ~400,000).
    historical_left_drift_mean : float
        Mean left-bloc percentage gain on special votes (default 1.65 pp).
    historical_left_drift_std : float
        Standard deviation of left-bloc swing (default 0.40 pp).
    iterations : int
        Number of Monte Carlo simulation runs (default 10,000).
    seed : int
        RNG seed for reproducibility.

    Returns
    -------
    SpecialVotesSensitivity
        Flip probabilities and overhang distribution.

    """
    rng = random.Random(seed)
    vulnerable_electorates: list[VulnerableElectorate] = []

    # Identify close electorates (margins under 1,500 votes)
    close_electorates = [e for e in electorates if e.get("margin", 99999) < 1500]

    flip_counts = {e["electorate_name"]: 0 for e in close_electorates}
    overhang_distribution_counts: dict[int, int] = {}
    right_bloc_majority_count = 0
    left_bloc_majority_count = 0

    base_overhang = 11  # 2026 preliminary baseline: National 7, TPM 4

    for _ in range(iterations):
        # Sample leftward drift for this simulation run
        drift = rng.gauss(historical_left_drift_mean, historical_left_drift_std)
        simulated_flips = 0

        for e in close_electorates:
            margin = e["margin"]
            tot = e.get("total_votes", 35000)
            spec_share = (
                (estimated_special_votes / (71 * tot)) * tot if tot > 0 else 5000
            )

            # Net swing in votes towards challenger
            net_special_swing = spec_share * (drift / 100.0)
            if net_special_swing > margin:
                flip_counts[e["electorate_name"]] += 1
                simulated_flips += 1

        # Adjust simulated overhang: flips in TPM or National change overhang
        simulated_overhang = max(8, min(14, base_overhang - (simulated_flips // 2)))
        overhang_distribution_counts[simulated_overhang] = (
            overhang_distribution_counts.get(simulated_overhang, 0) + 1
        )

        # Check majority status: majority threshold is floor((120 + overhang)/2) + 1
        majority_needed = (120 + simulated_overhang) // 2 + 1
        # Centre-right baseline ~67 seats minus flips
        right_seats = 67 - simulated_flips
        if right_seats >= majority_needed:
            right_bloc_majority_count += 1
        else:
            left_bloc_majority_count += 1

    # Format vulnerable electorate flip probabilities
    for e in close_electorates:
        prob = flip_counts[e["electorate_name"]] / iterations
        vulnerable_electorates.append(
            VulnerableElectorate(
                electorate_name=e["electorate_name"],
                preliminary_winner=e["winner"],
                preliminary_runner_up=e["runner_up"],
                preliminary_margin=e["margin"],
                flip_probability=round(prob, 4),
            )
        )

    # Sort vulnerable electorates by flip probability descending
    vulnerable_electorates.sort(key=lambda v: v.flip_probability, reverse=True)

    overhang_dist = {
        str(k): round(v / iterations, 4)
        for k, v in sorted(overhang_distribution_counts.items())
    }

    majority_probs = {
        "right_bloc_majority": round(right_bloc_majority_count / iterations, 4),
        "left_bloc_majority": round(left_bloc_majority_count / iterations, 4),
        "hung_parliament": round(
            max(
                0.0,
                1.0
                - (right_bloc_majority_count + left_bloc_majority_count) / iterations,
            ),
            4,
        ),
    }

    return SpecialVotesSensitivity(
        election_year=2026,
        preliminary_capture_date="2026-11-09",
        estimated_special_votes=estimated_special_votes,
        simulation_runs=iterations,
        vulnerable_electorates=vulnerable_electorates,
        overhang_probability_distribution=overhang_dist,
        majority_bloc_probabilities=majority_probs,
    )
