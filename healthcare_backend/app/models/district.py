"""
app/models/district.py
ORM model for the districts table (PostGIS-enabled).
"""
from sqlalchemy import (
    Boolean, Column, Float, Integer, SmallInteger,
    String, UniqueConstraint,
)
from geoalchemy2 import Geometry

from app.db.session import Base


class District(Base):
    __tablename__ = "districts"

    id                          = Column(Integer, primary_key=True, index=True)
    district_id                 = Column(String(12), unique=True, nullable=False, index=True)
    district_name               = Column(String(120), nullable=False)
    state                       = Column(String(80),  nullable=False, index=True)
    year                        = Column(SmallInteger, nullable=False, index=True)

    # Demographics
    population                  = Column(Integer)
    urban_population            = Column(Integer)
    rural_population            = Column(Integer)

    # Healthcare supply
    number_of_doctors           = Column(Integer)
    number_of_hospitals         = Column(Integer)
    hospital_beds               = Column(Integer)
    primary_health_centers      = Column(Integer)

    # Indices
    disease_burden_index        = Column(Float)
    doctor_to_population_ratio  = Column(Float)
    bed_availability_index      = Column(Float)
    healthcare_access_score     = Column(Float)
    under_served_flag           = Column(SmallInteger, default=0)

    # PostGIS point geometry (SRID 4326 = WGS-84 lat/lon)
    geom                        = Column(Geometry(geometry_type="POINT", srid=4326))

    __table_args__ = (
        UniqueConstraint("district_id", "year", name="uq_district_year"),
    )
