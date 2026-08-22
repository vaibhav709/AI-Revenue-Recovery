from typing import Literal
from pydantic import BaseModel, ConfigDict


class RecoveryPolicy(BaseModel):

    model_config = ConfigDict(extra="forbid")

    priority: Literal[
        "ROUTINE",
        "PROACTIVE",
        "HIGH"
    ]

    strategy: Literal[
        "BALANCE_CLARIFICATION",
        "ESCALATED_RECOVERY"
    ]

    communication_channel: Literal[
        "EMAIL",
        "SMS",
        "PHONE"
    ]

    follow_up_days: int

    escalation_candidate: bool


class FinalRecoveryPlan(BaseModel):

    model_config = ConfigDict(extra="forbid")

    customer_id: int
    
    # ML Outputs
    failure_probability: float
    predicted_failure: bool
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    credit_utilization: float
    payment_to_bill_ratio: float

    priority: Literal[
        "ROUTINE",
        "PROACTIVE",
        "HIGH"
    ]

    strategy: Literal[
        "BALANCE_CLARIFICATION",
        "ESCALATED_RECOVERY"
    ]

    communication_channel: Literal[
        "EMAIL",
        "SMS",
        "PHONE"
    ]

    follow_up_days: int

    escalation_candidate: bool

    final_action: str
    customer_message: str
    follow_up_action: str


def validate_final_plan(
    policy: RecoveryPolicy,
    plan: FinalRecoveryPlan
) -> None:

    # --------------------------------------------------
    # POLICY IMMUTABILITY CHECKS
    # --------------------------------------------------

    if plan.priority != policy.priority:
        raise ValueError(
            f"Policy violation: expected priority "
            f"{policy.priority}, got {plan.priority}"
        )

    if plan.strategy != policy.strategy:
        raise ValueError(
            f"Policy violation: expected strategy "
            f"{policy.strategy}, got {plan.strategy}"
        )

    if plan.communication_channel != policy.communication_channel:
        raise ValueError(
            f"Policy violation: expected communication channel "
            f"{policy.communication_channel}, got {plan.communication_channel}"
        )

    if plan.follow_up_days != policy.follow_up_days:
        raise ValueError(
            f"Policy violation: expected follow-up "
            f"{policy.follow_up_days} days, got {plan.follow_up_days}"
        )

    if plan.escalation_candidate != policy.escalation_candidate:
        raise ValueError(
            f"Policy violation: expected escalation_candidate "
            f"{policy.escalation_candidate}, got {plan.escalation_candidate}"
        )

    # --------------------------------------------------
    # ADDITIONAL SAFETY CHECK
    # --------------------------------------------------

    if (
        plan.strategy == "ESCALATED_RECOVERY"
        and not plan.escalation_candidate
    ):
        raise ValueError(
            "Invalid plan: ESCALATED_RECOVERY requires "
            "escalation_candidate=True"
        )