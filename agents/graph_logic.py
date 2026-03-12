"""
agents/graph_logic.py
LangGraph StateGraph orchestration for the Credpanion credit committee pipeline.

Workflow:
  extractor → auditor → sleuth → vision_agent → adversarial_evaluator
             ↓ (conditional)           ↓ (hard block shortcut)
         re-extractor             risk_engine → cam_generator
             ↓
       committee_vote → risk_engine → cam_generator
"""
from __future__ import annotations
import uuid
from typing import Literal
from models.state_schema import CreditCaseState
from agents.extractor_agent import run_extractor
from agents.auditor_agent import run_auditor
from agents.sleuth_agent import run_sleuth
from agents.vision_agent import run_vision_agent
from agents.adversarial_agent import run_adversarial_agent
from agents.committee_vote import run_committee_vote
from agents.risk_engine import run_risk_engine
from agents.cam_generator import run_cam_generator

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Conditional Edge Routers
# ─────────────────────────────────────────────────────────────────────────────

def _route_after_auditor(state: CreditCaseState) -> Literal["re_extract", "sleuth"]:
    """
    Re-route to extractor if:
    - GST sales is zero (bad parse), OR
    - bank mismatch > 20% AND still on first attempt (max 2 retries)
    """
    gst = state.get("gst_sales", 0.0)
    mismatch = state.get("bank_mismatch_pct", 0.0)
    attempts = state.get("reparse_attempts", 0)

    if (gst == 0 or mismatch > 20) and attempts < 2:
        return "re_extract"
    return "sleuth"


def _route_after_adversarial(state: CreditCaseState) -> Literal["committee_vote", "risk_engine"]:
    """
    Hard block → skip committee, go directly to risk engine.
    Normal path → committee vote.
    """
    if state.get("hard_block", False):
        return "risk_engine"
    return "committee_vote"


# ─────────────────────────────────────────────────────────────────────────────
# Graph Builder
# ─────────────────────────────────────────────────────────────────────────────

def build_graph():
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(CreditCaseState)

    # ── Register Nodes ──
    graph.add_node("extractor",            run_extractor)
    graph.add_node("auditor",              run_auditor)
    graph.add_node("sleuth",               run_sleuth)
    graph.add_node("vision_agent",         run_vision_agent)
    graph.add_node("adversarial_evaluator", run_adversarial_agent)
    graph.add_node("committee_vote",       run_committee_vote)
    graph.add_node("risk_engine",          run_risk_engine)
    graph.add_node("cam_generator",        run_cam_generator)

    # ── Entry Point ──
    graph.set_entry_point("extractor")

    # ── Linear Edges ──
    graph.add_edge("extractor", "auditor")

    # ── Conditional: auditor → re-extract OR sleuth ──
    graph.add_conditional_edges(
        "auditor",
        _route_after_auditor,
        {
            "re_extract": "extractor",
            "sleuth":     "sleuth",
        },
    )

    graph.add_edge("sleuth",    "vision_agent")
    graph.add_edge("vision_agent", "adversarial_evaluator")

    # ── Conditional: adversarial → committee OR risk engine (hard block) ──
    graph.add_conditional_edges(
        "adversarial_evaluator",
        _route_after_adversarial,
        {
            "committee_vote": "committee_vote",
            "risk_engine":    "risk_engine",
        },
    )

    graph.add_edge("committee_vote", "risk_engine")
    graph.add_edge("risk_engine",    "cam_generator")
    graph.add_edge("cam_generator",  END)

    return graph.compile()


# ─────────────────────────────────────────────────────────────────────────────
# Sequential Fallback (when LangGraph not available)
# ─────────────────────────────────────────────────────────────────────────────

def _run_sequential(state: CreditCaseState) -> CreditCaseState:
    """
    Pure Python sequential fallback when LangGraph is not installed.
    Respects the same conditional routing logic.
    """
    # Extractor (with retry loop)
    for _ in range(2):
        state = run_extractor(state)
        state = run_auditor(state)
        route = _route_after_auditor(state)
        if route == "sleuth":
            break

    state = run_sleuth(state)
    state = run_vision_agent(state)
    state = run_adversarial_agent(state)

    if _route_after_adversarial(state) == "committee_vote":
        state = run_committee_vote(state)

    state = run_risk_engine(state)
    state = run_cam_generator(state)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# Module-level compiled graph (built once)
_GRAPH = None


def get_compiled_graph():
    global _GRAPH
    if _GRAPH is None and LANGGRAPH_AVAILABLE:
        _GRAPH = build_graph()
    return _GRAPH


def run_analysis(initial_state: dict) -> CreditCaseState:
    """
    Run the full credit analysis pipeline.
    Uses LangGraph if available, otherwise falls back to sequential execution.

    Args:
        initial_state: dict with at minimum 'company_name'.

    Returns:
        Final CreditCaseState after all agents have run.
    """
    # Ensure required fields have defaults
    defaults: CreditCaseState = {
        "company_name":          initial_state.get("company_name", "CleanCorp"),
        "case_id":               initial_state.get("case_id", f"CRED-{uuid.uuid4().hex[:8].upper()}"),
        "gst_sales":             0.0,
        "bank_credits":          0.0,
        "transactions":          [],
        "legal_flags":           [],
        "circular_trading_detected": False,
        "revenue_inflation_detected": False,
        "bank_mismatch_pct":     0.0,
        "hard_block":            False,
        "forensic_report":       [],
        "vision_results":        [],
        "reality_score":         1.0,
        "committee_votes":       [],
        "risk_results":          None,
        "counterfactual_analysis": [],
        "cam_document_path":     "",
        "audit_trail":           [],
        "gst_file_paths":        initial_state.get("gst_file_paths", []),
        "bank_file_paths":       initial_state.get("bank_file_paths", []),
        "photo_file_paths":      initial_state.get("photo_file_paths", []),
        "reparse_attempts":      0,
        "promoter_contagion_detected": False,
        "adversarial_signals":   [],
        "committee_decision":    "",
        "committee_weighted_score": 0.0,
    }
    # Merge caller overrides
    defaults.update({k: v for k, v in initial_state.items() if v is not None})

    graph = get_compiled_graph()
    if graph is not None:
        result = graph.invoke(defaults)
    else:
        result = _run_sequential(defaults)

    return result
