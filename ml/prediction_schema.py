from dataclasses import dataclass


@dataclass
class PaymentRisk:
    customer_id: int
    failure_probability: float
    predicted_failure: bool
    risk_level: str

    num_delayed_payments: int
    max_payment_delay: int
    avg_payment_delay: float
    recent_payment_delay: int

    credit_utilization: float
    payment_to_bill_ratio: float
    recent_payment_ratio: float
    recent_payment_amount: float
    recent_bill_amount: float