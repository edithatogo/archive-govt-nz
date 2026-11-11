# Implementation Plan: Econometric Causal Attribution of the 11-Seat Overhang

## Phase 1: Canonical Contracts & Schema Alignment (COMPLETED)
- [x] Define `BoothLevelSplitRecord`, `MaoriRollTransferShock`, `OverhangDriverContribution`, and `CausalOverhangAttribution` in `contracts.py`.
- [x] Author JSON Schema `schemas/election/causal-overhang-attribution-v1.schema.json`.
- [x] Author contract unit tests in `tests/test_elections_contracts.py`.

## Phase 2: Econometric Engine Implementation (PENDING USER AUTHORIZATION)
- [ ] Implement `overhang_causal_attribution.py` in `src/archive_govt_nz/domains/elections/`:
  - `compute_oaxaca_blinder_overhang_decomposition()`
  - `estimate_incumbency_rdd_treatment_on_split()`
  - `estimate_maori_roll_switch_iv_effect()`
  - `compute_shapley_overhang_seat_attribution()`
- [ ] Implement unit & econometric tests in `tests/test_elections_causal_overhang.py`.

## Phase 3: Publication Figures & Visualization Space Integration (PENDING)
- [ ] Author `generate_overhang_causal_figures.py` to produce 300 DPI figures:
  - `figure_overhang_causal_waterfall.png`
  - `figure_rdd_incumbency_split_jump.png`
  - `figure_maori_roll_migration_iv.png`
- [ ] Embed interactive counterfactual decomposition sliders into `spaces/nz-election-explorer/index.html` and `gradio_app.py`.
- [ ] Update executive presentation deck and documentation.
