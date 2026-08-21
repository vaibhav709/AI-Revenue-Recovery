"""Pydantic request schemas for the recovery API."""

from pydantic import BaseModel, ConfigDict


class RecoveryAnalysisRequest(BaseModel):
    """Customer features required by the trained payment-failure model."""

    model_config = ConfigDict(extra="forbid")

    customer_id: int

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

    num_delayed_payments: int
    max_payment_delay: int
    avg_payment_delay: float
    recent_payment_delay: int

    avg_bill_amount: float
    avg_payment_amount: float
    total_bill_amount: int
    total_payment_amount: int

    payment_to_bill_ratio: float
    credit_utilization: float
    payment_std: float
    recent_payment_amount: int
    recent_bill_amount: int
    recent_payment_ratio: float
