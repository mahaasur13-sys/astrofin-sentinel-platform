"""meta_rl/visualization.py — ATOM-META-RL-011: Evolution Charts"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

VISUALIZATION_ENABLED = True


def generate_all_charts(
    history,
    elites,
    karl_state_history,
    basket_metrics,
    session_id: str = "no_session",
    output_dir: str | None = None,
) -> dict[str, str]:
    """
    Generate all evolution visualization charts.

    Returns dict of chart_name → output_path.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    out = Path(output_dir) if output_dir else Path(__file__).parent.parent / "data" / "meta_rl"
    out.mkdir(parents=True, exist_ok=True)

    results: dict[str, str] = {}

    try:
        # ── 1. Reward convergence ────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(10, 5))
        if history:
            gens = [s.generation for s in history]
            max_r = [s.max_reward for s in history]
            mean_r = [s.mean_reward for s in history]
            min_r = [s.min_reward for s in history]
            ax.plot(gens, max_r, "g-", linewidth=2, label="Best", marker="o", markersize=4)
            ax.plot(
                gens,
                mean_r,
                "b--",
                linewidth=1.5,
                label="Mean",
                marker="s",
                markersize=3,
            )
            ax.fill_between(gens, min_r, max_r, alpha=0.15, color="green", label="Range")
        ax.set_xlabel("Generation")
        ax.set_ylabel("Reward")
        ax.set_title(f"Reward Convergence — {session_id}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        p = out / f"{session_id}_reward_convergence.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        results["reward_convergence"] = str(p)
    except Exception as e:
        logger.warning(f"[META-RL-VIS] reward_convergence failed: {e}")

    try:
        # ── 2. KARL Q* over time ─────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(10, 4))
        if karl_state_history:
            qstars = [float(k.get("current_q_star", 0.0)) for k in karl_state_history]
            gens = list(range(len(qstars)))
            ax.plot(gens, qstars, "m-", linewidth=2, marker="D", markersize=4)
            ax.axhline(0.0, color="gray", linestyle="--", alpha=0.5)
        ax.set_xlabel("Generation")
        ax.set_ylabel("Q* (KARL)")
        ax.set_title(f"KARL Q* — {session_id}")
        ax.grid(True, alpha=0.3)
        p = out / f"{session_id}_karl_qstar.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        results["karl_qstar"] = str(p)
    except Exception as e:
        logger.warning(f"[META-RL-VIS] karl_qstar failed: {e}")

    try:
        # ── 3. Diversity / std over generations ───────────────────────────────
        fig, ax = plt.subplots(figsize=(10, 4))
        if history:
            gens = [s.generation for s in history]
            std_r = [s.std_reward for s in history]
            ax.bar(gens, std_r, color="steelblue", alpha=0.7)
            ax.set_xlabel("Generation")
            ax.set_ylabel("Std(Reward)")
            ax.set_title(f"Population Diversity — {session_id}")
            ax.grid(True, alpha=0.3, axis="y")
        p = out / f"{session_id}_diversity.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        results["diversity"] = str(p)
    except Exception as e:
        logger.warning(f"[META-RL-VIS] diversity failed: {e}")

    try:
        # ── 4. Top strategy chromosomes radar (top 3 elites) ────────────────
        if elites and len(elites) >= 1:
            top = sorted(elites, key=lambda s: s.reward, reverse=True)[:3]
            labels = [
                "conf_th",
                "pos_size",
                "atr_mult",
                "sig_bull",
                "sig_bear",
            ]
            num_vars = len(labels)

            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"polar": True})
            colors = ["#2ecc71", "#3498db", "#e74c3c"]
            for i, s in enumerate(top):
                c = s.strategy.chromosome
                values = [
                    float(c.get("confidence_threshold", 60)) / 100,
                    float(c.get("position_size_pct", 15)) / 30,
                    float(c.get("atr_multiplier", 2)) / 4,
                    float(c.get("signal_weights_bull", 0.7)),
                    float(c.get("signal_weights_bear", 0.5)),
                ]
                values += values[:1]
                ax.plot(
                    angles,
                    values,
                    color=colors[i % len(colors)],
                    linewidth=2,
                    label=f"#{i + 1} r={s.reward:.3f}",
                )
                ax.fill(angles, values, alpha=0.1, color=colors[i % len(colors)])

            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels, size=9)
            ax.set_title(f"Top Strategy Chromosomes — {session_id}", size=11)
            ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
            p = out / f"{session_id}_chromosomes_radar.png"
            fig.savefig(p, dpi=150, bbox_inches="tight")
            plt.close(fig)
            results["chromosomes_radar"] = str(p)
    except Exception as e:
        logger.warning(f"[META-RL-VIS] chromosomes_radar failed: {e}")

    try:
        # ── 5. Improvement rate over generations ──────────────────────────────
        fig, ax = plt.subplots(figsize=(10, 4))
        if history and len(history) >= 2:
            gens = [s.generation for s in history]
            improvements = [s.improvement_over_prev for s in history]
            colors = ["green" if v >= 0 else "red" for v in improvements]
            ax.bar(gens, improvements, color=colors, alpha=0.7)
            ax.axhline(0.0, color="gray", linestyle="--")
            ax.set_xlabel("Generation")
            ax.set_ylabel("Improvement Δ")
            ax.set_title(f"Reward Improvement — {session_id}")
            ax.grid(True, alpha=0.3, axis="y")
        p = out / f"{session_id}_improvement.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        results["improvement"] = str(p)
    except Exception as e:
        logger.warning(f"[META-RL-VIS] improvement failed: {e}")

    logger.info(f"[META-RL-VIS] Generated {len(results)}/5 charts: {list(results.keys())}")
    return results
