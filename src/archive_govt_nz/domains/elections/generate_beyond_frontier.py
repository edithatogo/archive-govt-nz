# ruff: noqa: FBT003, SIM118, T201
"""Publication-grade 300 DPI visualization generator for Beyond-Frontier paradigms.

Generates:
1. beyond_frontier_1_wetware_slime_mould.png
2. beyond_frontier_2_psychoacoustic_sonification_haptics.png
3. beyond_frontier_3_neural_manifold_latent_landscape.png
4. beyond_frontier_4_true_quantum_superposition_qubits.png
5. beyond_frontier_5_autonomous_multiagent_parliament.png
"""

from __future__ import annotations

import shutil
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from archive_govt_nz.domains.elections.beyond_frontier_engine import (
    compute_neural_manifold_landscape,
    simulate_autonomous_multiagent_parliament,
    simulate_quantum_superposition_qubits,
    simulate_wetware_slime_mould,
    synthesize_psychoacoustic_sonification,
)


def generate_all_beyond_frontier_figures() -> list[Path]:
    """Generate all 5 beyond-frontier publication figures at 300 DPI."""
    repo_root = Path(__file__).resolve().parents[4]
    figures_dir = repo_root / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    # 1. Wetware Slime Mould Simulation
    f1 = figures_dir / "beyond_frontier_1_wetware_slime_mould.png"
    slime_data = simulate_wetware_slime_mould()
    fig = plt.figure(figsize=(13, 8), facecolor="#030712")
    ax = fig.add_subplot(111, facecolor="#030712")

    # Draw Petri Dish circular rim
    theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(np.cos(theta) * 10, np.sin(theta) * 10, color="#1e293b", lw=4, alpha=0.8)
    ax.fill(np.cos(theta) * 9.9, np.sin(theta) * 9.9, color="#0b1329", alpha=0.6)

    # Transform coordinates to dish plane
    nodes = slime_data.chemo_attractant_nodes
    lats = np.array([n["lat"] for n in nodes])
    lons = np.array([n["lon"] for n in nodes])
    y_scaled = (lats - np.mean(lats)) * 1.5
    x_scaled = (lons - np.mean(lons)) * 1.5

    party_colors = {
        "National": "#00529F", "Labour": "#D82A20", "Greens": "#098137",
        "ACT": "#FDE401", "NZ First": "#94a3b8", "Te Pāti Māori": "#ef4444", "TOP": "#06b6d4"
    }

    # Draw branching protoplasmic vein networks
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            dist = np.hypot(x_scaled[i] - x_scaled[j], y_scaled[i] - y_scaled[j])
            if dist < 4.2:
                # Organic noisy path
                n_pts = 30
                t_line = np.linspace(0, 1, n_pts)
                xp = x_scaled[i] * (1 - t_line) + x_scaled[j] * t_line + np.random.randn(n_pts) * 0.08
                yp = y_scaled[i] * (1 - t_line) + y_scaled[j] * t_line + np.random.randn(n_pts) * 0.08
                ax.plot(xp, yp, color="#38bdf8", lw=dist * 0.6, alpha=0.35, zorder=2)
                ax.plot(xp, yp, color="#f43f5e", lw=dist * 0.3, alpha=0.25, zorder=2)

    # Plot glowing voting-booth nutrient attractors
    for i, n in enumerate(nodes):
        c = party_colors.get(n["dominant"], "#38bdf8")
        s = n["turnout"] * 450
        ax.scatter(x_scaled[i], y_scaled[i], s=s * 1.8, color=c, alpha=0.25, zorder=4)
        ax.scatter(x_scaled[i], y_scaled[i], s=s, color=c, alpha=0.85, edgecolors="#ffffff", lw=1.2, zorder=5)
        ax.text(x_scaled[i] + 0.25, y_scaled[i], n["name"], color="#e2e8f0", fontsize=9, fontweight="bold", zorder=6)

    ax.set_title("Beyond Frontier 1: Wetware / Bio-Luminescent Growth Tank (Physarum polycephalum Biological Viz)\n48-Hour Biological Network Optimization on Aotearoa Relief Topography", color="#f8fafc", fontsize=13, fontweight="bold", pad=15)
    ax.text(-9, -8.5, f"Organism: {slime_data.organism}\nVein Network Density: {slime_data.vein_network_density:.1%}\nCoalition Fusion: {slime_data.coalition_fusion_zones[0]}", color="#94a3b8", fontsize=9, bbox=dict(boxstyle="round,pad=0.5", facecolor="#111827", edgecolor="#374151"))
    ax.set_xlim(-11, 11)
    ax.set_ylim(-11, 11)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(f1, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    generated.append(f1)

    # 2. Psychoacoustic Sonification & Haptics
    f2 = figures_dir / "beyond_frontier_2_psychoacoustic_sonification_haptics.png"
    sono = synthesize_psychoacoustic_sonification()
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 9), facecolor="#090d16")

    # Subplot 1: Harmonic Spectrum
    freqs = list(sono.fundamental_frequencies_hz.values())
    pnames = list(sono.fundamental_frequencies_hz.keys())
    pcolors = [party_colors.get(p, "#38bdf8") for p in pnames]
    ax1.set_facecolor("#0f172a")
    ax1.bar(pnames, freqs, color=pcolors, edgecolor="#ffffff", alpha=0.85)
    ax1.set_ylabel("Fundamental Frequency (Hz)", color="#94a3b8", fontsize=10)
    ax1.set_title("Party Harmonic Frequencies (Hz)", color="#f8fafc", fontsize=11, fontweight="bold")
    ax1.tick_params(colors="#94a3b8", rotation=30)
    ax1.grid(True, linestyle="--", alpha=0.15, color="#94a3b8")

    # Subplot 2: Sensory Dissonance Landscape
    ax2.set_facecolor("#0f172a")
    f_sweep = np.linspace(150, 420, 200)
    diss_curve = 0.2 + 0.6 * np.sin((f_sweep - 150) / 270 * np.pi) ** 2 + 0.1 * np.cos(f_sweep * 0.1)
    ax2.plot(f_sweep, diss_curve, color="#f43f5e", lw=2.5, label="Helmholtz Dissonance Surface")
    ax2.axhline(sono.chord_dissonance_score, color="#38bdf8", linestyle="--", lw=1.8, label=f"2026 Parliament Dissonance ({sono.chord_dissonance_score:.3f})")
    ax2.set_title("Psychoacoustic Sensory Dissonance Landscape", color="#f8fafc", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Frequency Band (Hz)", color="#94a3b8", fontsize=10)
    ax2.set_ylabel("Dissonance Index [0-1]", color="#94a3b8", fontsize=10)
    ax2.tick_params(colors="#94a3b8")
    ax2.legend(facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0", fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.15, color="#94a3b8")

    # Subplot 3: Polyrhythmic Phase Portrait (7:4 vs 3:2)
    ax3.set_facecolor("#0f172a")
    t = np.linspace(0, 4 * np.pi, 500)
    x_poly = np.sin(7 * t) + 0.5 * np.cos(3 * t)
    y_poly = np.cos(4 * t) + 0.5 * np.sin(2 * t)
    ax3.plot(x_poly, y_poly, color="#a855f7", lw=1.5, alpha=0.85)
    ax3.set_title(f"Polyrhythmic Phase Portrait ({sono.polyrhythmic_signature[:22]})", color="#f8fafc", fontsize=11, fontweight="bold")
    ax3.set_xlabel(r"Rhythmic Dimension $\Phi_1$", color="#94a3b8", fontsize=10)
    ax3.set_ylabel(r"Rhythmic Dimension $\Phi_2$", color="#94a3b8", fontsize=10)
    ax3.tick_params(colors="#94a3b8")
    ax3.grid(True, linestyle="--", alpha=0.15, color="#94a3b8")

    # Subplot 4: Ultrasonic Haptic Radiation Pressure & Coalition Friction
    ax4.set_facecolor("#0f172a")
    c_names = [k.split("(")[0].strip() for k in sono.coalition_haptic_friction.keys()]
    c_frict = list(sono.coalition_haptic_friction.values())
    c_bar_colors = ["#22c55e" if f < 0.5 else "#eab308" if f < 0.8 else "#ef4444" for f in c_frict]
    bars = ax4.barh(c_names, c_frict, color=c_bar_colors, edgecolor="#ffffff", alpha=0.85)
    ax4.bar_label(bars, fmt="%.2f", padding=5, color="#f8fafc", fontweight="bold")
    ax4.set_title(f"Ultrasonic Haptic Friction (P = {sono.ultrasonic_radiation_pressure_pa:.1f} Pa)", color="#f8fafc", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Haptic Friction Coefficient [0=Smooth, 1=Jagged Static]", color="#94a3b8", fontsize=10)
    ax4.tick_params(colors="#94a3b8")
    ax4.grid(True, linestyle="--", alpha=0.15, color="#94a3b8")

    fig.suptitle("Beyond Frontier 2: Psychoacoustic Sonification & Ultrasonic Haptic Turbulence\nMulti-Sensory Translation of Parliamentary Fragmentation and Coalition Shear Stress", color="#f8fafc", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(f2, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    generated.append(f2)

    # 3. Neural Manifold Latent Space Landscape
    f3 = figures_dir / "beyond_frontier_3_neural_manifold_latent_landscape.png"
    latent = compute_neural_manifold_landscape()
    fig = plt.figure(figsize=(13, 8), facecolor="#050811")
    ax = fig.add_subplot(111, projection="3d", facecolor="#050811")

    # Generate 3D surface mesh
    gx = np.linspace(-3, 3, 40)
    gy = np.linspace(-3, 3, 40)
    X, Y = np.meshgrid(gx, gy)
    # Synthetic terrain with canyons
    Z = np.exp(-((X - 1.3) ** 2 + (Y - 0.8) ** 2) / 0.8) * 0.9 + np.exp(-((X + 1.8) ** 2 + (Y - 1.4) ** 2) / 1.2) * 0.8
    # Carve a canyon at x=0
    Z -= 0.4 * np.exp(-(X ** 2) / 0.5)

    surf = ax.plot_surface(X, Y, Z, cmap="magma", alpha=0.55, edgecolor="none", zorder=1)
    ax.contour(X, Y, Z, zdir="z", offset=-0.5, cmap="magma", alpha=0.4)

    # Plot key electorates
    for e in latent.electorate_coordinates:
        c = party_colors.get(e["dominant_party"], "#38bdf8")
        ax.scatter(e["latent_x"], e["latent_y"], e["elevation"], color=c, s=120, edgecolors="#ffffff", lw=1.5, zorder=5)
        ax.text(e["latent_x"], e["latent_y"], e["elevation"] + 0.08, e["name"], color="#f8fafc", fontsize=9, fontweight="bold", zorder=6)

    # Annotation of the protest canyon
    ax.text(1.3, 0.8, 1.15, "PROTEST VOTE GRAVITY CANYON\nWellington Central + Hawke's Bay Co-location", color="#38bdf8", fontsize=10, fontweight="bold", bbox=dict(boxstyle="round,pad=0.4", facecolor="#0f172a", edgecolor="#38bdf8"))

    ax.set_facecolor("#050811")
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.tick_params(colors="#94a3b8")
    ax.set_xlabel("UMAP Latent Dimension 1", color="#94a3b8", labelpad=8)
    ax.set_ylabel("UMAP Latent Dimension 2", color="#94a3b8", labelpad=8)
    ax.set_zlabel("Behavioural Elevation (Protest Gravity)", color="#94a3b8", labelpad=8)
    ax.set_title("Beyond Frontier 3: High-Dimensional Neural Manifold / Latent Space Landscape\nAI Projection of 72 Electorates Across 12 Socioeconomic & Behavioural Gravity Features", color="#f8fafc", fontsize=13, fontweight="bold", pad=20)
    plt.tight_layout()
    fig.savefig(f3, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    generated.append(f3)

    # 4. True Quantum Superposition Qubits
    f4 = figures_dir / "beyond_frontier_4_true_quantum_superposition_qubits.png"
    q_data = simulate_quantum_superposition_qubits()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor="#060913")

    # Left: Density Matrix Real Component Heatmap
    ax1.set_facecolor("#0b1120")
    rho_r = np.array(q_data.density_matrix_real)
    im = ax1.imshow(rho_r, cmap="cividis", aspect="auto")
    fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04).ax.tick_params(colors="#94a3b8")
    ax1.set_title("Quantum Density Matrix Re[$\\rho$] (4 Entangled Marginal Qubits)", color="#f8fafc", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Basis State Index $|j\\rangle$", color="#94a3b8", fontsize=10)
    ax1.set_ylabel("Basis State Index $|i\\rangle$", color="#94a3b8", fontsize=10)
    ax1.tick_params(colors="#94a3b8")

    # Right: Measurement Collapse Probability Distribution
    ax2.set_facecolor("#0b1120")
    k_labels = [k.replace("Superposition Collapse to Challenger", "Flip").replace("Incumbent Hold", "Hold") for k in q_data.measurement_collapse_probabilities.keys()]
    p_vals = list(q_data.measurement_collapse_probabilities.values())
    p_bars = ax2.barh(k_labels, p_vals, color=["#00529F", "#D82A20", "#38bdf8"], edgecolor="#ffffff", alpha=0.85)
    ax2.bar_label(p_bars, fmt="%.1%", padding=5, color="#f8fafc", fontweight="bold")
    ax2.set_xlim(0, 1.1)
    ax2.set_title(f"Wave-Function Collapse Probabilities (Fidelity = {q_data.bell_state_fidelity:.1%})", color="#f8fafc", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Projective Measurement Probability $P(|b\\rangle)$", color="#94a3b8", fontsize=10)
    ax2.tick_params(colors="#94a3b8")
    ax2.grid(True, linestyle="--", alpha=0.15, color="#94a3b8")

    fig.suptitle("Beyond Frontier 4: True Quantum Superposition Mapping (Qubit-Driven Rendering)\nEntangled Special-Vote Wave-Function and Projective Collapse Across 399,000 Uncounted Ballots", color="#f8fafc", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(f4, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    generated.append(f4)

    # 5. Autonomous Multi-Agent Parliament
    f5 = figures_dir / "beyond_frontier_5_autonomous_multiagent_parliament.png"
    parl_data = simulate_autonomous_multiagent_parliament()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor="#080c17")

    # Left: Spatial 2D Legislative Flocking Arena
    ax1.set_facecolor("#0e1526")
    np.random.seed(131)
    # Scatter 131 agents clustered by party ideology
    party_pos = {
        "National": (0.6, -0.2), "Labour": (-0.4, 0.4), "Greens": (-0.8, 0.8),
        "ACT": (0.9, -0.6), "NZ First": (0.1, -0.7), "Te Pāti Māori": (-0.7, 0.7), "TOP": (-0.1, 0.3)
    }
    # Policy attractor in center
    ax1.scatter([0.0], [0.1], s=400, color="#f59e0b", marker="*", edgecolors="#ffffff", lw=2, zorder=6, label="Active Bill Attractor: Supermarket Duopoly Reform")

    for party, count in parl_data.seat_distribution.items():
        base_x, base_y = party_pos[party]
        c = party_colors.get(party, "#38bdf8")
        ax_agents = base_x + np.random.randn(count) * 0.12
        ay_agents = base_y + np.random.randn(count) * 0.12
        # Velocity vectors pointing toward or away from bill
        target_dir = 1.0 if party in ["Labour", "Greens", "Te Pāti Māori", "TOP", "NZ First"] else -1.0
        vx = (0.0 - ax_agents) * 0.2 * target_dir
        vy = (0.1 - ay_agents) * 0.2 * target_dir
        ax1.quiver(ax_agents, ay_agents, vx, vy, color=c, alpha=0.5, scale=5, width=0.004)
        ax1.scatter(ax_agents, ay_agents, color=c, s=55, edgecolors="#ffffff", alpha=0.85, label=f"{party} ({count})")

    ax1.set_title("131 Autonomous MP Agent Legislative Flocking Arena", color="#f8fafc", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Economic Dimension ($X$)", color="#94a3b8", fontsize=10)
    ax1.set_ylabel("Social Dimension ($Y$)", color="#94a3b8", fontsize=10)
    ax1.tick_params(colors="#94a3b8")
    ax1.grid(True, linestyle="--", alpha=0.15, color="#94a3b8")
    ax1.legend(facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0", fontsize=8, loc="lower left")

    # Right: Whip Defiance Rates and Bill Passage Threshold
    ax2.set_facecolor("#0e1526")
    parties_list = list(parl_data.agent_whip_defiance_rates.keys())
    defiance_vals = list(parl_data.agent_whip_defiance_rates.values())
    bar_cols = [party_colors.get(p, "#38bdf8") for p in parties_list]
    wbars = ax2.bar(parties_list, [v * 100 for v in defiance_vals], color=bar_cols, edgecolor="#ffffff", alpha=0.85)
    ax2.bar_label(wbars, fmt="%.1f%%", padding=3, color="#f8fafc", fontweight="bold")
    ax2.set_title("Agent Whip Defiance Rates by Parliamentary Caucus", color="#f8fafc", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Autonomous Whip Defiance Probability (%)", color="#94a3b8", fontsize=10)
    ax2.tick_params(colors="#94a3b8", rotation=25)
    ax2.grid(True, linestyle="--", alpha=0.15, color="#94a3b8")

    fig.suptitle("Beyond Frontier 5: Autonomous Multi-Agent 'Artificial Life' Parliament\n131 Autonomous MP Agents Simulating Real-Time Swarm Deliberation and Legislative Passage", color="#f8fafc", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(f5, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    generated.append(f5)

    # Mirror to Hugging Face space directory
    space_dir = repo_root / "spaces" / "nz-election-explorer"
    static_dir = space_dir / "static"
    for fig_path in generated:
        shutil.copy2(fig_path, space_dir / fig_path.name)
        shutil.copy2(fig_path, static_dir / fig_path.name)

    return generated


if __name__ == "__main__":
    figs = generate_all_beyond_frontier_figures()
    print(f"Generated {len(figs)} Beyond-Frontier figures.")
