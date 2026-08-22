import unittest
from fastapi.testclient import TestClient
from api.main import app, get_db
from api.models import RecoveryCase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestCompleteCase(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        case = RecoveryCase(
            customer_id=1,
            failure_probability=0.8,
            predicted_failure=True,
            risk_level="HIGH",
            priority="HIGH",
            strategy="ESCALATED",
            communication_channel="PHONE",
            follow_up_days=1,
            escalation_candidate=True,
            status="Pending"
        )
        db.add(case)
        db.commit()
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)

    def test_complete_case(self):
        # Initial cases should not include completed in active view
        res = client.get("/recovery/cases")
        self.assertEqual(len(res.json()), 1)

        # Mark complete
        res = client.put("/recovery/cases/1/complete")
        self.assertEqual(res.status_code, 200)

        # Cases should now exclude the completed one by default
        res = client.get("/recovery/cases")
        self.assertEqual(len(res.json()), 0)

        # Can still fetch it directly
        res = client.get("/recovery/cases/1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["case"]["status"], "Completed")
        
        # Can fetch it with status filter
        res = client.get("/recovery/cases?status=Completed")
        self.assertEqual(len(res.json()), 1)

if __name__ == "__main__":
    unittest.main()
