from pathlib import Path
import sys
import pytest

# Ensure parent directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scholar_risk_model import ScholarRiskDecisionTree
from risk_service import evaluate_scholars_batch


def test_missing_gpa_at_risk():
    tree = ScholarRiskDecisionTree()
    res = tree.evaluate_scholar(
        gpa=0.0,
        maintaining_grade=85.0,
        compliance_rate=100,
        compliance_status="Compliant",
    )
    assert res["riskLabel"] == "At Risk"
    assert "No GPA recorded" in res["riskReason"]
    assert "gpa_recorded == 0" in res["decisionRule"]


def test_failing_gpa_margin_at_risk():
    tree = ScholarRiskDecisionTree()
    res = tree.evaluate_scholar(
        gpa=74.5,
        maintaining_grade=85.0,
        compliance_rate=90,
        compliance_status="Compliant",
    )
    assert res["riskLabel"] == "At Risk"
    assert res["gradeMargin"] == -10.5
    assert "grade_margin" in res["decisionRule"]
    assert res["probabilities"]["atRisk"] > 0.8


def test_borderline_buffer():
    tree = ScholarRiskDecisionTree()
    res = tree.evaluate_scholar(
        gpa=86.5,
        maintaining_grade=85.0,
        compliance_rate=85,
        compliance_status="Compliant",
    )
    assert res["riskLabel"] == "Borderline"
    assert res["gradeMargin"] == 1.5
    assert "Borderline" in res["decisionRule"]


def test_stable_buffer_and_compliance():
    tree = ScholarRiskDecisionTree()
    res = tree.evaluate_scholar(
        gpa=93.0,
        maintaining_grade=85.0,
        compliance_rate=95,
        compliance_status="Compliant",
    )
    assert res["riskLabel"] == "Stable"
    assert res["gradeMargin"] == 8.0
    assert res["probabilities"]["stable"] > 0.8


def test_evaluate_scholars_batch_end_to_end():
    payload = {
        "scholars": [
            {
                "id": 101,
                "scholarId": "SCH-001",
                "name": "Failing Student",
                "gpa": 72.0,
                "maintainingGrade": 85.0,
                "complianceRate": 30,
                "complianceStatus": "Non-Compliant",
            },
            {
                "id": 102,
                "scholarId": "SCH-002",
                "name": "Borderline Student",
                "gpa": 86.0,
                "maintainingGrade": 85.0,
                "complianceRate": 85,
                "complianceStatus": "Compliant",
            },
            {
                "id": 103,
                "scholarId": "SCH-003",
                "name": "Honors Student",
                "gpa": 94.0,
                "maintainingGrade": 85.0,
                "complianceRate": 100,
                "complianceStatus": "Compliant",
            },
        ]
    }

    res = evaluate_scholars_batch(payload)
    assert res["status"] == "success"
    assert "Decision Tree" in res["method"]
    assert len(res["results"]) == 3

    r1, r2, r3 = res["results"]
    assert r1["id"] == 101
    assert r1["riskLabel"] == "At Risk"

    assert r2["id"] == 102
    assert r2["riskLabel"] == "Borderline"

    assert r3["id"] == 103
    assert r3["riskLabel"] == "Stable"
