# Healthcare Access Inequality Map — Backend

Production-grade FastAPI backend with PostGIS, JWT auth, role-based access, and ML-powered risk scoring.

---

## Project Structure

```
healthcare_backend/
├── app/
│   ├── main.py                    # FastAPI app factory + lifespan
│   ├── api/v1/
│   │   ├── router.py              # Aggregates all routers
│   │   └── endpoints/
│   │       ├── auth.py            # /auth/register, /login, /me
│   │       ├── districts.py       # /districts, /districts/{id}, /map
│   │       └── predictions.py     # /predict, /admin/train, /reports
│   ├── core/
│   │   ├── config.py              # Pydantic settings (reads .env)
│   │   ├── security.py            # bcrypt + JWT
│   │   └── dependencies.py        # get_db, get_current_user, require_role
│   ├── db/
│   │   ├── session.py             # Async SQLAlchemy engine + Base
│   │   └── init_db.py             # create_all on startup
│   ├── models/                    # SQLAlchemy ORM
│   │   ├── district.py
│   │   ├── user.py
│   │   ├── prediction.py
│   │   └── nhp_target.py
│   ├── schemas/                   # Pydantic v2 request/response
│   │   ├── district.py
│   │   ├── user.py
│   │   └── prediction.py
│   └── ml/
│       └── model_service.py       # RF train + predict singleton
├── scripts/
│   └── setup_db.sql               # PostgreSQL + PostGIS setup
├── tests/
│   └── test_api.py
├── .env.example
├── requirements.txt
├── pytest.ini
└── TESTING.md
```

---

## Quick Start

```bash
# 1. Create & activate virtualenv
python -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup PostgreSQL
psql -U postgres -f scripts/setup_db.sql

# 4. Configure environment
cp .env.example .env
# Edit DATABASE_URL, SECRET_KEY, TRAINING_DATA_PATH

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## User Roles

| Role     | Access                                        |
|----------|-----------------------------------------------|
| public   | GET /districts, GET /map                      |
| analyst  | + POST /predict, GET /reports                 |
| admin    | + POST /admin/train, all analyst routes       |

---

## ML Workflow

1. Place your CSV at the path in `TRAINING_DATA_PATH`
2. Log in as admin → `POST /admin/train`
3. Model saved to `MODEL_PATH` (default: `app/ml/model.joblib`)
4. Any analyst can now call `POST /predict`

---

## Environment Variables

| Variable                    | Description                         |
|-----------------------------|-------------------------------------|
| `DATABASE_URL`              | PostgreSQL async connection string  |
| `SECRET_KEY`                | JWT signing secret (keep private!)  |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL (default 60)           |
| `MODEL_PATH`                | Where joblib saves the model        |
| `TRAINING_DATA_PATH`        | Path to the district CSV            |
| `CORS_ORIGINS`              | JSON array of allowed frontend URLs |
