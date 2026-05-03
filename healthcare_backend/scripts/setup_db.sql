-- ============================================================
-- scripts/setup_db.sql
-- Run this ONCE as the postgres superuser to prepare the DB.
-- psql -U postgres -f scripts/setup_db.sql
-- ============================================================

-- 1. Create database and user
CREATE USER healthcare_user WITH PASSWORD 'yourpassword';
CREATE DATABASE healthcare_db OWNER healthcare_user;
\c healthcare_db

-- 2. Enable PostGIS (requires postgis package installed)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- for fuzzy name matching

-- 3. Grant privileges
GRANT ALL PRIVILEGES ON DATABASE healthcare_db TO healthcare_user;
GRANT ALL ON SCHEMA public TO healthcare_user;

-- ============================================================
-- SQLAlchemy will auto-create tables via init_db.py
-- But if you prefer raw SQL, here are the CREATE TABLE statements:
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(120),
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'public',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS districts (
    id                          SERIAL PRIMARY KEY,
    district_id                 VARCHAR(12) NOT NULL,
    district_name               VARCHAR(120) NOT NULL,
    state                       VARCHAR(80) NOT NULL,
    year                        SMALLINT NOT NULL,
    population                  INTEGER,
    urban_population            INTEGER,
    rural_population            INTEGER,
    number_of_doctors           INTEGER,
    number_of_hospitals         INTEGER,
    hospital_beds               INTEGER,
    primary_health_centers      INTEGER,
    disease_burden_index        NUMERIC(6,4),
    doctor_to_population_ratio  NUMERIC(8,4),
    bed_availability_index      NUMERIC(6,4),
    healthcare_access_score     NUMERIC(6,4),
    under_served_flag           SMALLINT DEFAULT 0,
    geom                        GEOMETRY(Point, 4326),
    CONSTRAINT uq_district_year UNIQUE (district_id, year)
);

CREATE INDEX IF NOT EXISTS idx_districts_state  ON districts (state);
CREATE INDEX IF NOT EXISTS idx_districts_year   ON districts (year);
CREATE INDEX IF NOT EXISTS idx_districts_geom   ON districts USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_districts_score  ON districts (healthcare_access_score);

CREATE TABLE IF NOT EXISTS predictions (
    id                      SERIAL PRIMARY KEY,
    district_id             VARCHAR(12) NOT NULL,
    year                    INTEGER NOT NULL,
    predicted_access_score  NUMERIC(6,4) NOT NULL,
    risk_tier               VARCHAR(10),
    model_version           VARCHAR(50),
    requested_by            INTEGER REFERENCES users(id),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nhp_targets (
    id            SERIAL PRIMARY KEY,
    indicator     VARCHAR(120) UNIQUE NOT NULL,
    target_value  NUMERIC(10,4) NOT NULL,
    unit          VARCHAR(50),
    description   TEXT,
    nhp_year      INTEGER DEFAULT 2017
);

-- ── Seed NHP 2017 targets ──────────────────────────────────────────────────
INSERT INTO nhp_targets (indicator, target_value, unit, description) VALUES
  ('doctor_population_ratio',  1.0,  'per 1000',  'Doctors per 1000 population (WHO norm 1:1000)'),
  ('bed_per_1000',             2.0,  'per 1000',  'Hospital beds per 1000 population'),
  ('phc_per_30k_rural',        1.0,  'per 30000', '1 PHC per 30,000 rural population'),
  ('disease_burden_index_max', 0.30, '0-1 scale', 'Target max disease burden index')
ON CONFLICT (indicator) DO NOTHING;

-- ── Import CSV into districts (adjust path) ────────────────────────────────
-- \COPY districts(district_id, district_name, state, year, population, urban_population,
--   rural_population, number_of_doctors, number_of_hospitals, hospital_beds,
--   primary_health_centers, disease_burden_index, doctor_to_population_ratio,
--   bed_availability_index, healthcare_access_score, under_served_flag)
-- FROM '/absolute/path/to/india_healthcare_district_data.csv'
-- CSV HEADER;

-- ── Populate geometry from latitude/longitude columns in CSV ───────────────
-- If you loaded lat/lon as extra temp columns:
-- UPDATE districts
--   SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
--   WHERE geom IS NULL;

-- ── Useful analytical queries ──────────────────────────────────────────────

-- Top 20 worst-access districts in 2023
-- SELECT district_name, state, healthcare_access_score
-- FROM districts WHERE year = 2023
-- ORDER BY healthcare_access_score ASC LIMIT 20;

-- State-level average access score over time
-- SELECT state, year, ROUND(AVG(healthcare_access_score)::NUMERIC, 3) AS avg_score
-- FROM districts GROUP BY state, year ORDER BY state, year;

-- Districts within 150 km of Delhi (spatial query)
-- SELECT district_name, state,
--   ROUND(ST_Distance(geom::geography,
--     ST_SetSRID(ST_MakePoint(77.21, 28.63), 4326)::geography)::NUMERIC / 1000, 1) AS km
-- FROM districts WHERE year = 2023
--   AND ST_DWithin(geom::geography,
--     ST_SetSRID(ST_MakePoint(77.21, 28.63), 4326)::geography, 150000)
-- ORDER BY km;
