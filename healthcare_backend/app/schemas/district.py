"""
app/schemas/district.py
Pydantic v2 schemas for district request/response models.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DistrictBase(BaseModel):
    district_id:                str
    district_name:              str
    state:                      str
    year:                       int
    population:                 Optional[int]   = None
    urban_population:           Optional[int]   = None
    rural_population:           Optional[int]   = None
    number_of_doctors:          Optional[int]   = None
    number_of_hospitals:        Optional[int]   = None
    hospital_beds:              Optional[int]   = None
    primary_health_centers:     Optional[int]   = None
    disease_burden_index:       Optional[float] = None
    doctor_to_population_ratio: Optional[float] = None
    bed_availability_index:     Optional[float] = None
    healthcare_access_score:    Optional[float] = None
    under_served_flag:          Optional[int]   = 0


class DistrictRead(DistrictBase):
    id: int
    latitude:  Optional[float] = None
    longitude: Optional[float] = None

    # Risk tier derived from score
    risk_tier: Optional[str] = None

    @field_validator("risk_tier", mode="before")
    @classmethod
    def compute_tier(cls, v, info):
        score = info.data.get("healthcare_access_score")
        if score is None:
            return None
        if score >= 0.65:
            return "High"
        if score >= 0.40:
            return "Medium"
        return "Low"

    model_config = {"from_attributes": True}


class DistrictListResponse(BaseModel):
    total:   int
    page:    int
    size:    int
    results: List[DistrictRead]


# ── GeoJSON schemas ───────────────────────────────────────────────────────────
class GeoJSONGeometry(BaseModel):
    type:        str = "Point"
    coordinates: List[float]           # [lon, lat]


class GeoJSONFeature(BaseModel):
    type:       str = "Feature"
    geometry:   GeoJSONGeometry
    properties: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type:     str = "FeatureCollection"
    features: List[GeoJSONFeature]
