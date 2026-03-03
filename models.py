from datetime import datetime, timezone

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, JSON

from database import Base


class Member(Base):
    __tablename__ = "members"
    member_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    status = Column(String(10), nullable=False)  # active | inactive
    plan_type = Column(String(20), default="basic")


class Provider(Base):
    __tablename__ = "providers"
    provider_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    facility = Column(String(50), nullable=False)


class Procedure(Base):
    __tablename__ = "procedures"
    procedure_code = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    average_cost = Column(Numeric(12, 2), nullable=False)
    benefit_limit = Column(Numeric(12, 2), nullable=False)


class Claim(Base):
    __tablename__ = "claims"
    claim_id = Column(String(20), primary_key=True)
    member_id = Column(String(20), nullable=False)
    provider_id = Column(String(20), nullable=False)
    diagnosis_code = Column(String(20), nullable=False)
    procedure_code = Column(String(20), nullable=False)
    claim_amount = Column(Numeric(12, 2), nullable=False)
    approved_amount = Column(Numeric(12, 2))
    status = Column(String(10), nullable=False)
    fraud_flag = Column(Boolean, default=False)
    rejection_reasons = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
