"""
CLI Entry Point for Random Forest Forecasting Service.
Can be invoked by Laravel via Process execution (CLI / Stdin) or run directly.
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

from typing import Any, Dict

from model import ApplicantRandomForestForecaster


def run_forecast(payload: Dict[str, Any]) -> Dict[str, Any]:
    current_day = payload.get("currentDay")
    days_in_month = payload.get("daysInMonth")
    lookback_months = payload.get("lookbackMonths", 6)

    # 1. Scope: Summary (All Programs)
    summary_input = payload.get("summary", {})
    summary_history = summary_input.get("history", [])
    summary_slots = summary_input.get("slots", 100)

    summary_forecaster = ApplicantRandomForestForecaster(n_estimators=100, random_state=42)
    summary_forecast = summary_forecaster.forecast_scope(
        history_items=summary_history,
        slots=summary_slots,
        current_day=current_day,
        days_in_month=days_in_month,
    )
    summary_forecast["programId"] = None
    summary_forecast["programName"] = summary_input.get("programName", "All Programs")
    summary_forecast["history"] = summary_history

    # 2. Scope: Individual Programs
    programs_input = payload.get("programs", [])
    programs_forecasts = []

    for prog in programs_input:
        prog_history = prog.get("history", [])
        prog_slots = prog.get("slots", 50)
        prog_id = prog.get("programId")
        prog_name = prog.get("programName", "Unknown Program")

        prog_forecaster = ApplicantRandomForestForecaster(n_estimators=100, random_state=42)
        prog_res = prog_forecaster.forecast_scope(
            history_items=prog_history,
            slots=prog_slots,
            current_day=current_day,
            days_in_month=days_in_month,
        )
        prog_res["programId"] = prog_id
        prog_res["programName"] = prog_name
        prog_res["history"] = prog_history
        programs_forecasts.append(prog_res)

    return {
        "status": "success",
        "method": "Random Forest Regressor (lag & pace ensemble)",
        "lookbackMonths": lookback_months,
        "summary": summary_forecast,
        "programs": programs_forecasts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scholarship Applicant Random Forest Forecaster")
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
        # Read from stdin
        payload_text = sys.stdin.read()

    if not payload_text.strip():
        print(json.dumps({"status": "error", "message": "No input payload provided."}))
        sys.exit(1)

    try:
        payload = json.loads(payload_text)
        result = run_forecast(payload)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        error_res = {
            "status": "error",
            "message": str(e),
        }
        print(json.dumps(error_res))
        sys.exit(1)


if __name__ == "__main__":
    main()
