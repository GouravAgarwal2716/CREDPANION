"""
Smoke test — runs all 3 demo cases through the full pipeline.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.graph_logic import run_analysis

cases = ["CleanCorp", "FraudCo", "LitigationLtd"]
expected = {
    "CleanCorp":     {"max_score": 40, "decision": "APPROVE"},
    "FraudCo":       {"min_score": 71, "decision": "REJECT"},
    "LitigationLtd": {"decision": "REJECT"},
}

all_pass = True
for company in cases:
    print(f"\n{'='*55}")
    print(f"  Testing: {company}")
    print(f"{'='*55}")
    result = run_analysis({"company_name": company})
    rr = result.get("risk_results", {})
    score    = rr.get("total_score", 0)
    category = rr.get("category", "N/A")
    decision = rr.get("decision", "N/A")
    cam_path = result.get("cam_document_path", "")
    trail_len = len(result.get("audit_trail", []))
    cf_count  = len(result.get("counterfactual_analysis", []))

    print(f"  Score    : {score}/100")
    print(f"  Category : {category}")
    print(f"  Decision : {decision}")
    print(f"  CAM Path : {cam_path}")
    print(f"  Trail    : {trail_len} log entries")
    print(f"  Counterfactuals: {cf_count}")
    print(f"  CAM exists: {os.path.exists(cam_path) if cam_path else False}")

    votes = result.get("committee_votes", [])
    for v in votes:
        print(f"  [{v['agent']:12s}] {v['vote']} (score={v['score']:.2f})")

    # Assertions
    exp = expected.get(company, {})
    if "max_score" in exp and score > exp["max_score"]:
        print(f"  ❌ FAIL: score {score} exceeds expected max {exp['max_score']}")
        all_pass = False
    if "min_score" in exp and score < exp["min_score"]:
        print(f"  ❌ FAIL: score {score} below expected min {exp['min_score']}")
        all_pass = False
    if exp.get("decision") and decision != exp["decision"]:
        print(f"  ❌ FAIL: got {decision}, expected {exp['decision']}")
        all_pass = False
    else:
        print(f"  ✅ PASS")

print(f"\n{'='*55}")
if all_pass:
    print("  ✅ ALL TESTS PASSED")
else:
    print("  ❌ SOME TESTS FAILED")
print(f"{'='*55}\n")
sys.exit(0 if all_pass else 1)
