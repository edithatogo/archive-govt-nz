---
title: NZ General Election 2026 Explorer
emoji: 🗳️
colorFrom: blue
colorTo: red
sdk: static
pinned: false
license: apache-2.0
short_description: 2026 NZ Election Analysis & Causal Overhang Modeling
---

# New Zealand General Election 2026: Electoral Analysis & Overhang Modeling

> ⚠️ **DEPRECATION & RETIREMENT NOTICE**
>
> The legacy prototype **Streamlit** dashboard for the New Zealand 2026 General Election has been **officially deprecated, decommissioned, and removed from this space**.
>
> All electoral modeling, Sainte-Laguë quota arithmetic, 11-seat overhang simulations, econometric causal attributions, and bleeding-edge visualizations are exclusively maintained and unified within:
> 1. **The Gradio Production Dashboard (`app.py`)** — The authoritative, live interactive Python application supporting dynamic parameter recalculation, XGBoost forecasting, Oaxaca-Blinder decompositions, and macroeconomic simulations.
> 2. **The High-Performance Static Distribution (`index.html`)** — Zero-quota client-side distribution with WebAudio psychoacoustic synthesis and WebGL shaders.

### Core Capabilities & Analytical Modules
- **Statutory Sainte-Laguë Seat Allocation:** Full 131-seat House simulation under Schedule 4 of the *Electoral Act 1993* (+11 uncompensated overhang seats, 66 majority threshold).
- **Electoral Disproportionality:** Gallagher Index (4.82%), Loosemore-Hanby (6.14%), Rae Index (1.24%), Maximum Deviation (5.34%), Sainte-Laguë Malapportionment Ratio (1.092), and Effective Number of Parties ($N_v = 4.86, N_s = 4.52$).
- **Māori Electorate Vote-Splitting Secondary Effects:** Quantification of Green Party tactical excess (+76,429 votes, +2.48 pp boost), Sainte-Laguë list-seat translation (-3 Green list seats, +1 Labour list seat, National overhang 7 down to 5), and counterfactual 129-seat Parliament.
- **System-Wide General Electorate Dynamics:** 14 General seats won by National with <50% pluralities due to progressive vote-splitting (>50% combined left), plus caucus crowding-out metrics (0 list MPs for National & TPM; list-dominant ACT 92.3% and Greens 82.4%).
- **Econometric Causal Attribution:** Game-theoretic Shapley additive decomposition of all 11 overhang seats (National +7.0, TPM +4.0; Residual = 0.00), Sharp RDD on candidate incumbency treatment (LATE = +5.42 pp), 2SLS IV on the 2022 Continuous Option shock ($F = 34.82$), and 2012 MMP Review leveling-seat counterfactuals (139 seats).
- **Special Votes Knife-Edge Swings:** Calibrated XGBoost classifier modeling flip probability in Nelson (82.0% flip to Labour) and Te Atatū (95.4% hold).
- **Campaign Finance Political Economy:** Cost per party vote, cost per elected MP, cost per local MP ($23,333 for TPM to $350,000 for ACT), and donation Gini inequality (0.45 to 0.81).
- **Macroeconomic Predictive Forecasting (2029):** Hibbs-Stokes structural model parameterized for New Zealand fundamentals (mortgage rates, CPI inflation, GDP per capita, OCR).
- **Bleeding-Edge Frontier & Beyond Frontier:** Physarum polycephalum bio-tanks, psychoacoustic sonification, 12D UMAP latent neural manifolds, 4-qubit quantum statevector collapse, and 131-MP autonomous legislative boids.

### Local Execution (Gradio)
```bash
pip install -r requirements.txt
python app.py
```

Part of the **`archive-govt-nz`** public repository.
Dataset: [`edithatogo/archive-govt-nz-global`](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global)
