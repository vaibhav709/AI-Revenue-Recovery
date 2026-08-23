import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app
from api.models import Customer, RecoveryCase, MAX_RECOVERY_ATTEMPTS
from api.database import SessionLocal

class TestBatchAnalysis(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Cleanup
        self.db.query(RecoveryCase).delete()
        self.db.query(Customer).delete()
        self.db.commit()

    def tearDown(self):
        self.db.query(RecoveryCase).delete()
        self.db.query(Customer).delete()
        self.db.commit()
        self.db.close()

    @patch('api.main.run_recovery_pipeline')
    @patch('api.services.recovery_ai.OpenAI')
    def test_batch_requirements(self, mock_openai, mock_pipeline):
        # 1. Empty database -> 200, total_analyzed = 0
        res = self.client.post("/recovery/analyze-batch")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total_analyzed"], 0)
        
        # Add multiple customers
        c1 = Customer(customer_id=1, bill_amount_1=5000, credit_limit=10000, 
                      gender=1, education=1, marital_status=1, age=30,
                      pay_status_1=1, pay_status_2=1, pay_status_3=1, pay_status_4=1, pay_status_5=1, pay_status_6=1,
                      bill_amount_2=0, bill_amount_3=0, bill_amount_4=0, bill_amount_5=0, bill_amount_6=0,
                      payment_amount_1=0, payment_amount_2=0, payment_amount_3=0, payment_amount_4=0, payment_amount_5=0, payment_amount_6=0)
        c2 = Customer(customer_id=2, bill_amount_1=10000, credit_limit=20000,
                      gender=1, education=1, marital_status=1, age=40,
                      pay_status_1=1, pay_status_2=1, pay_status_3=1, pay_status_4=1, pay_status_5=1, pay_status_6=1,
                      bill_amount_2=0, bill_amount_3=0, bill_amount_4=0, bill_amount_5=0, bill_amount_6=0,
                      payment_amount_1=0, payment_amount_2=0, payment_amount_3=0, payment_amount_4=0, payment_amount_5=0, payment_amount_6=0)
        self.db.add(c1)
        self.db.add(c2)
        self.db.commit()
        
        # 2. Multiple customers -> all are analyzed
        # 3. New qualifying customer -> exactly one RecoveryCase created
        res = self.client.post("/recovery/analyze-batch")
        data = res.json()
        self.assertEqual(data["total_analyzed"], 2)
        self.assertEqual(data["new_cases_created"], 2)
        self.assertEqual(data["existing_cases_updated"], 0)
        
        # Verify that cases with HIGH priority do not get created with Escalated status
        cases = self.db.query(RecoveryCase).all()
        for c in cases:
            self.assertNotEqual(c.status, "Escalated")
            self.assertIsNone(c.escalation_reason)
        
        # 11. Highest amount_at_risk in batch receives the max exposure component
        cases = self.db.query(RecoveryCase).all()
        self.assertEqual(len(cases), 2)
        # Check scores (c2 has 10000, c1 has 5000)
        c1_case = next(c for c in cases if c.customer_id == 1)
        c2_case = next(c for c in cases if c.customer_id == 2)
        
        import json
        c2_factors = json.loads(c2_case.priority_factors)
        self.assertEqual(c2_factors["financial_exposure_score"], 30.0) # c2 should get max
        c1_factors = json.loads(c1_case.priority_factors)
        self.assertEqual(c1_factors["financial_exposure_score"], 15.0) # c1 should get 15.0 (5k/10k * 30)

        # 4. Batch run twice -> does NOT create duplicate active cases
        res2 = self.client.post("/recovery/analyze-batch")
        data2 = res2.json()
        self.assertEqual(data2["total_analyzed"], 2)
        self.assertEqual(data2["new_cases_created"], 0)
        self.assertEqual(data2["existing_cases_updated"], 2)
        
        # 5. Existing active case -> analytical fields update (tested above via existing_cases_updated)
        
        # Let's set some custom values to ensure they are preserved
        self.db.refresh(c1_case)
        c1_case.attempt_count = 3
        c1_case.amount_recovered = 100.0
        c1_case.ai_customer_message = "Test preservation"
        c1_case.status = "Proactive"
        c1_case.escalation_reason = "Manual override"
        self.db.commit()
        
        res3 = self.client.post("/recovery/analyze-batch")
        self.db.refresh(c1_case)
        # 6. Existing active case -> attempt_count remains unchanged
        self.assertEqual(c1_case.attempt_count, 3)
        # 7. Existing active case -> amount_recovered remains unchanged
        self.assertEqual(c1_case.amount_recovered, 100.0)
        # 8. Existing active case -> AI fields remain unchanged
        self.assertEqual(c1_case.ai_customer_message, "Test preservation")
        
        # Batch analysis does not alter status
        self.assertEqual(c1_case.status, "Proactive")
        # Batch analysis does not alter escalation_reason
        self.assertEqual(c1_case.escalation_reason, "Manual override")
        
        # 9. Completed case -> must not be overwritten as an active case
        c1_case.status = "Completed"
        self.db.commit()
        
        res4 = self.client.post("/recovery/analyze-batch")
        # Since it's completed, it shouldn't update it, but should create a new one!
        self.assertEqual(res4.json()["new_cases_created"], 1) # c1 gets a new case
        
        # 12. Priority scores remain 0-100
        cases = self.db.query(RecoveryCase).all()
        for case in cases:
            self.assertGreaterEqual(case.priority_score, 0)
            self.assertLessEqual(case.priority_score, 100)
            # 13. Priority tiers are correct
            self.assertIn(case.priority_tier, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            
        # 14. Batch does not call OpenAI
        mock_openai.assert_not_called()
        
        # PROVE THAT run_recovery_pipeline (and thus CrewAI) IS NOT CALLED
        mock_pipeline.assert_not_called()
        
        # 15. Batch does not increment attempt_count
        # Handled in point 6
        
    @patch('ml.predict.predict_payment_failure')
    def test_malformed_customer(self, mock_predict):
        
        def mock_run(customer_data, customer_id):
            if customer_id == 999:
                raise ValueError("Malformed")
            from ml.prediction_schema import PaymentRisk
            return PaymentRisk(
                customer_id=customer_id,
                failure_probability=0.8,
                predicted_failure=True,
                risk_level="HIGH",
                num_delayed_payments=1,
                max_payment_delay=1,
                avg_payment_delay=1.0,
                recent_payment_delay=1,
                credit_utilization=0.5,
                payment_to_bill_ratio=0.5,
                recent_payment_ratio=0.5,
                recent_payment_amount=100.0,
                recent_bill_amount=200.0
            )
        mock_predict.side_effect = mock_run
        # 17. One malformed customer does not unnecessarily prevent valid customers
        c_bad = Customer(customer_id=999) # Missing fields will cause crash in pipeline
        c_good = Customer(customer_id=1000, bill_amount_1=5000, credit_limit=10000, 
                          gender=1, education=1, marital_status=1, age=30,
                          pay_status_1=1, pay_status_2=1, pay_status_3=1, pay_status_4=1, pay_status_5=1, pay_status_6=1,
                          bill_amount_2=0, bill_amount_3=0, bill_amount_4=0, bill_amount_5=0, bill_amount_6=0,
                          payment_amount_1=0, payment_amount_2=0, payment_amount_3=0, payment_amount_4=0, payment_amount_5=0, payment_amount_6=0)
        self.db.add(c_bad)
        self.db.add(c_good)
        self.db.commit()
        
        res = self.client.post("/recovery/analyze-batch")
        data = res.json()
        self.assertEqual(data["total_analyzed"], 1) # 1 valid customer
        self.assertEqual(len(data["errors"]), 1)
        self.assertEqual(data["errors"][0]["customer_id"], 999)
        self.assertEqual(data["new_cases_created"], 1)

if __name__ == '__main__':
    unittest.main()
