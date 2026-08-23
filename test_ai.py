import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app
from api.models import Customer, RecoveryCase, MAX_RECOVERY_ATTEMPTS
from api.database import SessionLocal

class TestAIGeneration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Cleanup
        self.db.query(RecoveryCase).filter(RecoveryCase.customer_id == 88888).delete()
        self.db.query(Customer).filter(Customer.customer_id == 88888).delete()
        self.db.commit()
        
        # Create base customer
        cust = Customer(customer_id=88888, credit_limit=5000)
        self.db.add(cust)
        self.db.commit()
        
        # Create a clean case for each test
        case = RecoveryCase(
            customer_id=88888, failure_probability=0.8, predicted_failure=True,
            risk_level="HIGH", priority="HIGH", strategy="ESCALATED",
            communication_channel="PHONE", follow_up_days=1, escalation_candidate=True,
            status="Pending", amount_at_risk=10000.0, amount_recovered=0.0,
            attempt_count=0, max_attempts=MAX_RECOVERY_ATTEMPTS
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        self.case_id = case.id

    def tearDown(self):
        self.db.query(RecoveryCase).filter(RecoveryCase.customer_id == 88888).delete()
        self.db.query(Customer).filter(Customer.customer_id == 88888).delete()
        self.db.commit()
        self.db.close()

    @patch('api.services.recovery_ai.OpenAI')
    def test_normal_case_continue(self, mock_openai):
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''{
            "decision": "CONTINUE",
            "recommended_action": "Test Action",
            "reason": "Test Reason",
            "communication_channel": "EMAIL",
            "follow_up_days": 2,
            "customer_message": "Test Message",
            "confidence": 0.99
        }'''
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            res = self.client.post(f"/recovery/cases/{self.case_id}/generate-action")
            
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["ai_decision"], "CONTINUE")
        self.assertEqual(data["ai_customer_message"], "Test Message")

    @patch('api.services.recovery_ai.OpenAI')
    def test_fully_recovered_case(self, mock_openai):
        # Update case to fully recovered
        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == self.case_id).first()
        case.amount_recovered = 10000.0
        self.db.commit()

        res = self.client.post(f"/recovery/cases/{self.case_id}/generate-action")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["ai_decision"], "STOP")
        # Ensure OpenAI wasn't called
        mock_openai.assert_not_called()

    @patch('api.services.recovery_ai.OpenAI')
    def test_completed_case(self, mock_openai):
        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == self.case_id).first()
        case.status = "Completed"
        self.db.commit()

        res = self.client.post(f"/recovery/cases/{self.case_id}/generate-action")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["ai_decision"], "STOP")
        mock_openai.assert_not_called()
        
    @patch('api.services.recovery_ai.OpenAI')
    def test_escalated_case(self, mock_openai):
        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == self.case_id).first()
        case.status = "Escalated"
        self.db.commit()

        res = self.client.post(f"/recovery/cases/{self.case_id}/generate-action")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["ai_decision"], "STOP")
        mock_openai.assert_not_called()
        
    @patch('api.services.recovery_ai.OpenAI')
    def test_max_attempts_case(self, mock_openai):
        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == self.case_id).first()
        case.attempt_count = 5
        self.db.commit()

        res = self.client.post(f"/recovery/cases/{self.case_id}/generate-action")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["ai_decision"], "ESCALATE")
        mock_openai.assert_not_called()
        
    @patch('api.services.recovery_ai.OpenAI')
    def test_invalid_decision_from_ai(self, mock_openai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"decision": "DANCE"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            res = self.client.post(f"/recovery/cases/{self.case_id}/generate-action")
            
        self.assertEqual(res.status_code, 500)
        self.assertIn("Invalid decision from AI.", res.json()["detail"])

    def test_missing_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            res = self.client.post(f"/recovery/cases/{self.case_id}/generate-action")
            self.assertEqual(res.status_code, 503)
            self.assertIn("AI recovery service is not configured.", res.json()["detail"])

if __name__ == '__main__':
    unittest.main()
