import unittest
import json
from api.services.scoring import calculate_priority_score, update_active_case_analytics
from api.models import RecoveryCase

class TestPriorityScoring(unittest.TestCase):
    
    def test_failure_probability_boundaries(self):
        # 1. failure_probability = 0 -> risk_score = 0
        res1 = calculate_priority_score(0.0, 1000, 1000, 0, "Pending")
        factors1 = json.loads(res1["priority_factors"])
        self.assertEqual(factors1["risk_score"], 0.0)
        
        # 2. failure_probability = 1 -> risk_score = 50
        res2 = calculate_priority_score(1.0, 1000, 1000, 0, "Pending")
        factors2 = json.loads(res2["priority_factors"])
        self.assertEqual(factors2["risk_score"], 50.0)

    def test_financial_exposure(self):
        # 3. amount_at_risk = maximum batch exposure -> 30
        res1 = calculate_priority_score(0.5, 5000, 5000, 0, "Pending")
        factors1 = json.loads(res1["priority_factors"])
        self.assertEqual(factors1["financial_exposure_score"], 30.0)
        
        # 4. max_amount_at_risk = 0 -> 0, no division by zero
        res2 = calculate_priority_score(0.5, 0, 0, 0, "Pending")
        factors2 = json.loads(res2["priority_factors"])
        self.assertEqual(factors2["financial_exposure_score"], 0.0)

    def test_urgency(self):
        # 5. attempt_count = 0, not escalated -> urgency = 0
        res1 = calculate_priority_score(0.5, 100, 1000, 0, "Pending")
        factors1 = json.loads(res1["priority_factors"])
        self.assertEqual(factors1["urgency_score"], 0)
        
        # 6. attempt_count = 5, not escalated -> attempt = 10
        res2 = calculate_priority_score(0.5, 100, 1000, 5, "Pending")
        factors2 = json.loads(res2["priority_factors"])
        self.assertEqual(factors2["attempt_score"], 10)
        self.assertEqual(factors2["urgency_score"], 10)
        
        # 7. attempt_count > 5 -> attempt = 10
        res3 = calculate_priority_score(0.5, 100, 1000, 10, "Pending")
        factors3 = json.loads(res3["priority_factors"])
        self.assertEqual(factors3["attempt_score"], 10)
        
        # 8. escalated + 5 attempts -> urgency = 20
        res4 = calculate_priority_score(0.5, 100, 1000, 5, "Escalated")
        factors4 = json.loads(res4["priority_factors"])
        self.assertEqual(factors4["urgency_score"], 20)

    def test_score_clamp(self):
        # 9. Verify final score never goes below 0 or above 100
        res_high = calculate_priority_score(1.5, 2000, 1000, 15, "Escalated")
        self.assertLessEqual(res_high["priority_score"], 100)
        
        res_low = calculate_priority_score(-0.5, -100, 1000, -5, "Pending")
        self.assertGreaterEqual(res_low["priority_score"], 0)

    def test_tier_boundaries(self):
        # 10. Verify tier boundaries
        # 39 -> LOW
        self.assertEqual(calculate_priority_score(39/50.0, 0, 1000, 0, "Pending")["priority_tier"], "LOW")
        # 40 -> MEDIUM
        self.assertEqual(calculate_priority_score(40/50.0, 0, 1000, 0, "Pending")["priority_tier"], "MEDIUM")
        # 59 -> MEDIUM
        self.assertEqual(calculate_priority_score(1.0, 300, 1000, 0, "Pending")["priority_tier"], "MEDIUM")  # 50 + 9
        # 60 -> HIGH
        self.assertEqual(calculate_priority_score(1.0, 333.333, 1000, 0, "Pending")["priority_tier"], "HIGH") # 50 + 10
        # 79 -> HIGH
        self.assertEqual(calculate_priority_score(1.0, 966.666, 1000, 0, "Pending")["priority_tier"], "HIGH") # 50 + 29
        # 80 -> CRITICAL
        self.assertEqual(calculate_priority_score(1.0, 1000, 1000, 0, "Pending")["priority_tier"], "CRITICAL") # 50 + 30
        # 100 -> CRITICAL
        self.assertEqual(calculate_priority_score(1.0, 1000, 1000, 5, "Escalated")["priority_tier"], "CRITICAL")

    def test_json_factors(self):
        # 11. Verify priority_factors contains valid JSON
        res = calculate_priority_score(0.5, 500, 1000, 1, "Pending")
        try:
            json_obj = json.loads(res["priority_factors"])
            self.assertIn("risk_score", json_obj)
        except json.JSONDecodeError:
            self.fail("priority_factors is not valid JSON")

    def test_update_active_case_analytics(self):
        # 12. Verify an existing active case's state is protected
        case = RecoveryCase(
            attempt_count=3,
            amount_recovered=4000.0,
            ai_recommended_action="Send payment reminder",
            ai_reasoning="Customer has an outstanding balance...",
            failure_probability=0.2
        )
        
        new_analytics = {
            "failure_probability": 0.8,
            "risk_level": "HIGH",
            "priority_score": 90,
            "priority_tier": "CRITICAL",
            "priority_factors": '{"risk": 40}',
            "attempt_count": 0,  # Should NOT overwrite
            "amount_recovered": 0, # Should NOT overwrite
            "ai_recommended_action": "Something else" # Should NOT overwrite
        }
        
        updated_case = update_active_case_analytics(case, new_analytics)
        
        # Protected fields should remain the same
        self.assertEqual(updated_case.attempt_count, 3)
        self.assertEqual(updated_case.amount_recovered, 4000.0)
        self.assertEqual(updated_case.ai_recommended_action, "Send payment reminder")
        
        # Analytical fields should be updated
        self.assertEqual(updated_case.failure_probability, 0.8)
        self.assertEqual(updated_case.risk_level, "HIGH")
        self.assertEqual(updated_case.priority_score, 90)

if __name__ == '__main__':
    unittest.main()
