from pathlib import Path
import sys
import pytest

# Ensure parent directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from applicant_ranking_model import ApplicantRankingModel


def test_ranking_high_merit_high_need():
    model = ApplicantRankingModel()
    res = model.evaluate_applicant(
        gpa=94.5,
        maintaining_grade=85.0,
        income=120000.0,
        missing_requirements=[],
        is_priority_course=True,
    )
    assert res["compositeScore"] >= 90.0
    assert res["priorityCategory"] == "High Priority"
    assert res["meritScore"] == 94.5
    assert res["needScore"] == 100.0
    assert res["completenessScore"] == 100.0


def test_ranking_missing_documents_low_need():
    model = ApplicantRankingModel()
    res = model.evaluate_applicant(
        gpa=80.0,
        maintaining_grade=85.0,
        income=750000.0,
        missing_requirements=["Certificate of Indigency", "Form 137"],
        is_priority_course=False,
    )
    assert res["compositeScore"] < 75.0
    assert res["priorityCategory"] == "Needs Review"
    assert res["completenessScore"] == 60.0
