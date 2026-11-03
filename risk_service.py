"""
CLI Entry Point for Decision Tree Scholar Risk Service.
Evaluates single scholars or batches of scholars from JSON via standard input or CLI arguments.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import site
import sys

# Ensure user site packages are accessible across web server sessions
for p in [site.getusersitepackages(), r"C:\Users\BOSSJ\AppData\Roaming\Python\Python313\site-packages"]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

from typing import Any, Dict, List

from scholar_risk_model import ScholarRiskDecisionTree


def evaluate_scholars_batch(payload: Dict[str, Any]) -> Dict[str, Any]:
    tree = ScholarRiskDecisionTree()
    scholars: List[Dict[str, Any]] = payload.get("scholars", [])

    results = []
    for s in scholars:
        scholar_id = s.get("id")
        gpa = float(s.get("gpa") or 0.0)
        maintaining_grade = float(s.get("maintainingGrade") or 85.0)
        compliance_rate = int(s.get("complianceRate") or 100)
        compliance_status = str(s.get("complianceStatus") or "Compliant")
        enrollment_status = str(s.get("enrollmentStatus") or "Enrolled")

        eval_res = tree.evaluate_scholar(
            gpa=gpa,
            maintaining_grade=maintaining_grade,
            compliance_rate=compliance_rate,
            compliance_status=compliance_status,
            enrollment_status=enrollment_status,
        )
        eval_res["id"] = scholar_id
        results.append(eval_res)

    return {
        "status": "success",
        "method": "Decision Tree Classifier (depth=4)",
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scholar Academic At-Risk Decision Tree Classifier")
    parser.add_argument("--json", type=str, help="JSON input string")
    parser.add_argument("--input", type=str, help="Path to input JSON file")

    args = parser.parse_args()

    payload_text = ""
    if args.json:
        payload_text = args.json
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            payload_text = f.read()
    else:
        payload_text = sys.stdin.read()

    if not payload_text.strip():
        print(json.dumps({"status": "error", "message": "No input payload provided."}))
        sys.exit(1)

    try:
        payload = json.loads(payload_text)
        result = evaluate_scholars_batch(payload)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
