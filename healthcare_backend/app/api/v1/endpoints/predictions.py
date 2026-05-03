"""
app/api/v1/endpoints/predictions.py
POST /api/v1/predict           — predict access score for given features  (analyst+)
POST /api/v1/admin/train       — retrain model from CSV                   (admin only)
GET  /api/v1/reports           — analyst summary report                   (analyst+)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.dependencies import get_db, get_current_user, require_role
from app.ml.model_service import model_service
from app.models.prediction import Prediction
from app.models.district import District
from app.models.user import User
from app.schemas.prediction import (
    PredictRequest,
    PredictResponse,
    ReportResponse,
    ReportRow,
    TrainResponse,
)

router = APIRouter(tags=["Predictions & Reports"])


# ── POST /predict ─────────────────────────────────────────────────────────────
@router.post("/predict", response_model=PredictResponse)
async def predict(
    payload: PredictRequest,
    db:      AsyncSession = Depends(get_db),
    current_user: User    = Depends(require_role("admin", "analyst")),
):
    """
    Predicts the healthcare access score for a given district/year combination.
    Requires analyst or admin role.
    The result is persisted to the predictions table for auditing.
    """
    if not model_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model not trained. An admin must call POST /admin/train first.",
        )

    features = payload.model_dump()
    score, tier = model_service.predict(features)

    # Persist result
    record = Prediction(
        district_id=payload.district_id,
        year=payload.year,
        predicted_access_score=score,
        risk_tier=tier,
        model_version=model_service.model_version,
        requested_by=current_user.id,
    )
    db.add(record)
    await db.commit()

    return PredictResponse(
        district_id=payload.district_id,
        year=payload.year,
        predicted_access_score=score,
        risk_tier=tier,
        model_version=model_service.model_version,
        confidence_note="RandomForest regression — median-imputed missing values.",
    )


# ── POST /admin/train ─────────────────────────────────────────────────────────
@router.post("/admin/train", response_model=TrainResponse)
async def train_model(
    current_user: User = Depends(require_role("admin")),
):
    """
    Triggers a full model retrain from the configured CSV file.
    Admin only. May take 10–30 seconds on large datasets.
    """
    try:
        metrics = model_service.train()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Training data not found: {e}",
        )

    return TrainResponse(
        message="Model trained and saved successfully.",
        model_version=model_service.model_version,
        metrics=metrics,
    )


# ── GET /reports ──────────────────────────────────────────────────────────────
@router.get("/reports", response_model=ReportResponse)
async def get_reports(
    year:  int = Query(2023, ge=2019, le=2030),
    state: str = Query(None),
    db:    AsyncSession = Depends(get_db),
    current_user: User  = Depends(require_role("admin", "analyst")),
):
    """
    Returns a summary of districts with access scores and risk tiers.
    Analyst and admin access only.
    """
    query = select(District).where(District.year == year)
    if state:
        from sqlalchemy import func
        query = query.where(func.lower(District.state) == state.lower())

    rows = (await db.execute(query.order_by(District.healthcare_access_score.asc()))).scalars().all()

    def to_tier(score):
        if score is None:
            return None
        return "High" if score >= 0.65 else ("Medium" if score >= 0.40 else "Low")

    results = [
        ReportRow(
            district_id=d.district_id,
            district_name=d.district_name,
            state=d.state,
            year=d.year,
            healthcare_access_score=d.healthcare_access_score,
            risk_tier=to_tier(d.healthcare_access_score),
            under_served_flag=d.under_served_flag,
        )
        for d in rows
    ]

    return ReportResponse(total=len(results), results=results)
