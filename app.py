"""
FastAPI Microservice for Random Forest Forecasting.
Runs on http://127.0.0.1:8000 (or custom port).
"""

from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from forecast_service import run_forecast
from risk_service import evaluate_scholars_batch
from applicant_ranking_model import ApplicantRankingModel

app = FastAPI(
    title="ScholarSync ML Forecasting & Risk Service",
    description="Machine Learning REST API: Random Forest forecasting, Decision Tree risk classification, and Composite applicant ranking",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ForecastRequest(BaseModel):
    lookbackMonths: int = 6
    currentDay: int = 15
    daysInMonth: int = 30
    summary: Dict[str, Any]
    programs: list[Dict[str, Any]] = []


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "scholarship-forecasting"}


@app.post("/forecast")
def forecast(request: ForecastRequest) -> Dict[str, Any]:
    try:
        return run_forecast(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RiskEvaluationRequest(BaseModel):
    scholars: list[Dict[str, Any]]


@app.post("/risk-detection/evaluate")
def evaluate_risk(request: RiskEvaluationRequest) -> Dict[str, Any]:
    try:
        return evaluate_scholars_batch(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RankingBatchRequest(BaseModel):
    applicants: list[Dict[str, Any]]


@app.post("/ranking/evaluate")
def evaluate_ranking(request: RankingBatchRequest) -> Dict[str, Any]:
    try:
        model = ApplicantRankingModel()
        results = []
        for a in request.applicants:
            app_id = a.get("id")
            gpa = float(a.get("gpa") or 0.0)
            maintaining_grade = float(a.get("maintainingGrade") or 85.0)
            income = float(a.get("income") or a.get("annualIncome") or 0.0)
            missing = a.get("missingRequirements", [])
            is_priority = bool(a.get("isPriorityCourse", False))

            eval_res = model.evaluate_applicant(
                gpa=gpa,
                maintaining_grade=maintaining_grade,
                income=income,
                missing_requirements=missing,
                is_priority_course=is_priority,
            )
            eval_res["id"] = app_id
            results.append(eval_res)

        return {
            "status": "success",
            "method": "Multi-Factor Composite Ranking Model",
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
