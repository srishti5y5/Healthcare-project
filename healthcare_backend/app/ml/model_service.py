"""
app/ml/model_service.py
Handles RandomForest training, persistence (joblib), and inference.
Designed to be imported as a singleton in the FastAPI app.
"""
import os
from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from app.core.config import settings

# ── Feature columns used during training ──────────────────────────────────────
FEATURE_COLS = [
    "population",
    "urban_population",
    "rural_population",
    "number_of_doctors",
    "number_of_hospitals",
    "hospital_beds",
    "primary_health_centers",
    "disease_burden_index",
    "doctor_to_population_ratio",
    "bed_availability_index",
]

TARGET_COL = "healthcare_access_score"
MODEL_VERSION = "rf_v1.0"


class ModelService:
    """
    Wraps training + inference so the API layer never touches sklearn directly.
    """

    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self.model_version: str = MODEL_VERSION
        self._load_if_exists()

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load_if_exists(self) -> None:
        path = Path(settings.MODEL_PATH)
        if path.exists():
            self.pipeline = joblib.load(path)
            print(f"[ML] Model loaded from {path}")
        else:
            print("[ML] No saved model found — call /admin/train first.")

    def save(self) -> None:
        path = Path(settings.MODEL_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path)
        print(f"[ML] Model saved to {path}")

    @property
    def is_ready(self) -> bool:
        return self.pipeline is not None

    # ── Training ──────────────────────────────────────────────────────────────
    def train(self, csv_path: Optional[str] = None) -> dict:
        """
        Trains a RandomForest on the district CSV.
        Returns evaluation metrics + feature importances.
        """
        csv_path = csv_path or settings.TRAINING_DATA_PATH
        df = pd.read_csv(csv_path)

        # Drop rows where target is missing
        df = df.dropna(subset=[TARGET_COL])
        X = df[FEATURE_COLS]
        y = df[TARGET_COL]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Pipeline: impute → scale → RF
        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler",  StandardScaler()),
            ("model",   RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_leaf=4,
                n_jobs=-1,
                random_state=42,
            )),
        ])

        self.pipeline.fit(X_train, y_train)
        y_pred = self.pipeline.predict(X_test)

        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2   = float(r2_score(y_test, y_pred))

        importances = dict(zip(
            FEATURE_COLS,
            self.pipeline.named_steps["model"].feature_importances_.round(4).tolist(),
        ))

        self.save()

        return {
            "rmse": round(rmse, 4),
            "r2":   round(r2, 4),
            "training_samples": len(X_train),
            "test_samples":     len(X_test),
            "feature_importances": importances,
        }

    # ── Inference ─────────────────────────────────────────────────────────────
    def predict(self, features: dict) -> Tuple[float, str]:
        """
        Returns (predicted_score, risk_tier).
        Raises RuntimeError if model not loaded.
        """
        if not self.is_ready:
            raise RuntimeError("Model is not trained yet. Call POST /admin/train.")

        row = pd.DataFrame([{col: features.get(col) for col in FEATURE_COLS}])
        score = float(np.clip(self.pipeline.predict(row)[0], 0.0, 1.0))

        if score >= 0.65:
            tier = "High"
        elif score >= 0.40:
            tier = "Medium"
        else:
            tier = "Low"

        return round(score, 4), tier


# ── Singleton — imported by the FastAPI app ───────────────────────────────────
model_service = ModelService()
