import json
import unittest
from unittest.mock import patch

from crew.pipeline import run_recovery_pipeline
from crew.rules.recovery_rules import determine_recovery_policy
from crew.rules.recovery_schema import FinalRecoveryPlan


CUSTOMER_DATA = {
    "credit_limit": 50000, "gender": 2, "education": 3, "marital_status": 1, "age": 43,
    "pay_status_1": 0, "pay_status_2": 0, "pay_status_3": 0, "pay_status_4": 0, "pay_status_5": 0, "pay_status_6": 0,
    "bill_amount_1": 39177, "bill_amount_2": 39607, "bill_amount_3": 17070, "bill_amount_4": 13038, "bill_amount_5": 8904, "bill_amount_6": 4740,
    "payment_amount_1": 2000, "payment_amount_2": 1500, "payment_amount_3": 3500, "payment_amount_4": 600, "payment_amount_5": 500, "payment_amount_6": 4000,
    "num_delayed_payments": 0, "max_payment_delay": 0, "avg_payment_delay": 0, "recent_payment_delay": 0,
    "avg_bill_amount": 20422.666667, "avg_payment_amount": 2016.666667,
    "total_bill_amount": 122536, "total_payment_amount": 12100,
    "payment_to_bill_ratio": 0.098746, "credit_utilization": 0.408453,
    "payment_std": 1463.443428, "recent_payment_amount": 2000,
    "recent_bill_amount": 39177, "recent_payment_ratio": 0.051050,
}


class RecoveryPipelineTests(unittest.TestCase):
    def test_returns_validated_plan_with_unchanged_deterministic_policy(self):
        llm_output = json.dumps(
            {
                "final_action": "Send the approved recovery communication.",
                "customer_message": "Please review your account information.",
                "follow_up_action": "Follow up according to the approved schedule.",
                # These conflicting values must never become part of the plan.
                "priority": "HIGH",
                "strategy": "ESCALATED_RECOVERY",
                "communication_channel": "PHONE",
                "follow_up_days": 1,
                "escalation_candidate": True,
            }
        )

        with patch("crew.pipeline._run_crewai_workflow", return_value=llm_output) as workflow:
            plan = run_recovery_pipeline(CUSTOMER_DATA, customer_id=8681)

        expected_policy = determine_recovery_policy(
            risk_level="LOW",
            predicted_failure=False,
            num_delayed_payments=0,
            recent_payment_ratio=0.051050,
            payment_to_bill_ratio=0.098746,
        )
        self.assertIsInstance(plan, FinalRecoveryPlan)
        self.assertEqual(plan.customer_id, 8681)
        self.assertEqual(plan.priority, expected_policy.priority)
        self.assertEqual(plan.strategy, expected_policy.strategy)
        self.assertEqual(plan.communication_channel, expected_policy.communication_channel)
        self.assertEqual(plan.follow_up_days, expected_policy.follow_up_days)
        self.assertEqual(plan.escalation_candidate, expected_policy.escalation_candidate)
        self.assertEqual(plan.priority, "PROACTIVE")

        workflow_inputs = workflow.call_args.args[0]
        self.assertEqual(workflow_inputs["customer_data"]["failure_probability"], 0.2941)
        self.assertEqual(workflow_inputs["recovery_policy"], expected_policy.model_dump())

    def test_rejects_missing_llm_communication_field(self):
        llm_output = json.dumps(
            {
                "final_action": "Send the approved recovery communication.",
                "customer_message": "Please review your account information.",
            }
        )

        with patch("crew.pipeline._run_crewai_workflow", return_value=llm_output):
            with self.assertRaises(KeyError):
                run_recovery_pipeline(CUSTOMER_DATA, customer_id=8681)

    def test_preserves_deterministic_escalation_decision(self):
        customer_data = {**CUSTOMER_DATA, "num_delayed_payments": 3}
        llm_output = json.dumps(
            {
                "final_action": "Use the approved recovery action.",
                "customer_message": "Please review your account information.",
                "follow_up_action": "Follow up according to the approved schedule.",
            }
        )

        with patch("crew.pipeline._run_crewai_workflow", return_value=llm_output) as workflow:
            plan = run_recovery_pipeline(customer_data, customer_id=8681)

        self.assertEqual(plan.priority, "HIGH")
        self.assertEqual(plan.strategy, "ESCALATED_RECOVERY")
        self.assertEqual(plan.communication_channel, "PHONE")
        self.assertEqual(plan.follow_up_days, 1)
        self.assertTrue(plan.escalation_candidate)
        self.assertTrue(workflow.call_args.args[0]["escalation_candidate"])


if __name__ == "__main__":
    unittest.main()
