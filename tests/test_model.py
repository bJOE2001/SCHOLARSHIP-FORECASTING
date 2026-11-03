import json
from pathlib import Path
import sys

import numpy as np
import pytest

# Ensure parent directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model import ApplicantRandomForestForecaster
from forecast_service import run_forecast


def test_feature_extraction_insufficient_data():
    forecaster = ApplicantRandomForestForecaster()
    counts = [5, 10, 15]  # Only 3 periods; lag=3 requires at least 4 periods
    month_numbers = [1, 2, 3]

    X, y = forecaster.extract_features_from_history(counts, month_numbers, slots=50)
    assert len(X) == 0
    assert len(y) == 0


def test_feature_extraction_sufficient_data():
    forecaster = ApplicantRandomForestForecaster()
    counts = [10, 15, 20, 25, 30]
    month_numbers = [1, 2, 3, 4, 5]

    X, y = forecaster.extract_features_from_history(counts, month_numbers, slots=100)
    # We should have 5 - 3 = 2 training samples
    assert len(X) == 2
    assert len(y) == 2

    # Sample 0: target = counts[3] = 25
    assert y[0] == 25.0
    # Features: lag_1=20, lag_2=15, lag_3=10, rolling_mean=15, rolling_max=20, month=4, is_peak=0, trend_slope=5, slots=100
    np.testing.assert_array_equal(X[0][:3], [20.0, 15.0, 10.0])
    assert X[0][3] == 15.0  # rolling_mean
    assert X[0][4] == 20.0  # rolling_max
    assert X[0][5] == 4.0   # month 4
    assert X[0][6] == 0.0   # not peak
    assert X[0][7] == 5.0   # trend_slope (20 - 15)
    assert X[0][8] == 100.0 # slots


def test_forecast_scope_empty_history():
    forecaster = ApplicantRandomForestForecaster()
    result = forecaster.forecast_scope([])
    assert result["currentMonthApplicants"] == 0
    assert result["predictedApplicantsThisMonth"] == 0
    assert result["confidence"] == "Low"


def test_forecast_scope_with_synthetic_trajectory():
    forecaster = ApplicantRandomForestForecaster(n_estimators=50, random_state=42)
    history = [
        {"month": "Jan 2026", "monthKey": "2026-01", "applicants": 20},
        {"month": "Feb 2026", "monthKey": "2026-02", "applicants": 25},
        {"month": "Mar 2026", "monthKey": "2026-03", "applicants": 30},
        {"month": "Apr 2026", "monthKey": "2026-04", "applicants": 35},
        {"month": "May 2026", "monthKey": "2026-05", "applicants": 40},
        {"month": "Jun 2026", "monthKey": "2026-06", "applicants": 18},  # In progress
    ]

    result = forecaster.forecast_scope(
        history_items=history,
        slots=100,
        current_day=15,
        days_in_month=30,
    )

    assert result["currentMonthApplicants"] == 18
    assert result["predictedApplicantsThisMonth"] >= 18
    assert result["predictedApplicantsNextMonth"] > 0
    assert result["confidence"] in ["High", "Medium"]
    assert "featureImportances" in result


def test_run_forecast_end_to_end():
    payload = {
        "lookbackMonths": 6,
        "currentDay": 12,
        "daysInMonth": 31,
        "summary": {
            "programName": "All Programs",
            "slots": 145,
            "history": [
                {"month": "Feb 2026", "monthKey": "2026-02", "applicants": 10},
                {"month": "Mar 2026", "monthKey": "2026-03", "applicants": 15},
                {"month": "Apr 2026", "monthKey": "2026-04", "applicants": 20},
                {"month": "May 2026", "monthKey": "2026-05", "applicants": 8},
            ],
        },
        "programs": [
            {
                "programId": 1,
                "programName": "Tulong Dunong Program",
                "slots": 100,
                "history": [
                    {"month": "Feb 2026", "monthKey": "2026-02", "applicants": 6},
                    {"month": "Mar 2026", "monthKey": "2026-03", "applicants": 10},
                    {"month": "Apr 2026", "monthKey": "2026-04", "applicants": 12},
                    {"month": "May 2026", "monthKey": "2026-05", "applicants": 5},
                ],
            }
        ],
    }

    response = run_forecast(payload)
    assert response["status"] == "success"
    assert "Random Forest" in response["method"]
    assert response["summary"]["currentMonthApplicants"] == 8
    assert len(response["programs"]) == 1
    assert response["programs"][0]["programName"] == "Tulong Dunong Program"
