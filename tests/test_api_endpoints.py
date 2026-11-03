from pathlib import Path
import sys
import pytest
from starlette.testclient import TestClient

# Ensure parent directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_forecast_api_endpoint():
    payload = {
        "lookbackMonths": 6,
        "currentDay": 15,
        "daysInMonth": 30,
        "summary": {
            "programName": "All Programs",
            "slots": 100,
            "history": [
                {"month": "Jan 2026", "monthKey": "2026-01", "applicants": 12},
                {"month": "Feb 2026", "monthKey": "2026-02", "applicants": 18},
                {"month": "Mar 2026", "monthKey": "2026-03", "applicants": 25},
                {"month": "Apr 2026", "monthKey": "2026-04", "applicants": 10},
            ],
        },
        "programs": [],
    }

    response = client.post("/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Random Forest" in data["method"]
    assert data["summary"]["currentMonthApplicants"] == 10
    assert data["summary"]["predictedApplicantsThisMonth"] > 0
    assert data["summary"]["predictedApplicantsNextMonth"] > 0


def test_risk_detection_api_endpoint():
    payload = {
        "scholars": [
            {
                "id": 1,
                "scholarId": "SCH-001",
                "name": "Alex Student",
                "gpa": 71.5,
                "maintainingGrade": 85.0,
                "complianceRate": 30,
                "complianceStatus": "Non-Compliant",
            },
            {
                "id": 2,
                "scholarId": "SCH-002",
                "name": "Maria Honors",
                "gpa": 95.0,
                "maintainingGrade": 85.0,
                "complianceRate": 100,
                "complianceStatus": "Compliant",
            },
        ]
    }

    response = client.post("/risk-detection/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Decision Tree" in data["method"]
    assert len(data["results"]) == 2

    r1, r2 = data["results"]
    assert r1["id"] == 1
    assert r1["riskLabel"] == "At Risk"
    assert r1["gradeMargin"] == -13.5
    assert "IF grade_margin" in r1["decisionRule"]

    assert r2["id"] == 2
    assert r2["riskLabel"] == "Stable"


def test_ranking_api_endpoint():
    payload = {
        "applicants": [
            {
                "id": 101,
                "gpa": 92.5,
                "maintainingGrade": 85.0,
                "income": 120000.0,
                "missingRequirements": [],
                "isPriorityCourse": True,
            }
        ]
    }

    response = client.post("/ranking/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == 101
    assert data["results"][0]["compositeScore"] >= 88.0
    assert data["results"][0]["priorityCategory"] == "High Priority"
