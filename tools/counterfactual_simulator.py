"""
tools/counterfactual_simulator.py
Simulates "what-if" risk scenarios by removing individual risk factors.
"""
from __future__ import annotations
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Penalty Definitions (must match risk_engine.py)
# ─────────────────────────────────────────────────────────────────────────────

BASE_SCORE = 40

PENALTY_MAP = {
    "circular_trading":     25,
    "section_138":          20,
    "revenue_inflation":    15,
    "low_reality_score":    10,
    "promoter_contagion":   20,
}


def compute_risk_score(
    circular_trading: bool,
    section_138: bool,
    revenue_inflation: bool,
    low_reality_score: bool,
    promoter_contagion: bool,
) -> int:
    """Compute risk score from a set of boolean risk flags."""
    score = BASE_SCORE
    if circular_trading:
        score += PENALTY_MAP["circular_trading"]
    if section_138:
        score += PENALTY_MAP["section_138"]
    if revenue_inflation:
        score += PENALTY_MAP["revenue_inflation"]
    if low_reality_score:
        score += PENALTY_MAP["low_reality_score"]
    if promoter_contagion:
        score += PENALTY_MAP["promoter_contagion"]
    return min(score, 100)


def run_counterfactual_analysis(
    circular_trading: bool,
    section_138: bool,
    revenue_inflation: bool,
    reality_score: float,
    promoter_contagion: bool,
) -> Dict:
    """
    Generate counterfactual scenarios showing score improvement if each risk is removed.
    Returns a dict with current_score and a list of scenarios.
    """
    low_reality = reality_score < 0.5

    current_score = compute_risk_score(
        circular_trading, section_138, revenue_inflation, low_reality, promoter_contagion
    )

    scenarios: List[Dict] = []

    # Scenario: Remove Circular Trading
    if circular_trading:
        alt = compute_risk_score(False, section_138, revenue_inflation, low_reality, promoter_contagion)
        scenarios.append({
            "scenario": "Remove Circular Trading",
            "score_if_removed": alt,
            "delta": current_score - alt,
            "description": "Resolving the carousel transaction pattern would be the single largest improvement.",
        })

    # Scenario: Remove Section 138 Case
    if section_138:
        alt = compute_risk_score(circular_trading, False, revenue_inflation, low_reality, promoter_contagion)
        scenarios.append({
            "scenario": "Resolve Section 138 (Cheque Bounce) Case",
            "score_if_removed": alt,
            "delta": current_score - alt,
            "description": "Settlement or court clearance of the cheque bounce case would reduce legal risk.",
        })

    # Scenario: Remove Revenue Inflation
    if revenue_inflation:
        alt = compute_risk_score(circular_trading, section_138, False, low_reality, promoter_contagion)
        scenarios.append({
            "scenario": "Remove Revenue Inflation",
            "score_if_removed": alt,
            "delta": current_score - alt,
            "description": "Providing audited accounts that reconcile GST and bank figures would clear this flag.",
        })

    # Scenario: Improve Reality Score
    if low_reality:
        alt = compute_risk_score(circular_trading, section_138, revenue_inflation, False, promoter_contagion)
        scenarios.append({
            "scenario": "Improve Operational Reality Score (>0.5)",
            "score_if_removed": alt,
            "delta": current_score - alt,
            "description": "Demonstrating active plant utilisation above 50% would clear this operational flag.",
        })

    # Scenario: Resolve Promoter Contagion
    if promoter_contagion:
        alt = compute_risk_score(circular_trading, section_138, revenue_inflation, low_reality, False)
        scenarios.append({
            "scenario": "Resolve Promoter Contagion",
            "score_if_removed": alt,
            "delta": current_score - alt,
            "description": "Director resignation from blacklisted entities would eliminate contagion risk.",
        })

    # Best-case scenario: all risks removed
    best_case = BASE_SCORE
    scenarios.append({
        "scenario": "Best Possible Case (All Risks Resolved)",
        "score_if_removed": best_case,
        "delta": current_score - best_case,
        "description": "If all risk factors are fully resolved, the base score would be achieved.",
    })

    # Sort by impact (highest delta first, excluding best case sentinel)
    main_scenarios = [s for s in scenarios if s["scenario"] != "Best Possible Case (All Risks Resolved)"]
    main_scenarios.sort(key=lambda x: x["delta"], reverse=True)
    main_scenarios.append(scenarios[-1])  # Always show best case last

    return {
        "current_score": current_score,
        "base_score": BASE_SCORE,
        "scenarios": main_scenarios,
        "risk_flags_active": {
            "circular_trading": circular_trading,
            "section_138": section_138,
            "revenue_inflation": revenue_inflation,
            "low_reality_score": low_reality,
            "promoter_contagion": promoter_contagion,
        },
    }
