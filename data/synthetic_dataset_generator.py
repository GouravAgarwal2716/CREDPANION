"""
data/synthetic_dataset_generator.py
Generates 3 demo credit cases: CleanCorp, FraudCo, LitigationLtd.
Run directly to preview case summaries.
"""
from __future__ import annotations
import sys
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SYNTHETIC_CASES = {
    "CleanCorp": {
        "company_name": "CleanCorp",
        "gst_sales":    48_000_000.0,
        "bank_credits": 46_500_000.0,
        "transactions": [
            {"sender": "CleanCorp",  "receiver": "Vendor_A",  "amount": 5_000_000},
            {"sender": "CleanCorp",  "receiver": "Vendor_B",  "amount": 8_000_000},
            {"sender": "Client_X",   "receiver": "CleanCorp", "amount": 12_000_000},
            {"sender": "Client_Y",   "receiver": "CleanCorp", "amount": 15_000_000},
            {"sender": "Client_Z",   "receiver": "CleanCorp", "amount": 9_000_000},
        ],
        "expected_risk": "Low",
        "expected_decision": "APPROVE",
        "description": "Well-managed manufacturing firm with clean records, no legal disputes, and active plant.",
    },
    "FraudCo": {
        "company_name": "FraudCo",
        "gst_sales":    60_000_000.0,
        "bank_credits": 38_000_000.0,   # below 85% → inflation
        "transactions": [
            {"sender": "FraudCo",  "receiver": "Shell_B",  "amount": 9_000_000},
            {"sender": "Shell_B",  "receiver": "Shell_C",  "amount": 8_500_000},
            {"sender": "Shell_C",  "receiver": "Shell_D",  "amount": 8_000_000},
            {"sender": "Shell_D",  "receiver": "FraudCo",  "amount": 7_500_000},  # carousel
            {"sender": "FraudCo",  "receiver": "Vendor_Z", "amount": 2_000_000},
        ],
        "expected_risk": "High",
        "expected_decision": "REJECT",
        "description": (
            "Shell company engaged in circular carousel trading. "
            "Revenue heavily inflated vs bank credits. "
            "Director disqualified. Factory largely idle."
        ),
    },
    "LitigationLtd": {
        "company_name": "LitigationLtd",
        "gst_sales":    22_000_000.0,
        "bank_credits": 20_000_000.0,
        "transactions": [
            {"sender": "LitigationLtd", "receiver": "Creditor_P", "amount": 3_000_000},
            {"sender": "LitigationLtd", "receiver": "Creditor_Q", "amount": 4_500_000},
            {"sender": "Client_M",      "receiver": "LitigationLtd", "amount": 5_000_000},
            {"sender": "Client_N",      "receiver": "LitigationLtd", "amount": 6_000_000},
        ],
        "expected_risk": "Medium",
        "expected_decision": "REJECT",
        "description": (
            "Mid-size firm under active litigation including two Section 138 cheque bounce cases "
            "and a labour dispute. Revenue is reconciled but legal risk is elevated."
        ),
    },
}


def get_case(company_name: str) -> dict:
    """Return synthetic case data for a given company name."""
    return SYNTHETIC_CASES.get(company_name, SYNTHETIC_CASES["CleanCorp"])


def list_cases() -> list:
    """Return list of available demo case names."""
    return list(SYNTHETIC_CASES.keys())


def get_all_cases() -> dict:
    """Return all synthetic cases."""
    return SYNTHETIC_CASES


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CREDPANION — Synthetic Dataset Generator")
    print("=" * 60)
    for name, case in SYNTHETIC_CASES.items():
        print(f"\n{'─'*50}")
        print(f"  Company  : {case['company_name']}")
        print(f"  GST Sales: ₹{case['gst_sales']:>15,.0f}")
        print(f"  Bank Cred: ₹{case['bank_credits']:>15,.0f}")
        ratio = case['bank_credits'] / case['gst_sales']
        print(f"  Ratio    : {ratio:.2%}")
        print(f"  Txns     : {len(case['transactions'])}")
        print(f"  Expected : {case['expected_risk']} Risk → {case['expected_decision']}")
        print(f"  Summary  : {case['description']}")
    print("\n" + "=" * 60)
    print("  Run: python data/synthetic_dataset_generator.py")
    print("=" * 60 + "\n")
