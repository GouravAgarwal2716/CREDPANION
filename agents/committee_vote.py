"""
agents/committee_vote.py
Credit Committee: weighted voting simulation across 4 agent perspectives.
Auditor 0.35 | Sleuth 0.25 | Vision 0.20 | Adversarial 0.20
Decision: weighted_score > 0.7 → APPROVE, else → REJECT
"""
from __future__ import annotations
from typing import List
from models.state_schema import CreditCaseState, CommitteeVote

WEIGHTS = {
    "Auditor":     0.35,
    "Sleuth":      0.25,
    "Vision":      0.20,
    "Adversarial": 0.20,
}


def _auditor_vote(state: CreditCaseState) -> CommitteeVote:
    """Auditor votes based on financial health indicators."""
    flags = 0
    if state.get("circular_trading_detected"):
        flags += 1
    if state.get("revenue_inflation_detected"):
        flags += 1
    mismatch = state.get("bank_mismatch_pct", 0)
    if mismatch > 20:
        flags += 1

    score = max(0.0, 1.0 - flags * 0.33)
    vote = "APPROVE" if score >= 0.5 else "REJECT"
    rationale = (
        f"{flags} forensic flag(s) — circular: {state.get('circular_trading_detected')}, "
        f"inflation: {state.get('revenue_inflation_detected')}, "
        f"mismatch: {mismatch:.1f}%."
    )
    return CommitteeVote(agent="Auditor", vote=vote, score=round(score, 3), rationale=rationale)


def _sleuth_vote(state: CreditCaseState) -> CommitteeVote:
    """Sleuth votes based on legal risk profile."""
    legal_flags = state.get("legal_flags", [])
    s138_count = sum(1 for f in legal_flags if "138" in f)
    contagion = state.get("promoter_contagion_detected", False)

    penalty = s138_count * 0.25 + (0.30 if contagion else 0)
    score = max(0.0, 1.0 - penalty)
    vote = "APPROVE" if score >= 0.5 else "REJECT"
    rationale = (
        f"{len(legal_flags)} legal flag(s) | S.138 cases: {s138_count} | "
        f"Promoter contagion: {contagion}."
    )
    return CommitteeVote(agent="Sleuth", vote=vote, score=round(score, 3), rationale=rationale)


def _vision_vote(state: CreditCaseState) -> CommitteeVote:
    """Vision agent votes based on operational reality score."""
    reality = state.get("reality_score", 1.0)
    score = reality
    vote = "APPROVE" if score >= 0.5 else "REJECT"
    rationale = f"Operational reality score: {reality:.2f} (threshold: 0.50)."
    return CommitteeVote(agent="Vision", vote=vote, score=round(score, 3), rationale=rationale)


def _adversarial_vote(state: CreditCaseState) -> CommitteeVote:
    """Adversarial agent votes based on fraud signal count."""
    signals = state.get("adversarial_signals", [])
    hard_block = state.get("hard_block", False)

    if hard_block:
        score = 0.0
        vote = "REJECT"
        rationale = f"Hard block triggered — {len(signals)} concurrent fraud signal(s)."
    else:
        score = max(0.0, 1.0 - len(signals) * 0.20)
        vote = "APPROVE" if score >= 0.5 else "REJECT"
        rationale = f"{len(signals)} fraud signal(s): {signals or ['None']}."

    return CommitteeVote(agent="Adversarial", vote=vote, score=round(score, 3), rationale=rationale)


def run_committee_vote(state: CreditCaseState) -> CreditCaseState:
    """
    LangGraph node: Committee Vote.
    Aggregates weighted votes from all committee members.
    """
    state.setdefault("audit_trail", [])

    state["audit_trail"].append("Committee: Convening credit committee vote...")

    votes: List[CommitteeVote] = [
        _auditor_vote(state),
        _sleuth_vote(state),
        _vision_vote(state),
        _adversarial_vote(state),
    ]

    # Compute weighted score
    weighted_score = sum(WEIGHTS[v["agent"]] * v["score"] for v in votes)
    decision = "APPROVE" if weighted_score > 0.7 else "REJECT"

    for v in votes:
        state["audit_trail"].append(
            f"Committee [{v['agent']}]: {v['vote']} (score={v['score']:.2f}) — {v['rationale']}"
        )

    state["committee_votes"] = votes
    state["committee_decision"] = decision
    state["committee_weighted_score"] = round(weighted_score, 4)

    state["audit_trail"].append(
        f"Committee: Final weighted score = {weighted_score:.4f} → Decision: {decision}."
    )
    return state
