"""
app/models/nhp_target.py
National Health Policy targets for benchmarking district performance.
"""
from sqlalchemy import Column, Float, Integer, String, Text

from app.db.session import Base


class NHPTarget(Base):
    __tablename__ = "nhp_targets"

    id                          = Column(Integer, primary_key=True, index=True)
    indicator                   = Column(String(120), unique=True, nullable=False)
    target_value                = Column(Float, nullable=False)
    unit                        = Column(String(50))
    description                 = Column(Text)
    nhp_year                    = Column(Integer, default=2017)   # NHP 2017 reference
