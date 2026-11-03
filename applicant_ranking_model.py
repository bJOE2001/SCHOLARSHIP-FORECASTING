"""
Composite Ranking Model for Scholarship Applicants.
Calculates multi-factor composite priority scores balancing:
- Academic Merit (40%)
- Socioeconomic Need (35%)
- Documentary Completeness (15%)
- Program Field Alignment (10%)
"""

from __future__ import annotations

from typing import Any, Dict, List


class ApplicantRankingModel:
    """
    Computes explainable composite priority ranking for scholarship applicants.
    """

    @staticmethod
    def calculate_merit_score(gpa: float, maintaining_grade: float = 85.0) -> float:
        """
        Merit score normalized from 0 to 100.
        """
        if gpa <= 0:
            return 50.0
        # If GPA is already in percentage (e.g. 75 - 100)
        if gpa > 10.0:
            return max(0.0, min(100.0, float(gpa)))
        # If GPA is on a 4.0 or 5.0 scale (e.g. 1.0 to 4.0)
        # Assuming 1.0 is highest (Philippine system) or 4.0 is highest (US system)
        return 85.0

    @staticmethod
    def calculate_need_score(income: float) -> float:
        """
        Socioeconomic need score: lower household income yields higher priority.
        Brackets based on Philippine standard poverty thresholds / low income brackets:
        - <= 150,000 PHP: 100 pts
        - <= 250,000 PHP: 85 pts
        - <= 400,000 PHP: 70 pts
        - <= 600,000 PHP: 50 pts
        - > 600,000 PHP: 30 pts
        """
        if income <= 0:
            return 80.0  # Default assumption for public assistance applicants
        if income <= 150000:
            return 100.0
        if income <= 250000:
            return 85.0
        if income <= 400000:
            return 70.0
        if income <= 600000:
            return 50.0
        return 30.0

    @staticmethod
    def calculate_completeness_score(missing_requirements: List[str]) -> float:
        missing_count = len(missing_requirements)
        return max(0.0, 100.0 - (missing_count * 20.0))

    def evaluate_applicant(
        self,
        gpa: float,
        maintaining_grade: float = 85.0,
        income: float = 0.0,
        missing_requirements: Optional[List[str]] = None,
        is_priority_course: bool = False,
    ) -> Dict[str, Any]:
        missing = missing_requirements or []
        merit = self.calculate_merit_score(gpa, maintaining_grade)
        need = self.calculate_need_score(income)
        completeness = self.calculate_completeness_score(missing)
        priority = 95.0 if is_priority_course else 75.0

        composite = (0.40 * merit) + (0.35 * need) + (0.15 * completeness) + (0.10 * priority)
        composite = round(composite, 1)

        if composite >= 88.0 and completeness >= 80.0:
            category = "High Priority"
            recommendation = "Recommended for Immediate Approval"
        elif composite >= 75.0:
            category = "Standard Priority"
            recommendation = "Eligible for Regular Allocation"
        else:
            category = "Needs Review"
            recommendation = "Pending Verification / Incomplete Documents"

        return {
            "compositeScore": composite,
            "meritScore": round(merit, 1),
            "needScore": round(need, 1),
            "completenessScore": round(completeness, 1),
            "priorityScore": round(priority, 1),
            "priorityCategory": category,
            "recommendation": recommendation,
        }
