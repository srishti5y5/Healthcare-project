"""
app/schemas/user.py
Pydantic v2 schemas for auth and user management.
"""
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ── Registration ──────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email:     EmailStr
    full_name: Optional[str] = None
    password:  str = Field(min_length=8)
    role:      Literal["admin", "analyst", "public"] = "public"


class UserRead(BaseModel):
    id:        int
    email:     EmailStr
    full_name: Optional[str]
    role:      str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Login ─────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int               # seconds
    user:         UserRead
