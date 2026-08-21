from crew.rules.recovery_rules import determine_recovery_policy


policy = determine_recovery_policy(
    risk_level="LOW",
    predicted_failure=False,
    num_delayed_payments=0,
    recent_payment_ratio=0.05105,
    payment_to_bill_ratio=0.098746,
)


print("\n===== RECOVERY POLICY =====")
print(policy)