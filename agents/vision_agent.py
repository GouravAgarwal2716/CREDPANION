"""
agents/vision_agent.py
Factory Vision Agent: analyses uploaded factory photos and computes reality score.
"""
from __future__ import annotations
from models.state_schema import CreditCaseState
from tools.vision_analysis import analyse_factory_photos, synthesize_vision_result


def run_vision_agent(state: CreditCaseState) -> CreditCaseState:
    """
    LangGraph node: Vision Agent.
    Analyses factory photos (real or synthetic) and sets reality_score.
    """
    state.setdefault("audit_trail", [])
    state.setdefault("vision_results", [])

    company = state.get("company_name", "CleanCorp")
    photo_paths = state.get("photo_file_paths", [])

    state["audit_trail"].append("Vision: Processing factory imagery...")

    if photo_paths:
        results, aggregate_score = analyse_factory_photos(photo_paths)
        state["audit_trail"].append(
            f"Vision: Analysed {len(photo_paths)} factory photo(s) — "
            f"reality score = {aggregate_score:.2f}."
        )
    else:
        # Use synthetic vision data based on company type
        company_type_map = {
            "CleanCorp": "clean",
            "FraudCo": "fraud",
            "LitigationLtd": "litigation",
        }
        company_type = company_type_map.get(company, "clean")
        results, aggregate_score = synthesize_vision_result(company_type)
        state["audit_trail"].append(
            f"Vision: No photos uploaded — synthetic analysis for '{company}' "
            f"profile → reality score = {aggregate_score:.2f}."
        )

    state["vision_results"] = results
    state["reality_score"] = aggregate_score

    # Detailed per-image log
    for r in results:
        active = r.get("active_assets", 0)
        idle = r.get("idle_assets", 0)
        state["audit_trail"].append(
            f"Vision: Active assets = {active}, Idle assets = {idle}, "
            f"Reality score = {r.get('reality_score', 0):.2f}."
        )

    if aggregate_score < 0.5:
        state["audit_trail"].append("Vision: ⚠ Idle machinery detected — operational reality concerns.")
    else:
        state["audit_trail"].append("Vision: Plant utilisation appears satisfactory.")

    return state
