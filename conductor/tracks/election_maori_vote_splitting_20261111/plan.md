# Implementation Plan: Māori Electorate Vote-Splitting Secondary Effects

## Phases
1. [x] **Contracts & Models**: Define Pydantic models in `contracts.py` (`MaoriSeatReturnRecord`, `PartyExcessPVRecord`, `CounterfactualSeatRow`, `MaoriVoteSplittingAnalysis`).
2. [x] **Computational Engine**: Implement `maori_vote_splitting_engine.py` with Sainte-Laguë counterfactual re-allocation and Parquet export.
3. [x] **Test Verification**: Implement `test_elections_maori_splitting.py` covering per-electorate integrity, excess votes, seat impacts, and Parquet readback.
4. [x] **Publication Visualizations**: Implement `generate_vote_splitting_figures.py` delivering 5 publication charts (300 DPI dark theme) and HTML interactive explorer.
5. [x] **Space Integration**: Embed interactive explorer, plots, and tables into `spaces/nz-election-explorer/app.py` and `index.html`.
