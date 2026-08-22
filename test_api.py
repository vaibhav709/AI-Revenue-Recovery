import unittest
from unittest.mock import patch
from json import JSONDecodeError

from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.main import app
from crew.pipeline import CrewAIWorkflowError
from crew.rules.recovery_schema import FinalRecoveryPlan
from test_recovery_pipeline import CUSTOMER_DATA


class RecoveryApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
        # Remove derived fields from the API request payload because they are now computed server-side
        self.request_data = {"customer_id": 8681, **CUSTOMER_DATA}
        derived_keys = [
            "num_delayed_payments", "max_payment_delay", "avg_payment_delay", "recent_payment_delay",
            "avg_bill_amount", "avg_payment_amount", "total_bill_amount", "total_payment_amount",
            "payment_to_bill_ratio", "credit_utilization", "payment_std", "recent_payment_amount",
            "recent_bill_amount", "recent_payment_ratio"
        ]
        for key in derived_keys:
            self.request_data.pop(key, None)
            
        self.final_plan = FinalRecoveryPlan(
            customer_id=8681,
            failure_probability=0.2941,
            predicted_failure=False,
            risk_level="LOW",
            credit_utilization=0.45,
            payment_to_bill_ratio=0.15,
            priority="PROACTIVE",
            strategy="BALANCE_CLARIFICATION",
            communication_channel="EMAIL",
            follow_up_days=5,
            escalation_candidate=False,
            final_action="Send the approved recovery communication.",
            customer_message="Please review your account information.",
            follow_up_action="Follow up according to the approved schedule.",
        )

    def test_valid_request_returns_pipeline_final_plan(self):
        with patch(
            "api.main.run_recovery_pipeline", return_value=self.final_plan
        ) as pipeline:
            response = self.client.post("/recovery/analyze", json=self.request_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.final_plan.model_dump())
        self.assertEqual(response.json()["customer_id"], 8681)
        pipeline.assert_called_once()
        self.assertEqual(pipeline.call_args.kwargs["customer_id"], 8681)
        self.assertIn("avg_bill_amount", pipeline.call_args.kwargs["customer_data"])

    def test_invalid_request_is_rejected_before_pipeline_execution(self):
        invalid_request = self.request_data.copy()
        invalid_request.pop("credit_limit")

        with patch("api.main.run_recovery_pipeline") as pipeline:
            response = self.client.post("/recovery/analyze", json=invalid_request)

        self.assertEqual(response.status_code, 422)
        pipeline.assert_not_called()

    def test_invalid_feature_type_is_rejected_before_pipeline_execution(self):
        invalid_request = self.request_data.copy()
        invalid_request["credit_limit"] = "not-a-number"

        with patch("api.main.run_recovery_pipeline") as pipeline:
            response = self.client.post("/recovery/analyze", json=invalid_request)

        self.assertEqual(response.status_code, 422)
        pipeline.assert_not_called()

    def test_extra_request_field_is_rejected_before_pipeline_execution(self):
        invalid_request = {**self.request_data, "unexpected_field": 1}

        with patch("api.main.run_recovery_pipeline") as pipeline:
            response = self.client.post("/recovery/analyze", json=invalid_request)

        self.assertEqual(response.status_code, 422)
        pipeline.assert_not_called()

    def test_pipeline_value_error_returns_safe_validation_response(self):
        self._assert_safe_error_response(
            ValueError("ML failure detail must not be exposed"),
            expected_status=500,
            expected_detail="Recovery plan validation failed.",
            hidden_text="ML failure detail must not be exposed",
        )

    def test_crewai_failure_returns_safe_upstream_response(self):
        self._assert_safe_error_response(
            CrewAIWorkflowError("CrewAI failure detail must not be exposed"),
            expected_status=502,
            expected_detail="Recovery communication service is unavailable.",
            hidden_text="CrewAI failure detail must not be exposed",
        )

    def test_malformed_llm_output_returns_safe_upstream_response(self):
        self._assert_safe_error_response(
            JSONDecodeError("Malformed LLM output must not be exposed", "x", 0),
            expected_status=502,
            expected_detail="Recovery communication service returned an invalid response.",
            hidden_text="Malformed LLM output must not be exposed",
        )

    def test_pydantic_validation_error_returns_safe_validation_response(self):
        try:
            FinalRecoveryPlan.model_validate({})
        except ValidationError as error:
            validation_error = error
        else:
            self.fail("Expected FinalRecoveryPlan validation to fail.")

        self._assert_safe_error_response(
            validation_error,
            expected_status=500,
            expected_detail="Recovery plan validation failed.",
            hidden_text="validation error for FinalRecoveryPlan",
        )

    def test_policy_value_error_returns_safe_validation_response(self):
        self._assert_safe_error_response(
            ValueError("Policy violation detail must not be exposed"),
            expected_status=500,
            expected_detail="Recovery plan validation failed.",
            hidden_text="Policy violation detail must not be exposed",
        )

    def test_unexpected_error_returns_safe_internal_response(self):
        self._assert_safe_error_response(
            RuntimeError("Unexpected failure detail must not be exposed"),
            expected_status=500,
            expected_detail="An unexpected error occurred while processing the recovery analysis.",
            hidden_text="Unexpected failure detail must not be exposed",
        )

    def _assert_safe_error_response(
        self,
        error: Exception,
        expected_status: int,
        expected_detail: str,
        hidden_text: str,
    ) -> None:
        with patch("api.main.run_recovery_pipeline", side_effect=error):
            response = self.client.post("/recovery/analyze", json=self.request_data)

        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response.json(), {"detail": expected_detail})
        self.assertNotIn(hidden_text, response.text)


if __name__ == "__main__":
    unittest.main()

