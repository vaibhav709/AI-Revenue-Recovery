"""Pydantic request schemas for the recovery API."""

from pydantic import BaseModel, ConfigDict


class RecoveryAnalysisRequest(BaseModel):
    """Customer features required by the trained payment-failure model."""

    model_config = ConfigDict(extra="forbid")

    customer_id: int
    nickname: str | None = None

    credit_limit: int
    gender: int
    education: int
    marital_status: int
    age: int

    pay_status_1: int
    pay_status_2: int
    pay_status_3: int
    pay_status_4: int
    pay_status_5: int
    pay_status_6: int

    bill_amount_1: int
    bill_amount_2: int
    bill_amount_3: int
    bill_amount_4: int
    bill_amount_5: int
    bill_amount_6: int

    payment_amount_1: int
    payment_amount_2: int
    payment_amount_3: int
    payment_amount_4: int
    payment_amount_5: int
    payment_amount_6: int


