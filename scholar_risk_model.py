"""
Decision Tree Classifier for Scholar Academic At-Risk Assessment.
Implements an interpretable decision tree that evaluates academic standing,
grade margins, and documentary compliance to detect retention risks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.tree import DecisionTreeClassifier

try:
    import joblib
except ImportError:
    joblib = None

MODEL_DIR = Path(__file__).resolve().parent / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "scholar_risk_tree.joblib"


class ScholarRiskDecisionTree:
    """
    Interpretable Decision Tree for classifying scholars into:
    - Stable (0)
    - Borderline (1)
    - At Risk (2)
    """

    FEATURE_NAMES = [
        "grade_margin",          # gpa - maintaining_grade
        "compliance_rate",       # 0 - 100
        "is_compliant",          # 1 if compliance_status is 'Compliant', else 0
        "is_currently_enrolled", # 1 if enrolled, else 0
        "gpa_recorded",          # 0 if gpa is missing or 0, else 1
    ]

    CLASS_NAMES = ["Stable", "Borderline", "At Risk"]

    def __init__(
        self,
        max_depth: int = 4,
        random_state: int = 42,
        model_path: Optional[Path] = None,
    ):
        self.max_depth = max_depth
        self.random_state = random_state
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.model = DecisionTreeClassifier(
            max_depth=self.max_depth,
            criterion="gini",
            random_state=self.random_state,
        )
        self.is_fitted = False

        if joblib is not None and self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                self.is_fitted = True
            except Exception:
                self._bootstrap_reference_tree()
                self.save()
        else:
            self._bootstrap_reference_tree()
            self.save()

    def save(self, path: Optional[Path] = None) -> None:
        if joblib is None:
            return
        target = path or self.model_path
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, target)

    def _bootstrap_reference_tree(self) -> None:
        """
        Train the tree on verified institutional scholarship policy heuristics:
        1. GPA below maintaining grade (margin < 0) -> At Risk
        2. Missing GPA (gpa_recorded == 0) -> At Risk
        3. Razor-thin margin (0 <= margin < 3) and low compliance (< 75%) -> At Risk
        4. Razor-thin margin (0 <= margin < 5) and moderate compliance (>= 75%) -> Borderline
        5. Solid margin (margin >= 5) but non-compliant (< 50%) -> Borderline
        6. Solid margin (margin >= 5) and compliant (>= 75%) -> Stable
        7. Strong margin (margin >= 8) -> Stable
        """
        synthetic_samples: List[List[float]] = []
        synthetic_labels: List[int] = []

        # At Risk examples (Label 2)
        # Missing GPA
        synthetic_samples.append([0.0, 80.0, 1.0, 1.0, 0.0])
        synthetic_labels.append(2)
        # Margin < 0 (failed maintaining grade)
        for margin in [-15.0, -10.0, -5.0, -2.0, -0.5]:
            for comp in [20.0, 50.0, 80.0, 100.0]:
                synthetic_samples.append([margin, comp, 1.0 if comp >= 80 else 0.0, 1.0, 1.0])
                synthetic_labels.append(2)
        # Razor thin margin with poor compliance
        synthetic_samples.append([1.0, 40.0, 0.0, 1.0, 1.0])
        synthetic_labels.append(2)
        synthetic_samples.append([2.0, 50.0, 0.0, 1.0, 1.0])
        synthetic_labels.append(2)
        synthetic_samples.append([1.5, 60.0, 0.0, 1.0, 1.0])
        synthetic_labels.append(2)

        # Borderline examples (Label 1)
        # Margin close to threshold (0 to 4.9) with acceptable compliance
        for margin in [0.5, 1.5, 2.5, 3.5, 4.5]:
            synthetic_samples.append([margin, 80.0, 1.0, 1.0, 1.0])
            synthetic_labels.append(1)
            synthetic_samples.append([margin, 95.0, 1.0, 1.0, 1.0])
            synthetic_labels.append(1)
        # Good margin but neglected compliance
        synthetic_samples.append([6.0, 40.0, 0.0, 1.0, 1.0])
        synthetic_labels.append(1)
        synthetic_samples.append([7.0, 45.0, 0.0, 1.0, 1.0])
        synthetic_labels.append(1)

        # Stable examples (Label 0)
        # Margin >= 5 with good compliance
        for margin in [5.0, 6.5, 8.0, 10.0, 12.0, 15.0]:
            for comp in [75.0, 85.0, 95.0, 100.0]:
                synthetic_samples.append([margin, comp, 1.0, 1.0, 1.0])
                synthetic_labels.append(0)

        X = np.array(synthetic_samples, dtype=np.float64)
        y = np.array(synthetic_labels, dtype=np.int64)

        self.fit(X, y)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ScholarRiskDecisionTree":
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def extract_features(
        self,
        gpa: float,
        maintaining_grade: float,
        compliance_rate: int = 100,
        compliance_status: str = "Compliant",
        enrollment_status: str = "Enrolled",
    ) -> np.ndarray:
        has_gpa = 1.0 if gpa > 0 else 0.0
        grade_margin = (float(gpa) - float(maintaining_grade)) if has_gpa else 0.0
        is_comp = 1.0 if str(compliance_status).strip().lower() == "compliant" else 0.0
        is_enrolled = 1.0 if str(enrollment_status).strip().lower() in {"enrolled", "active"} else 0.0
        comp_rate = max(0.0, min(100.0, float(compliance_rate)))

        features = [
            grade_margin,
            comp_rate,
            is_comp,
            is_enrolled,
            has_gpa,
        ]
        return np.array([features], dtype=np.float64)

    def evaluate_scholar(
        self,
        gpa: float,
        maintaining_grade: float,
        compliance_rate: int = 100,
        compliance_status: str = "Compliant",
        enrollment_status: str = "Enrolled",
    ) -> Dict[str, Any]:
        """
        Evaluate a single scholar and return the decision tree classification,
        class probabilities, and readable decision rationale.
        """
        has_gpa = gpa > 0
        grade_margin = round(gpa - maintaining_grade, 2) if has_gpa else 0.0

        feat = self.extract_features(
            gpa=gpa,
            maintaining_grade=maintaining_grade,
            compliance_rate=compliance_rate,
            compliance_status=compliance_status,
            enrollment_status=enrollment_status,
        )

        class_idx = int(self.model.predict(feat)[0])
        probabilities = self.model.predict_proba(feat)[0]

        # Extract prob distribution mapped to class names
        prob_dict = {
            "stable": round(float(probabilities[0]), 3) if len(probabilities) > 0 else 0.0,
            "borderline": round(float(probabilities[1]), 3) if len(probabilities) > 1 else 0.0,
            "atRisk": round(float(probabilities[2]), 3) if len(probabilities) > 2 else 0.0,
        }

        risk_label = self.CLASS_NAMES[class_idx]

        # Construct rule explanation and recommended action
        rule_desc, reason_desc, action_desc = self._explain_decision(
            has_gpa=has_gpa,
            grade_margin=grade_margin,
            maintaining_grade=maintaining_grade,
            compliance_rate=compliance_rate,
            risk_label=risk_label,
        )

        return {
            "riskLabel": risk_label,
            "probabilities": prob_dict,
            "gradeMargin": grade_margin,
            "decisionRule": rule_desc,
            "riskReason": reason_desc,
            "recommendedAction": action_desc,
            "featureImportances": {
                name: round(float(imp), 4)
                for name, imp in zip(self.FEATURE_NAMES, self.model.feature_importances_)
            },
        }

    def _explain_decision(
        self,
        has_gpa: bool,
        grade_margin: float,
        maintaining_grade: float,
        compliance_rate: int,
        risk_label: str,
    ) -> Tuple[str, str, str]:
        if not has_gpa:
            rule = "IF gpa_recorded == 0 THEN At Risk"
            reason = f"No GPA recorded for academic evaluation. Required maintaining grade is {maintaining_grade}."
            action = "Request immediate transcript of grades submission and hold grant distribution."
            return rule, reason, action

        if risk_label == "At Risk":
            if grade_margin < 0:
                rule = f"IF grade_margin ({grade_margin:+.2f}) < 0.0 THEN At Risk"
                reason = f"GPA is below the maintaining grade of {maintaining_grade} by {abs(grade_margin):.2f} pts."
                action = "Schedule academic advising and establish a grade recovery improvement contract."
            else:
                rule = f"IF grade_margin ({grade_margin:+.2f}) < 3.0 AND compliance_rate ({compliance_rate}%) < 75% THEN At Risk"
                reason = f"GPA is near threshold ({grade_margin:+.2f}) with insufficient compliance rate ({compliance_rate}%)."
                action = "Issue formal notice of deficiency and require urgent completion of outstanding requirements."
            return rule, reason, action

        if risk_label == "Borderline":
            if compliance_rate < 50:
                rule = f"IF grade_margin ({grade_margin:+.2f}) >= 5.0 AND compliance_rate ({compliance_rate}%) < 50% THEN Borderline"
                reason = f"Passing GPA but severe compliance delinquency ({compliance_rate}% compliance)."
                action = "Send compliance reminder notice and monitor submission deadline."
            else:
                rule = f"IF 0.0 <= grade_margin ({grade_margin:+.2f}) < 5.0 THEN Borderline"
                reason = f"GPA is close to maintaining grade threshold ({grade_margin:+.2f} pts buffer)."
                action = "Send reminder and closely monitor midterm evaluation and requirement submissions."
            return rule, reason, action

        # Stable
        rule = f"IF grade_margin ({grade_margin:+.2f}) >= 5.0 AND compliance_rate ({compliance_rate}%) >= 75% THEN Stable"
        reason = f"GPA meets maintaining grade of {maintaining_grade} with healthy academic buffer (+{grade_margin:.2f} pts)."
        action = "Continue standard semester monitoring."
        return rule, reason, action
