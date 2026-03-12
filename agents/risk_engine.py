"""
agents/risk_engine.py
Deterministic credit risk scorer + counterfactual simulator.
Base: 40 | Penalties defined per risk factor.
Categories: Low (0-40) | Medium (41-70) | High (71-100)
"""
from __future__ import annotations
import json
import os
from datetime import datetime
from models.state_schema import CreditCaseState, RiskResult
from tools.counterfactual_simulator import run_counterfactual_analysis

BASE_SCORE = 40

PENALTIES = {
    "circular_trading":   25,
    "section_138":        20,
    "revenue_inflation":  15,
    "low_reality_score":  10,
    "promoter_contagion": 20,
}


def score_to_category(score: int) -> str:
    if score <= 40:
        return "Low"
    elif score <= 70:
        return "Medium"
    return "High"


def run_risk_engine(state: CreditCaseState) -> CreditCaseState:
    """
    LangGraph node: Risk Engine.
    Computes deterministic risk score, categories, and counterfactuals.
    """
    state.setdefault("audit_trail", [])
    state.setdefault("legal_flags", [])

    state["audit_trail"].append("Risk Engine: Computing deterministic credit risk score...")

    # ── Gather flags ──
    circular        = state.get("circular_trading_detected", False)
    inflation       = state.get("revenue_inflation_detected", False)
    reality_score   = state.get("reality_score", 1.0)
    low_reality     = reality_score < 0.5
    contagion       = state.get("promoter_contagion_detected", False)
    legal_flags     = state.get("legal_flags", [])
    section_138     = any("138" in f or "Section 138" in f for f in legal_flags)

    # ── Score Computation ──
    penalties_applied: dict = {}
    score = BASE_SCORE

    if circular:
        score += PENALTIES["circular_trading"]
        penalties_applied["Circular Trading"] = PENALTIES["circular_trading"]

    if section_138:
        score += PENALTIES["section_138"]
        penalties_applied["Section 138 NI Act"] = PENALTIES["section_138"]

    if inflation:
        score += PENALTIES["revenue_inflation"]
        penalties_applied["Revenue Inflation"] = PENALTIES["revenue_inflation"]

    if low_reality:
        score += PENALTIES["low_reality_score"]
        penalties_applied["Low Reality Score"] = PENALTIES["low_reality_score"]

    if contagion:
        score += PENALTIES["promoter_contagion"]
        penalties_applied["Promoter Contagion"] = PENALTIES["promoter_contagion"]

    score = min(score, 100)
    category = score_to_category(score)

    # Committee decision takes precedence if available; hard block always REJECT
    if state.get("hard_block", False):
        decision = "REJECT"
    else:
        decision = state.get("committee_decision", "APPROVE" if score <= 40 else "REJECT")

    risk_result: RiskResult = {
        "base_score": BASE_SCORE,
        "penalties": penalties_applied,
        "total_score": score,
        "category": category,
        "decision": decision,
    }
    state["risk_results"] = risk_result

    state["audit_trail"].append(
        f"Risk Engine: Score = {score}/100 | Category = {category} | Decision = {decision}."
    )

    for k, v in penalties_applied.items():
        state["audit_trail"].append(f"Risk Engine: Penalty [{k}] = +{v} points.")

    # ── Counterfactual Analysis ──
    state["audit_trail"].append("Risk Engine: Running counterfactual simulator...")
    cf = run_counterfactual_analysis(
        circular_trading=circular,
        section_138=section_138,
        revenue_inflation=inflation,
        reality_score=reality_score,
        promoter_contagion=contagion,
    )
    state["counterfactual_analysis"] = cf["scenarios"]
    state["audit_trail"].append(
        f"Risk Engine: {len(cf['scenarios'])} counterfactual scenario(s) generated."
    )

    # ── Write Committee Log ──
    _append_committee_log(state, score, decision, penalties_applied)

    return state


def _append_committee_log(state: CreditCaseState, score: int, decision: str, penalties: dict) -> None:
    """Persist the current case result to logs/committee_log.json."""
    log_path = "logs/committee_log.json"
    try:
        os.makedirs("logs", exist_ok=True)
        existing: list = []
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                try:
                    existing = json.load(f)
                except json.JSONDecodeError:
                    existing = []

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "case_id": state.get("case_id", "UNKNOWN"),
            "company_name": state.get("company_name", "UNKNOWN"),
            "risk_score": score,
            "decision": decision,
            "penalties": penalties,
            "committee_votes": [
                {"agent": v["agent"], "vote": v["vote"], "score": v["score"]}
                for v in state.get("committee_votes", [])
            ],
        }
        existing.append(entry)

        with open(log_path, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception:
        pass  # Non-fatal; logging failure should not break the pipeline
