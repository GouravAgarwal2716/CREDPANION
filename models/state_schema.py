"""
models/state_schema.py
Shared state schema for all Credpanion agents.
"""
from typing import TypedDict, List, Dict, Any, Optional


class CommitteeVote(TypedDict):
    agent: str
    vote: str          # "APPROVE" | "REJECT"
    score: float       # 0.0 – 1.0
    rationale: str


class RiskResult(TypedDict):
    base_score: int
    penalties: Dict[str, int]
    total_score: int
    category: str      # "Low" | "Medium" | "High"
    decision: str      # "APPROVE" | "REJECT"


class CounterfactualScenario(TypedDict):
    scenario: str
    score_if_removed: int
    delta: int


class VisionResult(TypedDict):
    active_assets: int
    idle_assets: int
    reality_score: float
    image_path: str


class Transaction(TypedDict):
    sender: str
    receiver: str
    amount: float


class CreditCaseState(TypedDict):
    # Identification
    company_name: str
    case_id: str

    # Extracted financials
    gst_sales: float
    bank_credits: float
    transactions: List[Transaction]

    # Audit flags
    legal_flags: List[str]
    circular_trading_detected: bool
    revenue_inflation_detected: bool
    bank_mismatch_pct: float
    hard_block: bool

    # Agent outputs
    forensic_report: List[str]
    vision_results: List[VisionResult]
    reality_score: float

    # Committee
    committee_votes: List[CommitteeVote]

    # Risk
    risk_results: Optional[RiskResult]

    # Counterfactuals
    counterfactual_analysis: List[CounterfactualScenario]

    # CAM
    cam_document_path: str

    # Audit trail (live log)
    audit_trail: List[str]

    # Uploaded file paths
    gst_file_paths: List[str]
    bank_file_paths: List[str]
    photo_file_paths: List[str]

    # Re-parse retry counter
    reparse_attempts: int
