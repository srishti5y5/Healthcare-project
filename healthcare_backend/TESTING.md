## Healthcare API — Manual Testing Guide
### Using curl and Postman

---

## 0. Start the server

```bash
cd healthcare_backend
pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL etc.
uvicorn app.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

---

## 1. Health Check

```bash
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0"}
```

---

## 2. Register Users

```bash
# Create an admin
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin1234!","role":"admin","full_name":"Admin User"}'

# Create an analyst
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@example.com","password":"Analyst123!","role":"analyst"}'

# Create a public user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"public@example.com","password":"Public123!","role":"public"}'
```

---

## 3. Login & Save Token

```bash
# Login as admin
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"
```

In **Postman**: use Collection Variables to store `{{token}}` and set it in the Authorization tab as `Bearer {{token}}`.

---

## 4. Check Current User

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 5. List Districts (public, no auth)

```bash
# All districts, year 2023
curl "http://localhost:8000/api/v1/districts?year=2023&size=20"

# Filter by state
curl "http://localhost:8000/api/v1/districts?state=Kerala&year=2023"

# Filter by risk tier
curl "http://localhost:8000/api/v1/districts?risk_tier=Low&year=2023&size=50"
```

---

## 6. Single District

```bash
curl "http://localhost:8000/api/v1/districts/IND_0001?year=2023"
```

---

## 7. GeoJSON Map

```bash
# Returns GeoJSON FeatureCollection — paste into geojson.io to visualise
curl "http://localhost:8000/api/v1/map?year=2023" | python3 -m json.tool | head -60
```

---

## 8. Train Model (admin only)

```bash
# First make sure TRAINING_DATA_PATH in .env points to your CSV
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/v1/admin/train \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# → {"message":"Model trained...","metrics":{"rmse":0.04,"r2":0.97,...}}
```

---

## 9. Predict (analyst or admin)

```bash
ANALYST_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@example.com","password":"Analyst123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ANALYST_TOKEN" \
  -d '{
    "district_id": "IND_TEST",
    "year": 2024,
    "population": 800000,
    "urban_population": 250000,
    "rural_population": 550000,
    "number_of_doctors": 480,
    "number_of_hospitals": 30,
    "hospital_beds": 900,
    "primary_health_centers": 18,
    "disease_burden_index": 0.55,
    "doctor_to_population_ratio": 0.6,
    "bed_availability_index": 0.3
  }'
```

Expected response:
```json
{
  "district_id": "IND_TEST",
  "year": 2024,
  "predicted_access_score": 0.3812,
  "risk_tier": "Low",
  "model_version": "rf_v1.0",
  "confidence_note": "RandomForest regression — median-imputed missing values."
}
```

---

## 10. Reports (analyst/admin)

```bash
# All India 2023
curl "http://localhost:8000/api/v1/reports?year=2023" \
  -H "Authorization: Bearer $ANALYST_TOKEN"

# State-specific
curl "http://localhost:8000/api/v1/reports?year=2023&state=Bihar" \
  -H "Authorization: Bearer $ANALYST_TOKEN"
```

---

## 11. Role-restriction test

```bash
PUB_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"public@example.com","password":"Public123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Should return 403 Forbidden
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PUB_TOKEN" \
  -d '{"district_id":"X","year":2023,"population":100000,"number_of_doctors":50,"number_of_hospitals":5,"hospital_beds":100,"primary_health_centers":3,"disease_burden_index":0.5}'
```

---

## 12. Run automated tests

```bash
pytest tests/ -v --tb=short
```

---

## Postman Collection (quick setup)

1. Create a new Collection named "Healthcare API"
2. Add a Collection Variable: `base_url = http://localhost:8000`
3. Add a Pre-request Script to the collection:
   ```javascript
   // Auto-refresh token if missing
   const token = pm.collectionVariables.get("token");
   if (!token) {
       pm.sendRequest({
           url: pm.collectionVariables.get("base_url") + "/api/v1/auth/login",
           method: "POST",
           header: {"Content-Type": "application/json"},
           body: { mode: "raw", raw: JSON.stringify({
               email: "admin@example.com", password: "Admin1234!"
           })}
       }, (err, res) => {
           pm.collectionVariables.set("token", res.json().access_token);
       });
   }
   ```
4. In each protected request, set Authorization → Bearer Token → `{{token}}`
