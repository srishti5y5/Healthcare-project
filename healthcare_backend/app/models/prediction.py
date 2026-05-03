"""
app/models/prediction.py
Stores ML prediction results so they can be audited and served via API.
"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func

from app.db.session import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id                      = Column(Integer, primary_key=True, index=True)
    district_id             = Column(String(12), nullable=False, index=True)
    year                    = Column(Integer, nullable=False)
    predicted_access_score  = Column(Float, nullable=False)
    risk_tier               = Column(String(10))          # Low / Medium / High
    model_version           = Column(String(50))
    requested_by            = Column(Integer, ForeignKey("users.id"))
    created_at              = Column(DateTime(timezone=True), server_default=func.now())
