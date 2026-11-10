# Interactive Election Visualization Space Track (2026-11-10)

## Overview
Deploys the New Zealand General Election interactive analytical explorer to Hugging Face Spaces (`edithatogo/nz-election-explorer`) and local runtimes. Features dual architecture: a 10-tab Python Gradio interface (`app.py`, `gradio_app.py`) for local execution and advanced compute environments, and an asynchronous client-side static engine (`index.html`) optimized for zero-quota static hosting.

## Core Capabilities
1. **Statutory MMP Sainte-Laguë & Overhang Engine:**
   - 131-seat House simulation (+11 overhang seats above statutory 120 baseline).
   - Dynamic majority target ($\lfloor 131/2 \rfloor + 1 = 66$).
2. **Special Votes Sensitivity Analysis:**
   - Real-time slider simulating 0% to 25% special votes and leftward swing.
   - Live recalculation of final margins for 5 key battleground electorates (Nelson, Te Atatū, Banks Peninsula, Mount Albert, Hauraki-Waikato).
3. **Calibrated XGBoost Marginal Electorate Classifier:**
   - Trained on 710 historical MMP contest records.
   - Evaluates flip probability based on candidate spend, incumbency, 2023 Census median age/income, and historical special vote swings.
4. **Campaign Finance & Local Representation Breakdown:**
   - Differentiates cost-per-vote, cost-per-elected-MP, and cost-per-local-electorate-MP.
   - Major donor disclosures (> $20,000 threshold) and Gini inequality metrics.
5. **Longitudinal Historical Assessment (1996–2026):**
   - CPI-deflated campaign expenditures across 10 MMP election cycles.
   - Historical overhang emergence tracking (2005, 2008, 2011, 2023, 2026).
6. **Macroeconomic & Environmental Predictive Modeling (2029):**
   - Hibbs-Stokes political-economic model parameterized for New Zealand fundamentals.
   - Dynamic parameters: real GDP growth, CPI inflation, 2-year fixed mortgage rates, term fatigue, NZDep deprivation index, and severe climate/drought anomalies.
7. **Geographic Mapping & Parliamentary Complex Systems:**
   - High-resolution electorate outcome map (`figures/electorate_map_2026.png`).
   - Overhang evolution timeline (`figures/overhang_expansion_timeline.png`).
   - Interactive 131-MP Boids caucus flocking simulation.

## Verification
- Test suite: 20 passing unit/integration tests in `tests/test_elections_*.py`.
- Linter: Ruff check 100% clean with zero warnings or errors.
- Deployment commit: Hugging Face Space `edithatogo/nz-election-explorer` commit `dad2e5e3e26ba480d6d52c1630e44555d6d9efd0`.
- Local verification: Gradio server active at `http://127.0.0.1:7860`.
