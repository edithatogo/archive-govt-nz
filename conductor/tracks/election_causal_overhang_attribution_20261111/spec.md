# Specification: Econometric Causal Attribution of the 11-Seat Overhang

## Theoretical Framework

Under Section 191 of the *Electoral Act 1993*, a party's overhang seats $\Omega_i$ equal:
$$\Omega_i = \max\Big(0, \, E_i - S_i(\mathbf{v}_{\text{party}})\Big)$$

### Identification Equations

1. **Gelman-King / Oaxaca-Blinder Counterfactual Decomposition:**
   $$\Delta \Omega_i = \underbrace{\Big[S_i(\mathbf{v}_{\text{party}}^{\text{actual}}) - S_i(\mathbf{v}_{\text{party}}^{\text{no-siphon}})\Big]}_{\text{Minor Party Siphon Effect}} + \underbrace{\Big[E_i(V_{\text{cand}}^{\text{actual}}) - E_i(V_{\text{cand}}^{\text{no-split}})\Big]}_{\text{Split-Ticket Voting Effect}} + \underbrace{\epsilon_i}_{\text{Residual Topography}}$$

2. **Sharp Regression Discontinuity (RDD) for Incumbency Bias:**
   $$\tau_{\text{RDD}} = \lim_{M_{2023} \downarrow 0} \mathbb{E}\big[\Delta V_{2026}^{\text{cand-party}} \mid M_{2023}\big] - \lim_{M_{2023} \uparrow 0} \mathbb{E}\big[\Delta V_{2026}^{\text{cand-party}} \mid M_{2023}\big]$$

3. **Instrumental Variables (2SLS) for Māori Roll Switching Shock:**
   $$\text{Stage 1: } \text{RollNetTransfers}_k = \gamma_0 + \gamma_1 Z_k + \mathbf{X}_k \boldsymbol{\Gamma} + u_k$$
   $$\text{Stage 2: } \Delta \text{TPM\_Margin}_k = \beta_0 + \beta_1 \widehat{\text{RollNetTransfers}}_k + \mathbf{X}_k \mathbf{B} + \varepsilon_k$$

4. **Cooperative Game-Theoretic Shapley Attribution:**
   $$\phi_j = \sum_{S \subseteq N \setminus \{j\}} \frac{|S|! (|N| - |S| - 1)!}{|N|!} \Big( v(S \cup \{j\}) - v(S) \Big)$$
   Ensuring efficiency: $\sum_{j} \phi_j(\text{National}) = 7.0$ and $\sum_{j} \phi_j(\text{TPM}) = 4.0$.
