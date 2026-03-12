"""
agents/adversarial_agent.py
Adversarial Evaluator: stress-tests the credit case.
If multiple fraud signals coexist, issues a hard block.
"""
from __future__ import annotations
from models.state_schema import CreditCaseState


# Hard block trigger: at least this many red signals simultaneously
HARD_BLOCK_THRESHOLD = 3


def run_adversarial_agent(state: CreditCaseState) -> CreditCaseState:
    """
    LangGraph node: Adversarial Evaluator.
    Reviews all signals and determines if a hard-block fraud condition exists.
    """
    state.setdefault("audit_trail", [])
    state.setdefault("forensic_report", [])

    state["audit_trail"].append("Adversarial: Running stress-test and adversarial evaluation...")

    fraud_signals = []

    # Signal 1: Circular Trading
    if state.get("circular_trading_detected", False):
        fraud_signals.append("Circular Trading (Carousel)")

    # Signal 2: Revenue Inflation
    if state.get("revenue_inflation_detected", False):
        fraud_signals.append("Revenue Inflation")

    # Signal 3: Section 138 / Legal Flags
    legal_flags = state.get("legal_flags", [])
    s138_flags = [f for f in legal_flags if "Section 138" in f or "138" in f]
    if s138_flags:
        fraud_signals.append(f"Section 138 NI Act ({len(s138_flags)} case(s))")

    # Signal 4: Promoter Contagion
    if state.get("promoter_contagion_detected", False):
        fraud_signals.append("Promoter Contagion")

    # Signal 5: Very low reality score
    reality_score = state.get("reality_score", 1.0)
    if reality_score < 0.3:
        fraud_signals.append(f"Critically low reality score ({reality_score:.2f})")

    # Signal 6: High bank mismatch
    mismatch = state.get("bank_mismatch_pct", 0.0)
    if mismatch > 40:
        fraud_signals.append(f"Extreme bank-GST mismatch ({mismatch:.1f}%)")

    # ── Hard Block Decision ──
    hard_block = len(fraud_signals) >= HARD_BLOCK_THRESHOLD
    state["hard_block"] = hard_block

    if hard_block:
        block_msg = (
            f"HARD BLOCK TRIGGERED — {len(fraud_signals)} concurrent fraud signal(s) detected: "
            + "; ".join(fraud_signals)
            + ". Case escalated directly to Risk Engine."
        )
        state["forensic_report"].append(block_msg)
        state["audit_trail"].append(f"Adversarial: ⛔ {block_msg}")
    else:
        state["audit_trail"].append(
            f"Adversarial: {len(fraud_signals)} fraud signal(s) — below hard-block threshold "
            f"({HARD_BLOCK_THRESHOLD}). Proceeding to committee vote."
        )

    state["adversarial_signals"] = fraud_signals
    state["audit_trail"].append(
        f"Adversarial: Hard block = {'YES' if hard_block else 'NO'} | "
        f"Signals: {fraud_signals or ['None']}"
    )
    return state
