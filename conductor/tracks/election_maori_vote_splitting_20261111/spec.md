# Technical Specification: Māori Electorate Vote-Splitting Secondary Effects

## 1. Mathematical Formulation
* **Total Valid Party Votes:**
  $$V_{\text{national}} = V_{\text{general}} + V_{\text{maori}} = 2,520,000 + 220,000 = 2,740,000$$
* **General Electorates Baseline Share:**
  $$s_{p,\text{gen}} = \frac{V_{p,\text{gen}}}{V_{\text{gen}}}$$
* **Counterfactual Māori Baseline PV:**
  $$\hat{V}_{p,\text{maori}} = s_{p,\text{gen}} \times V_{\text{maori}}$$
* **Tactical Excess Party Votes:**
  $$\Delta V_{p,\text{excess}} = \max\left(0, V_{p,\text{maori}} - \hat{V}_{p,\text{maori}}\right)$$
* **Sainte-Laguë Counterfactual Allocation:**
  $$V'_{p,\text{national}} = V_{p,\text{national}} - \Delta V_{p,\text{excess}}$$
  $$q_p(s) = \frac{V'_p}{2s + 1}, \quad s \in \{0, 1, \dots, 119\}$$
* **Overhang & House Size:**
  $$O_p = \max\left(0, E_p - S_p\right)$$
  $$H_{\text{total}} = 120 + \sum_{p} O_p$$

## 2. Vote-Splitting Index
$$\Delta_{\text{split}} = \text{Candidate Vote Share \%} - \text{Party Vote Share \%}$$
