from pydantic import ValidationError

from crew.rules.recovery_schema import RecoveryPolicy


print("===== VALID POLICY =====")

policy = RecoveryPolicy(
    priority="ROUTINE",
    strategy="BALANCE_CLARIFICATION",
    communication_channel="EMAIL",
    follow_up_days=7,
    escalation_candidate=False,
)

print(policy)


print("\n===== INVALID POLICY TEST =====")

try:

    invalid_policy = RecoveryPolicy(
        priority="EXTREME",
        strategy="BALANCE_CLARIFICATION",
        communication_channel="EMAIL",
        follow_up_days=7,
        escalation_candidate=False,
    )

except ValidationError as e:

    print("Validation correctly rejected invalid policy.")
    print(e)