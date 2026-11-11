# Track: Econometric Causal Inference and Attribution of the 11-Seat Overhang

## Status: Completed

### Objectives
1. **Estimate Causal Attribution:** Disentangle the exact causal mechanisms behind the 2026 11-seat overhang (National +7, Te Pāti Māori +4).
2. **Identification Strategies:**
   - Semi-parametric counterfactual decomposition (Gelman-King / Oaxaca-Blinder) isolating ticket-splitting from minor party denominator shrinkage.
   - Instrumental Variables (2SLS) on the 2023–2024 continuous Māori Electoral Option policy shock.
   - Sharp Regression Discontinuity Design (RDD) for officeholder incumbency treatment on candidate-party vote divergence.
   - Cooperative game-theoretic Shapley value attribution delivering exact additive seat contributions summing to $+11.0$ seats.
3. **Canonical Contracts & Schemas:** Defined in `contracts.py` (`CausalOverhangAttribution`, `BoothLevelSplitRecord`, `MaoriRollTransferShock`, `OverhangDriverContribution`) and `schemas/election/causal-overhang-attribution-v1.schema.json`.
4. **Publication Visualizations:** Generate publication figures (waterfall seat attribution, RDD incumbency jump, IV response curves) and interactive dashboard sliders.
