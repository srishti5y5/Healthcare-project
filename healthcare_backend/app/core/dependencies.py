"""
app/core/dependencies.py
FastAPI dependency injection:
  - get_db       → yields an async SQLAlchemy session
  - get_current_user → validates JWT and returns user
  - require_role → factory that enforces role-based access
"""
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Database session ──────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """Yields one DB session per request, always closed afterwards."""
    async with AsyncSessionLocal() as session:
        yield session


# ── Current user (JWT validation) ─────────────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exc

    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


# ── Role enforcement ──────────────────────────────────────────────────────────
def require_role(*roles: str):
    """
    Usage:
        @router.get("/admin/...", dependencies=[Depends(require_role("admin"))])
    or as a typed dependency:
        current_user: User = Depends(require_role("admin", "analyst"))
    """
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to roles: {list(roles)}",
            )
        return current_user

    return checker
