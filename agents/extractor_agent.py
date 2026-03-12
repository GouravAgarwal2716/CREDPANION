"""
agents/extractor_agent.py
Simulates PDF parsing of GST returns and bank statements.
Extracts: gst_sales, bank_credits, and transaction list.
"""
from __future__ import annotations
import os
import random
from functools import lru_cache
from typing import Dict, List
import json
from models.state_schema import CreditCaseState
from tools.document_rag import create_or_get_vectorstore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


# ─────────────────────────────────────────────────────────────────────────────
# Simulated PDF Extraction Profiles (keyed by company type)
# ─────────────────────────────────────────────────────────────────────────────

COMPANY_PROFILES = {
    "CleanCorp": {
        "gst_sales": 48_000_000.0,
        "bank_credits": 46_500_000.0,
        "transactions": [
            {"sender": "CleanCorp", "receiver": "Vendor_A", "amount": 5_000_000},
            {"sender": "CleanCorp", "receiver": "Vendor_B", "amount": 8_000_000},
            {"sender": "Client_X", "receiver": "CleanCorp", "amount": 12_000_000},
            {"sender": "Client_Y", "receiver": "CleanCorp", "amount": 15_000_000},
        ],
    },
    "FraudCo": {
        "gst_sales": 60_000_000.0,
        "bank_credits": 38_000_000.0,   # <85% → inflation
        "transactions": [
            {"sender": "FraudCo", "receiver": "Shell_B", "amount": 9_000_000},
            {"sender": "Shell_B", "receiver": "Shell_C", "amount": 8_500_000},
            {"sender": "Shell_C", "receiver": "Shell_D", "amount": 8_000_000},
            {"sender": "Shell_D", "receiver": "FraudCo", "amount": 7_500_000},   # carousel
            {"sender": "FraudCo", "receiver": "Vendor_Z", "amount": 2_000_000},
        ],
    },
    "LitigationLtd": {
        "gst_sales": 22_000_000.0,
        "bank_credits": 20_000_000.0,
        "transactions": [
            {"sender": "LitigationLtd", "receiver": "Creditor_P", "amount": 3_000_000},
            {"sender": "LitigationLtd", "receiver": "Creditor_Q", "amount": 4_500_000},
            {"sender": "Client_M", "receiver": "LitigationLtd", "amount": 5_000_000},
            {"sender": "Client_N", "receiver": "LitigationLtd", "amount": 6_000_000},
        ],
    },
}


@lru_cache(maxsize=8)
def _parse_pdf_cached(file_path: str) -> Dict:
    """
    Cached PDF parsing simulation.
    In production, replace with pdfplumber / PyMuPDF extraction.
    """
    filename = os.path.basename(file_path).lower()
    # Heuristic: match filename to a known profile
    for profile_name, data in COMPANY_PROFILES.items():
        if profile_name.lower() in filename:
            return data

    # ── REAL AI PDF EXTRACTION ──
    # If the file isn't one of the hardcoded demo profiles, actively extract it using RAG.
    try:
        vs = create_or_get_vectorstore([file_path])
        if not vs: raise ValueError("Empty Vectorstore")
        
        # Get all text chunks
        docs = vs.similarity_search("revenue sales transactions credits bank", k=10)
        content = "\n\n".join(d.page_content for d in docs)
        
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
        sys_prompt = (
            "You are a master financial data extraction bot. Read the provided text from a bank or GST statement. "
            "Extract 'gst_sales' (total revenue if it's a GST file), 'bank_credits' (total inward flow if it's a bank statement), "
            "and a list of 'transactions' (sender, receiver, amount). "
            "If a value is not found, output 0 or an empty list. "
            "Output STRICT VALID JSON ONLY."
            "Example format: {\"gst_sales\": 10000.0, \"bank_credits\": 20000.0, \"transactions\": [{\"sender\":\"A\", \"receiver\":\"B\", \"amount\":500}]}"
        )
        
        response = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=content)])
        
        raw_json = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_json)
        
        return {
            "gst_sales": float(data.get("gst_sales", 0.0)),
            "bank_credits": float(data.get("bank_credits", 0.0)),
            "transactions": data.get("transactions", [])
        }
    except Exception as e:
        print(f"Real Extractor fallback error: {e}")
        return {"gst_sales": 0.0, "bank_credits": 0.0, "transactions": []}
        gst = random.uniform(10_000_000, 80_000_000)
        return {
            "gst_sales": round(gst, 2),
            "bank_credits": round(gst * random.uniform(0.75, 1.05), 2),
            "transactions": [{"sender": "CompanyA", "receiver": "CompanyB", "amount": 1000000}],
        }


def run_extractor(state: CreditCaseState) -> CreditCaseState:
    """
    LangGraph node: Extractor Agent.
    Parses uploaded GST and bank statement PDFs.
    Falls back to synthetic company profiles when file paths not available.
    """
    company = state.get("company_name", "CleanCorp")
    gst_files = state.get("gst_file_paths", [])
    bank_files = state.get("bank_file_paths", [])

    state["audit_trail"] = state.get("audit_trail", [])
    state["audit_trail"].append("Extractor: Initialising document parser...")

    # ── GST Data ──
    if gst_files:
        gst_result = _parse_pdf_cached(gst_files[0])
        gst_sales = gst_result["gst_sales"]
        transactions: List[Dict] = gst_result.get("transactions", [])
        state["audit_trail"].append(f"Extractor: Parsed GSTR tables from {os.path.basename(gst_files[0])}.")
    else:
        profile = COMPANY_PROFILES.get(company, COMPANY_PROFILES["CleanCorp"])
        gst_sales = profile["gst_sales"]
        transactions = profile["transactions"]
        state["audit_trail"].append(f"Extractor: Using synthetic GST profile for '{company}'.")

    # ── Bank Statement Data ──
    if bank_files:
        bank_result = _parse_pdf_cached(bank_files[0])
        bank_credits = bank_result.get("bank_credits", 0.0)
        bank_txns = bank_result.get("transactions", [])
        if bank_txns:
            # If bank yielded transactions, merge or override them
            if not transactions or len(bank_txns) > len(transactions):
                transactions = bank_txns
            else:
                transactions.extend(bank_txns)
        state["audit_trail"].append(f"Extractor: Parsed bank credit ledger from {os.path.basename(bank_files[0])}.")
    else:
        profile = COMPANY_PROFILES.get(company, COMPANY_PROFILES["CleanCorp"])
        bank_credits = profile["bank_credits"]
        state["audit_trail"].append("Extractor: Using synthetic bank statement profile.")

    state["gst_sales"] = gst_sales
    state["bank_credits"] = bank_credits
    state["transactions"] = transactions
    state["reparse_attempts"] = state.get("reparse_attempts", 0) + 1

    state["audit_trail"].append(
        f"Extractor: GST Sales = ₹{gst_sales:,.0f} | Bank Credits = ₹{bank_credits:,.0f} | "
        f"Transactions = {len(transactions)}"
    )
    return state
