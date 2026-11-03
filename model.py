"""
Random Forest Applicant Forecasting Model
Implements tabular time-series feature engineering and Random Forest regression
for scholarship applicant demand forecasting.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestRegressor

try:
    import joblib
except ImportError:
    joblib = None


class ApplicantRandomForestForecaster:
    """
    Random Forest ensemble model for forecasting monthly applicant volume
    using lag dynamics, rolling statistics, calendar seasonality, and pace.
    """

    FEATURE_NAMES = [
        "lag_1",
        "lag_2",
        "lag_3",
        "rolling_mean_3",
        "rolling_max_3",
        "month_of_year",
        "is_peak_intake",
        "trend_slope",
        "slots",
    ]

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 5,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=self.random_state,
        )
        self.is_fitted = False

    @staticmethod
    def _is_peak_month(month: int) -> int:
        # Philippine academic intake typically peaks in Jan/Feb (2nd sem) and Aug/Sep (1st sem)
        return 1 if month in {1, 2, 8, 9} else 0

    def extract_features_from_history(
        self,
        counts: List[int],
        month_numbers: List[int],
        slots: int = 100,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert sequential monthly counts into supervised (X, y) tabular samples.
        Requires at least 4 historical periods to create at least 1 sample with lag=3.
        """
        X_rows: List[List[float]] = []
        y_vals: List[float] = []

        n = len(counts)
        if n < 4:
            return np.empty((0, len(self.FEATURE_NAMES))), np.empty((0,))

        for i in range(3, n):
            target = float(counts[i])
            lag_1 = float(counts[i - 1])
            lag_2 = float(counts[i - 2])
            lag_3 = float(counts[i - 3])
            past_3 = [lag_1, lag_2, lag_3]

            rolling_mean_3 = float(np.mean(past_3))
            rolling_max_3 = float(np.max(past_3))
            month_num = int(month_numbers[i]) if i < len(month_numbers) else 1
            is_peak = self._is_peak_month(month_num)
            trend_slope = lag_1 - lag_2

            features = [
                lag_1,
                lag_2,
                lag_3,
                rolling_mean_3,
                rolling_max_3,
                float(month_num),
                float(is_peak),
                float(trend_slope),
                float(slots),
            ]
            X_rows.append(features)
            y_vals.append(target)

        return np.array(X_rows, dtype=np.float64), np.array(y_vals, dtype=np.float64)

    def _build_feature_vector(
        self,
        prior_counts: List[int],
        target_month_num: int,
        slots: int,
    ) -> np.ndarray:
        """
        Build a single feature vector for an upcoming target month.
        """
        if len(prior_counts) >= 3:
            lag_1 = float(prior_counts[-1])
            lag_2 = float(prior_counts[-2])
            lag_3 = float(prior_counts[-3])
        elif len(prior_counts) == 2:
            lag_1 = float(prior_counts[-1])
            lag_2 = float(prior_counts[-2])
            lag_3 = float(prior_counts[-2])
        elif len(prior_counts) == 1:
            lag_1 = float(prior_counts[-1])
            lag_2 = float(prior_counts[-1])
            lag_3 = float(prior_counts[-1])
        else:
            lag_1 = lag_2 = lag_3 = 0.0

        past_3 = [lag_1, lag_2, lag_3]
        rolling_mean_3 = float(np.mean(past_3))
        rolling_max_3 = float(np.max(past_3))
        is_peak = self._is_peak_month(target_month_num)
        trend_slope = lag_1 - lag_2

        features = [
            lag_1,
            lag_2,
            lag_3,
            rolling_mean_3,
            rolling_max_3,
            float(target_month_num),
            float(is_peak),
            float(trend_slope),
            float(slots),
        ]
        return np.array([features], dtype=np.float64)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ApplicantRandomForestForecaster":
        """
        Fit the Random Forest Regressor on training pairs.
        """
        if len(X) == 0 or len(y) == 0:
            self.is_fitted = False
            return self

        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_with_uncertainty(self, X: np.ndarray) -> Tuple[float, float]:
        """
        Return point prediction (mean of trees) and standard deviation across ensemble trees.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")

        tree_predictions = np.array([tree.predict(X)[0] for tree in self.model.estimators_])
        mean_pred = float(np.mean(tree_predictions))
        std_pred = float(np.std(tree_predictions))
        return mean_pred, std_pred

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    @classmethod
    def load(cls, path: Path) -> "ApplicantRandomForestForecaster":
        forecaster = cls()
        forecaster.model = joblib.load(path)
        forecaster.is_fitted = True
        return forecaster

    def forecast_scope(
        self,
        history_items: List[Dict[str, Any]],
        slots: int = 100,
        current_day: Optional[int] = None,
        days_in_month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete forecast payload for a given scope (program or all-programs).
        """
        if not history_items:
            return {
                "currentMonthApplicants": 0,
                "predictedApplicantsThisMonth": 0,
                "predictedApplicantsNextMonth": 0,
                "averageMonthlyApplicants": 0.0,
                "trendDelta": 0,
                "confidence": "Low",
                "featureImportances": {},
            }

        # Separate complete months from the current in-progress month
        complete_items = history_items[:-1] if len(history_items) > 1 else []
        current_item = history_items[-1] if history_items else {}

        current_month_applicants = int(current_item.get("applicants", 0))
        complete_counts = [int(item.get("applicants", 0)) for item in complete_items]

        # Historical baseline calculations
        hist_avg = float(np.mean(complete_counts)) if complete_counts else 0.0

        # Current pace extrapolation
        pace_val = 0.0
        if current_month_applicants > 0:
            eff_day = max(int(current_day) if current_day else 15, 1)
            eff_dim = int(days_in_month) if days_in_month else 30
            pace_val = (current_month_applicants / eff_day) * eff_dim

        # Parse month numbers from monthKey (YYYY-MM)
        month_numbers: List[int] = []
        for item in history_items:
            key = str(item.get("monthKey", ""))
            try:
                m_num = int(key.split("-")[1])
            except Exception:
                m_num = 1
            month_numbers.append(m_num)

        complete_month_numbers = month_numbers[:-1] if len(month_numbers) > 1 else []
        current_month_num = month_numbers[-1] if month_numbers else 1
        next_month_num = (current_month_num % 12) + 1

        # Supervised tabular dataset from history
        X_train, y_train = self.extract_features_from_history(
            complete_counts,
            complete_month_numbers,
            slots=slots,
        )

        rf_pred_this_month = 0.0
        rf_pred_next_month = 0.0
        uncertainty = 1.0
        feature_importance_dict: Dict[str, float] = {}

        if len(X_train) >= 2:
            try:
                self.fit(X_train, y_train)
                # Feature for current month
                feat_this = self._build_feature_vector(complete_counts, current_month_num, slots)
                rf_pred_this_month, std_this = self.predict_with_uncertainty(feat_this)

                # Feature for next month (projecting lag_1 as predicted this month)
                projected_counts = complete_counts + [int(round(max(current_month_applicants, rf_pred_this_month)))]
                feat_next = self._build_feature_vector(projected_counts, next_month_num, slots)
                rf_pred_next_month, std_next = self.predict_with_uncertainty(feat_next)

                uncertainty = (std_this / max(rf_pred_this_month, 1.0) + std_next / max(rf_pred_next_month, 1.0)) / 2.0

                importances = self.model.feature_importances_
                feature_importance_dict = {
                    name: round(float(imp), 4)
                    for name, imp in zip(self.FEATURE_NAMES, importances)
                }
            except Exception:
                self.is_fitted = False

        # Fallback / heuristic blend
        weighted_avg = self._compute_weighted_average(complete_counts)

        if not self.is_fitted or rf_pred_this_month <= 0:
            rf_pred_this_month = weighted_avg
            rf_pred_next_month = weighted_avg

        # Blend Random Forest prediction with active current-month pace
        if current_month_applicants > 0:
            blended_this = (rf_pred_this_month + pace_val) / 2.0
            predicted_this_month = max(current_month_applicants, int(round(blended_this)))
        else:
            predicted_this_month = max(0, int(round(rf_pred_this_month)))

        predicted_next_month = max(0, int(round(rf_pred_next_month)))
        previous_count = complete_counts[-1] if complete_counts else 0

        # Confidence categorization
        confidence = self._compute_confidence(complete_counts, uncertainty)

        # When tree ensemble cannot be fit due to few periods, provide heuristic baseline weights
        if not feature_importance_dict and complete_counts:
            feature_importance_dict = {
                "lag_1": 0.35,
                "rolling_mean_3": 0.25,
                "trend_slope": 0.20,
                "is_peak_intake": 0.10,
                "slots": 0.10,
            }

        return {
            "currentMonthApplicants": current_month_applicants,
            "predictedApplicantsThisMonth": predicted_this_month,
            "predictedApplicantsNextMonth": predicted_next_month,
            "averageMonthlyApplicants": round(hist_avg, 1),
            "trendDelta": predicted_this_month - previous_count,
            "confidence": confidence,
            "featureImportances": feature_importance_dict,
        }

    @staticmethod
    def _compute_weighted_average(counts: List[int]) -> float:
        if not counts:
            return 0.0
        weighted_sum = sum(count * (idx + 1) for idx, count in enumerate(counts))
        weight_total = sum(idx + 1 for idx in range(len(counts)))
        return weighted_sum / weight_total if weight_total > 0 else 0.0

    def _compute_confidence(self, complete_counts: List[int], uncertainty: float) -> str:
        total_historical = sum(complete_counts)
        active_months = sum(1 for c in complete_counts if c > 0)

        if total_historical >= 12 and active_months >= 3 and (not self.is_fitted or uncertainty <= 0.35):
            return "High"
        if total_historical >= 4 and active_months >= 2:
            return "Medium"
        return "Low"
