# Ginja Claims  API

A minimal backend service that validates health insurance claims in real time, checking member eligibility, benefit coverage, and fraud signals.

## Architecture Decisions

| Decision | Rationale                                                                             |
|---|---------------------------------------------------------------------------------------|
| **FastAPI + Python** | Fastest path to a clean, typed, documented API. Auto-generates OpenAPI/Swagger docs.  |
| **SQLAlchemy ORM** | Database-agnostic — swap SQLite → PostgreSQL/MySQL by changing one connection string. |
| **SQLite (dev)** | Zero-config local development. No Docker-compose DB needed to test.                   |
| **Service layer pattern** | Business logic in `service.py`. Easy to test and extend.                              |
| **Pydantic validation** | Request validation at the API boundary.|

### Claim Processing Flow

```
POST /claims
  → Pydantic validates input (rejects bad data with 422)
  → Check member exists & is active
  → Check provider is recognized
  → Check procedure code exists
  → Fraud check: claim_amount > 2× average_cost?
  → Benefit check: cap at procedure benefit_limit
  → Save claim → Return decision
```

### Data Model

Four tables with a clear separation of concerns:

- **members** — who's covered
- **providers** — registered hospitals/clinics
- **procedures** — what's covered and at what cost
- **claims** — the adjudication results

Schemas for PostgreSQL and MySQL are in the `db-schemas/` directory.

---

## How to Run Locally

### Option 1: uv 

```bash
uv sync
uv run uvicorn app.main:app --reload
```

### Option 2: Docker

```bash
docker build -t ginja-claims .
docker run -p 8000:8000 ginja-claims
```

API is at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### Run Lint & Tests and other checks (via tox)

```bash
uv run tox           # runs both lint and test
uv run tox -e lint   # lint only
uv run tox -e test   # tests only
uv run tox -e bandit # code security check only
```

---

## Sample API Requests

### Submit a claim (within limit → APPROVED)

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 30000
  }'
```

Response:
```json
{
  "claim_id": "C1A2B3C4",
  "status": "APPROVED",
  "fraud_flag": false,
  "approved_amount": 30000,
  "rejection_reasons": []
}
```

### Submit a claim (exceeds limit → PARTIAL + fraud flag)

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 55000
  }'
```

Response:
```json
{
  "claim_id": "C9D8E7F6",
  "status": "PARTIAL",
  "fraud_flag": true,
  "approved_amount": 40000,
  "rejection_reasons": [
    "Claim amount (55,000) exceeds 2x average cost (25,000)",
    "Claim capped at benefit limit (40,000)"
  ]
}
```

### Submit a claim (inactive member → REJECTED)

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "M125",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 20000
  }'
```

### Retrieve a claim

```bash
curl http://localhost:8000/claims/C1A2B3C4
```

---

## Seed Data

| Members | Status |
|---|---|
| M123 — Jane Wanjiku | active (premium) |
| M124 — John Odhiambo | active (basic) |
| M125 — Grace Muthoni | **inactive** |

| Procedures | Avg Cost | Benefit Limit |
|---|---|---|
| P001 — General Consultation | 25,000 | 40,000 |
| P002 — Lab Work (Blood Panel) | 15,000 | 30,000 |
| P003 — X-Ray | 20,000 | 50,000 |
