"""
agents/sleuth_agent.py
Legal Intelligence Agent: simulates legal database lookups for
cheque bounce cases, director disqualifications, and litigation flags.
Also runs promoter contagion detection.
"""
from __future__ import annotations
from models.state_schema import CreditCaseState
from tools.promoter_contagion import detect_promoter_contagion
from tools.document_rag import query_documents
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# ─────────────────────────────────────────────────────────────────────────────
# Synthetic Legal Database (keyed by company name)
# ─────────────────────────────────────────────────────────────────────────────

LEGAL_DATABASE = {
    "CleanCorp": {
        "section_138_cases": [],
        "director_disqualified": False,
        "litigation": [],
        "directors": [
            {"din": "DIN11111111", "name": "Arun Sharma", "companies": ["CleanCorp"]},
        ],
    },
    "FraudCo": {
        "section_138_cases": [
            "Case No. 2023/CC/456 — Cheque bounce ₹1.2 Cr — Mumbai Court (pending)",
        ],
        "director_disqualified": True,
        "litigation": [
            "IBC Petition No. 2024/IBC/789 — Operational creditor default",
        ],
        "directors": [
            {
                "din": "DIN00000001",
                "name": "Vikram Mehta",
                "companies": ["FraudCo", "Carousel Holdings"],
            },
            {
                "din": "DIN22222222",
                "name": "Priya Shah",
                "companies": ["FraudCo", "Shell_B GmbH"],
            },
        ],
    },
    "LitigationLtd": {
        "section_138_cases": [
            "Case No. 2024/CC/112 — Cheque bounce ₹45 L — Delhi Court (sub-judice)",
            "Case No. 2022/CC/099 — Cheque bounce ₹80 L — Kolkata Court (resolved)",
        ],
        "director_disqualified": False,
        "litigation": [
            "Labour Dispute No. 2023/LD/232 — Unpaid salary arrears",
            "Tax Dispute No. 2023/TD/101 — GST demand of ₹2.3 Cr (contested)",
        ],
        "directors": [
            {
                "din": "DIN33333333",
                "name": "Santosh Nair",
                "companies": ["LitigationLtd", "NullAccounts Inc"],
            },
        ],
    },
}

_DEFAULT_LEGAL = {
    "section_138_cases": [],
    "director_disqualified": False,
    "litigation": [],
    "directors": [],
}


def run_sleuth(state: CreditCaseState) -> CreditCaseState:
    """
    LangGraph node: Sleuth Agent.
    Queries legal database and promoter contagion graph for the company.
    """
    state.setdefault("audit_trail", [])
    state.setdefault("legal_flags", [])
    state.setdefault("forensic_report", [])

    company = state.get("company_name", "CleanCorp")
    state["audit_trail"].append("Sleuth: Querying legal intelligence database...")

    legal = LEGAL_DATABASE.get(company, _DEFAULT_LEGAL)

    # ── Section 138 Cases ──
    if legal["section_138_cases"]:
        for case in legal["section_138_cases"]:
            flag = f"Section 138 NI Act: {case}"
            state["legal_flags"].append(flag)
            state["forensic_report"].append(flag)
        state["audit_trail"].append(
            f"Sleuth: ⚠ {len(legal['section_138_cases'])} cheque bounce case(s) under S.138 NI Act."
        )
    else:
        state["audit_trail"].append("Sleuth: No Section 138 cheque bounce cases found.")

    # ── Director Disqualification ──
    if legal["director_disqualified"]:
        flag = "Director Disqualification: One or more directors are disqualified under Section 164(2) Companies Act 2013."
        state["legal_flags"].append(flag)
        state["forensic_report"].append(flag)
        state["audit_trail"].append("Sleuth: ⚠ Director disqualification detected (MCA records).")
    else:
        state["audit_trail"].append("Sleuth: Directors clear — no disqualification on record.")

    # ── General Litigation ──
    for case in legal["litigation"]:
        flag = f"Litigation: {case}"
        state["legal_flags"].append(flag)
        state["forensic_report"].append(flag)
    if legal["litigation"]:
        state["audit_trail"].append(
            f"Sleuth: ⚠ {len(legal['litigation'])} active litigation(s) found."
        )

    # ── Promoter Contagion ──
    state["audit_trail"].append("Sleuth: Analysing promoter-director network...")
    directors = legal.get("directors", [])
    contagion_report = detect_promoter_contagion(directors)

    if contagion_report["contagion_detected"]:
        for cflag in contagion_report["contagion_flags"]:
            state["legal_flags"].append(cflag)
            state["forensic_report"].append(cflag)
        state["audit_trail"].append(
            f"Sleuth: ⚠ Promoter contagion risk — {len(contagion_report['contagion_flags'])} flag(s)."
        )
    else:
        state["audit_trail"].append("Sleuth: No promoter contagion detected.")

    # Store contagion flag for risk engine
    state["promoter_contagion_detected"] = contagion_report["contagion_detected"]

    # ── RAG Legal Document Scan ──
    pdf_paths = state.get("gst_file_paths", []) + state.get("bank_file_paths", [])
    if pdf_paths:
        state["audit_trail"].append("Sleuth: Scanning uploaded documents via RAG for hidden legal risks...")
        try:
            # Query the ephemeral ChromaDB for legal keywords
            context = query_documents("legal dispute litigation Section 138 court case penalty default disqualification", pdf_paths, k=5)
            if context:
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
                sys_prompt = (
                    "Analyze the following document excerpts. If there are any mentions of legal disputes, court cases, "
                    "Section 138 (cheque bounce), labour disputes, or penalties, list them concisely. "
                    "If none are found, output exactly 'None'.\n\n"
                    f"Excerpts:\n{context}"
                )
                response = llm.invoke([
                    SystemMessage(content="You are a strict bank legal analyst."),
                    HumanMessage(content=prompt)
                ])
                ans = response.content.strip()
                if ans and ans.lower() != "none" and "none" not in ans.lower()[:10]:
                    flag = f"RAG Document Discovery: {ans}"
                    state["legal_flags"].append(flag)
                    state["forensic_report"].append(flag)
                    state["audit_trail"].append("Sleuth: ⚠ Discovered legal risks in uploaded documents via RAG!")
                else:
                    state["audit_trail"].append("Sleuth: RAG scan found no explicit legal risks in documents.")
            else:
                state["audit_trail"].append("Sleuth: RAG scan found no relevant legal text in documents.")
        except Exception as e:
            state["audit_trail"].append(f"Sleuth: RAG legal analysis error ({str(e)})")

    state["audit_trail"].append(
        f"Sleuth: Legal scan complete — {len(state['legal_flags'])} flag(s) total."
    )
    return state
