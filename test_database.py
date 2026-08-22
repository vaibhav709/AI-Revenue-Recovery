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
        cust = Customer(customer_id=99999, credit_limit=100)
        db.add(cust)
        db.commit()
        db.refresh(cust)
        
        case = RecoveryCase(
            customer_id=99999, failure_probability=0.8, predicted_failure=True,
            risk_level="HIGH", priority="HIGH", strategy="ESCALATED",
            communication_channel="PHONE", follow_up_days=1, escalation_candidate=True,
            status="Pending"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        
        case_id = case.id
        db.close()

        # Complete the case
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

if __name__ == "__main__":
    unittest.main()
