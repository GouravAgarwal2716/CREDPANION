"""
agents/auditor_agent.py
Forensic financial auditor: revenue inflation, circular trading, mismatch detection.
"""
from __future__ import annotations
from models.state_schema import CreditCaseState
from tools.financial_reconciliation import full_forensic_audit
from tools.document_rag import query_documents
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


def run_auditor(state: CreditCaseState) -> CreditCaseState:
    """
    LangGraph node: Auditor Agent.
    Runs the full forensic audit on extracted financials.
    """
    state.setdefault("audit_trail", [])
    state.setdefault("forensic_report", [])
    state.setdefault("legal_flags", [])

    gst_sales = state.get("gst_sales", 0.0)
    bank_credits = state.get("bank_credits", 0.0)
    transactions = state.get("transactions", [])

    state["audit_trail"].append("Auditor: Running forensic financial reconciliation...")



    audit = full_forensic_audit(bank_credits, gst_sales, transactions)

    # ── Revenue Inflation ──
    state["revenue_inflation_detected"] = audit["inflation_detected"]
    if audit["inflation_detected"]:
        state["forensic_report"].append(audit["inflation_message"])
        state["audit_trail"].append(
            f"Auditor: ⚠ Revenue Inflation — bank/GST ratio = {audit['ratio']*100:.1f}%."
        )
    else:
        state["audit_trail"].append(
            f"Auditor: Revenue reconciled — ratio {audit['ratio']*100:.1f}%."
        )

    # ── Bank Mismatch ──
    state["bank_mismatch_pct"] = audit["mismatch_pct"]
    if audit["mismatch_pct"] > 20:
        state["forensic_report"].append(
            f"Bank-GST Mismatch: {audit['mismatch_pct']:.1f}% deviation exceeds 20% threshold."
        )
        state["audit_trail"].append(
            f"Auditor: ⚠ {audit['mismatch_pct']:.1f}% bank mismatch detected."
        )

    # ── Circular Trading ──
    state["circular_trading_detected"] = audit["circular_trading_detected"]
    if audit["circular_trading_detected"]:
        cycles_str = " | ".join(
            " → ".join(cycle + [cycle[0]]) for cycle in audit["carousel_cycles"]
        )
        msg = f"Circular Trading Carousel: {cycles_str}. {len(audit['carousel_cycles'])} pattern(s) found."
        state["forensic_report"].append(msg)
        state["audit_trail"].append(
            f"Auditor: ⚠ Circular trading detected — {len(audit['carousel_cycles'])} carousel(s)."
        )
    else:
        state["audit_trail"].append("Auditor: No circular trading pattern detected.")

    # ── RAG Audit Notes Scan ──
    pdf_paths = state.get("gst_file_paths", []) + state.get("bank_file_paths", [])
    if pdf_paths:
        state["audit_trail"].append("Auditor: Scanning uploaded documents via RAG for adverse audit remarks...")
        try:
            # Query the ephemeral ChromaDB for audit remarks
            context = query_documents("auditor report qualification adverse remark going concern anomaly discrepancy accounting policy", pdf_paths, k=5)
            if context:
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
                prompt = (
                    "Analyze the following document excerpts. If there are any mentions of adverse audit remarks, "
                    "qualified opinions, discrepancies, or going concern warnings, list them concisely. "
                    "If none are found, output exactly 'None'.\n\n"
                    f"Excerpts:\n{context}"
                )
                response = llm.invoke([
                    SystemMessage(content="You are a strict forensic financial auditor."),
                    HumanMessage(content=prompt)
                ])
                ans = response.content.strip()
                if ans and ans.lower() != "none" and "none" not in ans.lower()[:10]:
                    flag = f"RAG Audit Discovery: {ans}"
                    state["forensic_report"].append(flag)
                    state["audit_trail"].append("Auditor: ⚠ Discovered adverse audit remarks in uploaded documents via RAG!")
                else:
                    state["audit_trail"].append("Auditor: RAG scan found no adverse remarks in documents.")
            else:
                state["audit_trail"].append("Auditor: RAG scan found no relevant audit text in documents.")
        except Exception as e:
            state["audit_trail"].append(f"Auditor: RAG analysis error ({str(e)})")

    state["audit_trail"].append(
        f"Auditor: Forensic audit complete — {len(audit['flags'])} statistical flag(s) raised."
    )
    return state
