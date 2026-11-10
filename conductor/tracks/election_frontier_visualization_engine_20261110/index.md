# Frontier & Beyond-Frontier Election Visualisation Engine Track (2026-11-10)

## Overview
Deploys five novel, bleeding-edge frontier data visualization paradigms for the 7 November 2026 New Zealand General Election, moving beyond standard hexmaps and static swing meters to capture high-dimensional voter behavior, overhang decoupling, and parliamentary complex systems.

## The Five Bleeding-Edge Frontier Methodologies
1. **3D Kinetic Coalition Topology (Force-Directed Topography):**
   - Political parties modeled as heavy nodes in a 3D gravitational physics engine, with mass equal to caucus seats (including National's +7 and TPM's +4 overhangs).
   - Topological grid warps under ideological strain ($Z = -\sum m_i / (d_i^2 + \epsilon)$) with tension spring bonds illustrating coalition fragility and stability index.
2. **Multi-Dimensional Electorate 'Overhang' Voronoi Tessellations:**
   - Electorate cells dynamically scaled by voter density and the 25% surge in advance voting.
   - Dual-layer glass-like "floating" secondary layer rendering electorates where candidate victory decoupled from proportional party vote share (overhang epicenters: Nelson, Te Atatū, Banks Peninsula, Hauraki-Waikato).
3. **Hyper-Dimensional Parallel Coordinates for Vote Splitting:**
   - Interactive parallel coordinates plot across 4 axes: Electorate Type, Candidate Vote, Party Vote, and Victory Margin.
   - Colored neon thread splines tracking hundreds of thousands of ticket-splitting voters, explaining why National won 43 electorate seats but zero list seats.
4. **Special Vote Probability Cones (Generative Fan Charts):**
   - Meteorological hurricane-style uncertainty tracking over the 20-day tallying timeline, displaying expanding gradient confidence cones (50%, 80%, 95% CIs) with drifting stochastic particles crossing the 66-seat threshold line.
5. **Semantic Policy Visibility Networks (CiteCompass AI Visibility Monitor):**
   - Bimodal semantic web network mapping voter concerns (Cost of Living, Supermarket Reform, Healthcare Waitlists, Treaty Principles) to party visibility and generative search citation frequency, explaining the 41.4% third-party fracture.

## Deliverables & Artifacts
- **Python Generator:** `src/archive_govt_nz/domains/elections/generate_frontier_five.py`
- **Publication Figures (300 DPI):**
  - `figures/frontier_1_kinetic_coalition_3d.png`
  - `figures/frontier_2_overhang_voronoi.png`
  - `figures/frontier_3_parallel_coordinates.png`
  - `figures/frontier_4_special_votes_cone.png`
  - `figures/frontier_5_semantic_policy_network.png`
- **Executive Slide Deck:** `figures/nz_election_2026_executive_analysis.pptx` (17 slides, 3.8 MB).
- **Social Media Distribution:** `docs/nz_election_2026_tweet_threads.md` (16-part comprehensive thread).
- **Interactive Space Integration:** Integrated into Gradio app and static mirror on Hugging Face Spaces (`edithatogo/nz-election-explorer`).

## Verification
- Test suite: `pytest tests/test_elections_*.py` passing 22/22 tests in 3.6s.
- Linter: Ruff check 100% clean with zero errors.
- Deployment commit: HF Space commit `1f41890518ccb5b2c52120314551d00a7899e52e`.
