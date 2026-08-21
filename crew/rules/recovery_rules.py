from .recovery_schema import RecoveryPolicy


# --------------------------------------------------
# DETERMINISTIC RECOVERY POLICY
# --------------------------------------------------

def determine_recovery_policy(
    risk_level: str,
    predicted_failure: bool,
    num_delayed_payments: int,
    recent_payment_ratio: float,
    payment_to_bill_ratio: float,
) -> RecoveryPolicy:

    """
    Deterministic business rules.

    The LLM has NO authority over these decisions.
    """

    risk_level = risk_level.upper()

    # --------------------------------------------------
    # HIGH RISK / PREDICTED FAILURE
    # --------------------------------------------------

    if (
        risk_level == "HIGH"
        or predicted_failure is True
        or num_delayed_payments >= 3
    ):
        return RecoveryPolicy(
            priority="HIGH",
            strategy="ESCALATED_RECOVERY",
            communication_channel="PHONE",
            follow_up_days=1,
            escalation_candidate=True,
        )

    # --------------------------------------------------
    # PROACTIVE
    # --------------------------------------------------

    if (
        risk_level == "LOW"
        and (
            recent_payment_ratio < 0.10
            or payment_to_bill_ratio < 0.20
        )
    ):
        return RecoveryPolicy(
            priority="PROACTIVE",
            strategy="BALANCE_CLARIFICATION",
            communication_channel="EMAIL",
            follow_up_days=5,
            escalation_candidate=False,
        )

    # --------------------------------------------------
    # ROUTINE
    # --------------------------------------------------

    return RecoveryPolicy(
        priority="ROUTINE",
        strategy="BALANCE_CLARIFICATION",
        communication_channel="EMAIL",
        follow_up_days=7,
        escalation_candidate=False,
    )


# --------------------------------------------------
# DETERMINISTIC ESCALATION CONDITIONS
# --------------------------------------------------

def determine_escalation_conditions(
    policy: RecoveryPolicy,
    risk_level: str,
    predicted_failure: bool,
    num_delayed_payments: int,
) -> list[str]:

    """
    Determines WHY escalation was authorized.

    The recovery policy is the authoritative source
    for whether escalation is allowed.

    The LLM is never involved.
    """

    if not policy.escalation_candidate:
        return []

    conditions = []

    risk_level = risk_level.upper()

    if risk_level == "HIGH":
        conditions.append("risk_level == HIGH")

    if predicted_failure is True:
        conditions.append("predicted_failure == True")

    if num_delayed_payments >= 3:
        conditions.append("num_delayed_payments >= 3")

    return conditions