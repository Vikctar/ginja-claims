from fastapi.testclient import TestClient
from database import SessionLocal
from models import Member, Provider, Procedure
from main import app


def init_db():
    db = SessionLocal()
    if db.query(Member).first():
        db.close()
        return

    members = [
        Member(member_id="M123", name="Jane Wanjiku", status="active", plan_type="premium"),
        Member(member_id="M124", name="John Odhiambo", status="active", plan_type="basic"),
        Member(member_id="M125", name="Grace Muthoni", status="inactive", plan_type="basic"),
    ]

    providers = [
        Provider(provider_id="H456", name="Nairobi General Hospital", facility="hospital"),
        Provider(provider_id="H457", name="Kisumu Health Centre", facility="clinic"),
    ]

    procedures = [
        Procedure(procedure_code="P001", name="General Consultation", average_cost=25000, benefit_limit=40000),
        Procedure(procedure_code="P002", name="Lab Work - Blood Panel", average_cost=15000, benefit_limit=30000),
        Procedure(procedure_code="P003", name="X-Ray", average_cost=20000, benefit_limit=50000),
    ]

    db.add_all(members + providers + procedures)
    db.commit()
    db.close()


init_db()

client = TestClient(app)


def test_approved_claim():
    resp = client.post("/claims", json={
        "member_id": "M123",
        "provider_id": "H456",
        "diagnosis_code": "D001",
        "procedure_code": "P001",
        "claim_amount": 30000,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert data["approved_amount"] == 30000
    assert data["fraud_flag"] is False


def test_partial_claim():
    resp = client.post("/claims", json={
        "member_id": "M123",
        "provider_id": "H456",
        "diagnosis_code": "D001",
        "procedure_code": "P001",
        "claim_amount": 50000,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PARTIAL"
    assert data["approved_amount"] == 40000


def test_fraud_flag():
    resp = client.post("/claims", json={
        "member_id": "M123",
        "provider_id": "H456",
        "diagnosis_code": "D001",
        "procedure_code": "P001",
        "claim_amount": 55000,
    })
    data = resp.json()
    assert data["fraud_flag"] is True


def test_inactive_member_rejected():
    resp = client.post("/claims", json={
        "member_id": "M125",
        "provider_id": "H456",
        "diagnosis_code": "D001",
        "procedure_code": "P001",
        "claim_amount": 20000,
    })
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert "inactive" in data["rejection_reasons"][0].lower()


def test_unknown_member_rejected():
    resp = client.post("/claims", json={
        "member_id": "M999",
        "provider_id": "H456",
        "diagnosis_code": "D001",
        "procedure_code": "P001",
        "claim_amount": 20000,
    })
    data = resp.json()
    assert data["status"] == "REJECTED"


def test_invalid_amount():
    resp = client.post("/claims", json={
        "member_id": "M123",
        "provider_id": "H456",
        "diagnosis_code": "D001",
        "procedure_code": "P001",
        "claim_amount": -100,
    })
    assert resp.status_code == 422


def test_get_claim():
    post = client.post("/claims", json={
        "member_id": "M123",
        "provider_id": "H456",
        "diagnosis_code": "D001",
        "procedure_code": "P001",
        "claim_amount": 25000,
    })
    claim_id = post.json()["claim_id"]

    get = client.get(f"/claims/{claim_id}")
    assert get.status_code == 200
    assert get.json()["claim_id"] == claim_id


def test_get_nonexistent_claim():
    resp = client.get("/claims/CNOTREAL")
    assert resp.status_code == 404
