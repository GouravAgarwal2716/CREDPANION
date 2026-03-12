"""
backend/api_routes.py
All REST API endpoints for Credpanion.
"""
from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv()
import sys
import uuid
import json
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from agents.graph_logic import run_analysis
from tools.transaction_graph import build_graph_data
from data.synthetic_dataset_generator import get_case

router = APIRouter()

# Module-level state store  (single-session; use Redis/DB for production)
_current_state: dict = {}
_upload_store: dict  = {"gst": [], "bank": [], "photos": []}

UPLOAD_DIR = "uploads"


# ─────────────────────────────────────────────────────────────────────────────
# POST /upload
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/upload", summary="Upload financial documents and factory photos")
async def upload_files(
    gst_files:    list[UploadFile] = File(default=[]),
    bank_files:   list[UploadFile] = File(default=[]),
    photo_files:  list[UploadFile] = File(default=[]),
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved = {"gst": [], "bank": [], "photos": []}

    async def _save(files: list[UploadFile], category: str) -> list[str]:
        paths = []
        for f in files:
            if not f.filename:
                continue
            dest = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{f.filename}")
            content = await f.read()
            with open(dest, "wb") as out:
                out.write(content)
            paths.append(dest)
        return paths

    saved["gst"]    = await _save(gst_files,   "gst")
    saved["bank"]   = await _save(bank_files,  "bank")
    saved["photos"] = await _save(photo_files, "photos")

    _upload_store.update(saved)
    return {
        "message": "Files uploaded successfully",
        "counts":  {k: len(v) for k, v in saved.items()},
        "paths":   saved,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze", summary="Trigger the multi-agent credit analysis pipeline")
async def analyze(
    company: str = Form(default="CleanCorp"),
    case_id: Optional[str] = Form(default=None),
):
    """
    Runs the LangGraph multi-agent workflow.
    Uses uploaded files if present; falls back to synthetic demo data.
    """
    global _current_state

    init_state = {
        "company_name":     company,
        "case_id":          case_id or f"CRED-{uuid.uuid4().hex[:8].upper()}",
        "gst_file_paths":   _upload_store.get("gst",    []),
        "bank_file_paths":  _upload_store.get("bank",   []),
        "photo_file_paths": _upload_store.get("photos", []),
    }

    try:
        result = run_analysis(init_state)
        _current_state = result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(exc)}")

    # Serialize the result (strip non-JSON-serializable keys)
    return JSONResponse(content={
        "company_name":               result.get("company_name"),
        "case_id":                    result.get("case_id"),
        "gst_sales":                  result.get("gst_sales"),
        "bank_credits":               result.get("bank_credits"),
        "transactions":               result.get("transactions", []),
        "circular_trading_detected":  result.get("circular_trading_detected"),
        "revenue_inflation_detected": result.get("revenue_inflation_detected"),
        "hard_block":                 result.get("hard_block"),
        "forensic_report":            result.get("forensic_report"),
        "legal_flags":                result.get("legal_flags"),
        "reality_score":              result.get("reality_score"),
        "committee_votes":            result.get("committee_votes"),
        "risk_results":               result.get("risk_results"),
        "counterfactual_analysis":    result.get("counterfactual_analysis"),
        "cam_document_path":          result.get("cam_document_path"),
        "audit_trail":                result.get("audit_trail"),
        "committee_weighted_score":   result.get("committee_weighted_score"),
        "status":                     "completed",
    })


# ─────────────────────────────────────────────────────────────────────────────
# GET /graph
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/graph", summary="Get transaction network graph data")
def get_graph():
    """Returns node/edge data for the PyVis transaction network."""
    if not _current_state:
        raise HTTPException(status_code=404, detail="No analysis has been run yet.")
    transactions = _current_state.get("transactions", [])
    return build_graph_data(transactions)


# ─────────────────────────────────────────────────────────────────────────────
# GET /risk
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/risk", summary="Get risk score and committee decision")
def get_risk():
    """Returns deterministic risk score, category, decision, and counterfactuals."""
    if not _current_state:
        raise HTTPException(status_code=404, detail="No analysis has been run yet.")
    return {
        "risk_results":            _current_state.get("risk_results"),
        "committee_votes":         _current_state.get("committee_votes"),
        "committee_weighted_score": _current_state.get("committee_weighted_score"),
        "committee_decision":      _current_state.get("committee_decision"),
        "counterfactual_analysis": _current_state.get("counterfactual_analysis"),
        "hard_block":              _current_state.get("hard_block"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /report
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/report", summary="Download the generated CAM report")
def get_report():
    """Returns the CAM .docx file as a file download."""
    if not _current_state:
        raise HTTPException(status_code=404, detail="No analysis has been run yet.")

    cam_path = _current_state.get("cam_document_path", "")
    if not cam_path or not os.path.exists(cam_path):
        raise HTTPException(status_code=404, detail=f"CAM report file not found at: {cam_path}")

    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if cam_path.endswith(".docx") else "text/plain"
    )
    return FileResponse(
        path=cam_path,
        media_type=media_type,
        filename=os.path.basename(cam_path),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /demo-cases
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/demo-cases", summary="List available demo cases")
def get_demo_cases():
    """Returns the list of synthetic demo companies."""
    from data.synthetic_dataset_generator import list_cases, get_all_cases
    cases = get_all_cases()
    return {
        name: {
            "description":       c["description"],
            "expected_risk":     c["expected_risk"],
            "expected_decision": c["expected_decision"],
        }
        for name, c in cases.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/health", summary="Health check endpoint")
def health_check():
    """Returns the API health status."""
    return {"status": "ok", "message": "Credpanion API is running."}


# ─────────────────────────────────────────────────────────────────────────────
# POST /chat
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str

@router.post("/chat", summary="Real-time AI Co-Pilot Chat")
async def chat_copilot(req: ChatRequest):
    """Answers questions about the currently active case state."""
    if not _current_state:
        raise HTTPException(status_code=400, detail="Run an analysis first before asking questions.")

    # Create a concise summary of the state so we don't blow up the context window
    state_summary = {
        "company": _current_state.get("company_name"),
        "score": _current_state.get("risk_results", {}).get("total_score"),
        "decision": _current_state.get("committee_decision"),
        "legal_flags": _current_state.get("legal_flags"),
        "forensic_report": _current_state.get("forensic_report"),
        "reality_score": _current_state.get("reality_score"),
    }

    prompt = (
        f"You are the Credpanion AI Copilot—a senior credit risk analyst. "
        f"The user is asking a question about the current loan application for {state_summary['company']}.\n"
        f"Here is the context of this case:\n{json.dumps(state_summary, indent=2)}\n\n"
        f"User Query: {req.query}\n"
        f"Answer the query professionally and concisely."
    )

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    async def _stream():
        try:
            async for chunk in llm.astream([
                SystemMessage(content="You are a bank credit co-pilot. Keep answers brief (under 100 words)."),
                HumanMessage(content=prompt)
            ]):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            print(f"Error during streaming: {e}")
            yield f"Error: {str(e)}"

    return StreamingResponse(_stream(), media_type="text/event-stream")

