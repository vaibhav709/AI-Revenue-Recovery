import unittest
from fastapi.testclient import TestClient
from api.main import app, engine, Base
from sqlalchemy.orm import sessionmaker

class TestDatabaseAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def test_get_customers_returns_list(self):
        response = self.client.get("/customers")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_recovery_cases_returns_list(self):
        response = self.client.get("/recovery/cases")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_dashboard_metrics(self):
        response = self.client.get("/dashboard/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_analyzed", data)

    def test_complete_case_flow(self):
        # 1. Post a new recovery case so we have a customer and case in DB
        # Wait, posting to /recovery/analyze does not insert into DB automatically in this test unless it's configured to.
        # But we can test the PUT /recovery/cases/{id}/complete endpoint directly on an existing case.
        from api.models import Customer, RecoveryCase
        from api.database import SessionLocal
        
        db = SessionLocal()
        cust = db.query(Customer).filter(Customer.customer_id==99999).first()
        if not cust:
            cust = Customer(customer_id=99999, credit_limit=100)
            db.add(cust)
            db.commit()
        db.refresh(cust)
        
        case = RecoveryCase(
            customer_id=99999, failure_probability=0.8, predicted_failure=True,
            risk_level="HIGH", priority="HIGH", strategy="ESCALATED",
            communication_channel="PHONE", follow_up_days=1, escalation_candidate=True,
            status="Pending",
            amount_at_risk=200.0
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        
        case_id = case.id
        db.close()

        # Complete the case
        res = self.client.put(f"/recovery/cases/{case_id}/outcome", json={"amount_recovered": 100, "recovery_status": "Recovered"})
        self.assertEqual(res.status_code, 200)
        
        # Verify it shows up in analytics
        res_analytics = self.client.get("/analytics/metrics")
        analytics = res_analytics.json()
        self.assertGreaterEqual(analytics["total_amount_recovered"], 100)

        # Mark as completed
        res = self.client.put(f"/recovery/cases/{case_id}/complete")
        self.assertEqual(res.status_code, 200)

        # Check default cases API excludes it (should not find case_id in the returned list)
        res = self.client.get("/recovery/cases")
        cases = res.json()
        self.assertNotIn(case_id, [c['id'] for c in cases])

        # Check explicitly fetching it by status=Completed works
        res = self.client.get("/recovery/cases?status=Completed")
        completed_cases = res.json()
        self.assertIn(case_id, [c['id'] for c in completed_cases])


    def test_outcome_validation(self):
        from api.models import Customer, RecoveryCase
        from api.database import SessionLocal
        
        db = SessionLocal()
        cust = db.query(Customer).filter(Customer.customer_id==88888).first()
        if not cust:
            cust = Customer(customer_id=88888, credit_limit=100)
            db.add(cust)
            db.commit()
            
        case = RecoveryCase(
            customer_id=88888, failure_probability=0.8, predicted_failure=True,
            risk_level="HIGH", priority="HIGH", strategy="ESCALATED",
            communication_channel="PHONE", follow_up_days=1, escalation_candidate=True,
            status="Pending", amount_at_risk=1000.0, amount_recovered=0.0
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        case_id = case.id
        db.close()

        # 1. Negative amount_recovered -> rejected
        res = self.client.put(f"/recovery/cases/{case_id}/outcome", json={"amount_recovered": -50, "recovery_status": "Recovered"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot be negative", res.json()["detail"])

        # 2. amount_recovered > amount_at_risk -> rejected
        res = self.client.put(f"/recovery/cases/{case_id}/outcome", json={"amount_recovered": 1500, "recovery_status": "Recovered"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot exceed", res.json()["detail"])

        # 3. Invalid recovery_status -> rejected
        res = self.client.put(f"/recovery/cases/{case_id}/outcome", json={"amount_recovered": 100, "recovery_status": "Arbitrary"})
        self.assertEqual(res.status_code, 422)

        # 4. Valid partially recovered outcome -> accepted
        res = self.client.put(f"/recovery/cases/{case_id}/outcome", json={"amount_recovered": 500, "recovery_status": "Partially Recovered"})
        self.assertEqual(res.status_code, 200)

        # 5. Valid recovered outcome -> accepted
        res = self.client.put(f"/recovery/cases/{case_id}/outcome", json={"amount_recovered": 1000, "recovery_status": "Recovered"})
        self.assertEqual(res.status_code, 200)

        # 6. Analytics calculation remains correct
        res_analytics = self.client.get("/analytics/metrics")
        analytics = res_analytics.json()
        self.assertGreaterEqual(analytics["total_amount_recovered"], 1000)
        self.assertTrue(analytics["recovery_rate"] <= 100.0)

if __name__ == "__main__":
    unittest.main()
