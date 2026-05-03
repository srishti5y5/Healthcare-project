"""
app/api/v1/endpoints/districts.py
GET /api/v1/districts            — paginated list with filters
GET /api/v1/districts/{id}       — single district by district_id + year
GET /api/v1/map                  — GeoJSON FeatureCollection (all districts, latest year)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.functions import ST_AsGeoJSON, ST_X, ST_Y
from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.dependencies import get_db
from app.models.district import District
from app.schemas.district import (
    DistrictListResponse,
    DistrictRead,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
)

router = APIRouter(prefix="/districts", tags=["Districts"])


# ── Helper: attach lat/lon from PostGIS geometry ──────────────────────────────
def _enrich(row, lat, lon) -> DistrictRead:
    d = DistrictRead.model_validate(row)
    d.latitude  = lat
    d.longitude = lon
    return d


@router.get("", response_model=DistrictListResponse)
async def list_districts(
    state:     Optional[str]  = Query(None, description="Filter by state name"),
    year:      Optional[int]  = Query(None, description="Filter by year (2019–2023)"),
    risk_tier: Optional[str]  = Query(None, description="Low | Medium | High"),
    page:      int            = Query(1,   ge=1),
    size:      int            = Query(50,  ge=1, le=200),
    db:        AsyncSession   = Depends(get_db),
):
    """
    Returns a paginated list of districts.
    Public access — no authentication required.
    """
    query = select(
        District,
        ST_X(District.geom).label("lon"),
        ST_Y(District.geom).label("lat"),
    )

    if state:
        query = query.where(func.lower(District.state) == state.lower())
    if year:
        query = query.where(District.year == year)
    if risk_tier:
        bounds = {"low": (0, 0.4), "medium": (0.4, 0.65), "high": (0.65, 1.0)}
        tier = risk_tier.lower()
        if tier in bounds:
            lo, hi = bounds[tier]
            query = query.where(
                District.healthcare_access_score >= lo,
                District.healthcare_access_score < hi,
            )

    # Total count for pagination metadata
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    rows = (await db.execute(query.offset((page - 1) * size).limit(size))).all()
    results = [_enrich(row.District, row.lat, row.lon) for row in rows]

    return DistrictListResponse(total=total, page=page, size=size, results=results)


@router.get("/map", response_model=GeoJSONFeatureCollection)
async def get_map(
    year: int = Query(2023, description="Year for map snapshot"),
    db:   AsyncSession = Depends(get_db),
):
    """
    Returns a GeoJSON FeatureCollection suitable for Leaflet / MapLibre GL.
    Each feature carries healthcare indicators as properties.
    Public access.
    """
    rows = (await db.execute(
        select(
            District,
            ST_X(District.geom).label("lon"),
            ST_Y(District.geom).label("lat"),
        ).where(District.year == year)
    )).all()

    features = []
    for row in rows:
        d = row.District
        tier = None
        if d.healthcare_access_score is not None:
            s = d.healthcare_access_score
            tier = "High" if s >= 0.65 else ("Medium" if s >= 0.40 else "Low")

        features.append(GeoJSONFeature(
            geometry=GeoJSONGeometry(coordinates=[row.lon or 0.0, row.lat or 0.0]),
            properties={
                "district_id":             d.district_id,
                "district_name":           d.district_name,
                "state":                   d.state,
                "year":                    d.year,
                "healthcare_access_score": d.healthcare_access_score,
                "risk_tier":               tier,
                "disease_burden_index":    d.disease_burden_index,
                "under_served_flag":       d.under_served_flag,
                "doctor_to_population_ratio": d.doctor_to_population_ratio,
            },
        ))

    return GeoJSONFeatureCollection(features=features)


@router.get("/{district_id}", response_model=DistrictRead)
async def get_district(
    district_id: str,
    year: int = Query(2023),
    db:   AsyncSession = Depends(get_db),
):
    """Returns a single district record. Public access."""
    row = (await db.execute(
        select(
            District,
            ST_X(District.geom).label("lon"),
            ST_Y(District.geom).label("lat"),
        )
        .where(District.district_id == district_id, District.year == year)
    )).first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District '{district_id}' not found for year {year}",
        )

    return _enrich(row.District, row.lat, row.lon)
