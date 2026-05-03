"""
app/models/user.py
User model with role-based access control.
Roles: admin | analyst | public
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    full_name       = Column(String(120))
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(20),  nullable=False, default="public")   # admin | analyst | public
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
