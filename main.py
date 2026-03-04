from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from database import Base, engine, get_db, SessionLocal
from models import Member, Provider, Procedure
from schemas import ClaimRequest, ClaimResponse
from services import process_claim, get_claim, _to_response

Base.metadata.create_all(bind=engine)


def init_db():
    """Create tables and seed mock data."""
    db = SessionLocal()
    # Only seed if empty
    if db.query(Member).first():
        db.close()
        return

    # -- Seed members --
    members = [
        Member(member_id="M123", name="Jane Wanjiku", status="active", plan_type="premium"),
        Member(member_id="M124", name="John Odhiambo", status="active", plan_type="basic"),
        Member(member_id="M125", name="Grace Muthoni", status="inactive", plan_type="basic"),
    ]

    # -- Seed providers --
    providers = [
        Provider(provider_id="H456", name="Nairobi General Hospital", facility="hospital"),
        Provider(provider_id="H457", name="Kisumu Health Centre", facility="clinic"),
    ]

    # -- Seed procedures --
    procedures = [
        Procedure(procedure_code="P001", name="General Consultation", average_cost=25000, benefit_limit=40000),
        Procedure(procedure_code="P002", name="Lab Work - Blood Panel", average_cost=15000, benefit_limit=30000),
        Procedure(procedure_code="P003", name="X-Ray", average_cost=20000, benefit_limit=50000),
    ]

    db.add_all(members + providers + procedures)
    db.commit()
    db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and seed data on startup."""
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Welcome to Ginja Claims"}


@app.post("/claims", response_model=ClaimResponse, status_code=201)
def submit_claim(req: ClaimRequest, db: Session = Depends(get_db)):
    """Submit a new insurance claim for validation."""
    result = process_claim(db, req)
    return result


@app.get("/claims/{claim_id}", response_model=ClaimResponse)
def retrieve_claim(claim_id: str, db: Session = Depends(get_db)):
    """Retrieve a claim by ID."""
    claim = get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return _to_response(claim)
