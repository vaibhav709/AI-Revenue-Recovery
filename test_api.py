import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from crew.rules.recovery_schema import FinalRecoveryPlan
from test_recovery_pipeline import CUSTOMER_DATA


class RecoveryApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.request_data = {"customer_id": 8681, **CUSTOMER_DATA}
        self.final_plan = FinalRecoveryPlan(
            customer_id=8681,
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
        pipeline.assert_called_once_with(
            customer_data=CUSTOMER_DATA,
            customer_id=8681,
        )

    def test_invalid_request_is_rejected_before_pipeline_execution(self):
        invalid_request = self.request_data.copy()
        invalid_request.pop("credit_limit")

        with patch("api.main.run_recovery_pipeline") as pipeline:
            response = self.client.post("/recovery/analyze", json=invalid_request)

        self.assertEqual(response.status_code, 422)
        pipeline.assert_not_called()


if __name__ == "__main__":
    unittest.main()
