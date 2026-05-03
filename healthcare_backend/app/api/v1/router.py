"""
app/api/v1/router.py
Assembles all v1 endpoint routers into one APIRouter.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, districts, predictions

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(districts.router)
api_router.include_router(predictions.router)
