from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TravelType(str, Enum):
    DOMESTIC = "DOMESTIC"


class ExpenseCategory(str, Enum):
    FLIGHT = "FLIGHT"
    HOTEL = "HOTEL"
    MEAL = "MEAL"
    TAXI = "TAXI"
    OTHER = "OTHER"


class Decision(str, Enum):
    APPROVE = "APPROVE"
    PARTIALLY_APPROVE = "PARTIALLY_APPROVE"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ReceiptInput(BaseModel):
    available: bool
    file_reference: Optional[str] = None


class ExpenseInput(BaseModel):
    category: ExpenseCategory
    claimed_amount: float = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    expense_date: date
    description: Optional[str] = None


class ClaimRequest(BaseModel):
    claim_id: str = Field(min_length=1)
    employee_id: str = Field(min_length=1)
    travel_type: TravelType = TravelType.DOMESTIC
    expense: ExpenseInput
    receipt: ReceiptInput


class AmountBreakdown(BaseModel):
    claimed: float
    approved: float
    rejected: float
    currency: str = "INR"


class PolicyEvidence(BaseModel):
    policy_id: str
    section: str
    text: Optional[str] = None


class ReceiptResult(BaseModel):
    status: str
    extraction_confidence: Optional[float] = None


class ClaimDecisionResponse(BaseModel):
    claim_id: str
    decision: Decision
    amounts: AmountBreakdown
    policy_evidence: list[PolicyEvidence] = Field(default_factory=list)
    receipt: ReceiptResult
    reason: str
    explanation_source: str
    manual_review: bool
    reason_code: Optional[str] = None
    trace_id: str
