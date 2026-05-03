"""
app/db/init_db.py
Creates all tables on startup (dev only).
In production use Alembic migrations instead.
"""
from app.db.session import Base, engine
# Import models so SQLAlchemy registers them before create_all
from app.models import district, user, prediction, nhp_target  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        # PostGIS must already be enabled on the DB:
        #   CREATE EXTENSION IF NOT EXISTS postgis;
        await conn.run_sync(Base.metadata.create_all)
