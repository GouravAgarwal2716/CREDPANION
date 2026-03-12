"""
tools/financial_reconciliation.py
Forensic financial analysis: revenue inflation detection, bank-GST mismatch,
and circular trading (4-node carousel) detection using NetworkX.
"""
from __future__ import annotations
import networkx as nx
from typing import List, Dict, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Revenue Inflation Check
# ─────────────────────────────────────────────────────────────────────────────

def check_revenue_inflation(bank_credits: float, gst_sales: float) -> Tuple[bool, float, str]:
    """
    Rule: ratio = bank_credits / gst_sales
    If ratio < 0.85  → Revenue Inflation Detected
    Returns (detected: bool, ratio: float, message: str)
    """
    if gst_sales <= 0:
        return False, 0.0, "GST sales figure is zero; cannot compute ratio."

    ratio = bank_credits / gst_sales
    if ratio < 0.85:
        msg = (
            f"Revenue Inflation Detected — Bank credits (₹{bank_credits:,.0f}) are only "
            f"{ratio * 100:.1f}% of declared GST sales (₹{gst_sales:,.0f}). "
            f"Threshold: 85%. Delta: {(0.85 - ratio) * 100:.1f}pp below threshold."
        )
        return True, ratio, msg

    return False, ratio, (
        f"Revenue reconciled — ratio {ratio * 100:.1f}% ≥ 85% threshold. "
        f"Bank credits: ₹{bank_credits:,.0f} vs GST sales: ₹{gst_sales:,.0f}."
    )


def compute_bank_mismatch_pct(bank_credits: float, gst_sales: float) -> float:
    """
    Returns the absolute percentage mismatch between bank credits and GST sales.
    Used for conditional routing in LangGraph (re-parse if > 20%).
    """
    if gst_sales <= 0:
        return 100.0
    return abs(bank_credits - gst_sales) / gst_sales * 100


# ─────────────────────────────────────────────────────────────────────────────
# Circular Trading Detection
# ─────────────────────────────────────────────────────────────────────────────

def build_transaction_digraph(transactions: List[Dict]) -> nx.DiGraph:
    """Build a directed graph from a list of {sender, receiver, amount} dicts."""
    G = nx.DiGraph()
    for txn in transactions:
        sender = txn["sender"]
        receiver = txn["receiver"]
        amount = txn.get("amount", 0)
        if G.has_edge(sender, receiver):
            G[sender][receiver]["amount"] += amount
            G[sender][receiver]["count"] += 1
        else:
            G.add_edge(sender, receiver, amount=amount, count=1)
    return G


def detect_circular_trading(transactions: List[Dict], min_cycle_length: int = 3) -> Tuple[bool, List[List[str]]]:
    """
    Detect carousel fraud: find simple cycles of length >= min_cycle_length.
    A 4-node pattern A→B→C→D→A is the classic carousel.
    Returns (detected: bool, cycles: List[List[str]])
    """
    G = build_transaction_digraph(transactions)
    try:
        all_cycles = list(nx.simple_cycles(G))
    except Exception:
        return False, []

    suspicious = [c for c in all_cycles if len(c) >= min_cycle_length]
    return len(suspicious) > 0, suspicious


def get_fraud_nodes(transactions: List[Dict]) -> List[str]:
    """Return all node names that participate in a circular trading cycle."""
    _, cycles = detect_circular_trading(transactions)
    fraud_nodes: set[str] = set()
    for cycle in cycles:
        fraud_nodes.update(cycle)
    return list(fraud_nodes)


def full_forensic_audit(bank_credits: float, gst_sales: float, transactions: List[Dict]) -> Dict:
    """
    Run the complete forensic suite and return a structured audit report.
    """
    inflation_detected, ratio, inflation_msg = check_revenue_inflation(bank_credits, gst_sales)
    mismatch_pct = compute_bank_mismatch_pct(bank_credits, gst_sales)
    circular_detected, cycles = detect_circular_trading(transactions)
    fraud_nodes = get_fraud_nodes(transactions)

    flags = []
    if inflation_detected:
        flags.append("Revenue Inflation Detected")
    if circular_detected:
        flags.append(f"Circular Trading Detected ({len(cycles)} carousel(s) found)")

    return {
        "inflation_detected": inflation_detected,
        "ratio": ratio,
        "inflation_message": inflation_msg,
        "mismatch_pct": mismatch_pct,
        "circular_trading_detected": circular_detected,
        "carousel_cycles": cycles,
        "fraud_nodes": fraud_nodes,
        "flags": flags,
    }
