---
title: NZ General Election 2026 Explorer
emoji: 🗳️
colorFrom: blue
colorTo: red
sdk: static
pinned: false
license: apache-2.0
short_description: 2026 NZ Election Analysis and Overhang Modeling
---

# New Zealand General Election 2026: Electoral Analysis & Overhang Modeling

Electoral analysis of the 7 November 2026 New Zealand General Election provisional results:
- Statutory Sainte-Laguë seat allocation under Schedule 4 of the *Electoral Act 1993*.
- 11-seat overhang analysis and 131-seat House expansion (66-seat governing majority threshold).
- Special votes sensitivity modeling across marginal electorates.
- Econometric causal inference on campaign expenditure returns (1996–2025).
- Census 2023 demographic multivariate attribution (SHAP and PCA).
- Agent-based parliamentary caucus simulation.

### Local Execution (Gradio)
```bash
pip install -r requirements.txt
python app.py
```

Part of the **`archive-govt-nz`** public repository.
Dataset: [`edithatogo/archive-govt-nz-global`](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global)
