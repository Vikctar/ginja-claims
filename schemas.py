from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClaimRequest(BaseModel):
    member_id: str = Field(..., json_schema_extra={"example": "M123"})
    provider_id: str = Field(..., json_schema_extra={"example": "H456"})
    diagnosis_code: str = Field(..., json_schema_extra={"example": "D001"})
    procedure_code: str = Field(..., json_schema_extra={"example": "P001"})
    claim_amount: float = Field(..., gt=0, json_schema_extra={"example": 50000})

class ClaimResponse(BaseModel):
    claim_id: str
    status: str
    fraud_flag: bool
    approved_amount: float
    rejection_reasons: list[str] = []
    created_at: Optional[datetime] = None