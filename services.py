import uuid

from sqlalchemy.orm import Session

from models import Member, Provider, Procedure, Claim
from schemas import ClaimRequest, ClaimResponse

FRAUD_MULTIPLIER = 2.0


def process_claim(db: Session, claim_request: ClaimRequest) -> ClaimResponse:
    reasons: list[str] = []
    fraud_flag = False
    claim_id = f"C{uuid.uuid4().hex[:8].upper()}"

    member = db.query(Member).filter_by(member_id=claim_request.member_id).first()
    if not member:
        reasons.append("Member not found")
    elif member.status != "active":
        reasons.append("Member is inactive")

    provider = db.query(Provider).filter_by(provider_id=claim_request.provider_id).first()
    if not provider:
        reasons.append("Provider not recognized")

    procedure = db.query(Procedure).filter_by(procedure_code=claim_request.procedure_code).first()
    if not procedure:
        reasons.append("Procedure code not found")

    if reasons:
        claim = _save_claim(db, claim_id, claim_request, "REJECTED", False, 0, reasons)
        return _to_response(claim)

    avg_cost = float(procedure.average_cost)
    if claim_request.claim_amount > FRAUD_MULTIPLIER * avg_cost:
        fraud_flag = True
        reasons.append(
            f"Claim amount ({claim_request.claim_amount:,.0f}) exceeds "
            f"{FRAUD_MULTIPLIER:.0f}x average cost ({avg_cost:,.0f})"
        )

    benefit_limit = float(procedure.benefit_limit)

    if fraud_flag and not member:
        status, approved = "REJECTED", 0
    elif claim_request.claim_amount <= benefit_limit:
        status, approved = "APPROVED", claim_request.claim_amount
    else:
        status, approved = "PARTIAL", benefit_limit
        reasons.append(f"Claim capped at benefit limit ({benefit_limit:,.0f})")

    claim = _save_claim(db, claim_id, claim_request, status, fraud_flag, approved, reasons)
    return _to_response(claim)


def get_claim(db: Session, claim_id: str) -> Claim | None:
    return db.query(Claim).filter_by(claim_id=claim_id).first()


def _save_claim(
        db: Session, claim_id: str, req: ClaimRequest,
        status: str, fraud_flag: bool, approved: float, reasons: list[str]
) -> Claim:
    claim = Claim(
        claim_id=claim_id,
        member_id=req.member_id,
        provider_id=req.provider_id,
        diagnosis_code=req.diagnosis_code,
        procedure_code=req.procedure_code,
        claim_amount=req.claim_amount,
        approved_amount=approved,
        status=status,
        fraud_flag=fraud_flag,
        rejection_reasons=reasons,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def _to_response(claim: Claim) -> ClaimResponse:
    return ClaimResponse(
        claim_id=claim.claim_id,
        status=claim.status,
        fraud_flag=claim.fraud_flag,
        approved_amount=float(claim.approved_amount or 0),
        rejection_reasons=claim.rejection_reasons or [],
        created_at=claim.created_at,
    )
