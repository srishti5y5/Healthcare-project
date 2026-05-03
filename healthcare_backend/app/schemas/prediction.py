"""
app/schemas/prediction.py
Pydantic v2 schemas for ML prediction endpoints.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """
    Input features sent to POST /predict.
    All values matching the ML training features.
    """
    district_id:                str
    year:                       int = Field(ge=2019, le=2030)
    population:                 int = Field(gt=0)
    urban_population:           Optional[int]   = None
    rural_population:           Optional[int]   = None
    number_of_doctors:          int = Field(ge=0)
    number_of_hospitals:        int = Field(ge=0)
    hospital_beds:              int = Field(ge=0)
    primary_health_centers:     int = Field(ge=0)
    disease_burden_index:       float = Field(ge=0.0, le=1.0)
    doctor_to_population_ratio: Optional[float] = None
    bed_availability_index:     Optional[float] = None


class PredictResponse(BaseModel):
    district_id:            str
    year:                   int
    predicted_access_score: float
    risk_tier:              str           # Low / Medium / High
    model_version:          str
    confidence_note:        str


class TrainResponse(BaseModel):
    message:       str
    model_version: str
    metrics:       dict                    # rmse, r2, feature_importances


class ReportRow(BaseModel):
    district_id:             str
    district_name:           str
    state:                   str
    year:                    int
    healthcare_access_score: Optional[float]
    risk_tier:               Optional[str]
    under_served_flag:       Optional[int]


class ReportResponse(BaseModel):
    total:   int
    results: List[ReportRow]
